// analytics.js — Firebase Analytics(GA4) + Microsoft Clarity
// 정적 HTML 사이트(DotComponents)용 분석 연동. index.html <head>에서
// <script type="module" src="./analytics.js"></script> 로 로드된다.
//
// 주의: 아래 Firebase 웹 config와 Clarity 프로젝트 ID는 클라이언트에 노출되도록
// 설계된 공개 값이므로 그대로 커밋해도 보안상 문제 없다.

import { initializeApp } from "https://www.gstatic.com/firebasejs/12.15.0/firebase-app.js";
import { getAnalytics, logEvent } from "https://www.gstatic.com/firebasejs/12.15.0/firebase-analytics.js";

// ── 1) 설정값 ──────────────────────────────────────────────
const FIREBASE_CONFIG = {
  apiKey: "AIzaSyAA1obSBic4gU1NEYtkLPZzV8bER-dVnyk",
  authDomain: "buddybird-landing.firebaseapp.com",
  projectId: "buddybird-landing",
  storageBucket: "buddybird-landing.firebasestorage.app",
  messagingSenderId: "817671559020",
  appId: "1:817671559020:web:8aeba8cdc9be481f988549",
  measurementId: "G-7KBZ20F3C5",
};
const CLARITY_PROJECT_ID = "xeebvvdnhk";

// ── 2) Firebase 초기화 (page_view 자동 수집) ─────────────────
const app = initializeApp(FIREBASE_CONFIG);
const analytics = getAnalytics(app);

// ── 3) Microsoft Clarity 초기화 (공식 설치 스니펫) ───────────
(function (c, l, a, r, i, t, y) {
  c[a] = c[a] || function () { (c[a].q = c[a].q || []).push(arguments); };
  t = l.createElement(r); t.async = 1; t.src = "https://www.clarity.ms/tag/" + i;
  y = l.getElementsByTagName(r)[0]; y.parentNode.insertBefore(t, y);
})(window, document, "clarity", "script", CLARITY_PROJECT_ID);

// ── 4) 공통 추적 헬퍼: GA4 + Clarity 동시 전송 ───────────────
function track(name, params = {}) {
  logEvent(analytics, name, params);
  if (window.clarity) window.clarity("event", name);
}

// ── 5) 이벤트 위임 (DotComponents 리렌더에 안전) ─────────────
// 단일 리스너가 document 클릭을 받아 closest()로 대상 요소를 판별한다.
// 정적 <a>(다운로드/CTA/네비)와 DC가 렌더링하는 FAQ 토글 모두 대응.
document.addEventListener("click", (e) => {
  const t = e.target;

  // 앱 다운로드 (전환)
  if (t.closest('a[href*="apps.apple.com"]'))  return track("app_store_click");
  if (t.closest('a[href*="play.google.com"]')) return track("google_play_click");

  // 메인 CTA 버튼
  const cta = t.closest('a[href="#register"]');
  if (cta)  return track("cta_click", { label: cta.textContent.trim() });
  const feat = t.closest('a[href="#features"]');
  if (feat) return track("cta_features_click", { label: feat.textContent.trim() });

  // 상단 네비게이션 링크
  const nav = t.closest('header a[href^="#"]');
  if (nav)  return track("nav_click", { section: nav.getAttribute("href") });

  // FAQ 항목 펼침/접힘 (DC 렌더 결과는 cursor:pointer 인라인 스타일로 식별)
  const faq = t.closest('#faq [onclick], #faq div[style*="cursor:pointer"]');
  if (faq)  return track("faq_toggle", { question: faq.querySelector("span")?.textContent.trim() });
});
