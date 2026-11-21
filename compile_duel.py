"""스피릿 듀얼(duel.html) 암호화 빌드.

평문 소스 games_backup/duel.html.bak 을 읽어 <script> 블록의 JS 를 XOR+Base64 로
암호화하고, 최강자들·블레이드와 같은 형식의 배포용 HTML 을 만든다.
평문(.bak)은 절대 공개 저장소에 커밋하지 않는다.

빌드 식별자(__DUEL_BUILD_ID__)를 HTML 머리와 실행 코드에 심는다.
게임은 실행 직후 배포본의 식별자를 읽어, 다르면 스스로 새 주소로 넘어간다.
"""
import base64
import hashlib
import datetime

SRC = 'games_backup/duel.html.bak'
OUT = 'duel.html'
VERSION = '1.2.5'

with open(SRC, 'r', encoding='utf-8') as f:
    content = f.read()

html_part, rest = content.split('<script>', 1)
js_code, end_part = rest.rsplit('</script>', 1)

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
stamp = datetime.datetime.now().strftime('%Y%m%d%H%M')
digest = hashlib.sha256((html_part + js_code).encode('utf-8')).hexdigest()[:8]
BUILD_ID = f"{VERSION}-{stamp}-{digest}"
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

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(compiled_html)

print("duel.html successfully compiled! build", BUILD_ID)
