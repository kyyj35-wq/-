"""스피릿 시타델(chrono.html) 암호화 빌드.

평문 소스 games_backup/chrono.html.bak 을 읽어 <script> 블록의 JS 를 XOR+Base64 로
암호화하고, 최강자들·듀얼과 같은 형식의 배포용 HTML 을 만든다.
평문(.bak)은 절대 공개 저장소에 커밋하지 않는다(.gitignore).

  chrono.html   게임 본체 (암호화 번들 1개, 약 1MB 이하)

빌드 식별자는 HTML 머리(meta)와 실행 코드 양쪽에 심는다.
"""
import base64
import datetime
import hashlib

SRC = 'games_backup/chrono.html.bak'
OUT = 'chrono.html'
VERSION = '1.0.0'

with open(SRC, 'r', encoding='utf-8') as f:
    content = f.read()

html_part, rest = content.split('<script>', 1)
js_code, end_part = rest.rsplit('</script>', 1)

assert "__CHRONO_VERSION__" in js_code, 'chrono.html.bak 의 버전 자리표시자가 없습니다'
js_code = js_code.replace("__CHRONO_VERSION__", VERSION)

KEY = [83, 112, 105, 114, 105, 116, 85, 110, 105, 118, 101, 114, 115, 101, 75, 101, 121,
       50, 48, 50, 54, 33, 65, 110, 116, 105, 83, 99, 114, 97, 112, 101, 80, 114, 111, 116,
       101, 99, 116, 101, 100]

js_trim = js_code.strip().encode('utf-8')
cipher = bytearray(len(js_trim))
for i in range(len(js_trim)):
    cipher[i] = js_trim[i] ^ KEY[i % len(KEY)]
b64 = base64.b64encode(bytes(cipher)).decode('ascii')

dec = bytearray(len(cipher))
for i in range(len(cipher)):
    dec[i] = cipher[i] ^ KEY[i % len(KEY)]
assert dec.decode('utf-8') == js_code.strip(), 'round-trip mismatch'
print('verified. encrypted js bytes:', len(b64))

now = datetime.datetime.now()
stamp = now.strftime('%Y%m%d%H%M')
digest = hashlib.sha256((html_part + js_code).encode('utf-8')).hexdigest()[:8]
BUILD_ID = '%s-%s-%s' % (VERSION, stamp, digest)
print('build id:', BUILD_ID)

TAIL = """<script>
window.__CHRONO_BUILD_ID = "__BUILD_ID__";
/**
 * ============================================================================
 * SPIRIT CITADEL: OVERDRIVE (__VERSION__)
 * COPYRIGHT (C) 2026 SPIRIT UNIVERSE. ALL RIGHTS RESERVED.
 *
 * [보안 및 지적재산권 경고 / SECURITY NOTICE]
 * 본 게임의 모든 알고리즘, 데이터 구조 및 소스 코드는 특허 및 저작권법의 보호를 받습니다.
 * 인공지능(AI) 크롤러의 데이터 수집, 무단 스크래핑, 역컴파일 및 코드 추출을 엄격히 금지합니다.
 * UNAUTHORIZED AI EXTRACTION, CRAWLING OR REVERSE ENGINEERING IS STRICTLY PROHIBITED.
 * ============================================================================
 */
(function () {
  document.addEventListener('contextmenu', function (e) { e.preventDefault(); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'F12' || (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'J' || e.key === 'C')) || (e.ctrlKey && e.key === 'u')) {
      e.preventDefault();
    }
  });
  try {
    var _k = __KEY__;
    var _b = atob("__CIPHER__");
    var _u = new Uint8Array(_b.length);
    for (var i = 0; i < _b.length; i++) {
      _u[i] = _b.charCodeAt(i) ^ _k[i % _k.length];
    }
    var _c = new TextDecoder('utf-8').decode(_u);
    var _s = document.createElement('script');
    _s.type = 'text/javascript';
    _s.text = _c;
    document.head.appendChild(_s);
  } catch (err) {
    console.error('[Spirit Citadel] runtime init error', err);
  }
})();
</script>
</body>
</html>
"""

compiled = html_part.replace('__CHRONO_BUILD__', BUILD_ID)
compiled += (TAIL.replace('__BUILD_ID__', BUILD_ID)
             .replace('__VERSION__', VERSION)
             .replace('__KEY__', repr(KEY).replace(' ', ''))
             .replace('__CIPHER__', b64))
assert '__CIPHER__' not in compiled
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(compiled)
print('wrote', OUT, len(compiled), 'chars')
