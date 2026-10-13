# Исходные данные сайта

Сайт открытый (пароль убран 13.10.2026). Структура:
- `index.html` — главная: выбор «Учёба» или «Финансы» (старые ссылки `/#…` перенаправляются в `ucheba.html#…`).
- `ucheba.html` — конспекты, расписание, билеты, сессия. Собирается из `src/index.src.html`:
  `python3 src/finance/make_ucheba.py src/index.src.html ucheba.html`
- `finance.html` — «Финансы»: вкладки «Обучение» (справочник) и «Рынки» (живые котировки). Собирается так:
  `python3 src/finance/build_finance.py src/finance/content src/marked.min.js finance.html`
  Тексты глав — `src/finance/content/NN_*.md` (98 — глоссарий, 99 — источники; подсказки к терминам — `src/finance/terms.py` + глоссарий) (первая строка `# Заголовок`, вторая `short: …`; формулы в блоках ```f).
  Снимок мультипликаторов — `src/finance/static_data.py` (дата в полях *_ASOF).
- `markets.json` — снимок рынков, его обновляет GitHub Action «Обновить рынки» (`update_markets.py`) каждые 3 часа.
  Живые данные страница берёт прямо из браузера: Мосбиржа (ISS), ЦБ (cbr-xml-daily.ru), CoinGecko/Binance.
- `encrypt.py` больше не используется (шифрование отключено).

Данные учёбы:
- `data.json` — все предметы, конспекты (markdown), «О предметах», расписание и билеты в одном файле.
- `tickets.json` — билеты: konst (113), ugol (46), grazh (133). Поля: n, q, a.
- `questions.json` — только вопросы, как в PDF.
- `marked.min.js` — парсер markdown.
Тексты конспектов и билетов живут внутри `index.src.html` в `<script type="application/json" id="data|sched|tickets">`.
