#!/usr/bin/env python3
"""
로컬 개발용 정적 서버.

GitHub Pages처럼 "확장자 없는 깔끔한 URL"을 지원합니다.
  /privacy  →  privacy.html
  /terms    →  terms.html
  /support  →  support.html

기본 `python3 -m http.server`는 이 매핑을 못 해 /privacy 가 404가 납니다.
운영(GitHub Pages)과 동일하게 로컬에서도 확인하려면 이 서버를 쓰세요.

사용법:
  python3 serve.py          # http://localhost:8910
  python3 serve.py 8080     # 포트 지정
"""
import http.server
import os
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8910


class CleanURLHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        fpath = super().translate_path(path)
        # 실제 파일/디렉터리가 있으면 그대로 서빙
        if os.path.isfile(fpath) or os.path.isdir(fpath):
            return fpath
        # 확장자가 없고 같은 이름의 .html 이 있으면 그것을 서빙 (GitHub Pages 동작 모사)
        _, ext = os.path.splitext(fpath)
        if not ext and os.path.isfile(fpath + ".html"):
            return fpath + ".html"
        return fpath


if __name__ == "__main__":
    with http.server.ThreadingHTTPServer(("", PORT), CleanURLHandler) as httpd:
        print(f"Serving on http://localhost:{PORT}  (clean URLs: /privacy → privacy.html)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")
