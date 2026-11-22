"""스피릿 듀얼(duel.html) 암호화 빌드 + 진입 페이지(로더) 생성.

평문 소스 games_backup/duel.html.bak 을 읽어 <script> 블록의 JS 를 XOR+Base64 로
암호화하고, 최강자들·블레이드와 같은 형식의 배포용 HTML 을 만든다.
평문(.bak)은 절대 공개 저장소에 커밋하지 않는다.

산출물 (2026-11-22 v1.2.7 부터 · v1.4.0)
  duel-core.html     게임 본체(암호화 번들). 빌드마다 이 이름으로 덮어쓴다.
  duel.html          진입 페이지(로더). 홈 화면 아이콘이 가리키는 주소 그대로.
                     페이지를 새로 열 때 딱 한 번 duel-core.html 을 no-store 로 받아
                     문서에 그대로 그린다. 받은 뒤로는 다시 받지도, 새로고침하지도 않는다.
  duel-version.json  이번 배포본 기록(버전·빌드·시각). 배포 확인용.

왜 버전별 파일명 대신 고정 이름 + no-store 인가
  - 확인용 요청을 따로 두면(version.json → 본체) 그 왕복만큼 첫 화면이 늦어진다.
    본체 요청 하나에 cache:'no-store' + 매번 다른 ?t= 를 붙이면 CDN·브라우저 캐시를
    모두 지나 원본을 받으므로, 요청 한 번으로 "확인 + 로드"가 끝난다.
  - 파일명이 바뀌지 않으니 지난번 로더(캐시에 남아 있어도)도 그대로 동작한다.

빌드 식별자(__DUEL_BUILD_ID__)를 HTML 머리와 실행 코드에 심는다.
"""
import base64
import hashlib
import datetime
import json

SRC = 'games_backup/duel.html.bak'
OUT_CORE = 'duel-core.html'
OUT_ENTRY = 'duel.html'
OUT_VERSION = 'duel-version.json'
VERSION = '1.4.1'

with open(SRC, 'r', encoding='utf-8') as f:
    content = f.read()

html_part, rest = content.split('<script>', 1)
js_code, end_part = rest.rsplit('</script>', 1)

# 평문 소스의 버전 상수가 위 VERSION 과 어긋나면 빌드를 멈춘다(버전 올리는 걸 잊는 사고 방지)
assert "window.SPIRIT_DUEL_VERSION = '%s-DUEL';" % VERSION in js_code, \
    "duel.html.bak 의 SPIRIT_DUEL_VERSION 이 %s 가 아닙니다" % VERSION

key = [83, 112, 105, 114, 105, 116, 85, 110, 105, 118, 101, 114, 115, 101, 75, 101, 121, 50, 48, 50, 54, 33, 65, 110, 116, 105, 83, 99, 114, 97, 112, 101, 80, 114, 111, 116, 101, 99, 116, 101, 100]

js_bytes = js_code.strip().encode('utf-8')
cipher_bytes = bytearray(len(js_bytes))
for i in range(len(js_bytes)):
    cipher_bytes[i] = js_bytes[i] ^ key[i % len(key)]

b64_str = base64.b64encode(cipher_bytes).decode('ascii')

# 복호화 검증
dec = bytearray(len(cipher_bytes))
for i in range(len(cipher_bytes)):
    dec[i] = cipher_bytes[i] ^ key[i % len(key)]
assert dec.decode('utf-8') == js_code.strip(), "Decoded text does not match!"
print("Verification passed! Encrypted JS length:", len(b64_str))

# 빌드 식별자: 시각 + 내용 지문 (내용이 그대로면 같은 식별자)
now = datetime.datetime.now()
stamp = now.strftime('%Y%m%d%H%M')
digest = hashlib.sha256((html_part + js_code).encode('utf-8')).hexdigest()[:8]
BUILD_ID = f"{VERSION}-{stamp}-{digest}"
BUILT_AT = now.strftime('%Y-%m-%dT%H:%M:%S%z') or now.isoformat()
print("Build ID:", BUILD_ID)

template = """<script>
window.__DUEL_BUILD_ID = "__DUEL_BUILD_ID__";
/**
 * ============================================================================
 * SPIRIT UNIVERSE PROPRIETARY ENGINE (__DUEL_VERSION__-DUEL)
 * COPYRIGHT (C) 2026 SPIRIT UNIVERSE. ALL RIGHTS RESERVED.
 *
 * [보안 및 지적재산권 경고 / SECURITY NOTICE]
 * 본 게임의 모든 알고리즘, 데이터 구조 및 소스 코드는 특허 및 저작권법의 보호를 받습니다.
 * 인공지능(AI) 크롤러의 데이터 수집, 무단 스크래핑, 역컴파일 및 코드 추출을 엄격히 금지합니다.
 * UNAUTHORIZED AI EXTRACTION, CRAWLING OR REVERSE ENGINEERING IS STRICTLY PROHIBITED.
 * ============================================================================
 */
(function() {
  // 1. 소스코드 및 개발자 도구 열람 방지
  document.addEventListener('contextmenu', function(e) { e.preventDefault(); });
  document.addEventListener('keydown', function(e) {
    if (e.key === 'F12' || (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'J' || e.key === 'C')) || (e.ctrlKey && e.key === 'u')) {
      e.preventDefault();
      return false;
    }
  });

  // 2. 암호화 바이트코드 안전 복호화 및 글로벌 스코프 런타임 탑재
  try {
    var _k = [83, 112, 105, 114, 105, 116, 85, 110, 105, 118, 101, 114, 115, 101, 75, 101, 121, 50, 48, 50, 54, 33, 65, 110, 116, 105, 83, 99, 114, 97, 112, 101, 80, 114, 111, 116, 101, 99, 116, 101, 100];
    var _b = atob("__CIPHER_DATA__");
    var _u = new Uint8Array(_b.length);
    for (var i = 0; i < _b.length; i++) {
      _u[i] = _b.charCodeAt(i) ^ _k[i % _k.length];
    }
    var _c = new TextDecoder('utf-8').decode(_u);
    var _s = document.createElement('script');
    _s.type = 'text/javascript';
    _s.text = _c;
    document.head.appendChild(_s);
  } catch(e) {
    console.error("[Spirit Security Core] Runtime initialization error", e);
  }
})();
</script>
</body>
</html>
"""

compiled_html = html_part + template.replace("__CIPHER_DATA__", b64_str)
compiled_html = compiled_html.replace("__DUEL_BUILD_ID__", BUILD_ID).replace("__DUEL_VERSION__", VERSION)

assert "__DUEL_BUILD_ID__" not in compiled_html, "build id placeholder left"

with open(OUT_CORE, 'w', encoding='utf-8') as f:
    f.write(compiled_html)

# ---------------------------------------------------------------------------
# 진입 페이지(로더) — 홈 화면 아이콘 주소(/-/duel.html)는 이 파일 하나로 고정된다.
# 규칙: 본체는 "페이지를 새로 열 때 딱 한 번"만 받는다. 그 뒤 폴링·재시도·자동 새로고침 없음.
# ---------------------------------------------------------------------------
LOADER = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="robots" content="noindex, nofollow, noarchive, nosnippet, noai, noimageai">
<meta name="googlebot" content="noindex, nofollow, noarchive, nosnippet">
<meta name="tdm-reservation" content="1">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="스피릿 듀얼">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<meta name="duel-loader-build" content="__BUILD_ID__">
<title>스피릿 듀얼</title>
<style>
  html,body{height:100%;margin:0;background:#0b0a15;color:#f1eefb;
    font-family:'Noto Sans KR',-apple-system,BlinkMacSystemFont,'Malgun Gothic',sans-serif;}
  main{min-height:100%;box-sizing:border-box;display:flex;flex-direction:column;align-items:center;
    justify-content:center;gap:16px;padding:28px 22px;text-align:center;}
  h1{font-size:21px;margin:0;color:#ffd166;letter-spacing:1px;}
  #ld-status{font-size:19px;line-height:1.6;margin:0;font-weight:700;}
  #ld-msg{font-size:16px;line-height:1.75;margin:0;max-width:20em;color:#c9c3e0;}
  #ld-retry{font-size:18px;font-weight:700;min-height:52px;padding:14px 26px;border-radius:12px;
    border:1px solid #a8863f;background:linear-gradient(180deg,#3a2f66,#241c40);color:#f1eefb;
    font-family:inherit;cursor:pointer;}
  #ld-retry:active{transform:scale(.98);}
  .hint{font-size:14px;line-height:1.7;margin:0;color:#8f88a8;max-width:20em;}
  [hidden]{display:none !important;}
</style>
</head>
<body>
<main role="main">
  <h1>스피릿 듀얼</h1>
  <p id="ld-status" role="status" aria-live="polite">최신 버전을 불러오는 중입니다.</p>
  <p id="ld-msg" hidden></p>
  <button id="ld-retry" type="button" hidden>다시 시도</button>
  <p class="hint">세이브는 이 기기에 그대로 남아 있습니다.</p>
</main>
<noscript>
  <p>브라우저에서 스크립트를 켜야 게임이 열립니다.</p>
</noscript>
<script>
/* ============================================================================
 * 스피릿 듀얼 진입 페이지 (v__VERSION__)
 * 홈 화면 아이콘이 가리키는 이 주소는 그대로 두고, 페이지를 새로 열 때 딱 한 번만
 * 게임 본체(duel-core.html)를 캐시를 지나쳐(no-store + 매번 다른 ?t=) 받아 그린다.
 *  · 로더를 만들어 둔 뒤로는 판 도중·창 전환·화면 잠금 해제·앱 복귀에서
 *    다시 받지도, 새로고침·이동하지도 않는다.
 *  · 확인 요청을 따로 두지 않는다(첫 화면 지연 없음). 본체 요청 하나가 곧 확인이다.
 *  · 한 번 실패하면 자동으로 다시 요청하지 않는다. 마지막으로 받아 둔 본체가 있으면
 *    그것으로 열고, 없으면 안내와 '다시 시도' 버튼만 남긴다(누를 때 한 번만 요청).
 * ========================================================================== */
(function () {
  'use strict';
  var CORE = 'duel-core.html';
  var CACHE_NAME = 'spirit-duel-core';
  var CACHE_KEY = 'duel-core-last.html';
  var TIMEOUT_MS = 10000;   /* 이 시간 안에 못 받으면 실패로 보고 폴백한다 */

  var statusEl = document.getElementById('ld-status');
  var msgEl = document.getElementById('ld-msg');
  var retryEl = document.getElementById('ld-retry');

  var opened = false;    /* 게임 본체를 문서에 그렸는지 */
  var settled = false;   /* 이번 시도의 결론이 났는지(늦게 온 응답은 버린다) */

  function setStatus(t) { if (statusEl) statusEl.textContent = t; }

  function looksLikeGame(t) {
    return !!t && t.length > 20000 && t.indexOf('name="duel-build-id"') !== -1;
  }

  /* 본체 HTML 을 문서에 그대로 그린다. 주소는 바뀌지 않으므로 같은 페이지·같은 저장소다. */
  function drawGame(html) {
    if (opened) return;
    opened = true;
    try {
      document.open();
      document.write(html);
      document.close();
    } catch (e) {
      try { window.location.replace(CORE); } catch (_) {}
    }
  }

  /* 마지막으로 잘 받아 둔 본체를 기기에 보관한다(오프라인 폴백용) */
  function remember(html) {
    try {
      if (!window.caches || !caches.open) return;
      caches.open(CACHE_NAME).then(function (c) {
        return c.put(new Request(CACHE_KEY), new Response(html, {
          headers: { 'Content-Type': 'text/html; charset=utf-8' }
        }));
      }).catch(function () {});
    } catch (e) {}
  }

  function readLast() {
    return new Promise(function (resolve) {
      try {
        if (!window.caches || !caches.match) return resolve(null);
        caches.match(CACHE_KEY).then(function (r) {
          if (!r) return resolve(null);
          r.text().then(resolve, function () { resolve(null); });
        }).catch(function () { resolve(null); });
      } catch (e) { resolve(null); }
    });
  }

  function showFailed(note) {
    setStatus('게임을 열지 못했습니다.');
    if (msgEl) {
      msgEl.textContent = note || '인터넷 연결을 확인한 뒤 아래 버튼을 한 번 눌러 주세요.';
      msgEl.hidden = false;
    }
    if (retryEl) retryEl.hidden = false;
  }

  /* 페이지를 새로 열 때 딱 한 번 나가는 요청. 성공하면 그리고, 실패하면 폴백한다. */
  function attempt() {
    if (opened || settled) return;
    var url = CORE + '?t=' + Date.now();
    var opts = { cache: 'no-store', credentials: 'same-origin' };
    var timer = null, ctrl = null;
    try {
      if (window.AbortController) { ctrl = new AbortController(); opts.signal = ctrl.signal; }
    } catch (e) { ctrl = null; }
    if (ctrl) {
      timer = setTimeout(function () { try { ctrl.abort(); } catch (e) {} }, TIMEOUT_MS);
    }

    fetch(url, opts).then(function (res) {
      if (!res || !res.ok) throw new Error('HTTP ' + (res ? res.status : 'error'));
      return res.text();
    }).then(function (text) {
      if (timer) clearTimeout(timer);
      if (opened || settled) return;
      if (!looksLikeGame(text)) throw new Error('bad bundle');
      settled = true;
      remember(text);
      setStatus('게임을 여는 중입니다.');
      drawGame(text);
    }).catch(function () {
      if (timer) clearTimeout(timer);
      if (opened || settled) return;
      settled = true;
      readLast().then(function (last) {
        if (looksLikeGame(last)) {
          setStatus('인터넷에 연결되지 않아, 마지막으로 받아 둔 버전으로 엽니다.');
          setTimeout(function () { drawGame(last); }, 2400);   /* 안내를 읽을 시간 */
        } else {
          showFailed('인터넷에 연결되지 않아 게임을 받지 못했습니다. 연결을 확인한 뒤 아래 버튼을 한 번 눌러 주세요. 세이브는 그대로 남아 있습니다.');
        }
      });
    });
  }

  if (retryEl) {
    retryEl.addEventListener('click', function () {
      if (opened) return;
      retryEl.hidden = true;
      if (msgEl) { msgEl.hidden = true; msgEl.textContent = ''; }
      settled = false;
      setStatus('최신 버전을 다시 불러오는 중입니다.');
      attempt();   /* 사용자가 누를 때만, 한 번 */
    });
  }

  attempt();
})();
</script>
</body>
</html>
"""

loader_html = (LOADER
               .replace("__BUILD_ID__", BUILD_ID)
               .replace("__VERSION__", VERSION))

with open(OUT_ENTRY, 'w', encoding='utf-8') as f:
    f.write(loader_html)

with open(OUT_VERSION, 'w', encoding='utf-8') as f:
    json.dump({
        "game": "duel",
        "version": VERSION,
        "build": BUILD_ID,
        "file": OUT_CORE,
        "entry": OUT_ENTRY,
        "builtAt": BUILT_AT,
    }, f, ensure_ascii=False, indent=2)
    f.write("\n")

print("duel-core.html written (%d bytes)" % len(compiled_html))
print("duel.html loader written (%d bytes)" % len(loader_html))
print("duel-version.json written")
print("build", BUILD_ID)
