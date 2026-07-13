#!/usr/bin/env python3
"""검색 인덱스 기사 단위 분해 — contentIndex.json의 호(vol) 엔트리를 기사별 엔트리로 쪼갠다.
사용: python3 split_search_index.py <빌드출력폴더>   (예: site/public, site/public-publish)
효과: 검색 결과에 호 제목 대신 기사 제목이 뜨고, 클릭 시 해당 기사 앵커로 바로 이동.
빌드 후 실행 (publish.sh가 호출). 재실행해도 안전(멱등)."""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


class ArticleExtractor(HTMLParser):
    """article 내 h3(id) 단위로 제목·본문 텍스트를 모은다. h2(섹션)는 태그로만 기억."""

    def __init__(self):
        super().__init__()
        self.articles = []  # {id, title, body, section}
        self.section = ""
        self.cur = None          # 진행 중인 기사
        self.in_h = None         # 'h2' | 'h3' 헤딩 수집 중
        self.buf = []
        self.in_article = False
        self.skip_depth = 0      # script/style 등 무시

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "article":
            self.in_article = True
        if not self.in_article:
            return
        if tag in ("script", "style"):
            self.skip_depth += 1
        elif tag == "h2":
            self._flush()
            self.cur = None  # 섹션 배너에서 기사 종료
            self.in_h = "h2"
            self.buf = []
        elif tag == "h3" and a.get("id"):
            self._flush()
            self.cur = {"id": a["id"], "title": "", "body": [], "section": self.section}
            self.articles.append(self.cur)
            self.in_h = "h3"
            self.buf = []

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip_depth:
            self.skip_depth -= 1
        elif tag == "h2" and self.in_h == "h2":
            self.section = " ".join("".join(self.buf).split())
            self.in_h = None
        elif tag == "h3" and self.in_h == "h3":
            self.cur["title"] = " ".join("".join(self.buf).split())
            self.in_h = None
        elif tag == "article":
            self._flush()
            self.in_article = False

    def handle_data(self, data):
        if not self.in_article or self.skip_depth:
            return
        if self.in_h:
            self.buf.append(data)
        elif self.cur is not None:
            self.cur["body"].append(data)

    def _flush(self):
        if self.cur is not None:
            self.cur["body"] = " ".join(" ".join(self.cur["body"]).split())
            self.cur = None


def main(outdir):
    idx_path = Path(outdir) / "static" / "contentIndex.json"
    data = json.loads(idx_path.read_text(encoding="utf-8"))

    # 멱등성: 이전 실행이 만든 #앵커 엔트리 제거 후 다시 생성
    data = {k: v for k, v in data.items() if "#" not in k}

    vols = [k for k in data if re.match(r"20\d\d-.*/index$", k)]
    added = 0
    for key in vols:
        html_path = Path(outdir) / key.replace("/index", "") / "index.html"
        if not html_path.exists():
            continue
        p = ArticleExtractor()
        p.feed(html_path.read_text(encoding="utf-8"))
        if not p.articles:
            continue
        vol_title = data[key].get("title", "")
        tags = data[key].get("tags", [])
        for art in p.articles:
            if not art["title"]:
                continue
            body = art["body"] if isinstance(art["body"], str) else " ".join(art["body"])
            data[f"{key}#{art['id']}"] = {
                "slug": f"{key}#{art['id']}",
                "title": f"{art['title']} — {vol_title}",
                "content": body,
                "tags": tags + ([art["section"]] if art["section"] else []),
                "links": [],
            }
            added += 1
        # 호 엔트리는 제목 검색용으로만 유지 (본문은 기사 엔트리가 담당 — 중복 히트 방지)
        data[key]["content"] = ""

    idx_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(f"기사 엔트리 {added}개 생성 (호 {len(vols)}개 분해, 총 {len(data)}개)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "public")
