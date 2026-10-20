# buddybird-landing

BuddyBird 랜딩페이지 (DotComponents 기반).

## 구성

### 페이지
- `index.html` — 루트 언어 라우터. 브라우저의 선호 언어 목록(`navigator.languages`)을 순서대로 보고 지원하는 첫 언어(`/ko/`·`/ja/`·`/ru/`·`/es/`·`/en/`)로 보낸다. 맞는 언어가 없으면 영어. 한 번 고른 언어는 `localStorage`의 `bb-lang`에 남는다. 새 언어를 열면 라우터의 `LANGS`와 각 페이지의 언어 메뉴에 추가한다
- `ko/`, `en/` — 실제 랜딩 본문. 각 언어 아래에 `privacy/`, `terms/`, `support/`가 있다
- `ja/` — 일본어 랜딩과 `privacy/`, `terms/`, `support/`. 개인정보 처리방침·이용약관은 한국어판을 번역한 것이다
- `ru/` — 러시아어 랜딩과 `privacy/`, `terms/`, `support/`. 구성은 `ja/`와 같다. 키릴 문자는 Nunito(Google Fonts)가 그리므로 글꼴 서브셋이 따로 없다
- `es/` — 스페인어(스페인, 앱과 같은 es-ES·tú) 랜딩과 `privacy/`, `terms/`, `support/`. 구성은 `ja/`와 같고, 글자는 Nunito가 그린다
- 개인정보 처리방침·이용약관은 한국어판이 원본이다. 각 언어판의 마지막 조항(언어)에 "번역본과 다르면 한국어판이 우선한다"고 적어 두었으니, 한국어판을 고치면 다른 언어판도 함께 고친다
- 언어 없는 `/privacy/`, `/terms/`, `/support/` — 파일은 없다. CloudFront 가 없는 경로에 루트 `index.html`을 돌려주므로, 라우터가 경로를 보고 방문자 언어의 같은 문서(`/ja/privacy/` 등)로 보낸다
- `dl/` — 스토어 진입점. 아래 "스토어 링크와 QR" 참고

### 에셋
- `assets/js/` — `support.js`(DotComponents 런타임), `analytics.js`(Firebase Analytics + Clarity), `consent.js`(쿠키 동의)
- 쿠키 동의 — 페이지는 `analytics.js`를 직접 로드하지 않고 `consent.js`를 로드한다. 브라우저 시간대가 유럽(`Europe/*`, 카나리아·키프로스 등 포함)이면 동의 배너를 띄우고, 허용해야 `analytics.js`를 불러온다. 선택은 `localStorage`의 `bb-consent`에 남고 푸터의 "쿠키 설정"으로 바꿀 수 있다. 그 밖의 시간대는 바로 로드한다. 배너 일본어 문구도 글꼴 서브셋 대상이라 문구를 고치면 `subset-fonts.py`를 다시 돌린다
- `assets/images/ko/`, `assets/images/en/`, `assets/images/ja/`, `assets/images/ru/`, `assets/images/es/` — 언어별 앱 스크린샷. `ja`·`ru`·`es`는 로컬 mock 데이터로 찍은 화면이다
- `assets/icons/` — `app-icon.png`(앵무새 원본 2048), `apple-touch-icon.png`(180), `favicon.png`(48)
- `assets/og-image.png`, `og-image-en.png`, `og-image-ja.png`, `og-image-ru.png`, `og-image-es.png` — 언어별 링크 공유 미리보기(Open Graph) 이미지 (1200×630)
- `assets/fonts/` — 일본어 글꼴(M PLUS Rounded 1c) 서브셋. 페이지에 쓰인 글자만 담아 굵기당 40~100KB다. 일본어 문구를 고치면 `pip install fonttools brotli` 후 `python3 scripts/subset-fonts.py`로 다시 만든다. CI가 `--check`로 빠진 글자를 잡는다
- 글꼴: 영문·숫자는 Nunito, 일본어는 M PLUS Rounded 1c, 한글은 Pretendard. 글꼴 목록은 Nunito → (언어 글꼴) → Pretendard 순서이고, 브라우저는 앞 글꼴에 없는 글자만 다음 글꼴로 그린다. 새 언어는 같은 둥근 계열을 목록에 더한다(힌디어 Baloo 2, 벵골어 Baloo Da 2)
- `assets/qr/` — `/dl/`로 가는 QR 코드
- `scripts/og-card.html` — OG 이미지 생성용 소스 (헤드리스 Chrome로 렌더). 서빙 대상이 아니라 HTML 검사에서 뺀다
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

Google Play는 `hl` 파라미터가 페이지 언어를 정한다. 언어가 분명한 랜딩(`/ko/`, `/en/`, `/ja/`, `/ru/`, `/es/`)에서는 해당 언어를 붙이고, 언어를 알 수 없는 `/dl/`에서는 붙이지 않아 기기 언어를 따르게 한다.

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
- 캐시: `assets/`는 브라우저에 1년 캐시(immutable)한다. 배포 직전 `scripts/stamp-assets.py`가 HTML의 `/assets/…` 참조에 내용 해시(`?v=…`)를 붙여, 파일이 바뀌면 URL도 바뀐다. 이 스크립트는 HTML을 직접 고치므로 로컬에서 돌렸다면 `git checkout -- '*.html'`로 되돌린다
- HTML 등 나머지는 브라우저가 매번 확인하고(`max-age=0`), CloudFront 엣지는 1년 보관한다(`s-maxage`). 배포 때 무효화(`/*`)로 엣지를 비운다
- `og-image*.png`, `icons/app-icon.png`는 외부(SNS·검색)에 절대 URL로 노출돼 해시를 붙일 수 없으므로 HTML과 같은 규칙이다. `assets/` 파일을 HTML이 아닌 곳에서 절대 URL로 새로 쓰게 되면 `deploy.yml`의 두 sync 목록에 같이 옮긴다
- 인증은 OIDC로 aws-infra가 만든 사이트 배포 역할을 assume한다(장기 키 없음). 사이트 신뢰 정책 sub이 `ref:refs/heads/main`이라 배포 job에는 `environment:`를 붙이지 않는다.
- 인프라 식별자는 repo secrets로 주입한다(Settings → Secrets and variables → Actions → Secrets): `AWS_DEPLOY_ROLE_ARN`, `SITE_BUCKET`, `SITE_DISTRIBUTION_ID`. 이 저장소는 public이고 aws-infra는 private이라 계정 정보를 코드·로그에 남기지 않는다.
- 인프라 정의(S3·CloudFront·OIDC 역할)는 사내 `aws-infra`의 `buddybird-app`(Pulumi)에 있다. 리전 `ap-northeast-2`.

### 버전과 릴리스

배포된 버전은 태그(`vX.Y.Z`)와 GitHub Release, `CHANGELOG.md`로 남긴다. buddybird-mobile·api와 같은 release-please를 쓴다(`.github/workflows/release.yml`).

1. `dev` → `main` 머지로 배포되면, release-please가 마지막 태그 이후 커밋을 읽어 릴리스 PR(`chore(main): release X.Y.Z`)을 만들거나 갱신한다
2. 릴리스 PR을 머지하면 태그와 GitHub Release가 생긴다. 릴리스 PR은 `CHANGELOG.md`와 `.github/.release-please-manifest.json`만 고치므로 `deploy.yml`이 다시 배포하지 않는다
3. 다음 배포 전에 릴리스 PR을 머지해 두지 않으면, 다음 배포 내용이 같은 릴리스 PR에 쌓인다

설정은 `.github/release-please-config.json`에 있다. 버전은 커밋 접두어로 정해진다. `feat`는 마이너, `fix`·`perf`·`docs`는 패치, 커밋 본문의 `BREAKING CHANGE:`는 메이저다. `docs`는 처리방침·약관 개정이라 릴리스에 넣는다. `ci`·`chore`·`refactor`·`style`은 릴리스를 만들지 않는다. 시작 버전은 2026-10-20 배포(#50)를 `v1.0.0`으로 잡았다(`bootstrap-sha`).

같은 변경이 CHANGELOG에 두 번 들어가지 않게 하는 규칙:

- release-please는 커밋 본문에서 빈 줄 뒤의 `feat:`·`fix:` 줄을 별도 커밋으로 읽는다. 머지 커밋 본문이 `feat(…)`로 시작하는 PR 제목이면 dev에서 이미 읽은 변경이 한 번 더 들어간다(2026-10-20 드라이런으로 재현). 그래서 저장소 설정에서 머지 커밋과 squash 커밋 모두 제목은 PR 제목, 본문은 비운다(Settings → General → Pull Requests의 "Pull request title"). buddybird-mobile과 같은 설정이다
- `dev` → `main` 배포 PR은 반드시 "Create a merge commit"으로 머지한다. squash로 머지하면 dev의 `feat`·`fix` 커밋이 `release(landing): …` 한 커밋으로 합쳐져 릴리스가 만들어지지 않고, rebase로 머지하면 dev 커밋이 새 해시로 복사돼 dev와 main 이력이 갈라진다
- 머지 커밋 제목이 PR 제목이 되므로, `dev` → `main` 배포 PR 제목은 `release(landing): …`처럼 CHANGELOG에 안 들어가는 접두어를 쓴다. `feat:`로 시작하면 dev에서 이미 들어간 변경이 한 번 더 들어간다
- 릴리스 PR의 커밋은 `main`에만 생긴다. `dev`는 이 파일들을 고치지 않으므로 충돌은 없고, 다음 배포 PR에서 그대로 합쳐진다
