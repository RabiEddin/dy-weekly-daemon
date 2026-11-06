// 기사 짧은 고정 앵커(#34-07) + 제목 클릭 = 링크 복사.
// 로컬: ai_search_server.py(8081 프록시)가 /__local/anchors.js로 주입. 발행본: publish.sh 2.7이 /static/article-anchors.js로 주입.
// - 번호 = 페이지 안 기사 순서(1면 포함, md의 <!-- badge:N -->와 같은 순번). 헤드라인을 고쳐도 안 바뀐다.
// - 제목 오른쪽에 작은 클립 아이콘. 제목(아이콘 포함) 클릭 → 링크 복사, 아이콘이 잠깐 체크로 바뀜.
// - 기존 헤드라인 슬러그 앵커(#memoryagentbench-…)·목차·검색은 건드리지 않는다.
// - 링크엔 호·번호만 들어간다(이름 등 개인정보 없음).
(() => {
  const article = document.querySelector("article");
  const vol = (article?.querySelector(".mast-meta span")?.textContent || "").match(/Vol\.(\d+)/)?.[1];
  if (!vol) return; // 신문 호 페이지가 아님(랜딩 등)
  const heads = [...article.querySelectorAll("h3[id]")];
  if (!heads.length) return;

  const SVG = (d) =>
    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${d}</svg>`;
  const CLIP = SVG('<path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>');
  const CHECK = SVG('<polyline points="20 6 9 17 4 12"/>');

  const style = document.createElement("style");
  style.textContent = `
    article h3.art-linkable { cursor: pointer; }
    .art-clip { display: inline-block; width: .62em; height: .62em; margin-left: .28em; vertical-align: .02em;
      color: var(--gray); opacity: .55; transition: opacity .15s, color .15s; }
    .art-clip svg { width: 100%; height: 100%; display: block; }
    h3.art-linkable:hover .art-clip { opacity: 1; color: var(--dark); }
    .art-clip.done { opacity: 1; color: var(--tertiary); }
    .art-nowrap { white-space: nowrap; }`;
  document.head.appendChild(style);

  const esc = (s) => s.replace(/[&<>"]/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[ch]);

  // 두 형식을 같이 싣는다: 서식 붙여넣기(Slack·Notion·메일)에선 제목에 링크가 걸리고, 일반 텍스트에선 "제목(링크)"
  async function copy(title, url) {
    const plain = `${title}(${url})`;
    const html = `<a href="${esc(url)}">${esc(title)}</a>`;
    try {
      await navigator.clipboard.write([new ClipboardItem({
        "text/html": new Blob([html], { type: "text/html" }),
        "text/plain": new Blob([plain], { type: "text/plain" }),
      })]);
      return true;
    } catch {}
    // http://<사내 IP> 처럼 보안 컨텍스트가 아니면 Clipboard API가 없다 → copy 이벤트로 직접 채운다
    const fill = (e) => {
      e.clipboardData.setData("text/html", html);
      e.clipboardData.setData("text/plain", plain);
      e.preventDefault();
    };
    document.addEventListener("copy", fill, { once: true });
    let ok = false;
    try { ok = document.execCommand("copy"); } catch {}
    document.removeEventListener("copy", fill);
    return ok;
  }

  const byId = new Map();
  heads.forEach((h, i) => {
    const id = `${vol}-${String(i + 1).padStart(2, "0")}`;
    const url = () => `${location.origin}${location.pathname}#${id}`;
    byId.set(id, h);

    const clip = document.createElement("span");
    clip.className = "art-clip";
    clip.innerHTML = CLIP;
    // 아이콘만 다음 줄로 떨어지지 않게 마지막 단어와 묶는다
    const textNode = [...h.childNodes].reverse().find((n) => n.nodeType === Node.TEXT_NODE && n.textContent.trim());
    if (textNode) {
      const t = textNode.textContent.replace(/\s+$/, "");
      const cut = t.search(/\S+$/);
      const tail = document.createElement("span");
      tail.className = "art-nowrap";
      tail.append(t.slice(cut), clip);
      textNode.textContent = t.slice(0, cut);
      textNode.after(tail);
    } else h.append(clip);

    h.classList.add("art-linkable");
    h.title = `클릭하면 링크 복사 (#${id})`;
    h.addEventListener("click", async (e) => {
      // 같은 h3 안의 로컬 도장 버튼(.badge-controls)·링크를 누른 건 복사가 아님
      if (e.target.closest(".badge-controls, a, button, input")) return;
      if (String(getSelection())) return; // 제목 글자를 드래그로 고르는 중이면 복사하지 않음
      // 제목 = 도장·숨은 앵커·아이콘을 뺀 제목 글자만
      const c = h.cloneNode(true);
      c.querySelectorAll(".badge-controls, a, .art-clip").forEach((n) => n.remove());
      const ok = await copy(c.textContent.replace(/\s+/g, " ").trim(), url());
      clip.innerHTML = ok ? CHECK : CLIP;
      clip.classList.toggle("done", ok);
      setTimeout(() => { clip.innerHTML = CLIP; clip.classList.remove("done"); }, 1500);
    });
  });

  // #34-07 로 들어오면 해당 기사로 이동. 이 id는 JS가 만든 것이라 브라우저 기본 점프가 안 되므로 직접 스크롤.
  // h3의 scroll-margin-top(고정 배너+아이브로우 여유)이 그대로 적용된다. 이미지 로드로 밀리면 load 때 한 번 더.
  // 첫 진입은 즉시 이동(html이 scroll-behavior:smooth라 기본값이면 애니메이션 도중 이미지 로드로 목표가 어긋난다).
  const jump = (behavior) => byId.get(decodeURIComponent(location.hash.slice(1)))?.scrollIntoView({ behavior });
  jump("instant");
  addEventListener("load", () => jump("instant"), { once: true });
  addEventListener("hashchange", () => jump("smooth"));
})();
