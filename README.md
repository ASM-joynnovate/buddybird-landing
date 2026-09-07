# buddybird-landing

BuddyBird 랜딩페이지 (DotComponents 기반).

## 구성

### 페이지
- `index.html` — 루트 언어 라우터. 브라우저 언어를 보고 `/ko/` 또는 `/en/`으로 보낸다. 한 번 고른 언어는 `localStorage`의 `bb-lang`에 남는다
- `ko/`, `en/` — 실제 랜딩 본문. 각 언어 아래에 `privacy/`, `terms/`, `support/`가 있다
- `privacy/`, `terms/`, `support/` — 예전 경로. `/ko/`의 같은 페이지로 넘기는 리다이렉트 스텁이며 외부에 이미 퍼진 링크 때문에 남겨 둔다
- `dl/` — 스토어 진입점. 아래 "스토어 링크와 QR" 참고

### 에셋
- `assets/js/` — `support.js`(DotComponents 런타임), `analytics.js`(Firebase Analytics + Clarity)
- `assets/images/ko/`, `assets/images/en/` — 언어별 앱 스크린샷
- `assets/icons/` — `app-icon.png`(앵무새 원본 2048), `apple-touch-icon.png`(180), `favicon.png`(48)
- `assets/og-image.png` — 링크 공유 미리보기(Open Graph) 이미지 (1200×630)
- `assets/qr/` — `/dl/`로 가는 QR 코드
- `tools/og-card.html` — OG 이미지 생성용 소스 (헤드리스 Chrome로 렌더)
- `DESIGN.md` — 디자인 가이드
- `.thumbnail` — 페이지 미리보기 이미지 (WebP)

## 실행

`assets/js/`의 스크립트와 외부 폰트/CSS가 상대 경로로 로드되므로 `file://`이 아닌 HTTP로 서빙해야 합니다.

```bash
python3 -m http.server 8910
# 브라우저에서 http://localhost:8910/ 열기
```

정책·지원 페이지는 폴더형이라 `/ko/privacy/`, `/en/terms/` 처럼 접속됩니다.

## 스토어 링크와 QR

### 링크 규칙

App Store 링크에는 **지역 코드를 넣지 않는다.**

```
https://apps.apple.com/app/id6783652711
```

`/kr/`이나 `/us/`를 끼우면 그 지역 스토어로 고정되어, 다른 지역 계정 사용자는 설치할 수 없는 페이지를 보게 된다. 지역 코드를 빼면 Apple이 방문자 계정 지역의 스토어로 라우팅한다.

Google Play는 `hl` 파라미터가 페이지 언어를 정한다. 언어가 분명한 랜딩(`/ko/`, `/en/`)에서는 해당 언어를 붙이고, 언어를 알 수 없는 `/dl/`에서는 붙이지 않아 기기 언어를 따르게 한다.

링크가 들어 있는 곳은 언어별 랜딩의 하단 CTA와 `<head>`의 JSON-LD `downloadUrl`, 그리고 `dl/index.html`이다. 앱 ID가 바뀌면 세 곳을 함께 고쳐야 한다.

### `/dl/` 진입점

QR 코드는 URL 문자열 하나만 담을 수 있어 iOS·Android를 코드 자체로 가를 수 없다. 그래서 `https://buddybird.xyz/dl/` 한 곳으로 보내고, 페이지가 User-Agent를 보고 각 스토어로 넘긴다.

- iOS(iPadOS 13+ 의 Mac 위장 UA 포함) → App Store
- Android → Google Play
- 데스크톱 → 넘기지 않고 두 스토어 버튼을 보여준다

리다이렉트 스크립트는 스타일·폰트보다 먼저 실행되도록 `<head>` 맨 위에 둔다. 아래 리소스를 기다리면 그만큼 이동이 늦어진다. 버튼은 리다이렉트 성공 여부와 무관하게 항상 DOM에 있는데, 카카오톡·인스타그램 인앱 브라우저처럼 이동이 막히는 환경에서 폴백이 되기 때문이다.

`noindex`라 검색 색인과 `sitemap.xml`에 넣지 않는다.

### `/dl/` 유입 집계

QR로 몇 명이 들어왔는지는 GA4에서 본다. 랜딩과 같은 속성(`G-7KBZ20F3C5`)의 `page_view` 이벤트이므로 **보고서 → 페이지 및 화면**에서 경로 `/dl/`로 찾으면 되고, `platform` 이벤트 파라미터에 `ios`·`android`·`desktop`이 들어가 OS별로도 갈린다.

다른 페이지처럼 `analytics.js`를 붙이지 않은 이유가 있다. 모바일에서는 리다이렉트가 먼저 일어나 Firebase 모듈을 받아오는 동안 이미 페이지를 떠나므로 이벤트가 나가지 않는다. 그래서 라이브러리 없이 `navigator.sendBeacon`으로 GA4에 직접 쏜다. 큐에 넣는 즉시 리턴하고 언로드 중에도 전송이 보장되므로 이동이 늦어지지 않는다.

`platform` 을 GA4 보고서에서 차원으로 쓰려면 **관리 → 맞춤 정의**에서 이벤트 매개변수 `platform` 을 맞춤 측정기준으로 한 번 등록해야 한다. 등록하지 않아도 실시간 보고서에서는 보인다.

집계에 쓰는 `/g/collect` 는 gtag.js 가 내부적으로 쓰는 엔드포인트다. API secret이 필요 없는 대신 공식 문서에 없는 경로라서, GA4에서 `/dl/` 수치가 갑자기 0이 되면 이 호출부터 확인한다.

### QR 코드

| 파일 | 용도 |
|---|---|
| `assets/qr/buddybird-dl.svg` | 인쇄물 (포스터·명함·배너) |
| `assets/qr/buddybird-dl.png` | 화면·슬라이드·SNS (1024px) |

`https://buddybird.xyz/dl/`을 오류정정 레벨 H로 인코딩했다. 레벨 H는 코드의 30%가 가려져도 복원되므로 가운데에 로고를 얹어도 스캔된다.

다시 만들어야 하면:

```bash
npx qrcode -e H -t svg -o assets/qr/buddybird-dl.svg "https://buddybird.xyz/dl/"
npx qrcode -e H -t png -w 1024 -o assets/qr/buddybird-dl.png "https://buddybird.xyz/dl/"
```

**목적지 URL은 바꾸지 않는다.** 이미 인쇄해 뿌린 QR은 회수할 수 없다. 스토어 링크가 바뀌든 웹 버전이 생기든 `dl/index.html` 내용만 고치면 기존 QR이 그대로 살아 있고, 이게 자체 도메인을 거치는 이유다.

인쇄 전에는 실물 크기로 뽑아 실제 스캔 거리에서 읽히는지 확인한다. 포스터라면 QR 한 변을 스캔 거리의 1/10 정도로 잡는다(2m 거리 → 20cm). QR 둘레의 흰 여백은 잘라내지 않는다.

## 배포

`main`에 머지되면 GitHub Actions(`.github/workflows/deploy.yml`)가 AWS S3로 파일을 sync하고 CloudFront 캐시를 무효화한다. 도메인 `buddybird.xyz`는 Cloudflare DNS(CNAME, DNS-only)로 CloudFront에 붙는다.

작업 브랜치에서 `dev`로 PR을 올려 머지하고, 배포할 때 `dev` → `main` PR을 머지하면 main push로 배포가 돈다.

- S3 sync는 allowlist 방식이다. `--exclude "*"`로 전부 막고 서빙 대상만 `--include`로 열기 때문에, 새 서빙 경로를 만들면 `deploy.yml`의 목록에 같이 추가해야 한다. 빼먹으면 배포는 성공하고 그 경로만 404가 된다.
- 인증은 OIDC로 aws-infra가 만든 사이트 배포 역할을 assume한다(장기 키 없음). 사이트 신뢰 정책 sub이 `ref:refs/heads/main`이라 배포 job에는 `environment:`를 붙이지 않는다.
- 인프라 식별자는 repo secrets로 주입한다(Settings → Secrets and variables → Actions → Secrets): `AWS_DEPLOY_ROLE_ARN`, `SITE_BUCKET`, `SITE_DISTRIBUTION_ID`. 이 저장소는 public이고 aws-infra는 private이라 계정 정보를 코드·로그에 남기지 않는다.
- 인프라 정의(S3·CloudFront·OIDC 역할)는 사내 `aws-infra`의 `buddybird-app`(Pulumi)에 있다. 리전 `ap-northeast-2`.
