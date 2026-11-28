import base64

with open('games_backup/champions.html.bak', 'r', encoding='utf-8') as f:
    content = f.read()

html_part, rest = content.split('<script>', 1)
js_code, end_part = rest.rsplit('</script>', 1)

key = [83, 112, 105, 114, 105, 116, 85, 110, 105, 118, 101, 114, 115, 101, 75, 101, 121, 50, 48, 50, 54, 33, 65, 110, 116, 105, 83, 99, 114, 97, 112, 101, 80, 114, 111, 116, 101, 99, 116, 101, 100]

js_bytes = js_code.strip().encode('utf-8')
cipher_bytes = bytearray(len(js_bytes))
for i in range(len(js_bytes)):
    cipher_bytes[i] = js_bytes[i] ^ key[i % len(key)]

b64_str = base64.b64encode(cipher_bytes).decode('ascii')

# Verify decoding
dec_bytes = bytearray(len(cipher_bytes))
for i in range(len(cipher_bytes)):
    dec_bytes[i] = cipher_bytes[i] ^ key[i % len(key)]

decoded_text = dec_bytes.decode('utf-8')
assert decoded_text == js_code.strip(), "Decoded text does not match!"
print("Verification passed! Encrypted JS length:", len(b64_str))

template = """<script>
/**
 * ============================================================================
 * SPIRIT UNIVERSE PROPRIETARY ENGINE (v4.6.1-ABYSS)
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

with open('champions.html', 'w', encoding='utf-8') as f:
    f.write(compiled_html)

print("champions.html successfully compiled!")
