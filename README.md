# buddybird-landing

BuddyBird 랜딩페이지 (DotComponents 기반).

## 구성
- `index.html` — 랜딩페이지 마크업 (DotComponents `.dc` 문법)
- `assets/js/` — `support.js`(DotComponents 런타임), `analytics.js`(Firebase Analytics + Clarity)
- `assets/images/` — 앱 스크린샷
- `assets/icons/` — `app-icon.png`(앵무새 원본 2048), `apple-touch-icon.png`(180), `favicon.png`(48)
- `assets/og-image.png` — 링크 공유 미리보기(Open Graph) 이미지 (1200×630)
- `tools/og-card.html` — OG 이미지 생성용 소스 (헤드리스 Chrome로 렌더)
- `DESIGN.md` — 디자인 가이드
- `.thumbnail` — 페이지 미리보기 이미지 (WebP)

## 실행
`assets/js/`의 스크립트와 외부 폰트/CSS가 상대 경로로 로드되므로 `file://`이 아닌 HTTP로 서빙해야 합니다.

```bash
python3 -m http.server 8910
# 브라우저에서 http://localhost:8910/index.html 열기
```

정책·지원 페이지는 폴더형(`privacy/index.html` 등)이라 `/privacy/`, `/terms/`, `/support/` 로 접속됩니다.
