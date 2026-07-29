#!/bin/bash
# Export data.json and push it to the GitHub repo so the public Pages site
# reflects this Mac's live monitoring. Throttled so we don't exceed GitHub
# Pages' ~10-builds/hour limit (default: at most once every 7 minutes).
#
# Requires: this folder is a clone of your GitHub repo, `git push` already works
# from here (credentials cached), and docs/index.html + docs/.nojekyll exist.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

MIN_INTERVAL="${PUBLISH_MIN_SECONDS:-420}"   # 7 min between pushes
STAMP="$DIR/.last_publish"
NOW="$(date +%s)"

# Skip if we pushed too recently (data is still recorded locally either way).
if [ -f "$STAMP" ] && [ $((NOW - $(cat "$STAMP" 2>/dev/null || echo 0))) -lt "$MIN_INTERVAL" ]; then
  echo "$(date -u +%FT%TZ) throttled (last push < ${MIN_INTERVAL}s ago)"
  exit 0
fi

set -a; [ -f "$DIR/.env" ] && . "$DIR/.env"; set +a
export DB_PATH="$DIR/pickup_history.db"

python3 export_json.py

if [ -n "$(git status --porcelain docs/data.json)" ]; then
  git add docs/data.json
  git commit -m "live data $(date -u +%FT%TZ)" -q
  git pull --rebase --autostash -q || true
  if git push -q; then
    echo "$NOW" > "$STAMP"
    echo "$(date -u +%FT%TZ) pushed data.json"
  else
    echo "$(date -u +%FT%TZ) push failed (check git auth)"
  fi
else
  echo "$(date -u +%FT%TZ) no data.json change"
fi
