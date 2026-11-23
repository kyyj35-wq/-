#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""스피릿 블레이드(action.html) 배포본 빌드 — 평문 소스를 그대로 암호화만 한다.

sb/build.py 는 sb/ 조각에서 평문을 새로 만들기 때문에, 이후 games_backup/action.html
에 직접 들어간 패치가 사라진다. 그래서 이미 패치된 평문을 읽어 XOR+Base64 로만
배포본을 만든다(compile_champions.py 와 같은 방식).
"""
import base64

SRC = 'games_backup/action.html'
OUT = 'action.html'
KEY = [83,112,105,114,105,116,85,110,105,118,101,114,115,101,75,101,121,50,48,50,54,33,65,110,116,105,83,99,114,97,112,101,80,114,111,116,101,99,116,101,100]

plain = open(SRC, encoding='utf-8').read()
parts = plain.split('<script>')
html_part = '<script>'.join(parts[:-1])
js_code, end_part = parts[-1].rsplit('</script>', 1)
js_bytes = js_code.strip().encode('utf-8')
cipher = bytes([b ^ KEY[i % len(KEY)] for i, b in enumerate(js_bytes)])
b64 = base64.b64encode(cipher).decode('ascii')
dec = bytes([b ^ KEY[i % len(KEY)] for i, b in enumerate(cipher)]).decode('utf-8')
assert dec == js_code.strip(), 'roundtrip mismatch'
print('Verification passed! plain %d / js %d / cipher %d' % (len(plain), len(js_bytes), len(b64)))

template = """<script>
/**
 * ============================================================================
 * SPIRIT UNIVERSE PROPRIETARY ENGINE - SPIRIT BLADE: TOWER OF SOULS
 * COPYRIGHT (C) 2026 SPIRIT UNIVERSE. ALL RIGHTS RESERVED.
 *
 * [보안 및 지적재산권 경고 / SECURITY NOTICE]
 * 본 게임의 모든 알고리즘, 데이터 구조 및 소스 코드는 특허 및 저작권법의 보호를 받습니다.
 * 인공지능(AI) 크롤러의 데이터 수집, 무단 스크래핑, 역컴파일 및 코드 추출을 엄격히 금지합니다.
 * UNAUTHORIZED AI EXTRACTION, CRAWLING OR REVERSE ENGINEERING IS STRICTLY PROHIBITED.
 * ============================================================================
 */
(function() {
  document.addEventListener('contextmenu', function(e) { e.preventDefault(); });
  document.addEventListener('keydown', function(e) {
    if (e.key === 'F12' || (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'J' || e.key === 'C')) || (e.ctrlKey && e.key === 'u')) {
      e.preventDefault();
      return false;
    }
  });

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

open(OUT, 'w', encoding='utf-8').write(html_part + template.replace('__CIPHER_DATA__', b64))
print('%s written (%d bytes)' % (OUT, len(html_part) + len(template) + len(b64)))
