#!/usr/bin/env python3
"""clean PDF에 수동으로 붙인 스티커(Stamp 주석)를 웹 텍스트판 배지로 동기화.

사용:
    uv run --with pypdf --with pdfminer.six python3 src/sync_stickers.py            # 전체 주차 리포트만
    uv run --with pypdf --with pdfminer.six python3 src/sync_stickers.py --apply    # md에 배지 반영
    ... --week 2026-06-18_06-25 [--apply]                                           # 특정 주차만

원리:
- 스탬프 종류는 **appearance XObject의 md5 앞 10자리**로 판별한다 (HASH_KIND).
  (예전 주석에 'rect 비율로 판별'이라 적혀 있었으나 실제 구현과 다른 낡은 설명이었다.
   비율 판별은 새 로고 도장 5종이 모두 정사각이라 애초에 성립하지 않는다.)
- pdfminer로 페이지 텍스트 라인 bbox 추출 → md 헤드라인과 대조해 기사 앵커 좌표 확보
- 스탬프 중심이 속한 (컬럼, 헤드라인 아래 구간)의 기사로 귀속
- md의 <!-- badge:N --> 자리표시를 아이브로우 줄로 치환
"""
import argparse
import re
import unicodedata
from pathlib import Path

from pypdf import PdfReader
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTTextLine

PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "newspaper"
OUTPUT = PROJECT / "output"

# 스탬프 XObject md5 앞 10자리 → 종류 (PDF에 붙일 때 동일 원본이 재사용됨)
# ⚠️ 종류만 담는다. 등급(기본/강조)은 아래 HASH_LEVEL 에서 따로 본다.
HASH_KIND = {
    # 옛 원형 도장 (Vol.1~18)
    "6e76f686b2": "editors",  # Editor's Pick (일반)
    "60e6888776": "editors",  # Editor's Pick (고해상)
    "4ee11a5924": "s7c",      # Recommended for Searchdoc
    "b56fd2bf9a": "claude",   # Claude Pick (일반)
    "c4da362d60": "claude",   # Claude Pick (고해상)
    # 새 정사각 로고 도장 (Vol.19~) — src/migrate_pdf_stamps.py 가 출력한 값
    "cebb034d9b": "claude",   # logo-claude
    "ac6a03aa9a": "editors",  # logo-editors
    "1ce46681a5": "editors",  # logo-editors-key
    "a4df991731": "s7c",      # logo-s7c
    "2835ec734f": "s7c",      # logo-s7c-key
}

# 강조 등급 해시 — 개수 반복이 아니라 에셋 색 변형으로 등급을 표현하므로
# 되읽을 때도 해시로 등급을 알아야 한다.
HASH_LEVEL = {
    "1ce46681a5": "key",      # logo-editors-key
    "2835ec734f": "key",      # logo-s7c-key
}


def classify(annot) -> str | None:
    """스탬프 appearance 이미지 해시로 종류 판별. 미지의 스탬프는 None."""
    import hashlib
    try:
        ap = annot["/AP"]["/N"].get_object()
        xo = ap.get("/Resources", {}).get("/XObject", {})
        for _, v in xo.items():
            h = hashlib.md5(v.get_object().get_data()).hexdigest()[:10]
            return HASH_KIND.get(h)
    except Exception:
        return None
    return None


def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    return re.sub(r"[\s ]+", "", s)


def md_headlines(week: str) -> list[tuple[int, str]]:
    """md에서 (순서번호, 제목) 추출 — 기사(h3)의 문서 내 등장 순서가 곧 번호."""
    text = (OUT / week / "index.md").read_text()
    out = []
    for i, m in enumerate(re.finditer(r"^### (.+?)(?:\s*(?:<!--|<img).*)?$", text, re.M), 1):
        out.append((i, m.group(1).strip()))
    return out


def stamp_level(annot) -> str:
    """appearance XObject 해시로 등급 판별. 강조본 해시가 아니면 기본."""
    import hashlib
    try:
        xo = annot["/AP"]["/N"].get_object().get("/Resources", {}).get("/XObject", {})
        for _, v in xo.items():
            return HASH_LEVEL.get(hashlib.md5(v.get_object().get_data()).hexdigest()[:10], "base")
    except Exception:
        pass
    return "base"


def stamps_of(pdf: Path) -> list[tuple[int, float, float, str, str]]:
    """(page_idx, cx, cy, kind, level) — 종류 판별된 스탬프만."""
    r = PdfReader(pdf)
    out = []
    for i, page in enumerate(r.pages):
        for a in page.get("/Annots") or []:
            o = a.get_object()
            if str(o.get("/Subtype")) != "/Stamp":
                continue
            kind = classify(o)
            if not kind:
                continue
            x0, y0, x1, y1 = (float(v) for v in o["/Rect"])
            out.append((i, (x0 + x1) / 2, (y0 + y1) / 2, kind, stamp_level(o)))
    return out


def pdf_path(week: str) -> Path | None:
    """주차 폴더(+_release/_v2 변형) 안 clean PDF 중 스탬프가 가장 많은 것."""
    cands = []
    for d in [OUTPUT / week, OUTPUT / f"{week}_release", OUTPUT / f"{week}_v2"]:
        if d.is_dir():
            cands.extend(d.glob("*_clean.pdf"))
    if not cands:
        return None
    return max(cands, key=lambda p: len(stamps_of(p)))


def headline_anchors(pdf: Path, titles: list[tuple[int, str]]):
    """pdfminer로 각 기사 헤드라인의 (page, x0, y_top) 좌표를 찾는다."""
    want = {norm(t)[:12]: n for n, t in titles if len(norm(t)) >= 6}
    anchors = {}  # n -> (page, x0, y_top)
    for pidx, layout in enumerate(extract_pages(str(pdf))):
        for el in layout:
            if not isinstance(el, LTTextContainer):
                continue
            for line in el:
                if not isinstance(line, LTTextLine):
                    continue
                key = norm(line.get_text())[:12]
                if len(key) < 6:
                    continue
                for wk, n in want.items():
                    if n in anchors:
                        continue
                    if key.startswith(wk[: len(key)]) and len(key) >= min(8, len(wk)):
                        anchors[n] = (pidx, line.x0, line.y1)
    return anchors


def assign(stamps, anchors, mid_x=297.6):
    """스탬프 → 기사번호. 반환: {n: {kind: level}}, skipped 수.

    옛 방식은 같은 종류를 반복해 중요도를 표현했으므로 리스트에 중복을 보존했다.
    이제는 등급을 에셋 색 변형으로 표현하니 종류당 하나만 남기고, 같은 종류가
    여러 개면 강조가 하나라도 있으면 강조로 본다 (옛 PDF와의 호환).
    """
    by_page: dict[int, list] = {}
    for n, (p, x0, y_top) in anchors.items():
        by_page.setdefault(p, []).append((n, x0, y_top))
    result: dict[int, dict[str, str]] = {}
    skipped = 0
    repeats: dict[tuple[int, str], int] = {}
    for p, cx, cy, kind, level in stamps:
        cands = by_page.get(p, [])
        col = "L" if cx < mid_x else "R"
        best = None
        for n, x0, y_top in cands:
            hcol = "L" if x0 < mid_x else "R"
            # 전폭 톱기사(해당 페이지에서 가장 위 & 왼쪽 시작)는 양 컬럼 모두 허용
            fullwidth = x0 < mid_x and y_top == max(y for _, _, y in cands)
            if hcol != col and not fullwidth:
                continue
            if y_top + 30 >= cy:  # 헤드라인(약간 위 포함)보다 아래에 있는 스탬프
                d = y_top - cy
                if best is None or d < best[0]:
                    best = (d, n)
        if best:
            n = best[1]
            slot = result.setdefault(n, {})
            repeats[(n, kind)] = repeats.get((n, kind), 0) + 1
            # 옛 PDF 호환: 같은 종류가 3개 이상 반복이면 강조로 승격
            promote = repeats[(n, kind)] >= 3
            if slot.get(kind) != "key":
                slot[kind] = "key" if (level == "key" or promote) else "base"
        else:
            skipped += 1
    return result, skipped


BADGE_STRIP = re.compile(r'\s*(?:<!-- badge:\d+ -->|<img src="(?:\.\./|/)assets/badges/[^"]*"[^>]*>)')
HEADLINE_RE = re.compile(r"^### ")


EYEBROW_LINE_RE = re.compile(r'^(?:<!-- badge:\d+ -->|<div class="(?:eyebrow|badges)">.*</div>)\s*$')

KINDS_ORDER = ("claude", "editors", "s7c")
HAS_KEY = {"claude": False, "editors": True, "s7c": True}
ALT = {"claude": "Claude's Pick", "editors": "Editor's Pick",
       "s7c": "Recommended for searchdoc"}


def eyebrow_html(picks: dict[str, str]) -> str:
    """{kind: level} → 아이브로우 줄. 가로 pill과 정사각 로고를 둘 다 심는다
    (좁은 컬럼에서 CSS 컨테이너 쿼리가 정사각으로 교체)."""
    parts = []
    for k in KINDS_ORDER:
        lv = picks.get(k)
        if lv is None:
            continue
        sfx = "-key" if (lv == "key" and HAS_KEY[k]) else ""
        key_cls = " is-key" if sfx else ""
        alt = ALT[k] + (" (강조)" if sfx else "")
        parts.append(f'<img src="../assets/badges/pick-{k}{sfx}.png" '
                     f'class="pick pick-wide {k}{key_cls}" alt="{alt}">')
        parts.append(f'<img src="../assets/badges/logo-{k}{sfx}.png" '
                     f'class="pick pick-sq {k}{key_cls}" alt="{alt}">')
    return '<div class="eyebrow">' + " ".join(parts) + "</div>"


def apply_md(week: str, mapping: dict[int, dict[str, str]]) -> int:
    """아이브로우 줄을 헤드라인 **위**에 쓴다. 멱등.

    ⚠️ '### ' 바로 위는 반드시 빈 줄이어야 한다 — CommonMark HTML 블록은 빈 줄에서만
       끝나므로 빈 줄이 없으면 헤드라인이 raw 텍스트로 흡수돼 h3·앵커·TOC가 사라진다.
    """
    p = OUT / week / "index.md"
    lines = p.read_text().splitlines()
    out: list[str] = []
    applied = 0
    counter = 0
    for i, line in enumerate(lines):
        if EYEBROW_LINE_RE.match(line.strip()):
            continue                      # 기존 아이브로우/자리표시 줄은 버리고 새로 쓴다
        if not HEADLINE_RE.match(line):
            out.append(line)
            continue
        counter += 1
        n = counter
        while out and not out[-1].strip():   # 헤드라인 앞 빈 줄 정리
            out.pop()
        out.append("")
        picks = mapping.get(n)
        if picks:
            out.append(eyebrow_html(picks))
            applied += 1
        else:
            out.append(f"<!-- badge:{n} -->")
        out.append("")                       # ⚠️ 필수
        out.append(BADGE_STRIP.sub("", line).rstrip())   # 헤드라인 (인라인 배지 제거)
    text = "\n".join(out) + "\n"
    # 자체 검증: 헤드라인이 흡수될 구조면 쓰지 않는다
    ls = text.splitlines()
    bad = [k + 1 for k, l in enumerate(ls)
           if l.startswith("### ") and (k == 0 or ls[k - 1].strip() != "")]
    if bad:
        raise SystemExit(f"구조 오류 — '### ' 위 빈 줄 누락 {bad[:5]} · 쓰지 않았다")
    p.write_text(text)
    return applied


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="md의 픽이 줄어드는 반영도 강행 (기본은 거부)")
    args = ap.parse_args()

    weeks = [args.week] if args.week else sorted(
        d.name for d in OUT.iterdir() if d.is_dir() and d.name[:4].isdigit()
    )
    for week in weeks:
        pdf = pdf_path(week)
        if not pdf:
            print(f"{week}: PDF 없음 — 스킵")
            continue
        titles = md_headlines(week)
        stamps = stamps_of(pdf)
        if not stamps:
            print(f"{week}: 스탬프 없음")
            continue
        anchors = headline_anchors(pdf, titles)
        mapping, skipped = assign(stamps, anchors)
        summary = ", ".join(
            f"{n}(" + "+".join(f"{k}{'!' if v == 'key' else ''}" for k, v in sorted(ks.items())) + ")"
            for n, ks in sorted(mapping.items()))
        print(f"{week}: 스탬프 {len(stamps)}개 → 기사 {len(mapping)}건 매핑 [{summary}] / 미귀속 {skipped}"
              f" / 앵커 {len(anchors)}/{len(titles)}   (! = 강조)")

        # 안전장치: PDF가 부분적으로만 스탬프돼 있으면 반영이 md의 픽을 지운다.
        # 픽 관리를 웹(badge_server)에서 하게 된 뒤로는 md가 더 최신인 경우가 많다.
        cur = 0
        md_lines = (OUT / week / "index.md").read_text().splitlines()
        for line in md_lines:
            if '<div class="eyebrow">' in line or '<div class="badges">' in line:
                cur += len(re.findall(r"badges/(?:pick|logo|claude|editors|s7c)", line))
        new_cnt = sum(len(v) for v in mapping.values())
        if args.apply and cur and new_cnt < cur and not args.force:
            print(f"  ⚠️ 거부: 반영하면 픽이 줄어든다 (md 참조 {cur} → 새 매핑 {new_cnt}). "
                  f"PDF가 md보다 오래됐을 수 있다. 정말 덮으려면 --force")
            continue
        if args.apply:
            n_applied = apply_md(week, mapping)
            print(f"  ↳ md 반영 {n_applied}건")


if __name__ == "__main__":
    main()
