#!/usr/bin/env python3
"""CJK·태국어·벵골어 페이지에 쓰인 글자만 담은 글꼴 서브셋(woff2)을 만든다.

- 일본어: M PLUS Rounded 1c (google/fonts)
- 번체 중국어: 源泉圓體 TW (GenSen Rounded 2 TW, ButTaiwan/gensen-font). 대만 교육부 표준 자형이라
  일본 자형인 M PLUS 를 쓰지 않는다
- 간체 중국어: 自由圆体 CN (Resource Han Rounded CN, CyanoHao/Resource-Han-Rounded). 본토 표준 자형이고
  번체의 GenSen 처럼 Source Han Sans 를 둥글린 글꼴이다. 가변 글꼴만 배포돼서 700·900 으로 고정해 쓴다
- 벵골어: Baloo Da 2 (google/fonts). Nunito 처럼 획 끝이 둥근 Baloo 계열의 벵골 문자판이다.
  가변 글꼴(wght 400~800)이라 페이지 굵기 700·800·900 을 600·700·800 으로 고정해 쓴다
- 태국어: Mitr (google/fonts). 획 끝이 둥근 고리 없는 태국 문자 글꼴이라 Nunito 와 어울린다.
  Mitr 는 700 까지라 페이지 굵기 700·800·900 을 Mitr 500·600·700 으로 그린다

CJK 글꼴은 한 굵기가 3~16MB 이고, Google Fonts 로 받으면 조각 수십 개(일본어 랜딩에서 약 650KB)를 받는다.
페이지에 실제로 쓰인 글자만 잘라 직접 올리면 굵기당 40~110KB 다.

- 만들기: `python3 scripts/subset-fonts.py` (fonttools·brotli·py7zr 필요: `pip install fonttools brotli py7zr`)
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
import unicodedata
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCK = ROOT / "scripts" / "fonts.lock.json"
OUT = ROOT / "assets" / "fonts"
CACHE = ROOT / ".cache" / "fonts"

MPLUS_COMMIT = "84efd8ad78c3710ad14bd909e3bc407151885628"  # google/fonts, 2026-05-01
GENSEN_RELEASE = "v2.100"  # ButTaiwan/gensen-font, 2024-08-22
RHR_RELEASE = "v1.910"  # CyanoHao/Resource-Han-Rounded, 2022-04-23
FONTS = {
    "mplus-rounded-1c": {
        "source": MPLUS_COMMIT,
        "url": f"https://raw.githubusercontent.com/google/fonts/{MPLUS_COMMIT}/ofl/mplusrounded1c/MPLUSRounded1c-{{style}}.ttf",
        "weights": {700: "Bold", 800: "ExtraBold", 900: "Black"},
    },
    "mitr": {
        "source": MPLUS_COMMIT,
        "url": f"https://raw.githubusercontent.com/google/fonts/{MPLUS_COMMIT}/ofl/mitr/Mitr-{{style}}.ttf",
        "weights": {500: "Medium", 600: "SemiBold", 700: "Bold"},
        # 페이지 글자가 아니라 태국 문자 블록 전체를 담는다(굵기당 10KB 안팎). 브라우저는 ำ 를 ํ + า 로
        # 나눠 그리므로 페이지에 없는 글자도 필요하다. 쿠키 배너의 일본어·중국어 문구는 이 글꼴과 상관없다
        "only": ("\u0e00", "\u0e7f"),
    },
    "baloo-da-2": {
        "source": MPLUS_COMMIT,
        "url": f"https://raw.githubusercontent.com/google/fonts/{MPLUS_COMMIT}/ofl/balooda2/BalooDa2%5Bwght%5D.ttf",
        "variable": "BalooDa2[wght].ttf",
        "weights": {600: 600, 700: 700, 800: 800},
        # 벵골 문자는 자음이 겹쳐 합자(যুক্তাক্ষর)가 되므로 페이지 글자가 아니라 블록 전체를 담는다.
        # 단다(। ॥)는 데바나가리 블록에 있고, ZWNJ·ZWJ 는 합자를 끊거나 잇는 데 쓴다
        "only": ("\u0980", "\u09ff"),
        "extra": "\u0964\u0965\u200c\u200d\u25cc",
    },
    # 굵기가 B(700)·H(900)로 벌어져 있어 페이지의 700·800 은 B 한 벌로 그린다(@font-face 의 font-weight:700 800)
    "gensen-rounded-tw": {
        "source": GENSEN_RELEASE,
        "zip": f"https://github.com/ButTaiwan/gensen-font/releases/download/{GENSEN_RELEASE}/GenSenRounded2TW-otf.zip",
        "zip_sha256": "c5a18c0661c0b26effe5503431f2fee176137f6451be3ae37b9787c6179cf325",
        "weights": {700: "GenSenRounded2TW-B.otf", 900: "GenSenRounded2TW-H.otf"},
    },
    # 가변 글꼴(wght 200~900, ROND 0~100)을 잘라낸 뒤 굵기를 고정한다. 굵기 축 사이 단계는 쓰지 않는다
    "resource-han-rounded-cn": {
        "source": RHR_RELEASE,
        "archive": f"https://github.com/CyanoHao/Resource-Han-Rounded/releases/download/{RHR_RELEASE}/RHR-CFF2-CN-1.910.7z",
        "archive_sha256": "4ad7b141535a1f11831287b0a6f71ddcec8daa92dc1d82c59892068f8ae5df09",
        "variable": "ResourceHanRoundedCN-VF.otf",
        "weights": {700: 700, 900: 900},
    },
}

# 랜딩과 문서 페이지는 글자 수 차이가 커서 따로 자른다.
# consent.js 는 두 그룹 페이지 모두에 쿠키 배너(언어별 문구 포함)를 띄우므로 양쪽에 넣는다.
GROUPS = {
    "ja-landing": ("mplus-rounded-1c", ["ja/index.html", "assets/js/consent.js"]),
    "ja-docs": ("mplus-rounded-1c", ["ja/support/index.html", "ja/privacy/index.html", "ja/terms/index.html", "assets/js/consent.js"]),
    "zh-tw-landing": ("gensen-rounded-tw", ["zh-tw/index.html", "assets/js/consent.js"]),
    "zh-tw-docs": ("gensen-rounded-tw", ["zh-tw/support/index.html", "zh-tw/privacy/index.html", "zh-tw/terms/index.html", "assets/js/consent.js"]),
    "zh-cn-landing": ("resource-han-rounded-cn", ["zh-cn/index.html", "assets/js/consent.js"]),
    "zh-cn-docs": ("resource-han-rounded-cn", ["zh-cn/support/index.html", "zh-cn/privacy/index.html", "zh-cn/terms/index.html", "assets/js/consent.js"]),
    "bn": ("baloo-da-2", ["bn/index.html", "bn/support/index.html", "bn/privacy/index.html", "bn/terms/index.html"]),
    # 태국어는 블록 전체를 담아 랜딩·문서 서브셋이 같아지므로 한 벌만 만든다
    "th": ("mitr", ["th/index.html", "th/support/index.html", "th/privacy/index.html", "th/terms/index.html"]),
}


def needed_chars(pages: list[str], only: tuple[str, str] | None = None, extra: str = "") -> str:
    chars: set[str] = set()
    for page in pages:
        text = (ROOT / page).read_text(encoding="utf-8")
        text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
        # 한글·라틴·키릴은 다른 글꼴이 그리고, 쿠키 배너의 태국어·벵골어 문구는 블록 전체를 담은 각 언어 서브셋이 맡는다
        chars.update(c for c in text if ord(c) > 0x7F and not ("가" <= c <= "힣") and not (" " <= c <= "ɏ") and not ("Ѐ" <= c <= "ӿ") and not ("\u0964" <= c <= "\u09ff") and not ("\u0e00" <= c <= "\u0e7f"))
    if only:
        chars = {chr(i) for i in range(ord(only[0]), ord(only[1]) + 1) if unicodedata.category(chr(i)) != "Cn"}
        chars.update(extra)
    return "".join(sorted(chars))


def font_path(font: str, group: str, weight: int) -> Path:
    return OUT / f"{font}-{group}-{weight}.woff2"


def variable_source(font: str) -> Path:
    import py7zr

    spec = FONTS[font]
    path = CACHE / spec["variable"]
    if not path.is_file() and "url" in spec:
        CACHE.mkdir(parents=True, exist_ok=True)
        print(f"원본 받는 중: {path.name}")
        urllib.request.urlretrieve(spec["url"], path)
    if not path.is_file():
        CACHE.mkdir(parents=True, exist_ok=True)
        print(f"원본 받는 중: {spec['archive'].rsplit('/', 1)[1]}")
        data = urllib.request.urlopen(spec["archive"]).read()
        if hashlib.sha256(data).hexdigest() != spec["archive_sha256"]:
            sys.exit(f"{font}: 받은 7z 의 sha256 이 고정값과 다르다")
        with py7zr.SevenZipFile(io.BytesIO(data)) as z:
            z.extract(path=CACHE, targets=[spec["variable"]])
    return path


def subset_variable(font: str, weight: int, chars: str, out: Path) -> None:
    from fontTools import subset
    from fontTools.cffLib.CFF2ToCFF import convertCFF2ToCFF
    from fontTools.varLib import instancer

    if "url" in FONTS[font]:
        # TrueType 가변 글꼴은 굵기를 먼저 고정하고 자른다. 벵골 문자의 모음 부호 위치가 GPOS 에 있어 남긴다
        fixed = instancer.instantiateVariableFont(subset.load_font(str(variable_source(font)), subset.Options()), {"wght": FONTS[font]["weights"][weight]})
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["*"]
        opts.name_IDs = ["*"]
        sub = subset.Subsetter(opts)
        sub.populate(text=chars)
        sub.subset(fixed)
        subset.save_font(fixed, str(out), opts)
        return
    opts = subset.Options()
    opts.layout_features = ["*"]
    opts.name_IDs = ["*"]
    # 이 글꼴의 GPOS 는 굵기 고정 때 병합되지 않는다(InconsistentGlyphOrder).
    # 라틴 커닝·세로쓰기 조정뿐이라 뺀다: 라틴은 Nunito 가 그리고 페이지는 가로쓰기다
    opts.drop_tables += ["GPOS"]
    loaded = subset.load_font(str(variable_source(font)), opts)
    sub = subset.Subsetter(opts)
    sub.populate(text=chars)
    sub.subset(loaded)
    fixed = instancer.instantiateVariableFont(loaded, {"wght": FONTS[font]["weights"][weight], "ROND": 100})
    convertCFF2ToCFF(fixed)
    fixed.flavor = "woff2"
    fixed.save(str(out))


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
    path = CACHE / spec["url"].format(style=name).rsplit("/", 1)[1]
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
        chars = needed_chars(pages, FONTS[font].get("only"), FONTS[font].get("extra", ""))
        entry = {"font": font, "pages": pages, "chars": chars, "files": {}}
        missing: set[str] = set()
        for weight in FONTS[font]["weights"]:
            out = font_path(font, group, weight)
            if "variable" in FONTS[font]:
                cmap = TTFont(variable_source(font))["cmap"].getBestCmap()
                missing.update(c for c in chars if ord(c) not in cmap)
                subset_variable(font, weight, chars, out)
                entry["files"][out.name] = hashlib.md5(out.read_bytes()).hexdigest()
                print(f"{out.relative_to(ROOT)}  {len(chars)}자  {out.stat().st_size // 1024}KB")
                continue
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
        new = [c for c in needed_chars(pages, FONTS[font].get("only"), FONTS[font].get("extra", "")) if c not in covered]
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
