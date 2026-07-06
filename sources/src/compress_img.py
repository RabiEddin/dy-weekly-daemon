#!/usr/bin/env python3
"""웹 발행용 기사 이미지 경량화: 폭 1400px 상한 + 재압축 (원본 불변).

사용: python3 compress_img.py <src_images_dir> <dst_images_dir>
- dst가 src보다 새로우면 스킵 (멱등 — publish.sh가 매번 불러도 갱신분만 처리)
- 파일명·포맷 유지 (HTML이 파일명을 직접 참조하므로 확장자 변경 금지)
- 결과가 원본보다 커지면 원본 그대로 복사
"""
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageOps

MAX_W = 1400          # 기사 칼럼 표시폭(~700px)의 2배 — 레티나까지 커버
JPEG_QUALITY = 80
SMALL_ENOUGH = 150_000  # 이보다 작고 폭도 넘지 않으면 그대로 복사


def process(src: Path, dst: Path) -> str:
    try:
        im = Image.open(src)
        im = ImageOps.exif_transpose(im)  # EXIF 회전 반영 (리사이즈 시 EXIF 소실 대비)
    except Exception:
        shutil.copy2(src, dst)
        return "copy"
    fmt = (im.format or Image.open(src).format or "").upper()
    w, h = im.size
    if w <= MAX_W and src.stat().st_size < SMALL_ENOUGH:
        shutil.copy2(src, dst)
        return "copy"
    if w > MAX_W:
        im = im.resize((MAX_W, max(1, int(h * MAX_W / w))), Image.LANCZOS)
    try:
        if fmt == "JPEG":
            im.convert("RGB").save(dst, "JPEG", quality=JPEG_QUALITY,
                                   optimize=True, progressive=True)
        elif fmt == "PNG":
            im.save(dst, "PNG", optimize=True)
        else:  # GIF·WebP·SVG 등은 건드리지 않음
            shutil.copy2(src, dst)
            return "copy"
    except Exception:
        shutil.copy2(src, dst)
        return "copy"
    if dst.stat().st_size >= src.stat().st_size:  # 오히려 커지면 원본 유지
        shutil.copy2(src, dst)
        return "copy"
    return "opt"


def main() -> None:
    sdir, ddir = Path(sys.argv[1]), Path(sys.argv[2])
    ddir.mkdir(parents=True, exist_ok=True)
    n = {"opt": 0, "copy": 0, "skip": 0}
    before = after = 0
    for src in sorted(p for p in sdir.iterdir() if p.is_file()):
        dst = ddir / src.name
        if dst.exists() and dst.stat().st_mtime > src.stat().st_mtime:
            n["skip"] += 1
            continue
        n[process(src, dst)] += 1
        before += src.stat().st_size
        after += dst.stat().st_size
    week = sdir.parent.name
    if before:
        print(f"{week}: 경량화 {n['opt']} / 복사 {n['copy']} / 스킵 {n['skip']}"
              f" ({before/1e6:.1f}MB → {after/1e6:.1f}MB)")
    elif n["skip"]:
        print(f"{week}: 변경 없음 (스킵 {n['skip']})")


if __name__ == "__main__":
    main()
