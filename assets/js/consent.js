// consent.js — 분석(analytics.js) 로드 전에 쿠키 동의를 확인한다.
// 페이지에서 <script src="/assets/js/consent.js" data-analytics="/assets/js/analytics.js" defer></script> 로 로드한다.
// analytics.js 경로를 data 속성으로 받는 이유: 배포 때 stamp-assets.py 가 HTML 안의 /assets/ 참조에만
// 버전 쿼리(?v=)를 붙이므로, JS 안에 경로를 적으면 1년 캐시된 옛 파일을 계속 받는다.
//
// EU 등 사전 동의가 필요한 지역(브라우저 시간대로 판별)에서만 배너를 띄운다.
// 그 밖의 방문자는 지금까지처럼 바로 분석을 로드한다.

(function () {
  var ANALYTICS = document.currentScript && document.currentScript.dataset.analytics;
  var KEY = 'bb-consent'; // 'granted' | 'denied'

  // ── 1) 동의가 필요한 지역 ─────────────────────────────────
  // EU·EEA·영국·스위스(GDPR, ePrivacy)와 튀르키예(KVKK)가 Europe/* 시간대에 들어간다.
  // 유럽 밖 시간대를 쓰는 EU 지역(카나리아·마데이라·아조레스, 키프로스, 아이슬란드)을 더한다.
  var EXTRA_ZONES = ['Atlantic/Canary', 'Atlantic/Madeira', 'Atlantic/Azores', 'Atlantic/Reykjavik',
    'Atlantic/Faroe', 'Asia/Nicosia', 'Asia/Famagusta'];

  function needsConsent() {
    try {
      var tz = Intl.DateTimeFormat().resolvedOptions().timeZone || '';
      return tz.indexOf('Europe/') === 0 || EXTRA_ZONES.indexOf(tz) !== -1;
    } catch (e) {
      return true; // 판별할 수 없으면 동의를 받는 쪽이 안전하다
    }
  }

  function read() {
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function write(v) {
    try { localStorage.setItem(KEY, v); } catch (e) {}
  }

  function loadAnalytics(signalClarity) {
    if (!ANALYTICS) return;
    import(ANALYTICS).then(function () {
      // Clarity 는 EEA·영국·스위스 방문자에게 동의 신호가 없으면 쿠키를 쓰지 않는다
      if (signalClarity && window.clarity) {
        window.clarity('consentv2', { ad_Storage: 'denied', analytics_Storage: 'granted' });
      }
    }).catch(function () {});
  }

  // ── 2) 문구 ──────────────────────────────────────────────
  var T = {
    ko: { text: '방문 통계를 위해 Google Analytics와 Microsoft Clarity 쿠키를 사용해도 될까요? 거절해도 사이트 이용에는 차이가 없어요.',
          accept: '허용', reject: '거절', settings: '쿠키 설정', policy: '개인정보 처리방침', label: '쿠키 동의' },
    en: { text: 'Can we use Google Analytics and Microsoft Clarity cookies to see how visitors use this site? Declining won’t change anything else.',
          accept: 'Accept', reject: 'Decline', settings: 'Cookie settings', policy: 'Privacy policy', label: 'Cookie consent' },
    ja: { text: 'サイトの利用状況を知るため、Google Analytics と Microsoft Clarity の Cookie を使ってもよいですか？拒否してもサイトはそのまま使えます。',
          accept: '許可', reject: '拒否', settings: 'Cookie 設定', policy: 'プライバシーポリシー', label: 'Cookie の同意' },
    ru: { text: 'Можно использовать файлы cookie Google Analytics и Microsoft Clarity, чтобы понимать, как посетители пользуются сайтом? Если откажетесь, сайт будет работать как обычно.',
          accept: 'Принять', reject: 'Отклонить', settings: 'Настройки cookie', policy: 'Политика конфиденциальности', label: 'Согласие на cookie' },
    es: { text: '¿Podemos usar cookies de Google Analytics y Microsoft Clarity para saber cómo se usa esta web? Si las rechazas, la web funciona igual.',
          accept: 'Aceptar', reject: 'Rechazar', settings: 'Configurar cookies', policy: 'Política de privacidad', label: 'Consentimiento de cookies' }
  };
  var lang = (document.documentElement.lang || 'en').slice(0, 2);
  var t = T[lang] || T.en;
  var base = T[lang] ? '/' + lang : '/en';

  // ── 3) 배너 ──────────────────────────────────────────────
  var CSS =
    '.bb-consent{position:fixed;z-index:1000;left:16px;right:16px;bottom:16px;max-width:560px;margin:0 auto;' +
    'background:#fff;color:#3C3C3C;border:2px solid #E5E5E5;border-radius:16px;box-shadow:0 4px 0 #E5E5E5;' +
    'padding:16px 18px;font:700 14px/1.55 Nunito,"Pretendard Variable",Pretendard,-apple-system,system-ui,sans-serif}' +
    '.bb-consent p{margin:0 0 12px}' +
    '.bb-consent a{color:inherit;text-decoration:underline}' +
    '.bb-consent .row{display:flex;gap:10px}' +
    '.bb-consent button{flex:1;min-height:44px;border-radius:12px;border:2px solid #D4D4D4;background:#fff;' +
    'color:#3C3C3C;font-family:inherit;font-weight:800;font-size:15px;line-height:1;cursor:pointer;box-shadow:0 3px 0 #D4D4D4}' +
    '.bb-consent button:active{transform:translateY(2px);box-shadow:0 1px 0 #D4D4D4}' +
    '.bb-consent button:focus-visible{outline:3px solid #1CB0F6;outline-offset:2px}' +
    '.bb-cookie-settings{background:none;border:0;padding:0;cursor:pointer}' +
    '.bb-cookie-settings:hover{color:#FF9600!important}';

  function addStyle() {
    if (document.getElementById('bb-consent-css')) return;
    var s = document.createElement('style');
    s.id = 'bb-consent-css';
    s.textContent = CSS;
    document.head.appendChild(s);
  }

  function showBanner() {
    if (document.querySelector('.bb-consent')) return;
    addStyle();
    var box = document.createElement('div');
    box.className = 'bb-consent';
    box.setAttribute('role', 'region');
    box.setAttribute('aria-label', t.label);
    box.innerHTML = '<p></p><div class="row"><button type="button" data-v="denied"></button>' +
      '<button type="button" data-v="granted"></button></div>';
    var p = box.querySelector('p');
    p.textContent = t.text + ' ';
    var a = document.createElement('a');
    a.href = base + '/privacy/';
    a.textContent = t.policy;
    p.appendChild(a);
    box.querySelector('[data-v="denied"]').textContent = t.reject;
    box.querySelector('[data-v="granted"]').textContent = t.accept;
    box.addEventListener('click', function (e) {
      var v = e.target.closest('button') && e.target.closest('button').getAttribute('data-v');
      if (!v) return;
      var before = read();
      write(v);
      box.remove();
      if (v === 'granted' && before !== 'granted') loadAnalytics(true);
      // 이미 로드된 분석은 내릴 수 없으므로 쿠키를 지우고 새로 연다
      if (v === 'denied' && before === 'granted') {
        if (window.clarity) window.clarity('consent', false);
        clearCookies();
        location.reload();
      }
    });
    document.body.appendChild(box);
  }

  function clearCookies() {
    document.cookie.split(';').forEach(function (c) {
      var name = c.split('=')[0].trim();
      if (/^(_ga|_gid|_cl)/.test(name)) {
        var host = location.hostname;
        document.cookie = name + '=; Max-Age=0; path=/';
        document.cookie = name + '=; Max-Age=0; path=/; domain=.' + host.replace(/^www\./, '');
      }
    });
  }

  // 푸터의 고객지원 링크 뒤에 '쿠키 설정'을 붙여 선택을 다시 바꿀 수 있게 한다
  function addSettingsLink() {
    var support = document.querySelector('footer a[href="' + base + '/support/"]');
    if (!support) return;
    addStyle();
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'bb-cookie-settings' + (support.className ? ' ' + support.className : '');
    btn.textContent = t.settings;
    btn.addEventListener('click', showBanner);
    // 랜딩과 문서 페이지의 푸터 스타일이 달라, 옆 링크의 글꼴과 색을 그대로 따른다
    var cs = getComputedStyle(support);
    ['fontFamily', 'fontSize', 'fontWeight', 'lineHeight', 'letterSpacing', 'color'].forEach(function (k) { btn.style[k] = cs[k]; });
    // 문서 페이지 푸터는 링크 사이에 '·' 구분자를 둔다
    var sep = support.previousElementSibling;
    if (sep && sep.tagName === 'SPAN') {
      var s2 = sep.cloneNode(true);
      support.after(s2);
      s2.after(btn);
    } else {
      support.after(btn);
    }
  }

  // ── 4) 시작 ──────────────────────────────────────────────
  if (!needsConsent()) {
    loadAnalytics(false);
    return;
  }
  addSettingsLink();
  var state = read();
  if (state === 'granted') loadAnalytics(true);
  else if (state !== 'denied') showBanner();
})();
