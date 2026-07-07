#!/usr/bin/env python3
"""스티커 딸깍 도우미 서버 (로컬 전용, 127.0.0.1:8099).

웹 신문에서 기사 옆 버튼을 클릭하면:
  1. newspaper/{week}/index.md 의 배지(div.badges) 추가/제거
  2. newspaper/{week}/vol-NN.pdf 에 스탬프 주석 삽입/제거 (헤드라인 위치 자동)
  3. 04_Wiki/research/weekly-daemon-vol-NN.md 색인 줄에 픽 마커 ⟨C⟩⟨E⟩⟨S⟩ 반영

실행:
  uv run --with pypdf --with pillow --with pdfminer.six python3 src/badge_server.py
"""
import json
import os
import re
import subprocess
import threading
import unicodedata
import zlib
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
NEWS = PROJECT / "newspaper"
WIKI_RESEARCH = Path.home() / "Documents" / "04_Wiki" / "research"
STICKER_PNG = {
    "claude": NEWS / "assets" / "badges" / "claude-pick.png",
    "editors": NEWS / "assets" / "badges" / "editors-pick.png",
    "s7c": NEWS / "assets" / "badges" / "s7c-pick.png",
}
BADGE_IMG = {
    "claude": '<img src="../assets/badges/claude-pick.png" class="badge" alt="Claude\'s Pick">',
    "editors": '<img src="../assets/badges/editors-pick.png" class="badge" alt="Editor\'s Pick">',
    "s7c": '<img src="../assets/badges/s7c-pick.png" class="badge" alt="S7C Pick">',
}
KIND_MARK = {"claude": "⟨C⟩", "editors": "⟨E⟩", "s7c": "⟨S⟩"}
IMG_KIND_RE = re.compile(r'<img src="\.\./assets/badges/(claude|editors|s7c)-pick\.png"[^>]*>')
BADGE_LINE_RE = re.compile(r'^(?:<!-- badge:\d+ -->|<div class="badges">.*</div>)\s*$')
HEADLINE_RE = re.compile(r"^### ")


def norm(s: str) -> str:
    return re.sub(r"[\s ]+", "", unicodedata.normalize("NFC", s))


# ---------- md 편집 ----------

def edit_md(week: str, n: int, kind: str, op: str) -> str:
    """n번째(1-based) 기사 배지 줄에 kind 추가/제거. 반환: 기사 제목."""
    p = NEWS / week / "index.md"
    lines = p.read_text().splitlines()
    counter = 0
    title = ""
    for i, line in enumerate(lines):
        if not HEADLINE_RE.match(line):
            continue
        counter += 1
        if counter != n:
            continue
        title = line[4:].strip()
        # 헤드라인 다음의 배지 줄 탐색 (빈 줄 하나 허용)
        j = i + 1
        if j < len(lines) and lines[j].strip() == "":
            j += 1
        if j < len(lines) and BADGE_LINE_RE.match(lines[j].strip()):
            kinds = IMG_KIND_RE.findall(lines[j])
        else:
            # 배지 줄이 없으면 새로 만든다
            lines.insert(i + 1, "")
            j = i + 2
            lines.insert(j, "")
            kinds = []
        if op == "add":
            kinds.append(kind)
        elif op == "remove" and kind in kinds:
            kinds.remove(kind)
        if kinds:
            lines[j] = '<div class="badges">' + " ".join(BADGE_IMG[k] for k in sorted(kinds)) + "</div>"
        else:
            lines[j] = f"<!-- badge:{n} -->"
        # HTML 블록이 다음 줄(이미지/본문)을 삼키지 않도록 빈 줄 보장
        if j + 1 < len(lines) and lines[j + 1].strip():
            lines.insert(j + 1, "")
        p.write_text("\n".join(lines) + "\n")
        return title
    raise ValueError(f"기사 {n} 없음 (총 {counter})")


# ---------- 위키 색인 마커 ----------

def edit_wiki(week: str, title: str, kind: str, op: str) -> bool:
    weeks = sorted(d.name for d in NEWS.iterdir() if d.is_dir() and d.name[:4].isdigit())
    if week not in weeks:
        return False
    vol = weeks.index(week) + 1
    wp = WIKI_RESEARCH / f"weekly-daemon-vol-{vol:02d}.md"
    if not wp.exists():
        return False
    key = norm(title)[:14]
    lines = wp.read_text().splitlines()
    mark = KIND_MARK[kind]
    for i, line in enumerate(lines):
        if not line.startswith("- ") or key not in norm(line)[:120]:
            continue
        if op == "add":
            lines[i] = line + " " + mark
        elif mark in line:
            lines[i] = "".join(line.rsplit(" " + mark, 1)) if (" " + mark) in line else line.replace(mark, "", 1)
        wp.write_text("\n".join(lines) + "\n")
        return True
    return False


# ---------- 발행 ----------

PUBLISH_STATE = {"running": False, "ok": None, "log": "", "released": None}


def _latest_week():
    weeks = sorted(d for d in NEWS.iterdir() if d.is_dir() and d.name[:4].isdigit())
    return weeks[-1] if weeks else None


def _latest_draft():
    """최신 호가 draft: true면 주차명, 아니면 None."""
    d = _latest_week()
    if d and re.search(r"^draft: true$", (d / "index.md").read_text(), re.M):
        return d.name
    return None


def _run_publish():
    # 로그인 셸 + ~/.zshrc 로 npx/uv/gh/git 인증 환경 확보 (데몬에서 실행되므로)
    cmd = f'source ~/.zshrc >/dev/null 2>&1; exec "{PROJECT}/src/publish.sh"'
    try:
        proc = subprocess.Popen(
            ["/bin/zsh", "-lc", cmd], cwd=str(PROJECT), text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        for line in proc.stdout:
            PUBLISH_STATE["log"] += line
        PUBLISH_STATE["ok"] = proc.wait() == 0
    except Exception as e:
        PUBLISH_STATE["log"] += f"\n{e}"
        PUBLISH_STATE["ok"] = False
    finally:
        PUBLISH_STATE["running"] = False


def start_publish() -> str | None:
    """최신 호 draft 해제 + publish.sh 백그라운드 실행. 반환: 해제한 주차명(없으면 None)."""
    if PUBLISH_STATE["running"]:
        raise ValueError("이미 발행이 진행 중입니다")
    released = None
    week = _latest_draft()
    if week:
        p = NEWS / week / "index.md"
        p.write_text(re.sub(r"^draft: true$", "draft: false", p.read_text(), count=1, flags=re.M))
        released = week
    PUBLISH_STATE.update(running=True, ok=None, log="", released=released)
    threading.Thread(target=_run_publish, daemon=True).start()
    return released


# ---------- PDF 스탬프 ----------

def _find_anchor(pdf_path: Path, title: str):
    """제목의 마지막 줄 기준 앵커 탐색.

    반환: (page, last_x0, last_x1, last_y0, last_y1, col_right, n_lines)
    제목이 줄바꿈되면 이어지는 줄(같은 x0, 바로 아래, 비슷한 높이)을 따라가
    마지막 줄을 찾는다. col_right = 제목 줄들의 최대 x1 (칼럼 오른쪽 추정).
    """
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTTextContainer, LTTextLine
    key = norm(title)
    for pidx, layout in enumerate(extract_pages(str(pdf_path))):
        all_lines = []
        for el in layout:
            if isinstance(el, LTTextContainer):
                all_lines.extend(l for l in el if isinstance(l, LTTextLine))
        for line in all_lines:
            if not norm(line.get_text())[:12].startswith(key[:8]):
                continue
            tls = [line]
            acc = norm(line.get_text())
            h0 = line.height
            cur = line
            while len(acc) < len(key) - 1:
                nxt = None
                for l2 in all_lines:
                    if l2 in tls or abs(l2.height - h0) > h0 * 0.35:
                        continue
                    if abs(l2.x0 - cur.x0) < 12 and -2 <= (cur.y0 - l2.y1) < h0 * 1.2:
                        nxt = l2
                        break
                if not nxt:
                    break
                tls.append(nxt)
                acc += norm(nxt.get_text())
                cur = nxt
            first, last = tls[0], tls[-1]
            return (pidx, first.x0, first.x1, first.y0, first.y1,
                    last.x0, last.x1, last.y0, last.y1, max(l.x1 for l in tls), len(tls))
    return None


def edit_pdf(week: str, n: int, title: str, kind: str, op: str) -> bool:
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import (ArrayObject, DictionaryObject, FloatObject,
                               NameObject, NumberObject, StreamObject, TextStringObject)
    from PIL import Image

    weeks = sorted(d.name for d in NEWS.iterdir() if d.is_dir() and d.name[:4].isdigit())
    vol = weeks.index(week) + 1
    pdf_path = NEWS / week / f"vol-{vol:02d}.pdf"
    if not pdf_path.exists():
        return False

    nm = f"dybadge:{kind}:{n}"
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    writer.append(reader)

    if op == "remove":
        removed = False
        for page in writer.pages:
            annots = page.get("/Annots")
            if not annots:
                continue
            keep = ArrayObject()
            for a in annots:
                o = a.get_object()
                if not removed and str(o.get("/NM", "")) == nm:
                    removed = True
                    continue
                keep.append(a)
            page[NameObject("/Annots")] = keep
        if not removed:
            return False
    else:
        anchor = _find_anchor(pdf_path, title)
        if not anchor:
            return False
        pidx, fx0, fx1, fy0, fy1, lx0, lx1, ly0, ly1, col_right, nlines = anchor
        page = writer.pages[pidx]
        existing = 0
        for a in page.get("/Annots") or []:
            nm_ = str(a.get_object().get("/NM", ""))
            if nm_.startswith("dybadge:") and nm_.split(":")[-1] == str(n):
                existing += 1
        size = 34.0
        if n == 1:
            # 헤드라인: 마지막 줄 끝 오른쪽 (한 줄이면 제목 끝 아래)
            if nlines >= 2:
                x0 = lx1 + 6 + existing * (size * 0.55)
                x0 = min(x0, col_right - size + 14)
                y0 = ly1 - size + 10
            else:
                x0 = lx1 - size + 4 - existing * (size * 0.55)
                y0 = ly0 - size - 2
        else:
            # 일반 기사: 제목 왼쪽 위 (추가 스탬프는 오른쪽으로)
            x0 = fx0 - 4 + existing * (size * 0.55)
            y0 = fy1 - 6  # 스탬프 하단이 제목 첫 줄 상단에 살짝 걸침
        x0 = max(8.0, min(x0, float(page.mediabox.width) - size - 4))
        rect = [x0, y0, x0 + size, y0 + size]

        img = Image.open(STICKER_PNG[kind]).convert("RGBA")
        img.thumbnail((160, 160))
        w, h = img.size
        rgb = zlib.compress(img.convert("RGB").tobytes())
        alpha = zlib.compress(img.getchannel("A").tobytes())

        smask = StreamObject()
        smask._data = alpha
        smask.update({NameObject("/Type"): NameObject("/XObject"), NameObject("/Subtype"): NameObject("/Image"),
                      NameObject("/Width"): NumberObject(w), NameObject("/Height"): NumberObject(h),
                      NameObject("/ColorSpace"): NameObject("/DeviceGray"), NameObject("/BitsPerComponent"): NumberObject(8),
                      NameObject("/Filter"): NameObject("/FlateDecode")})
        smask_ref = writer._add_object(smask)

        imx = StreamObject()
        imx._data = rgb
        imx.update({NameObject("/Type"): NameObject("/XObject"), NameObject("/Subtype"): NameObject("/Image"),
                    NameObject("/Width"): NumberObject(w), NameObject("/Height"): NumberObject(h),
                    NameObject("/ColorSpace"): NameObject("/DeviceRGB"), NameObject("/BitsPerComponent"): NumberObject(8),
                    NameObject("/Filter"): NameObject("/FlateDecode"), NameObject("/SMask"): smask_ref})
        imx_ref = writer._add_object(imx)

        form = StreamObject()
        form._data = f"q {size} 0 0 {size} 0 0 cm /Im0 Do Q".encode()
        form.update({NameObject("/Type"): NameObject("/XObject"), NameObject("/Subtype"): NameObject("/Form"),
                     NameObject("/BBox"): ArrayObject([NumberObject(0), NumberObject(0), FloatObject(size), FloatObject(size)]),
                     NameObject("/Resources"): DictionaryObject({NameObject("/XObject"): DictionaryObject({NameObject("/Im0"): imx_ref})})})
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

    tmp = pdf_path.with_suffix(".tmp.pdf")
    with tmp.open("wb") as f:
        writer.write(f)
    PdfReader(tmp)  # 검증: 깨졌으면 예외 → 원본 보존
    tmp.replace(pdf_path)
    return True


# ---------- 클라이언트 스크립트 ----------

BADGE_JS = r"""
(function () {
  if (!/^(localhost|127\.0\.0\.1)$/.test(location.hostname)) return;
  var API = "http://127.0.0.1:8099";

  // ---- 발행 버튼 (localhost 전용, 모든 페이지 우하단) ----
  var btn = document.createElement("button");
  btn.textContent = "발행";
  btn.style.cssText = "position:fixed;right:18px;bottom:18px;z-index:9999;" +
    "padding:10px 20px;border:none;border-radius:24px;cursor:pointer;" +
    "background:#6B3FA0;color:#fff;font-weight:700;font-size:14px;font-family:inherit;" +
    "box-shadow:0 2px 8px rgba(0,0,0,.3);";
  document.body.appendChild(btn);

  function setBusy(last) {
    btn.disabled = true;
    btn.style.opacity = ".6";
    btn.style.cursor = "wait";
    btn.textContent = "발행 중…";
    btn.title = last || "";
  }
  function setIdle() {
    btn.disabled = false;
    btn.style.opacity = "1";
    btn.style.cursor = "pointer";
    btn.textContent = "발행";
    btn.title = "";
  }

  function pollPublish() {
    fetch(API + "/api/publish/status").then(function (r) { return r.json(); }).then(function (s) {
      if (s.running) {
        setBusy(s.last);
        setTimeout(pollPublish, 3000);
      } else if (s.ok === true) {
        setIdle();
        alert("✅ 발행 완료 — 1~2분 후 라이브 반영\nhttps://rabieddin.github.io/dy-weekly-daemon/" +
          (s.released ? "\n(draft 해제: " + s.released + ")" : ""));
      } else if (s.ok === false) {
        setIdle();
        alert("❌ 발행 실패:\n" + (s.tail || "로그 없음"));
      } else {
        setIdle();
      }
    }).catch(function () { setIdle(); });
  }

  btn.addEventListener("click", function () {
    fetch(API + "/api/publish/status").then(function (r) { return r.json(); }).then(function (s) {
      if (s.running) { setBusy(s.last); pollPublish(); return; }
      var msg = s.latest_draft
        ? "이번 호(" + s.latest_draft + ") draft를 해제하고 발행할까요?"
        : "새 draft 없음 — 현재 상태 그대로 재발행할까요?";
      if (!confirm(msg + "\n(빌드+업로드 1~3분 소요)")) return;
      setBusy("");
      fetch(API + "/api/publish", { method: "POST" }).then(function (r) { return r.json(); }).then(function (res) {
        if (!res.ok) { setIdle(); alert("발행 시작 실패: " + res.error); return; }
        pollPublish();
      }).catch(function () { setIdle(); alert("배지 서버가 꺼져 있습니다"); });
    }).catch(function () { alert("배지 서버가 꺼져 있습니다"); });
  });

  // 페이지 이동 후에도 진행 중이던 발행 이어서 표시
  fetch(API + "/api/publish/status").then(function (r) { return r.json(); }).then(function (s) {
    if (s.running) { setBusy(s.last); pollPublish(); }
  }).catch(function () {});

  var slug = document.body.dataset.slug || "";
  var m = slug.match(/^(\d{4}-\d{2}-\d{2}_\d{2}-\d{2})/);
  if (!m) return;
  var week = m[1];
  var KINDS = ["claude", "editors", "s7c"];
  var SRC = { claude: "/assets/badges/claude-pick.png", editors: "/assets/badges/editors-pick.png", s7c: "/assets/badges/s7c-pick.png" };

  function post(n, kind, op, cb) {
    fetch("http://127.0.0.1:8099/api/badge", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ week: week, n: n, kind: kind, op: op }),
    }).then(function (r) { return r.json(); }).then(cb).catch(function () { alert("배지 서버가 꺼져 있습니다"); });
  }

  function badgesDivFor(h3) {
    var el = h3.nextElementSibling;
    for (var i = 0; i < 3 && el; i++) {
      if (el.classList && el.classList.contains("badges")) return el;
      if (["H2", "H3"].indexOf(el.tagName) >= 0) break;
      el = el.nextElementSibling;
    }
    return null;
  }

  function wireRemove(img, n) {
    img.style.cursor = "pointer";
    img.title = "클릭하면 이 스티커 제거";
    img.addEventListener("click", function () {
      var kind = (img.src.match(/(claude|editors|s7c)-pick/) || [])[1];
      if (!kind) return;
      post(n, kind, "remove", function () { img.remove(); });
    });
  }

  var article = document.querySelector(".center article");
  if (!article) return;
  var h3s = Array.from(article.querySelectorAll("h3"));
  h3s.forEach(function (h3, idx) {
    var n = idx + 1;
    var ctrl = document.createElement("span");
    ctrl.className = "badge-controls";
    KINDS.forEach(function (kind) {
      var b = document.createElement("img");
      b.src = SRC[kind];
      b.title = kind + " 스티커 붙이기";
      b.addEventListener("click", function (e) {
        e.stopPropagation();
        post(n, kind, "add", function () {
          var div = badgesDivFor(h3);
          if (!div) {
            div = document.createElement("div");
            div.className = "badges";
            h3.insertAdjacentElement("afterend", div);
          }
          var img = document.createElement("img");
          img.src = SRC[kind].replace(/^\//, "../");
          img.className = "badge";
          div.appendChild(img);
          wireRemove(img, n);
        });
      });
      ctrl.appendChild(b);
    });
    h3.appendChild(ctrl);
    var div = badgesDivFor(h3);
    if (div) Array.from(div.querySelectorAll("img.badge")).forEach(function (img) { wireRemove(img, n); });
  });
})();
"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self._send(200, "{}")

    def do_GET(self):
        if self.path == "/badge.js":
            self._send(200, BADGE_JS, "application/javascript")
        elif self.path == "/ping":
            self._send(200, '{"ok":true}')
        elif self.path == "/api/publish/status":
            lines = [l for l in PUBLISH_STATE["log"].splitlines() if l.strip()]
            self._send(200, json.dumps({
                "running": PUBLISH_STATE["running"], "ok": PUBLISH_STATE["ok"],
                "released": PUBLISH_STATE["released"],
                "last": lines[-1] if lines else "",
                "tail": "\n".join(lines[-15:]),
                "latest_draft": _latest_draft(),
            }, ensure_ascii=False))
        else:
            self._send(404, '{"error":"not found"}')

    def do_POST(self):
        if self.path == "/api/publish":
            try:
                released = start_publish()
                return self._send(200, json.dumps({"ok": True, "released": released}, ensure_ascii=False))
            except Exception as e:
                return self._send(500, json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        if self.path != "/api/badge":
            return self._send(404, '{"error":"not found"}')
        try:
            req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            week, n, kind, op = req["week"], int(req["n"]), req["kind"], req["op"]
            assert kind in BADGE_IMG and op in ("add", "remove") and re.fullmatch(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}", week)
            title = edit_md(week, n, kind, op)
            wiki_ok = edit_wiki(week, title, kind, op)
            try:
                pdf_ok = edit_pdf(week, n, title, kind, op)
            except Exception as e:
                pdf_ok = f"error: {e}"
            self._send(200, json.dumps({"ok": True, "title": title, "wiki": wiki_ok, "pdf": pdf_ok}, ensure_ascii=False))
        except Exception as e:
            self._send(500, json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    print("badge server: http://127.0.0.1:8099 (ctrl+c로 종료)")
    HTTPServer(("127.0.0.1", 8099), Handler).serve_forever()
