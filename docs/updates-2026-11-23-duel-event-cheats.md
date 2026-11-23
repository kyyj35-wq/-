## 🏆 v1.4.14-DUEL — 개발자 치트 4종 + 격파 보석 이벤트 전용 웹 (2026-11-23)

- 대상: 스피릿 듀얼(`duel.html`, v1.4.14-DUEL) · 어드민(`admin.html`) · 이벤트 웹(`event.html` 신설)
- 링크: https://kyyj35-wq.github.io/-/duel.html · /admin.html · /event.html
- 사용자 요청: "개발자 계정 듀얼 치트 더 추가하고 그리고 이벤트 할 수 있게 상대방이 나 이기면 보석 몇 개씩 지급 하는 이벤트 할 수 있게 그거 전용 서버도 만들어 줘 아니 그것도 그냥 웹으로 만들어 줘"
- 정정(같은 날): "아니, 자동으로 쏘는 게 아니고 내가 개수 정해놓고 하게 그래서 웹으로 만들어 달라 그런 거임" — **보석은 자동 지급하지 않고, 전용 웹에서 운영자가 직접 지급한다.**

### 1. 듀얼 개발자 치트 7종 (기존 3 + 신규 4)

| 키 | 이름 | 동작 |
|---|---|---|
| `noTribute` | 제물 없이 소환 | (기존) |
| `firstTurnAttack` | 선공 첫 턴 공격 허용 | (기존) |
| `godLp` | 생명점 99,999 시작 | (기존) |
| `atk_10x` | ⚔️ 내 몬스터 공격력 10배 | `statAtk()` 계산값 ×10. 내 진영에만 |
| `invincible` | 🛡️ 내 몬스터·LP 무적 | `lpDamage()` 가 0, `destroyMonster()` 파괴 면역. 내 진영에만 |
| `draw_3` | 🃏 매 턴 3장 드로우 | `beginTurn()` 드로우 3장(선공 첫 턴은 규칙대로 0장) |
| `free_shop` | 💎 상점·제작 무료 | 카드팩·골드팩·한정 패키지·카드 제작 비용 0 |

- 기존 원칙 유지: `spirit-cheats/toggles` 의 `masterEnabled` + 적용 대상(`dev` 또는 `admin`)일 때만, 계정이 열 때 한 번 읽는다.
- 온라인 대전: 진입 시 "치트키 해제 확인" 팝업이 그대로 뜨고, 두 화면이 같은 판을 세우도록 **진영별 규칙(`B.cheatRules`)** 으로 계산한다. 공격력·드로우·무적 모두 진영 규칙을 보므로 양쪽 클라이언트 계산이 갈라지지 않는다.
- LP 피해는 전부 `lpDamage()` 를 지나게 바꿔, 무적일 때 로그·낭독이 실제 수치(0)와 어긋나지 않는다.

### 2. 격파 보석 이벤트 — "이기면 자동 지급"이 아니라 "운영자가 직접 지급"

저장소(MantleDB, `spirit-duel-pvp` 네임스페이스):

| 문서 | 내용 |
|---|---|
| `event_config` | `enabled`, `title`, `hostIds`(예: kyyj35·dev), `rewardGems`, `oncePerPlayer`, `eventId` |
| `event_pending` | `{ eventId, title, items:[{ id, winner, loser, at, turns, code, gems }] }` — **지급 대기 목록** |
| `event_claims` | `{ claims:[{ user, gems, at, source, opponent, eventId }] }` — 지급 완료 내역 |

흐름:
1. 듀얼 PvP에서 `hostIds` 계정을 이기면 → 결과 창에 "🏆 [제목] 대상자(kyyj35)를 이겼습니다! 운영자 확인 후 💎N개가 지급됩니다." 를 띄우고 `event_pending` 에 **기록만** 남긴다. `ST.diamonds` 는 건드리지 않는다.
2. 운영자가 `event.html` 대기 목록에서 개수를 확인·수정하고 **[💎 보석 지급]** 을 누르면 → `spirit-cheats/queue/<아이디>` 에 `{ game:'duel', target:<아이디>, action:'add_gems', amount:N }` 이 들어가고, 그 계정이 다음에 듀얼을 열 때 `cheatApply()` 가 다이아로 더한다. 동시에 `event_claims` 에 기록하고 대기 목록에서 제거한다.
3. 대기 목록에 없는 사람에게도 [직접 아이디 입력 지급] 으로 바로 줄 수 있다.

부가:
- 이벤트가 켜져 있으면 듀얼 홈에 한 줄 배너(`🏆 제목 · kyyj35·dev를 이기면 💎N개 · 운영자 확인 후 지급`).
- 양쪽 계정 아이디를 방 설정(`_config` 의 `hostAccount`·`guestAccount`)에 남겨 대상 판정을 한다. 화면에 보이는 이름(방장·도전자)은 그대로라 상대에게 계정이 드러나지 않는다.
- 이벤트가 꺼져 있으면 아무 기록도, 네트워크 요청도 하지 않는다.
- `oncePerPlayer: true` 면 같은 사람이 여러 번 이겨도 대기 목록에 한 번만 쌓인다.

### 3. event.html (신설)

- 주소: https://kyyj35-wq.github.io/-/event.html — 마스터 키(`spirit2026admin`)로 여는 전용 페이지. `?key=` 자동 인증 지원.
- 구성: ① 이벤트 설정(켜기/끄기·제목·대상 아이디·기본 보석 개수·1인 1회·새 이벤트로 리셋) ② 나를 이긴 도전자 대기 목록(행마다 보석 개수 칸 + [💎 보석 지급] + [✖ 무시]) ③ 직접 아이디 입력 지급 ④ 지급 완료 내역.
- 보이스오버: 모든 버튼 `aria-label`, 상태 문구 `role="status" aria-live="polite"`, 대기 항목은 `role="group"` + 승자·상대·시각·턴 낭독.
- `admin.html` 은 치트 페이지와 섞지 않고, 아래쪽에 **작은 안내 카드 + [이벤트 관리 웹 열기] 버튼 + 현재 상태 한 줄**만 둔다.

### 4. 검증

- `test_duel_event_cheats_2026-11-23.py` (QuickJS, 실소스 그대로): 치트 7종 등록·진영 규칙 정리 / atk_10x 내 진영만 10배 / invincible LP 0·파괴 면역 / draw_3 3장 / free_shop 다이아·골드 0으로 팩·패키지·제작 / 이벤트 설정 정규화 / PvP 승리 시 `event_pending` 1회 기록·보석 미지급 / 방장(진영0) 승리·비대상자·꺼짐 / 1인 1회 중복 차단 / `add_gems` → 다이아 지급. 전 항목 통과.
- `test_event_page_2026-11-23.py` (QuickJS, event.html 스크립트): 설정 정규화·저장·리셋 / 대기 행 렌더(기본 개수·이미 지급 배지·HTML 이스케이프) / [보석 지급] 시 기존 큐 보존 + add_gems 예약 + claims 기록 + 대기 목록 제거 / [무시] / 직접 지급 / 잘못된 입력 거부 / 내역 렌더. 전 항목 통과.
- 컴파일 산출물 복호화 왕복 일치 확인(event.html·admin.html), `sim_duel_tribute_test.py` 회귀 통과.
- 실서버 `event_config` 는 배포 후 `enabled:false` 로 두고, `spirit-cheats/toggles` 는 OFF, `queue/kyyj35` 는 건드리지 않았다.
