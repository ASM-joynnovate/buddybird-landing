# buddybird-landing

BuddyBird 랜딩페이지 (DotComponents 기반).

## 구성
- `index.html` — 랜딩페이지 마크업 (DotComponents `.dc` 문법, `support.js` 런타임 로드)
- `support.js` — DotComponents 런타임
- `DESIGN.md` — 디자인 가이드
- `.thumbnail` — 페이지 미리보기 이미지 (WebP)

## 실행
`support.js`와 외부 폰트/CSS가 상대 경로로 로드되므로 `file://`이 아닌 HTTP로 서빙해야 합니다.

```bash
python3 -m http.server 8910
# 브라우저에서 http://localhost:8910/index.html 열기
```
