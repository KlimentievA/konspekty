#!/usr/bin/env python3
"""Скачивает расписание группы с hse.ru и сохраняет нужные пары в schedule.json.
Запускается GitHub Actions по расписанию (см. .github/workflows/schedule.yml)."""
import datetime, html, json, os, re, sys, urllib.request

GROUP = "48037"
URL = ("https://www.hse.ru/ba/dlawyer/timetable?fromdate={a}&todate={b}&groupoid=" + GROUP +
       "&receiverType=3&timetable-courses=2&timetable-groups=" + GROUP + "&timetable-view-switcher=list")
# (часть названия дисциплины, id предмета на сайте или None)
KEEP = [("Гражданское право", "civil"), ("Конституционное право", "const"), ("Уголовное право", "crim"),
        ("Основы программирования на Python", "python"), ("Экономика", None), ("Цифровая грамотность", None)]
KINDS = (("лекц", "Лекция"), ("семин", "Семинар"), ("практ", "Практика"))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schedule.json")


DIAG = []


def fetch(a, b):
    local = os.environ.get("LOCAL_HTML")
    if local:
        return open(local, encoding="utf-8", errors="replace").read()
    req = urllib.request.Request(URL.format(a=a, b=b), headers={"User-Agent": "Mozilla/5.0 (konspekty schedule bot)", "Accept-Language": "ru"})
    with urllib.request.urlopen(req, timeout=40) as r:
        body = r.read().decode("utf-8", "replace")
        DIAG.append(f"HTTP {r.status} {r.geturl()}")
        return body


def parse(page):
    out = []
    for raw in re.findall(r'data-lesson-source="([^"]*)"', page):
        try:
            x = json.loads(html.unescape(raw))
        except ValueError:
            continue
        name = str(x.get("discipline", ""))
        hit = next((k for k in KEEP if k[0] in name), None)
        if not hit or not x.get("date") or not x.get("beginLesson"):
            continue
        kd = str(x.get("kindOfWork", "")).lower()
        kind = next((v for k, v in KINDS if k in kd), str(x.get("kindOfWork", "")))
        out.append({"d": x["date"].replace(".", "-"), "b": x["beginLesson"], "e": x["endLesson"],
                    "n": re.sub(r"\s*\((рус|анг)\)\s*$", "", name), "k": kind,
                    "r": str(x.get("auditorium", "")), "s": hit[1], "t": x.get("lecturer_title") or x.get("lecturer") or ""})
    return out


def main():
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    lessons, ok = [], 0
    for w in range(3):  # эта неделя и две следующие
        a = monday + datetime.timedelta(days=7 * w)
        b = a + datetime.timedelta(days=6)
        try:
            page = fetch(a.strftime("%Y.%m.%d"), b.strftime("%Y.%m.%d"))
            got = parse(page)
            print(f"{a}..{b}: страница {len(page)} байт, пар найдено {len(got)}")
            t = re.search(r"<title>(.*?)</title>", page, re.S)
            DIAG.append(f"{a}..{b}: {len(page)} байт; title={t.group(1).strip()[:120] if t else None}; lesson-node={page.count('lesson-node')}; lesson-source={page.count('data-lesson-source')}; пар={len(got)}")
            if not got:
                DIAG.append("начало страницы: " + re.sub(r"\s+", " ", page[:400]))
            lessons += got
            ok += 1
        except Exception as e:  # не роняем workflow
            print(f"{a}..{b}: ошибка {e!r}")
            DIAG.append(f"{a}..{b}: ОШИБКА {e!r}")
        if os.environ.get("LOCAL_HTML"):
            break
    open(os.path.join(os.path.dirname(OUT), "schedule_debug.txt"), "w", encoding="utf-8").write("\n".join(DIAG) + "\n")
    if not ok or not lessons:
        print("Не удалось получить пары — schedule.json не менялся.")
        return 0
    seen, uniq = set(), []
    for l in sorted(lessons, key=lambda l: (l["d"], l["b"], l["n"])):
        key = (l["d"], l["b"], l["n"], l["r"])
        if key not in seen:
            seen.add(key); uniq.append(l)
    try:
        old = json.load(open(OUT, encoding="utf-8")).get("list")
    except Exception:
        old = None
    if uniq == old:
        print("Без изменений.")
        return 0
    json.dump({"updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "list": uniq},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"Записано пар: {len(uniq)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
