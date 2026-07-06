#!/bin/bash
# THE WEEKLY DAEMON 발행 — 한 방 스크립트
#   빌드(draft 제외) → PDF 경량화 → publish/ repo 커밋 + push (= GitHub Pages 발행)
# 사용: src/publish.sh            (배지 지정 + draft:false 후 실행)
set -euo pipefail

PROJECT="$(cd "$(dirname "$0")/.." && pwd)"
SITE="$PROJECT/site"
PUB="$PROJECT/publish"
DOCS="$PUB/docs"
BUILD="$SITE/public-publish"

# 0) draft 안내 (draft: true인 호는 이번 발행에서 제외됨)
drafts=$(grep -l "^draft: true$" "$PROJECT"/newspaper/*/index.md 2>/dev/null || true)
[ -n "$drafts" ] && echo "ℹ️  발행 제외(draft): $drafts"

# 1) remove-draft 켠 발행 빌드 (별도 출력 폴더 — 로컬 프리뷰 8081엔 영향 없음)
cd "$SITE"
perl -0pi -e 's/(remove-draft\n\s*enabled: )false/${1}true/' quartz.config.yaml
trap 'cd "$SITE" && perl -0pi -e "s/(remove-draft\n\s*enabled: )true/\${1}false/" quartz.config.yaml' EXIT
npx quartz build -o public-publish

# 2) 사이트 → docs/ (PDF·기사 이미지 제외 동기화, GitHub Pages가 이 폴더를 서빙)
mkdir -p "$DOCS"
rsync -a --delete --exclude='vol-*.pdf' --exclude='/20*/images/' "$BUILD/" "$DOCS/"
rm -f "$DOCS/CNAME"          # 커스텀 도메인 아님 — 있으면 Pages 설정 충돌
touch "$DOCS/.nojekyll"

# 2.5) 기사 이미지 경량화 (원본이 갱신된 것만 — 폭 1400px 상한 + 재압축, 원본 불변)
for d in "$PROJECT"/newspaper/*/images; do
  week="$(basename "$(dirname "$d")")"
  [ -d "$DOCS/$week" ] || continue   # draft 제외된 주차
  uv run --with pillow python3 "$PROJECT/src/compress_img.py" "$d" "$DOCS/$week/images"
done

# 2.6) 이미지 lazy loading 부여 (스크롤로 보일 때만 다운로드 — 빌드 HTML 후처리)
find "$DOCS" -name '*.html' -exec perl -pi -e 's/<img (?![^>]*loading=)/<img loading="lazy" /g' {} +

# 3) PDF 경량화 (원본이 갱신된 것만 — AAPL 사설키 제거 + 스탬프 dedup + 이미지 재압축)
for src in "$PROJECT"/newspaper/*/vol-*.pdf; do
  week="$(basename "$(dirname "$src")")"
  [ -d "$DOCS/$week" ] || continue   # draft 제외된 주차
  dst="$DOCS/$week/$(basename "$src")"
  if [ ! -f "$dst" ] || [ "$src" -nt "$dst" ]; then
    uv run --with pikepdf --with pillow python3 "$PROJECT/src/compress_pdf.py" "$src" "$dst" 2>/dev/null
  fi
done

# 4) 소스 백업 (디자인·스크립트·신문 md — 재해 복구용)
SRCDIR="$PUB/sources"
mkdir -p "$SRCDIR/site/toc-dist-patch/components" "$SRCDIR/src" "$SRCDIR/newspaper"
cp "$SITE/quartz.config.yaml" "$SITE/quartz/styles/custom.scss" "$SRCDIR/site/"
cp "$SITE/.quartz/plugins/table-of-contents/dist/index.js" "$SRCDIR/site/toc-dist-patch/"
cp "$SITE/.quartz/plugins/table-of-contents/dist/components/index.js" "$SRCDIR/site/toc-dist-patch/components/"
for f in render_newspaper_md.py sync_stickers.py badge_server.py compress_pdf.py compress_img.py serve.sh publish.sh; do
  cp "$PROJECT/src/$f" "$SRCDIR/src/"
done
cp "$PROJECT/newspaper/index.md" "$SRCDIR/newspaper/"
for d in "$PROJECT"/newspaper/*/; do
  w="$(basename "$d")"
  [ -f "$d/index.md" ] && mkdir -p "$SRCDIR/newspaper/$w" && cp "$d/index.md" "$SRCDIR/newspaper/$w/"
done

# 5) 커밋 + push
cd "$PUB"
git add -A
if git diff --cached --quiet; then
  echo "변경 없음 — push 생략"
else
  git commit -m "publish $(date +%F)"
  git push origin main
  # 2026-07 GitHub Pages 장애 우회: push 후 배포를 API로 직접 트리거 (자동 배포가 실패해도 이걸로 뜸)
  gh api -X POST "repos/RabiEddin/dy-weekly-daemon/pages/builds" >/dev/null 2>&1 || true
  echo "✅ 발행 완료 → https://rabieddin.github.io/dy-weekly-daemon/ (반영까지 1~2분)"
fi
