#!/usr/bin/env python3
"""웹 발행용 PDF 경량화: 본문 이미지 XObject만 다운스케일+JPEG 재압축.
주석(스탬프)은 페이지 리소스가 아니라 annotation AP라 건드리지 않음.
사용: python3 compress_pdf.py in.pdf out.pdf [max_dim] [quality]
"""
import io
import sys

import pikepdf
from pikepdf import PdfImage
from PIL import Image


def compress(src: str, dst: str, max_dim: int = 1800, quality: int = 72) -> None:
    pdf = pikepdf.open(src)
    done, skipped = 0, 0
    seen = set()
    for page in pdf.pages:
        for name, raw in page.images.items():
            objid = raw.objgen
            if objid in seen:
                continue
            seen.add(objid)
            try:
                if "/SMask" in raw:  # 알파 보유 → JPEG 불가, 스킵
                    skipped += 1
                    continue
                pimg = PdfImage(raw)
                im = pimg.as_pil_image()
            except Exception:
                skipped += 1
                continue
            w, h = im.size
            # 이미 작은 JPEG이면 스킵
            cur_len = int(raw.stream_dict.get("/Length", 0))
            if cur_len < 120_000 and max(w, h) <= max_dim:
                skipped += 1
                continue
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            if max(w, h) > max_dim:
                scale = max_dim / max(w, h)
                im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=quality, optimize=True)
            data = buf.getvalue()
            if len(data) >= cur_len:  # 오히려 커지면 유지
                skipped += 1
                continue
            raw.write(data, filter=pikepdf.Name("/DCTDecode"))
            raw.Width, raw.Height = im.size
            raw.ColorSpace = pikepdf.Name("/DeviceGray" if im.mode == "L" else "/DeviceRGB")
            raw.BitsPerComponent = 8
            for k in ("/DecodeParms", "/Decode", "/Intent"):
                if k in raw:
                    del raw[k]
            done += 1
    stripped = strip_apple_extras(pdf)
    deduped = dedup_stamp_images(pdf)
    pdf.save(dst, compress_streams=True,
             object_stream_mode=pikepdf.ObjectStreamMode.generate)
    print(f"{src} → {dst}: 재압축 {done} / 스킵 {skipped} / 스탬프 dedup {deduped} / AAPL 제거 {stripped}")


def strip_apple_extras(pdf) -> int:
    """Preview가 주석마다 심는 AAPL:* 사설 키(재편집용 원본 사본) 제거 — 렌더링은 /AP 사용."""
    n = 0
    for page in pdf.pages:
        for a in page.get("/Annots", []):
            for k in [k for k in a.keys() if str(k).startswith("/AAPL")]:
                del a[k]
                n += 1
    return n


def _img_key(obj) -> str:
    import hashlib
    h = hashlib.md5(obj.read_raw_bytes()).hexdigest()
    if "/SMask" in obj:
        h += hashlib.md5(obj.SMask.read_raw_bytes()).hexdigest()
    return f"{h}:{obj.get('/Width')}x{obj.get('/Height')}:{obj.get('/ColorSpace')}"


def dedup_stamp_images(pdf) -> int:
    """스탬프 주석 AP 안의 이미지 XObject가 내용 동일하면 한 객체로 통합."""
    canon: dict[str, object] = {}
    n = 0
    for page in pdf.pages:
        for a in page.get("/Annots", []):
            try:
                ap = a.AP.N
                xo = ap.Resources.XObject
            except (AttributeError, KeyError):
                continue
            for name in list(xo.keys()):
                img = xo[name]
                if not isinstance(img, pikepdf.Stream):
                    continue
                if img.get("/Subtype") != pikepdf.Name("/Image"):
                    continue
                key = _img_key(img)
                if key in canon:
                    if canon[key].objgen != img.objgen:
                        xo[name] = canon[key]
                        n += 1
                else:
                    canon[key] = img
    return n


if __name__ == "__main__":
    a = sys.argv
    compress(a[1], a[2], int(a[3]) if len(a) > 3 else 1800, int(a[4]) if len(a) > 4 else 72)
