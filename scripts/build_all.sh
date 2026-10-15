#!/usr/bin/env bash
# Собирает все страницы сайта из исходников:
#   src/finance/hub.html + make_hub.py      → index.html, artem.html, nastya.html, nastya-ucheba.html (+ замок для Артема)
#   src/index.src.html + make_ucheba.py     → ucheba.html
#   src/finance/content/*.md + шаблон       → finance.html
#   src/english/lessons|ref/*.md + шаблон   → english.html (курс английского)
set -e
cd "$(git rev-parse --show-toplevel)"
python3 src/finance/make_hub.py
python3 src/finance/make_ucheba.py src/index.src.html ucheba.html
python3 src/finance/build_finance.py src/finance/content src/marked.min.js finance.html
python3 src/english/build_english.py
python3 src/finance/make_search.py
