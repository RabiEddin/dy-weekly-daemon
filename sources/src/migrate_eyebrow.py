#!/usr/bin/env python3
"""원형 도장(개수 반복) → 제목 위 가로 라벨 아이브로우(2단계) 마이그레이션.

사용:
    python3 src/migrate_eyebrow.py --week 2026-07-16_07-23            # 미리보기
    python3 src/migrate_eyebrow.py --week 2026-07-16_07-23 --apply     # 반영
    python3 src/migrate_eyebrow.py --week 2026-07-16_07-23 --revert    # 백업 복구

변환:
- 기존 `<div class="badges">` 의 종류별 반복 개수를 읽어 등급을 정한다.
  N >= KEY_THRESHOLD → 강조(-key 에셋), 그 외 → 기본.
  19호 전수 실측에서 개수가 1개(82%) 아니면 3개(13%)로 몰려 사실상 2단계였다.
- claude 는 강조 에셋이 없다 (98%가 1개 = 중요도 축 없음) → 항상 기본.
- 아이브로우 줄을 `### ` **위**로 옮긴다.

⚠️ CommonMark HTML 블록(type 6)은 빈 줄에서만 끝난다. `<div>` 바로 다음 줄에
`### `가 오면 헤드라인이 raw 텍스트로 흡수돼 h3·앵커·TOC가 전부 사라진다.
그래서 항상 `<div>` → 빈 줄 → `### ` 순서로 쓰고, verify()로 확인한다.
"""

import argparse
import re
import shutil
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
NEWS = PROJECT / "newspaper"

KEY_THRESHOLD = 3
ORDER = ["claude", "editors", "s7c"]
ALT = {
    "claude": "Claude's Pick",
    "editors": "Editor's Pick",
    "s7c": "Recommended for searchdoc",
}
HAS_KEY = {"claude": False, "editors": True, "s7c": True}   # 강조 에셋 보유 여부

IMG_KIND_RE = re.compile(r"badges/(claude|editors|s7c)-pick\.png")
BADGES_DIV_RE = re.compile(r'^<div class="badges">.*</div>\s*$')
BADGE_COMMENT_RE = re.compile(r"^<!-- badge:(\d+) -->\s*$")


def asset(prefix: str, kind: str, level: str) -> str:
    suffix = "-key" if (level == "key" and HAS_KEY[kind]) else ""
    return f"{prefix}-{kind}{suffix}.png"


def eyebrow_html(picks: dict[str, int]) -> str:
    """가로 pill과 정사각 로고를 둘 다 내보낸다.

    좁은 컬럼에서는 pill 3개(451px)가 한 줄에 안 들어간다. 실측 컬럼폭 기준으로
    288/343/382/444px 구간이 해당된다(뷰포트 801px에서 좌측 사이드바가 컬럼으로
    서면서 444px로 떨어지는 비단조 구간 포함). 정사각 로고 3개는 162px이라
    최소 컬럼에서도 126px 여유가 남는다. 전환은 CSS 컨테이너 쿼리가 담당하고,
    여기서는 두 형태를 모두 심어둔다 — 뷰포트가 아니라 컬럼 폭이 기준이라
    미디어 쿼리로는 정확히 표현할 수 없다.
    """
    parts = []
    for k in ORDER:
        if k not in picks:
            continue
        level = "key" if picks[k] >= KEY_THRESHOLD else "base"
        key_cls = " is-key" if level == "key" and HAS_KEY[k] else ""
        alt = ALT[k] + (" (강조)" if level == "key" and HAS_KEY[k] else "")
        parts.append(
            f'<img src="../assets/badges/{asset("pick", k, level)}" '
            f'class="pick pick-wide {k}{key_cls}" alt="{alt}">'
        )
        parts.append(
            f'<img src="../assets/badges/{asset("logo", k, level)}" '
            f'class="pick pick-sq {k}{key_cls}" alt="{alt}">'
        )
    return '<div class="eyebrow">' + " ".join(parts) + "</div>"


def convert(text: str) -> tuple[str, dict]:
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    n = 0
    st = {"articles": 0, "with_picks": 0, "none": 0, "key_articles": 0, "labels": 0}

    while i < len(lines):
        if not lines[i].startswith("### "):
            out.append(lines[i])
            i += 1
            continue

        n += 1
        st["articles"] += 1
        head = lines[i]

        # 헤드라인 뒤 배지 줄 찾기 (빈 줄 건너뛰고)
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        picks: dict[str, int] = {}
        after = i + 1
        if j < len(lines) and BADGES_DIV_RE.match(lines[j].strip()):
            for k in IMG_KIND_RE.findall(lines[j]):
                picks[k] = picks.get(k, 0) + 1
            after = j + 1
        elif j < len(lines) and BADGE_COMMENT_RE.match(lines[j].strip()):
            after = j + 1

        # 직전에 남은 빈 줄 정리 (아이브로우가 자체 margin을 가짐)
        while out and not out[-1].strip():
            out.pop()
        out.append("")

        if picks:
            out.append(eyebrow_html(picks))
            st["with_picks"] += 1
            st["labels"] += len(picks)
            if any(c >= KEY_THRESHOLD for c in picks.values()):
                st["key_articles"] += 1
        else:
            out.append(f"<!-- badge:{n} -->")
            st["none"] += 1

        out.append("")          # ⚠️ 필수: 여기가 없으면 h3가 안 만들어진다
        out.append(head)

        # 본문: 배지 줄 다음부터 그대로
        rest = lines[after:]
        end = 0
        while end < len(rest) and not (
            rest[end].startswith("### ") or rest[end].startswith("## ")
        ):
            end += 1
        body = rest[:end]
        while body and not body[0].strip():
            body.pop(0)
        out.append("")
        out.extend(body)
        i = after + end

    return "\n".join(out) + "\n", st


def verify(text: str) -> list[str]:
    """구조 자체 검증 — 조용히 깨지는 경우를 잡는다."""
    errs = []
    lines = text.splitlines()
    for idx, l in enumerate(lines):
        if l.startswith("### "):
            prev = lines[idx - 1] if idx else ""
            if prev.strip() != "":
                errs.append(f"{idx+1}행: '### ' 바로 위가 빈 줄이 아님 → h3 소멸 위험: {prev[:60]!r}")
        if l.strip().startswith('<div class="eyebrow">'):
            nxt = lines[idx + 1] if idx + 1 < len(lines) else ""
            if nxt.strip() != "":
                errs.append(f"{idx+1}행: 아이브로우 다음 줄이 빈 줄이 아님: {nxt[:60]!r}")
    if 'class="badges"' in text:
        errs.append("옛 배지 줄이 남아 있음")
    return errs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    a = ap.parse_args()

    md = NEWS / a.week / "index.md"
    bak = md.with_suffix(".md.bak-eyebrow")
    if not md.exists():
        raise SystemExit(f"없음: {md}")

    if a.revert:
        if not bak.exists():
            raise SystemExit(f"백업 없음: {bak}")
        shutil.copy2(bak, md)
        print(f"복구 완료: {md} ← {bak.name}")
        return

    text = md.read_text(encoding="utf-8")
    if 'class="badges"' not in text and 'class="eyebrow"' in text:
        raise SystemExit("이미 변환됨. 다시 하려면 --revert 먼저.")

    new, st = convert(text)
    errs = verify(new)

    print(f"기사 {st['articles']}건 / 라벨 {st['labels']}개")
    print(f"  아이브로우 있음 {st['with_picks']}건 (그 중 강조 포함 {st['key_articles']}건)"
          f" / 라벨없음 {st['none']}건")
    print(f"  구조 검증: {'✅ 통과' if not errs else '❌ ' + str(len(errs)) + '건'}")
    for e in errs:
        print(f"     {e}")
    if errs:
        raise SystemExit("구조 오류 — 반영하지 않았다.")

    if not a.apply:
        print("\n--- 앞부분 (dry-run) ---")
        print("\n".join(new.splitlines()[:26]))
        print("\n반영하려면 --apply")
        return

    if not bak.exists():
        shutil.copy2(md, bak)
        print(f"백업: {bak.name}")
    md.write_text(new, encoding="utf-8")
    print(f"변환 완료: {md}")


if __name__ == "__main__":
    main()
