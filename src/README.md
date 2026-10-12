# Исходные данные сайта

- `data.json` — все предметы, конспекты (markdown), «О предметах», расписание и билеты в одном файле. Из него собираются варианты оформления.
- `tickets.json` — билеты: konst (113), ugol (46), grazh (133). Поля: n, q, a (краткий ответ на 2–3 минуты, markdown).
- `questions.json` — только вопросы, как в PDF.
- `marked.min.js` — парсер markdown, встроен в index.html.

Тексты конспектов и билетов живут внутри `index.html` в `<script type="application/json" id="data|sched|tickets">`.
