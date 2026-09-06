#!/usr/bin/env python3
"""내부 링크·에셋 존재 검사.

정적 사이트라 빌드가 없으므로, HTML 이 가리키는 상대 경로와 자기 도메인
(buddybird.xyz) 절대 경로가 실제 파일/디렉터리로 존재하는지 로컬에서 확인한다.
외부 링크(인스타·스토어·폰트 CDN 등)는 봇 차단으로 flaky 하므로 검사하지 않는다.

깨진 링크가 하나라도 있으면 목록을 출력하고 종료코드 1 로 끝낸다.
"""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
SELF_HOSTS = {"buddybird.xyz", "www.buddybird.xyz"}
# href/src 를 들고 있는 태그·속성
URL_ATTRS = {"a": "href", "link": "href", "script": "src", "img": "src",
             "source": "src", "iframe": "src", "video": "src", "audio": "src"}


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[int, str, str]] = []  # (line, tag, url)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        wanted = URL_ATTRS.get(tag)
        if not wanted:
            return
        for name, value in attrs:
            if name == wanted and value:
                self.links.append((self.getpos()[0], tag, value))


def is_skippable(url: str) -> bool:
    lowered = url.strip().lower()
    if not lowered:
        return True
    return lowered.startswith(("mailto:", "tel:", "javascript:", "data:", "#"))


def to_local_path(url: str, html_file: Path) -> Path | None:
    """검사 대상 URL 을 로컬 파일시스템 경로로 변환. 외부/스킵이면 None."""
    parts = urlsplit(url)
    if parts.scheme in ("http", "https"):
        if parts.netloc not in SELF_HOSTS:
            return None  # 외부 링크
        path = parts.path  # 자기 도메인 절대 링크
    elif parts.netloc:  # //fonts.googleapis.com 같은 프로토콜 상대 → 외부
        return None
    else:
        path = parts.path

    if not path:  # "#frag" 나 "?query" 만 있는 경우
        return None

    if path.startswith("/"):
        base = ROOT / path.lstrip("/")
    else:
        base = (html_file.parent / path).resolve()

    # "/ko/" 처럼 디렉터리로 끝나면 index.html 을 본다
    if path.endswith("/") or base.is_dir():
        return base / "index.html"
    return base


def main() -> int:
    html_files = sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts)
    broken: list[str] = []

    for html_file in html_files:
        parser = LinkCollector()
        parser.feed(html_file.read_text(encoding="utf-8"))
        for line, tag, url in parser.links:
            if is_skippable(url):
                continue
            target = to_local_path(url, html_file)
            if target is None:
                continue
            if not target.exists():
                rel = html_file.relative_to(ROOT)
                broken.append(f"{rel}:{line}  <{tag}> -> {url}  (없음: {target.relative_to(ROOT)})")

    if broken:
        print("깨진 내부 링크/에셋:")
        for item in broken:
            print(f"  {item}")
        print(f"\n총 {len(broken)}건")
        return 1

    print(f"OK — {len(html_files)}개 HTML 의 내부 링크·에셋 모두 존재")
    return 0


if __name__ == "__main__":
    sys.exit(main())
