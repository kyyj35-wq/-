"""event.html 안내(리다이렉트) 페이지 빌드 — 2026-11-24 이벤트 기능 admin.html 통합.

이벤트 기능이 개발자 관리자 센터(admin.html)로 완전히 옮겨져서, event.html 은
"관리자 센터 이벤트 칸으로 이동" 안내 + 자동 이동 페이지만 남긴다.
평문 소스는 games_backup/event-redirect.html (옛 전체 콘솔 평문은
games_backup/event.html.full.before_integration-2026-11-24 에 보관).
<script> 블록은 admin.html 과 같은 키로 XOR+Base64 로 감싼다.
"""
import base64

SRC = 'games_backup/event-redirect.html'
OUT = 'event.html'

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

template = """<script>
/**
 * SPIRIT DUEL EVENT REDIRECT (v1.2.0-ADMIN)
 */
(function() {
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
})();
</script>
</body>
</html>
"""

compiled_html = html_part + template.replace("__CIPHER_DATA__", b64_str)

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(compiled_html)

print('event.html successfully compiled!')
