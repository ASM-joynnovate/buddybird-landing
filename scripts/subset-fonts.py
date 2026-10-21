#!/usr/bin/env python3
"""CJK 페이지에 쓰인 글자만 담은 글꼴 서브셋(woff2)을 만든다.

- 일본어: M PLUS Rounded 1c (google/fonts)
- 번체 중국어: 源泉圓體 TW (GenSen Rounded 2 TW, ButTaiwan/gensen-font). 대만 교육부 표준 자형이라
  일본 자형인 M PLUS 를 쓰지 않는다

CJK 글꼴은 한 굵기가 3~16MB 이고, Google Fonts 로 받으면 조각 수십 개(일본어 랜딩에서 약 650KB)를 받는다.
페이지에 실제로 쓰인 글자만 잘라 직접 올리면 굵기당 40~110KB 다.

- 만들기: `python3 scripts/subset-fonts.py` (fonttools·brotli 필요: `pip install fonttools brotli`)
  원본은 아래 커밋·릴리스로 고정해 받아 .cache/fonts/ 에 둔다(레포에 넣지 않는다).
- 검사: `python3 scripts/subset-fonts.py --check` (표준 라이브러리만 쓴다, CI 에서 실행)
  CJK 문구에 새 글자가 생겼는데 서브셋을 다시 만들지 않았으면 실패한다.
  다시 만들지 않으면 그 글자만 다음 글꼴(Pretendard)로 보인다.

영문·숫자·라틴 확장(언어 메뉴의 «Español»)·키릴 문자(«Русский»)는 앞선 Nunito 가 맡으므로 담지 않는다. 한글은 Pretendard 가 맡는다.
"""
import hashlib
import io
import json
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCK = ROOT / "scripts" / "fonts.lock.json"
OUT = ROOT / "assets" / "fonts"
CACHE = ROOT / ".cache" / "fonts"

MPLUS_COMMIT = "84efd8ad78c3710ad14bd909e3bc407151885628"  # google/fonts, 2026-05-01
GENSEN_RELEASE = "v2.100"  # ButTaiwan/gensen-font, 2024-08-22
FONTS = {
    "mplus-rounded-1c": {
        "source": MPLUS_COMMIT,
        "url": f"https://raw.githubusercontent.com/google/fonts/{MPLUS_COMMIT}/ofl/mplusrounded1c/MPLUSRounded1c-{{style}}.ttf",
        "weights": {700: "Bold", 800: "ExtraBold", 900: "Black"},
    },
    # 굵기가 B(700)·H(900)로 벌어져 있어 페이지의 700·800 은 B 한 벌로 그린다(@font-face 의 font-weight:700 800)
    "gensen-rounded-tw": {
        "source": GENSEN_RELEASE,
        "zip": f"https://github.com/ButTaiwan/gensen-font/releases/download/{GENSEN_RELEASE}/GenSenRounded2TW-otf.zip",
        "zip_sha256": "c5a18c0661c0b26effe5503431f2fee176137f6451be3ae37b9787c6179cf325",
        "weights": {700: "GenSenRounded2TW-B.otf", 900: "GenSenRounded2TW-H.otf"},
    },
}

# 랜딩과 문서 페이지는 글자 수 차이가 커서 따로 자른다.
# consent.js 는 두 그룹 페이지 모두에 쿠키 배너(언어별 문구 포함)를 띄우므로 양쪽에 넣는다.
GROUPS = {
    "ja-landing": ("mplus-rounded-1c", ["ja/index.html", "assets/js/consent.js"]),
    "ja-docs": ("mplus-rounded-1c", ["ja/support/index.html", "ja/privacy/index.html", "ja/terms/index.html", "assets/js/consent.js"]),
    "zh-tw-landing": ("gensen-rounded-tw", ["zh-tw/index.html", "assets/js/consent.js"]),
    "zh-tw-docs": ("gensen-rounded-tw", ["zh-tw/support/index.html", "zh-tw/privacy/index.html", "zh-tw/terms/index.html", "assets/js/consent.js"]),
}


def needed_chars(pages: list[str]) -> str:
    chars: set[str] = set()
    for page in pages:
        text = (ROOT / page).read_text(encoding="utf-8")
        text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
        chars.update(c for c in text if ord(c) > 0x7F and not ("가" <= c <= "힣") and not (" " <= c <= "ɏ") and not ("Ѐ" <= c <= "ӿ"))
    return "".join(sorted(chars))


def font_path(font: str, group: str, weight: int) -> Path:
    return OUT / f"{font}-{group}-{weight}.woff2"


def source(font: str, weight: int) -> Path:
    spec = FONTS[font]
    name = spec["weights"][weight]
    if "zip" in spec:
        path = CACHE / name
        if not path.is_file():
            CACHE.mkdir(parents=True, exist_ok=True)
            print(f"원본 받는 중: {spec['zip'].rsplit('/', 1)[1]}")
            data = urllib.request.urlopen(spec["zip"]).read()
            if hashlib.sha256(data).hexdigest() != spec["zip_sha256"]:
                sys.exit(f"{font}: 받은 zip 의 sha256 이 고정값과 다르다")
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                for member in spec["weights"].values():
                    (CACHE / member).write_bytes(z.read(member))
        return path
    path = CACHE / f"MPLUSRounded1c-{name}.ttf"
    if not path.is_file():
        CACHE.mkdir(parents=True, exist_ok=True)
        print(f"원본 받는 중: {path.name}")
        urllib.request.urlretrieve(spec["url"].format(style=name), path)
    return path


def build() -> int:
    from fontTools import subset
    from fontTools.ttLib import TTFont

    OUT.mkdir(parents=True, exist_ok=True)
    lock = {"sources": {font: spec["source"] for font, spec in FONTS.items()}, "groups": {}}
    for group, (font, pages) in GROUPS.items():
        chars = needed_chars(pages)
        entry = {"font": font, "pages": pages, "chars": chars, "files": {}}
        missing: set[str] = set()
        for weight in FONTS[font]["weights"]:
            src = source(font, weight)
            cmap = TTFont(src)["cmap"].getBestCmap()
            missing.update(c for c in chars if ord(c) not in cmap)
            opts = subset.Options()
            opts.flavor = "woff2"
            opts.layout_features = ["*"]
            opts.name_IDs = ["*"]  # 라이선스(OFL) 표기를 남긴다
            loaded = subset.load_font(str(src), opts)
            sub = subset.Subsetter(opts)
            sub.populate(text=chars)
            sub.subset(loaded)
            out = font_path(font, group, weight)
            subset.save_font(loaded, str(out), opts)
            entry["files"][out.name] = hashlib.md5(out.read_bytes()).hexdigest()
            print(f"{out.relative_to(ROOT)}  {len(chars)}자  {out.stat().st_size // 1024}KB")
        entry["missing"] = "".join(sorted(missing))
        lock["groups"][group] = entry
        if entry["missing"]:
            print(f"  {group}: 원본에 없는 글자 {entry['missing']!r} 는 다음 글꼴로 보인다")
    LOCK.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


def check() -> int:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    errors = []
    for group, (font, pages) in GROUPS.items():
        entry = lock["groups"].get(group)
        if entry is None or entry.get("font") != font:
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
        print("CJK 글꼴 서브셋을 다시 만들어야 한다 (python3 scripts/subset-fonts.py):\n  "
              + "\n  ".join(errors), file=sys.stderr)
        return 1
    print("OK — CJK 글꼴 서브셋이 페이지 글자를 모두 담고 있다")
    return 0


if __name__ == "__main__":
    sys.exit(check() if "--check" in sys.argv else build())
