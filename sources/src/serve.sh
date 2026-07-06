#!/bin/zsh
# THE WEEKLY DAEMON 로컬 환경 기동: 배지 서버(8099) + Quartz 사이트(8081)
cd "$(dirname "$0")/.."
(uv run --with pypdf --with pillow --with pdfminer.six python3 src/badge_server.py &)
cd site && npx quartz build --serve --port 8081
