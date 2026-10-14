#!/usr/bin/env node
/* Геометрия стран для карты «Мир» (finance.html#world) → world/countries.json (TopoJSON).
   Источник — Natural Earth 1:50m из npm-пакета world-atlas, коды и русские названия — i18n-iso-countries.
   Как пересобрать (из корня репозитория; пакеты ставятся во временную папку и в репо не попадают):
     d=$(mktemp -d) && npm i --prefix "$d" --no-save world-atlas@2 topojson-client@3 topojson-simplify@3 i18n-iso-countries@7 d3-geo@3
     NODE_PATH="$d/node_modules" node scripts/make_world_geo.js world/countries.json
   Там же лежат vendor/d3.min.js (d3@7, dist/d3.min.js) и vendor/topojson-client.min.js (topojson-client@3, dist/…min.js) — копии из тех же пакетов.
   Размер результата ~250–300 КБ; регулируется SIMPLIFY_Q (доля «веса» точек, которые выбрасываем) и QUANT.
   Островные государства, от которых после упрощения не осталось контура (Мальдивы, Науру…), сохраняются точкой (Point) в центре —
   карта рисует их кружком, чтобы по ним можно было нажать. */
const fs = require('fs');
const out = process.argv[2] || 'world/countries.json';
const topo = JSON.parse(JSON.stringify(require('world-atlas/countries-50m.json')));
const simp = require('topojson-simplify');
const iso = require('i18n-iso-countries');
const client = require('topojson-client');
const d3 = require('d3-geo');
iso.registerLocale(require('i18n-iso-countries/langs/ru.json'));

const SIMPLIFY_Q = 0.42, QUANT = 1e4;
// короткие привычные названия вместо официальных
const RU = {
  RUS: 'Россия', CHN: 'Китай', KOR: 'Южная Корея', PRK: 'КНДР', COD: 'ДР Конго', COG: 'Конго', PSE: 'Палестина',
  ESH: 'Западная Сахара', SHN: 'О-в Святой Елены', SGS: 'Южная Георгия', IOT: 'Брит. терр. в Индийском океане',
  VGB: 'Брит. Виргинские о-ва', VIR: 'Виргинские о-ва (США)', ATF: 'Французские Южные терр.', HMD: 'О-ва Херд и Макдональд',
  MNP: 'Сев. Марианские о-ва', TKM: 'Туркменистан', MDA: 'Молдова', SYC: 'Сейшелы', MHL: 'Маршалловы о-ва',
  SLB: 'Соломоновы о-ва', CYM: 'Каймановы о-ва', FLK: 'Фолклендские о-ва', PCN: 'О-ва Питкэрн', TCA: 'Теркс и Кайкос',
  ALA: 'Аландские о-ва', FRO: 'Фарерские о-ва', VCT: 'Сент-Винсент и Гренадины', STP: 'Сан-Томе и Принсипи',
  NFK: 'О-в Норфолк', IMN: 'О-в Мэн', COK: 'О-ва Кука', USA: 'США', GBR: 'Великобритания', ARE: 'ОАЭ', ZAF: 'ЮАР', CAF: 'ЦАР',
  CIV: "Кот-д'Ивуар", DOM: 'Доминиканская Респ.', BIH: 'Босния и Герцеговина', TLS: 'Восточный Тимор'
};
const NOISO = { 'Somaliland': 'Сомалиленд', 'Kosovo': 'Косово', 'N. Cyprus': 'Северный Кипр' };   // без кода ISO — без данных
const DROP = new Set(['010', 'Siachen Glacier', 'Indian Ocean Ter.']);                               // Антарктида и мелочь

const geoms = [], byIso = {};
for (const g of topo.objects.countries.geometries) {
  if (DROP.has(g.id) || DROP.has(g.properties.name)) continue;
  const a3 = g.id ? iso.numericToAlpha3(g.id) : null;
  if (!a3 && !NOISO[g.properties.name]) continue;
  const polys = g.type === 'Polygon' ? [g.arcs] : g.arcs;
  if (a3 && byIso[a3]) { byIso[a3].arcs = byIso[a3].arcs.concat(polys); continue; }   // Австралия + о-ва Ашмор и Картье
  const ng = { type: 'MultiPolygon', arcs: polys, properties: { iso3: a3 || '', name: a3 ? (RU[a3] || iso.getName(a3, 'ru')) : NOISO[g.properties.name] } };
  if (a3) { ng.id = a3; byIso[a3] = ng; }
  geoms.push(ng);
}
for (const g of geoms) if (g.arcs.length === 1) { g.type = 'Polygon'; g.arcs = g.arcs[0]; }
topo.objects = { countries: { type: 'GeometryCollection', geometries: geoms } };

const cen = {};   // центр каждой страны — по исходной (не упрощённой) геометрии
for (const g of geoms) if (g.id) cen[g.id] = d3.geoCentroid(client.feature(topo, g));

let t = simp.presimplify(topo, simp.sphericalTriangleArea);
t = simp.simplify(t, simp.quantile(t, SIMPLIFY_Q));
t = simp.filter(t, simp.filterWeight(t, 1e-6, simp.sphericalRingArea));   // выкинуть совсем крошечные островки
const left = new Set(t.objects.countries.geometries.map(g => g.id));
for (const g of geoms) if (g.id && !left.has(g.id)) {
  const c = cen[g.id].map(v => Math.round(v * 100) / 100);
  t.objects.countries.geometries.push({ type: 'Point', coordinates: c, id: g.id, properties: g.properties });
}
t = client.quantize(t, QUANT);   // меньше цифр в координатах
fs.writeFileSync(out, JSON.stringify(t));
console.log(out, t.objects.countries.geometries.length, 'стран (из них точкой:', t.objects.countries.geometries.filter(g => g.type === 'Point').length + '),', fs.statSync(out).size, 'байт');
