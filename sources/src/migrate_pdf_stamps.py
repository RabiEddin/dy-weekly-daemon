#!/usr/bin/env python3
"""PDF 스탬프를 옛 원형 도장(개수 반복) → 새 정사각 로고 도장(2단계)으로 교체.

사용:
    uv run --with pypdf --with pillow python3 src/migrate_pdf_stamps.py --week 2026-07-16_07-23
    ... --apply     # 실제 반영 (원본은 .bak-stamps 로 백업)
    ... --revert

동작:
- 기존 dybadge 주석에서 (쪽, 기사번호 n, 종류, 좌표)를 수집한다.
- 같은 (n, 종류)가 3개 이상 반복이면 강조 등급으로 본다 (웹과 동일한 임계값).
- 반복을 하나로 합치고, 그 종류의 **첫 좌표**를 그대로 재사용한다
  (손으로 맞춰둔 위치를 잃지 않기 위해).
- 새 에셋은 logo-*.png (정사각). 정사각이라 edit_pdf의 정사각 CTM을 안 고쳐도 된다.

주석 구조는 badge_server.edit_pdf와 동일하게 만든다 — 그래야 sync_stickers.classify()가
appearance XObject의 md5로 종류를 되읽을 수 있다. 스크립트 끝에 등록할 md5를 출력한다.
"""

import argparse
import collections
import hashlib
import shutil
import zlib
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
NEWS = PROJECT / "newspaper"
BADGES = NEWS / "assets" / "badges"

KEY_THRESHOLD = 3
HAS_KEY = {"claude": False, "editors": True, "s7c": True}


def asset(kind: str, level: str) -> Path:
    suffix = "-key" if (level == "key" and HAS_KEY[kind]) else ""
    return BADGES / f"logo-{kind}{suffix}.png"


def build_stamp(writer, page, kind: str, level: str, rect, nm: str):
    """badge_server.edit_pdf와 동일한 구조의 Stamp 주석을 만든다."""
    from pypdf.generic import (ArrayObject, DictionaryObject, FloatObject,
                               NameObject, NumberObject, StreamObject,
                               TextStringObject)
    from PIL import Image

    size = float(rect[2] - rect[0])
    img = Image.open(asset(kind, level)).convert("RGBA")
    img.thumbnail((160, 160))
    w, h = img.size
    rgb_raw = img.convert("RGB").tobytes()
    rgb = zlib.compress(rgb_raw)
    alpha = zlib.compress(img.getchannel("A").tobytes())

    smask = StreamObject()
    smask._data = alpha
    smask.update({NameObject("/Type"): NameObject("/XObject"), NameObject("/Subtype"): NameObject("/Image"),
                  NameObject("/Width"): NumberObject(w), NameObject("/Height"): NumberObject(h),
                  NameObject("/ColorSpace"): NameObject("/DeviceGray"),
                  NameObject("/BitsPerComponent"): NumberObject(8),
                  NameObject("/Filter"): NameObject("/FlateDecode")})
    smask_ref = writer._add_object(smask)

    imx = StreamObject()
    imx._data = rgb
    imx.update({NameObject("/Type"): NameObject("/XObject"), NameObject("/Subtype"): NameObject("/Image"),
                NameObject("/Width"): NumberObject(w), NameObject("/Height"): NumberObject(h),
                NameObject("/ColorSpace"): NameObject("/DeviceRGB"),
                NameObject("/BitsPerComponent"): NumberObject(8),
                NameObject("/Filter"): NameObject("/FlateDecode"), NameObject("/SMask"): smask_ref})
    imx_ref = writer._add_object(imx)

    form = StreamObject()
    form._data = f"q {size} 0 0 {size} 0 0 cm /Im0 Do Q".encode()
    form.update({NameObject("/Type"): NameObject("/XObject"), NameObject("/Subtype"): NameObject("/Form"),
                 NameObject("/BBox"): ArrayObject([NumberObject(0), NumberObject(0),
                                                   FloatObject(size), FloatObject(size)]),
                 NameObject("/Resources"): DictionaryObject(
                     {NameObject("/XObject"): DictionaryObject({NameObject("/Im0"): imx_ref})})})
    form_ref = writer._add_object(form)

    annot = DictionaryObject({
        NameObject("/Type"): NameObject("/Annot"), NameObject("/Subtype"): NameObject("/Stamp"),
        NameObject("/Rect"): ArrayObject([FloatObject(v) for v in rect]),
        NameObject("/AP"): DictionaryObject({NameObject("/N"): form_ref}),
        NameObject("/NM"): TextStringObject(nm), NameObject("/F"): NumberObject(4),
    })
    annot_ref = writer._add_object(annot)
    annots = page.get("/Annots")
    if annots is None:
        page[NameObject("/Annots")] = ArrayObject([annot_ref])
    else:
        annots.append(annot_ref)
    # sync_stickers.classify()가 쓰는 해시 = 압축 해제된 RGB 바이트의 md5가 아니라
    # StreamObject.get_data() 결과(=압축 해제본)의 md5다. 동일하게 계산해 돌려준다.
    return hashlib.md5(rgb_raw).hexdigest()[:10]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    a = ap.parse_args()

    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import ArrayObject

    weeks = sorted(d.name for d in NEWS.iterdir() if d.is_dir() and d.name[:4].isdigit())
    vol = weeks.index(a.week) + 1
    pdf = NEWS / a.week / f"vol-{vol:02d}.pdf"
    bak = pdf.with_suffix(".pdf.bak-stamps")
    if not pdf.exists():
        raise SystemExit(f"없음: {pdf}")

    if a.revert:
        if not bak.exists():
            raise SystemExit(f"백업 없음: {bak}")
        shutil.copy2(bak, pdf)
        print(f"복구 완료: {pdf.name} ← {bak.name}")
        return

    reader = PdfReader(pdf)
    SIZE = 34.0

    # 1) md를 기준(source of truth)으로 읽는다 — 웹에서 큐레이션한 결과가 md에 있다
    import re
    lines = (NEWS / a.week / "index.md").read_text(encoding="utf-8").splitlines()
    md_picks: dict[int, dict[str, str]] = {}
    titles: dict[int, str] = {}
    n = 0
    pending: dict[str, str] = {}
    for l in lines:
        if 'class="eyebrow"' in l:
            pending = {m.group(1): ("key" if m.group(2) else "base")
                       for m in re.finditer(r"badges/pick-(claude|editors|s7c)(-key)?\.png", l)}
        elif l.startswith("### "):
            n += 1
            titles[n] = l[4:].strip()
            if pending:
                md_picks[n] = pending
            pending = {}
    total_labels = sum(len(v) for v in md_picks.values())
    print(f"md 기준: 기사 {n}건 · 라벨 {total_labels}개")

    # 2) 기존 PDF 스탬프의 좌표를 (n, kind)별로 보존 (손으로 맞춘 위치를 잃지 않기 위해)
    existing: dict[tuple[int, str], list] = {}
    old_cnt = 0
    for pi, page in enumerate(reader.pages):
        for ref in (page.get("/Annots") or []):
            o = ref.get_object()
            nm = str(o.get("/NM", ""))
            if not nm.startswith("dybadge:"):
                continue
            old_cnt += 1
            parts = nm.split(":")
            existing.setdefault((int(parts[-1]), parts[1]), []).append(
                (pi, [float(v) for v in o["/Rect"]]))
    print(f"기존 dybadge 스탬프 {old_cnt}개 → 종류쌍 {len(existing)}개")

    # 3) 배치 계획. PDF에 없는 (n, kind)는 _find_anchor로 새로 계산한다.
    import sys
    sys.path.insert(0, str(PROJECT / "src"))
    from badge_server import _find_anchor          # __main__ 가드가 있어 안전

    plan = []                                      # (pidx, n, kind, level, rect)
    lv = collections.Counter()
    missing, failed = [], []
    for art in sorted(md_picks):
        used_x: list[float] = []
        anchor = None
        for kind in ("claude", "editors", "s7c"):
            level = md_picks[art].get(kind)
            if level is None:
                continue
            hit = existing.get((art, kind))
            if hit:
                pi, rect = hit[0]                  # 첫 좌표 재사용 (반복은 하나로 합침)
            else:
                # PDF에 없던 스탬프 — edit_pdf와 같은 규칙으로 좌표 산출
                if anchor is None:
                    anchor = _find_anchor(pdf, titles[art])
                if not anchor:
                    failed.append((art, kind)); continue
                pi, fx0, fx1, fy0, fy1, lx0, lx1, ly0, ly1, col_right, nlines = anchor
                step = SIZE * 0.55
                x0 = (max(used_x) + step) if used_x else (fx0 - 4)
                y0 = fy1 - 6
                x0 = max(8.0, min(x0, float(reader.pages[pi].mediabox.width) - SIZE - 4))
                rect = [x0, y0, x0 + SIZE, y0 + SIZE]
                missing.append((art, kind))
            used_x.append(rect[0])
            plan.append((pi, art, kind, level, rect))
            lv[f"{kind}-{level}"] += 1

    print(f"배치 계획 {len(plan)}개")
    for k, v in sorted(lv.items()):
        print(f"     {k:16s} {v}개")
    if missing:
        print(f"  PDF에 없어 새로 좌표 계산: {len(missing)}개 → "
              + ", ".join(f"기사{a}/{k}" for a, k in missing))
    if failed:
        print(f"  ⚠️ 앵커(제목) 못 찾아 배치 실패: {failed}")

    if not a.apply:
        print("\n반영하려면 --apply")
        return

    # 3) 옛 스탬프 제거 후 새로 삽입
    writer = PdfWriter()
    writer.append(reader)
    for page in writer.pages:
        annots = page.get("/Annots")
        if not annots:
            continue
        keep = ArrayObject()
        for ref in annots:
            if not str(ref.get_object().get("/NM", "")).startswith("dybadge:"):
                keep.append(ref)
        page[__import__("pypdf").generic.NameObject("/Annots")] = keep

    hashes = {}
    for pi, art, kind, level, rect in plan:
        nm = f"dybadge:{kind}:{art}"
        h = build_stamp(writer, writer.pages[pi], kind, level, rect, nm)
        hashes[h] = f"{kind} ({level})"

    if not bak.exists():
        shutil.copy2(pdf, bak)
        print(f"\n백업: {bak.name}")
    tmp = pdf.with_suffix(".tmp.pdf")
    with tmp.open("wb") as f:
        writer.write(f)
    PdfReader(tmp)          # 검증
    tmp.replace(pdf)
    print(f"반영 완료: {pdf.name}")

    print("\n--- sync_stickers.HASH_KIND 에 등록할 값 ---")
    for h, desc in sorted(hashes.items(), key=lambda kv: kv[1]):
        kind = desc.split()[0]
        print(f'    "{h}": "{kind}",   # {desc} — logo')


if __name__ == "__main__":
    main()
