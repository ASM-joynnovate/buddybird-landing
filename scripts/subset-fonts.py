#!/usr/bin/env python3
"""일본어 페이지에 쓰인 글자만 담은 M PLUS Rounded 1c 서브셋(woff2)을 만든다.

일본어 글꼴은 한 굵기가 3MB 넘고, Google Fonts 로 받으면 조각 수십 개(랜딩에서 약 650KB)를 받는다.
페이지에 실제로 쓰인 글자만 잘라 직접 올리면 굵기당 40~110KB 다.

- 만들기: `python3 scripts/subset-fonts.py` (fonttools·brotli 필요: `pip install fonttools brotli`)
  원본 TTF 는 아래 커밋으로 고정해 google/fonts 에서 받아 .cache/fonts/ 에 둔다(레포에 넣지 않는다).
- 검사: `python3 scripts/subset-fonts.py --check` (표준 라이브러리만 쓴다, CI 에서 실행)
  일본어 문구에 새 글자가 생겼는데 서브셋을 다시 만들지 않았으면 실패한다.
  다시 만들지 않으면 그 글자만 다음 글꼴(Pretendard)로 보인다.

영문·숫자·라틴 확장(언어 메뉴의 «Español»)·키릴 문자(«Русский»)는 앞선 Nunito 가 맡으므로 담지 않는다. 한글은 원본에 없어 Pretendard 가 맡는다.
"""
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCK = ROOT / "scripts" / "fonts.lock.json"
OUT = ROOT / "assets" / "fonts"
CACHE = ROOT / ".cache" / "fonts"

SRC_COMMIT = "84efd8ad78c3710ad14bd909e3bc407151885628"  # google/fonts, 2026-05-01
SRC_URL = f"https://raw.githubusercontent.com/google/fonts/{SRC_COMMIT}/ofl/mplusrounded1c/MPLUSRounded1c-{{style}}.ttf"
WEIGHTS = {700: "Bold", 800: "ExtraBold", 900: "Black"}

# 랜딩과 문서 페이지는 글자 수 차이가 커서(약 260자 / 650자) 따로 자른다.
# consent.js 는 두 그룹 페이지 모두에 쿠키 배너(일본어 문구 포함)를 띄우므로 양쪽에 넣는다.
GROUPS = {
    "ja-landing": ["ja/index.html", "assets/js/consent.js"],
    "ja-docs": ["ja/support/index.html", "ja/privacy/index.html", "ja/terms/index.html", "assets/js/consent.js"],
}


def needed_chars(pages: list[str]) -> str:
    chars: set[str] = set()
    for page in pages:
        text = (ROOT / page).read_text(encoding="utf-8")
        text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
        chars.update(c for c in text if ord(c) > 0x7F and not ("가" <= c <= "힣") and not ("\u00a0" <= c <= "\u024f") and not ("\u0400" <= c <= "\u04ff"))
    return "".join(sorted(chars))


def font_path(group: str, weight: int) -> Path:
    return OUT / f"mplus-rounded-1c-{group}-{weight}.woff2"


def source(style: str) -> Path:
    path = CACHE / f"MPLUSRounded1c-{style}.ttf"
    if not path.is_file():
        CACHE.mkdir(parents=True, exist_ok=True)
        print(f"원본 받는 중: {path.name}")
        urllib.request.urlretrieve(SRC_URL.format(style=style), path)
    return path


def build() -> int:
    from fontTools import subset
    from fontTools.ttLib import TTFont

    OUT.mkdir(parents=True, exist_ok=True)
    lock = {"source": SRC_COMMIT, "groups": {}}
    for group, pages in GROUPS.items():
        chars = needed_chars(pages)
        entry = {"pages": pages, "chars": chars, "files": {}}
        for weight, style in WEIGHTS.items():
            src = source(style)
            cmap = TTFont(src)["cmap"].getBestCmap()
            entry["missing"] = "".join(c for c in chars if ord(c) not in cmap)
            opts = subset.Options()
            opts.flavor = "woff2"
            opts.layout_features = ["*"]
            opts.name_IDs = ["*"]  # 라이선스(OFL) 표기를 남긴다
            font = subset.load_font(str(src), opts)
            sub = subset.Subsetter(opts)
            sub.populate(text=chars)
            sub.subset(font)
            out = font_path(group, weight)
            subset.save_font(font, str(out), opts)
            entry["files"][out.name] = hashlib.md5(out.read_bytes()).hexdigest()
            print(f"{out.relative_to(ROOT)}  {len(chars)}자  {out.stat().st_size // 1024}KB")
        lock["groups"][group] = entry
        if entry["missing"]:
            print(f"  {group}: 원본에 없는 글자 {entry['missing']!r} 는 다음 글꼴로 보인다")
    LOCK.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


def check() -> int:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    errors = []
    for group, pages in GROUPS.items():
        entry = lock["groups"].get(group)
        if entry is None:
            errors.append(f"{group}: 서브셋이 없다")
            continue
        covered = set(entry["chars"])
        new = [c for c in needed_chars(pages) if c not in covered]
        if new:
            errors.append(f"{group}: 서브셋에 없는 새 글자 {''.join(new)!r}")
        for name, digest in entry["files"].items():
            path = OUT / name
            if not path.is_file() or hashlib.md5(path.read_bytes()).hexdigest() != digest:
                errors.append(f"{group}: {name} 가 fonts.lock.json 과 다르다")
    if errors:
        print("일본어 글꼴 서브셋을 다시 만들어야 한다 (python3 scripts/subset-fonts.py):\n  "
              + "\n  ".join(errors), file=sys.stderr)
        return 1
    print("OK — 일본어 글꼴 서브셋이 페이지 글자를 모두 담고 있다")
    return 0


if __name__ == "__main__":
    sys.exit(check() if "--check" in sys.argv else build())
