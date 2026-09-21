#!/bin/zsh
# THE WEEKLY DAEMON 로컬 환경 기동
#   배지 서버(8099) + Quartz 미리보기(내부 8082, 자동 리빌드) + AI 검색 프록시(8081 — 8082 앞단, HTML에 패널 스크립트 주입)
#   브라우저는 http://localhost:8081 하나만 연다. AI 서버 로그: /tmp/ai_search_server.log
#   예전처럼 AI 없이(Quartz가 직접 8081): AI_SEARCH=0 src/serve.sh
#   AI 검색은 로컬 전용 — 서버는 127.0.0.1에만 바인딩, 사이트 소스·publish.sh·prod에는 관여하지 않는다.
cd "$(dirname "$0")/.."
# 재실행해도 되게: 이전에 띄운 같은 서버들을 먼저 정리 (패턴은 이 스크립트의 argv에 없으므로 자기 자신은 안 죽음)
pkill -f "src/badge_server.py" 2>/dev/null
pkill -f "quartz build --serve" 2>/dev/null
pkill -f "src/ai_search_server.py" 2>/dev/null
sleep 1
(uv run --with pypdf --with pillow --with pdfminer.six python3 src/badge_server.py &)

if [[ "${AI_SEARCH:-1}" == "0" ]]; then
  cd site && exec npx quartz build --serve --port 8081
fi

(uv run src/ai_search_server.py --port 8081 --upstream http://127.0.0.1:8082 > /tmp/ai_search_server.log 2>&1 &)
trap 'pkill -f "src/ai_search_server.py" 2>/dev/null' EXIT INT TERM
echo "AI 검색 프록시: http://localhost:8081  (Quartz 내부 :8082 · 로그 /tmp/ai_search_server.log)"
cd site && npx quartz build --serve --port 8082
