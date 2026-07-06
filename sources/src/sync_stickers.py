#!/usr/bin/env python3
"""clean PDF에 수동으로 붙인 스티커(Stamp 주석)를 웹 텍스트판 배지로 동기화.

사용:
    uv run --with pypdf --with pdfminer.six python3 src/sync_stickers.py            # 전체 주차 리포트만
    uv run --with pypdf --with pdfminer.six python3 src/sync_stickers.py --apply    # md에 배지 반영
    ... --week 2026-06-18_06-25 [--apply]                                           # 특정 주차만

원리:
- 스탬프 rect 비율로 스티커 종류 판별 (claude≈4.7 가로형 / editors≈0.63 세로형 / s7c≈1.17 정방형)
- pdfminer로 페이지 텍스트 라인 bbox 추출 → md 헤드라인과 대조해 기사 앵커 좌표 확보
- 스탬프 중심이 속한 (컬럼, 헤드라인 아래 구간)의 기사로 귀속
- md의 <!-- badge:N --> 자리표시를 <img class="badge">로 치환
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

BADGE_IMG = {
    "claude": '<img src="../assets/badges/claude-pick.png" class="badge" alt="Claude\'s Pick">',
    "editors": '<img src="../assets/badges/editors-pick.png" class="badge" alt="Editor\'s Pick">',
    "s7c": '<img src="../assets/badges/s7c-pick.png" class="badge" alt="S7C Pick">',
}


# 스탬프 XObject md5 앞 10자리 → 종류 (PDF에 붙일 때 동일 원본이 재사용됨)
HASH_KIND = {
    "6e76f686b2": "editors",  # Editor's Pick (일반)
    "60e6888776": "editors",  # Editor's Pick (고해상)
    "4ee11a5924": "s7c",      # Recommended for Searchdoc
    "b56fd2bf9a": "claude",   # Claude Pick (일반)
    "c4da362d60": "claude",   # Claude Pick (고해상)
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


def stamps_of(pdf: Path) -> list[tuple[int, float, float, str]]:
    """(page_idx, cx, cy, kind) — 종류 판별된 스탬프만."""
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
            out.append((i, (x0 + x1) / 2, (y0 + y1) / 2, kind))
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
    """스탬프 → 기사번호. 반환: {n: set(kinds)}, skipped 수."""
    by_page: dict[int, list] = {}
    for n, (p, x0, y_top) in anchors.items():
        by_page.setdefault(p, []).append((n, x0, y_top))
    result: dict[int, list] = {}
    skipped = 0
    for p, cx, cy, kind in stamps:
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
            result.setdefault(best[1], []).append(kind)  # 중복 스티커 보존
        else:
            skipped += 1
    return result, skipped


BADGE_STRIP = re.compile(r'\s*(?:<!-- badge:\d+ -->|<img src="(?:\.\./|/)assets/badges/[^"]*"[^>]*>)')
HEADLINE_RE = re.compile(r"^### ")


BADGE_LINE_RE = re.compile(r'^(?:<!-- badge:\d+ -->|<div class="badges">.*</div>)\s*$')


def apply_md(week: str, mapping: dict[int, list]) -> int:
    """헤드라인은 깨끗하게 유지, 배지는 바로 다음 줄의 <div class="badges">에 부착. 멱등."""
    p = OUT / week / "index.md"
    lines = p.read_text().splitlines()
    out: list[str] = []
    applied = 0
    i = 0
    counter = 0
    while i < len(lines):
        line = lines[i]
        m = HEADLINE_RE.match(line)
        if not m:
            out.append(line)
            i += 1
            continue
        counter += 1
        n = counter
        out.append(BADGE_STRIP.sub("", line).rstrip())  # 헤드라인 정리 (인라인 배지 제거)
        # 헤드라인 뒤 기존 배지/자리표시 줄 제거 (빈 줄 하나 건너뛰며 탐색)
        j = i + 1
        pending_blank = False
        if j < len(lines) and lines[j].strip() == "":
            pending_blank = True
            j += 1
        if j < len(lines) and BADGE_LINE_RE.match(lines[j].strip()):
            j += 1  # 기존 배지 줄 소비
        else:
            j = i + 1  # 배지 줄 없음 — 원래 위치로
            pending_blank = False
        # 새 배지 줄 삽입
        out.append("")
        kinds = mapping.get(n)
        if kinds:
            imgs = " ".join(BADGE_IMG[k] for k in sorted(kinds))
            out.append(f'<div class="badges">{imgs}</div>')
            applied += 1
        else:
            out.append(f"<!-- badge:{n} -->")
        i = j
    p.write_text("\n".join(out) + "\n")
    return applied


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week")
    ap.add_argument("--apply", action="store_true")
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
        tmap = dict(titles)
        summary = ", ".join(f"{n}({'+'.join(sorted(ks))})" for n, ks in sorted(mapping.items()))
        print(f"{week}: 스탬프 {len(stamps)}개 → 기사 {len(mapping)}건 매핑 [{summary}] / 미귀속 {skipped}"
              f" / 앵커 {len(anchors)}/{len(titles)}")
        if args.apply:
            n_applied = apply_md(week, mapping)
            print(f"  ↳ md 반영 {n_applied}건")


if __name__ == "__main__":
    main()
