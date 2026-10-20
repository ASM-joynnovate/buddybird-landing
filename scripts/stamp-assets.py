#!/usr/bin/env python3
"""배포 직전에 HTML 안의 /assets/ 참조 뒤에 내용 해시(?v=xxxxxxxx)를 붙인다.

assets/ 는 브라우저에 1년(immutable) 캐시시키므로, 파일 내용이 바뀌면 URL 도 바뀌어야
방문자가 새 파일을 받는다. 파일 이름은 그대로 두고 쿼리만 바꾸므로 레포에서는 할 일이 없다.
CI 작업 디렉터리에서만 실행하고 결과는 커밋하지 않는다(로컬에서 돌렸다면 git checkout 으로 되돌린다).

- 대상: 따옴표·괄호·= 바로 뒤에 오는 루트 상대 경로 "/assets/..." (src, href, data-src, CSS url(), JS 문자열)
- 제외: https://buddybird.xyz/assets/... 같은 절대 URL(og:image 등). 이 파일들은 짧은 캐시로 올린다
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF = re.compile(r"""(?<=["'(=])(/assets/[A-Za-z0-9_./-]+)(?![A-Za-z0-9_./?-])""")

_hashes: dict[str, str] = {}


def version(path: str) -> str:
    if path not in _hashes:
        _hashes[path] = hashlib.md5((ROOT / path.lstrip("/")).read_bytes()).hexdigest()[:8]
    return _hashes[path]


def main() -> int:
    missing: list[str] = []
    stamped = 0
    for html in sorted(ROOT.rglob("*.html")):
        if ".git" in html.parts or "scripts" in html.parts:
            continue
        text = html.read_text(encoding="utf-8")

        def repl(m: re.Match) -> str:
            nonlocal stamped
            path = m.group(1)
            if not (ROOT / path.lstrip("/")).is_file():
                missing.append(f"{html.relative_to(ROOT)} -> {path}")
                return path
            stamped += 1
            return f"{path}?v={version(path)}"

        new = REF.sub(repl, text)
        if new != text:
            html.write_text(new, encoding="utf-8")

    if missing:
        print("없는 에셋 참조:\n  " + "\n  ".join(missing), file=sys.stderr)
        return 1
    print(f"OK — 에셋 참조 {stamped}개에 버전 쿼리를 붙임 (파일 {len(_hashes)}개)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
