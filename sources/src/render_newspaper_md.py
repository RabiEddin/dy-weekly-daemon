#!/usr/bin/env python3
"""THE WEEKLY DAEMON — enriched JSON → Quartz용 신문 마크다운 렌더러.

사용법:
    python3 src/render_newspaper_md.py             # data/의 최신 주차 렌더
    python3 src/render_newspaper_md.py --week 2026-06-25_07-02
    python3 src/render_newspaper_md.py --all       # 전체 주차 일괄 렌더

출력: newspaper/{주차}/index.md + newspaper/{주차}/images/
- frontmatter draft: true 로 생성됨 → 배지 지정 후 draft: false 로 발행
- 배지 자리표시: 각 헤드라인 뒤 <!-- badge:N --> 주석. 배지를 붙일 때
  <img src="../assets/badges/{claude-pick|editors-pick|s7c-pick}.png" class="badge" alt="..."> 로 치환.
- 링크 정책은 clean 버전과 동일: resource_links만 노출, @handle 미노출.
"""

import argparse
import json
import re
import shutil
from datetime import date, datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data"
OUT = PROJECT / "newspaper"

SECTION_ORDER = ["AI & Research", "DevTools & Open Source", "Engineering", "Product & Industry"]
SECTION_DISPLAY = {
    "AI & Research": "AI & RESEARCH",
    "DevTools & Open Source": "DEVTOOLS & OPEN SOURCE",
    "Engineering": "ENGINEERING",
    "Product & Industry": "PRODUCT & INDUSTRY",
}

WEEK_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}$")


def link_label(url: str, max_len: int = 42) -> str:
    """링크 표시 텍스트: 스킴·www 제거 + 퍼센트 인코딩 복원(한글) + 길면 말줄임."""
    from urllib.parse import unquote
    label = re.sub(r"^https?://(www\.)?", "", url)
    label = unquote(label)
    if len(label) > max_len:
        label = label[: max_len - 1].rstrip("-_/. ") + "…"
    return label


def week_dirs() -> list[Path]:
    return sorted(p for p in DATA.iterdir() if p.is_dir() and WEEK_RE.match(p.name))


def week_end_date(week: str) -> date:
    start = datetime.strptime(week[:10], "%Y-%m-%d").date()
    end_month, end_day = map(int, week[11:].split("-"))
    end_year = start.year + 1 if end_month < start.month else start.year
    return date(end_year, end_month, end_day)


def latest_enriched(week_dir: Path) -> Path:
    files = list(week_dir.glob("enriched_*.json"))
    if not files:
        raise FileNotFoundError(f"enriched_*.json 없음: {week_dir}")
    return max(files, key=lambda p: p.stat().st_mtime)


def esc_yaml(s: str) -> str:
    return s.replace('"', '\\"')


def core_link(item: dict) -> str:
    """clean 버전 링크 정책 재현 (weekly_newspaper.py _render_links):
    threads 글이 아니면 item.url, threads 글이면 첫 resource_link."""
    url = item.get("url") or ""
    if url and "threads.com" not in url:
        return url
    rl = item.get("resource_links") or []
    if rl and rl[0].get("url"):
        return rl[0]["url"]
    return url


def featured_indices(items: list[dict]) -> list[int]:
    """1면 기사 선정 재현 (weekly_newspaper.py _select_featured):
    (1+링크수)*(1+키포인트길이//25), 이미지 있으면 ×2 — 상위 3개."""
    scored = []
    for i, it in enumerate(items):
        rl = it.get("resource_links") or []
        kp = it.get("key_points") or ""
        img = it.get("image") or ""
        has_img = bool(img) and not img.startswith("http") and Path(img).is_file()
        score = (1 + len(rl)) * (1 + len(kp) // 25)
        if has_img:
            score *= 2
        scored.append((score, i))
    scored.sort(reverse=True)
    return [i for _, i in scored[: min(3, len(scored))]]


def copy_image(item: dict, images_out: Path) -> str | None:
    src = item.get("image") or ""
    if not src:
        return None
    src_path = Path(src)
    if not src_path.is_file():
        return None
    images_out.mkdir(parents=True, exist_ok=True)
    dest = images_out / src_path.name
    if not dest.exists():
        shutil.copy2(src_path, dest)
    return f"images/{src_path.name}"


def render_item(n: int, item: dict, images_out: Path, lead: bool = False) -> str:
    lines: list[str] = []
    headline = (item.get("headline") or "(제목 없음)").strip()
    lines.append(f"### {headline}")
    lines.append("")
    lines.append(f"<!-- badge:{n} -->")
    lines.append("")

    img = copy_image(item, images_out)
    if img:
        lines.append(f"![{headline}]({img})")
        lines.append("")

    summary = (item.get("summary") or "").strip()
    if summary:
        lines.append(summary)
        lines.append("")

    key_points = (item.get("key_points") or "").strip()
    if key_points:
        lines.append(f"**핵심 포인트:** {key_points}")
        lines.append("")

    implication = (item.get("implication") or "").strip()
    if implication:
        lines.append(f"**시사점:** {implication}")
        lines.append("")

    link = core_link(item)
    if link:
        lines.append(f"🔗 [{link_label(link)}]({link})")
        lines.append("")

    category = (item.get("category") or "").strip()
    if category:
        lines.append(f"*{category}*")
        lines.append("")

    return "\n".join(lines)


def render_week(week: str, vol: int) -> Path:
    week_dir = DATA / week
    enriched = latest_enriched(week_dir)
    data = json.loads(enriched.read_text())
    items = data.get("items", [])
    date_range = data.get("date_range", week)

    out_dir = OUT / week
    out_dir.mkdir(parents=True, exist_ok=True)
    images_out = out_dir / "images"

    featured = featured_indices(items)

    end = week_end_date(week)
    fm = [
        "---",
        f'title: "Vol.{vol} ({int(week[5:7])}/{int(week[8:10])}-{int(week[11:13])}/{int(week[14:16])})"',
        f"date: {end.isoformat()}",
        "draft: true",
        "---",
        "",
        f'<div class="masthead"><div class="mast-title">THE WEEKLY DAEMON</div>'
        f'<div class="mast-meta"><span>Vol.{vol} {esc_yaml(date_range)}</span>'
        f"<span>WEEKLY TECH &amp; AI DIGEST</span>"
        f"<span>{len(items)} Articles This Week</span></div></div>",
        "",
    ]

    body: list[str] = []
    n = 0

    if featured:
        body.append("## CLAUDE'S PICK")
        body.append("")
        for rank, i in enumerate(featured):
            n += 1
            body.append(render_item(n, items[i], images_out, lead=(rank == 0)))
        body.append("")

    groups: dict[str, list[int]] = {}
    for i, it in enumerate(items):
        if i in featured:
            continue
        groups.setdefault(it.get("section") or "기타", []).append(i)

    ordered_sections = [s for s in SECTION_ORDER if s in groups] + [
        s for s in groups if s not in SECTION_ORDER
    ]
    for sec in ordered_sections:
        body.append(f"## {SECTION_DISPLAY.get(sec, sec.upper())}")
        body.append("")
        for i in groups[sec]:
            n += 1
            body.append(render_item(n, items[i], images_out))
        body.append("")


    out_md = out_dir / "index.md"
    out_md.write_text("\n".join(fm + body))
    return out_md


def copy_pdf(week: str, vol: int) -> bool:
    """output/{week}/*_clean.pdf → newspaper/{week}/vol-NN.pdf (신문 원본 PDF 발행용)."""
    outdir = PROJECT / "output" / week
    if not outdir.is_dir():
        return False
    pdfs = sorted(outdir.glob("*_clean.pdf")) or sorted(outdir.glob("*.pdf"))
    if not pdfs:
        return False
    dest = OUT / week / f"vol-{vol:02d}.pdf"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_mtime > pdfs[-1].stat().st_mtime:
        return True  # 사이트 PDF에 스탬프 등 후속 수정이 있으면 보존
    shutil.copy2(pdfs[-1], dest)
    return True


def write_landing(weeks, vol_of) -> None:
    """랜딩(newspaper/index.md) 재생성 — 최신호 위, PDF 원본이 1차 링크."""
    lines = ["---", "title: THE WEEKLY DAEMON", "---", "",
             "## ARCHIVE", ""]
    for p in reversed(weeks):
        w = p.name
        vol = vol_of[w]
        rng = f"{int(w[5:7])}/{int(w[8:10])}-{int(w[11:13])}/{int(w[14:16])}"
        pdf = OUT / w / f"vol-{vol:02d}.pdf"
        if pdf.exists():
            lines.append(f'- [**Vol.{vol}** ({rng})]({w}) · <a href="{w}/vol-{vol:02d}.pdf" target="_blank" rel="noopener">PDF</a>')
        else:
            lines.append(f"- [Vol.{vol} ({rng})]({w})")
    (OUT / "index.md").write_text("\n".join(lines) + "\n")
    print(f"✓ 랜딩 갱신: newspaper/index.md ({len(weeks)}권)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", help="주차 폴더명 (예: 2026-06-25_07-02)")
    ap.add_argument("--all", action="store_true", help="전체 주차 렌더")
    ap.add_argument("--landing-only", action="store_true",
                    help="md 재렌더 없이 전 주차 PDF 복사 + 랜딩만 재생성 (배지 보존)")
    args = ap.parse_args()

    weeks = week_dirs()
    if not weeks:
        raise SystemExit("data/에 주차 폴더가 없습니다")
    vol_of = {p.name: i + 1 for i, p in enumerate(weeks)}

    if args.landing_only:
        n = sum(copy_pdf(p.name, vol_of[p.name]) for p in weeks)
        print(f"✓ PDF 복사: {n}/{len(weeks)}권")
        write_landing(weeks, vol_of)
        return

    targets = (
        [p.name for p in weeks]
        if args.all
        else [args.week]
        if args.week
        else [weeks[-1].name]
    )
    for week in targets:
        if week not in vol_of:
            raise SystemExit(f"data/{week} 없음")
        out = render_week(week, vol_of[week])
        pdf_ok = copy_pdf(week, vol_of[week])
        print(f"✓ Vol.{vol_of[week]} {week} → {out.relative_to(PROJECT)} (PDF {'복사됨' if pdf_ok else '없음'})")

    write_landing(weeks, vol_of)


if __name__ == "__main__":
    main()
