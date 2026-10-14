#!/usr/bin/env bash
# Быстрый канал новостей: каждую минуту собирает заголовки и кладёт news-live.json в ветку data (без истории, force-push).
# Использование: scripts/live_news.sh <сколько секунд работать>. Вызывается из workflow «Автообновление данных» вместо паузы между часами.
set -u
cd "$(git rev-parse --show-toplevel)"
export GIT_AUTHOR_NAME=hub-bot GIT_AUTHOR_EMAIL=hub-bot@users.noreply.github.com GIT_COMMITTER_NAME=hub-bot GIT_COMMITTER_EMAIL=hub-bot@users.noreply.github.com
REPO_URL="https://x-access-token:${GH_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
D="${RUNNER_TEMP:-/tmp}/live_hist"
end=$(( $(date +%s) + ${1:-600} ))
rm -rf "$D"
git clone -q --depth 1 -b data "$REPO_URL" "$D" 2>/dev/null || { mkdir -p "$D"; git -C "$D" init -q -b data; }
n=0; fails=0
while [ $(( $(date +%s) + 20 )) -lt "$end" ]; do
  t0=$(date +%s)
  if timeout 100 python3 update_news_live.py "$D/news-live.json"; then
    # отправляем, если набор заголовков изменился, а без изменений — раз в 5 минут (чтобы «проверка в …» на странице не отставала)
    if [ "$(cat "$D/.changed" 2>/dev/null || echo 1)" = 1 ] || [ $(( n % 5 )) -eq 0 ]; then
      (cd "$D" && rm -f .changed.tmp && git add news-live.json && { git commit -q --amend -m "Живая лента" 2>/dev/null || git commit -q -m "Живая лента"; } && git push -q -f "$REPO_URL" HEAD:data) \
        && fails=0 || { fails=$((fails+1)); echo "::warning::живая лента не отправилась ($fails)"; }
    fi
  else
    echo "::warning::update_news_live.py завершился с ошибкой"
  fi
  n=$((n+1))
  [ $fails -lt 8 ] || { echo "слишком много ошибок отправки — выходим из быстрого цикла"; break; }
  left=$(( 60 - ($(date +%s) - t0) )); [ $left -gt 0 ] && sleep $left
done
rm -rf "$D"
