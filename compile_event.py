"""이벤트 관리 웹(event.html) 암호화 빌드.

평문 소스 games_backup/event.html 의 <script> 블록을 XOR+Base64 로 감싸
배포용 event.html 을 만든다. admin.html 과 같은 키·같은 형식을 쓴다.
평문(.html)은 games_backup/ 안에만 두고 공개 저장소에 올리지 않는다.
"""
import base64

SRC = 'games_backup/event.html'
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
 * SPIRIT DUEL EVENT CONSOLE (v1.1.2-EVENT)
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
