# 🎁 격파 보상 이벤트 → 개발자 어드민 센터(admin.html) 완전 통합 — 2026-11-24

## 왜
사용자 요청: **"따로 웹으로 만드니까 안 되는 것 같다. 그냥 개발자 서버(`admin.html`)에 통합시켜 버리자 이벤트!"**
관리자 센터에 있던 이벤트 카드는 상태 요약 + `event.html` 새 창 링크뿐이었고, 실제 설정·지급은 전용 웹에서만 됐다.
이제 마스터 키로 들어온 **한 화면 안에서** 이벤트 설정·지급·내역·리셋을 모두 한다.

## 무엇이 바뀌었나 (admin.html)
`admin.html` 의 `2.9 🎁 격파 보상 이벤트` 카드(`id="event"`) 하나에 전부 들어갔다.
(치트 ON/OFF 카드 바로 아래, 유저 관리 위)

1. **이벤트 설정**
   - ON/OFF 스위치(`role="switch"`, `aria-checked`, 문구·`aria-label` 동기화)
   - 이벤트 제목 · 대상 아이디(쉼표) · 지급 방식(1인 1회 / 매 승리마다 = `oncePerPlayer`)
   - **기본 보상 5종 개별 선택**(라디오): 💎 보석(`gems`) · 🪙 코인(`gold`) ·
     ⚔️ 공격력 +25% 7일 체험권(`trial_atk_25`) · ❤️ 시작 라이프 +100 7일 체험권(`trial_lp_100`) ·
     🃏 매 턴 +1장 드로우 7일 체험권(`trial_draw_1`)
   - 체험권을 고르면 수량 칸이 `사용 기간 (일) = 7`로 잠기고, 재화로 돌아오면 마지막 수량을 복원
   - 이벤트 ID 표시 · `💾 설정 저장` · `🔄 새 이벤트로 리셋`(eventId 갱신 + 대기 목록 비움)
2. **대기 목록** — 5초 자동 동기화(설정·내역은 1분에 한 번), 행마다 보상 종류·수량을 바꿔 `지급` / `✖ 무시`
3. **직접 아이디 입력 지급** — 보석 / 코인 / 체험권 3종 중 선택, 수량 입력
4. **지급 완료 내역** — 누구에게 무엇을 몇 개, 대기 목록/직접 지급 구분
5. 카드 상단 상태 배지 + 요약 줄(진행 상태·제목·대상·기본 보상·지급 대기 인원)

추가로 상단 **섹션 바로가기**(`#event` · `#cheats` · `#toggles` · `#users` · `#links`)를 넣어
페이지가 길어져도 보이스오버 링크 목록에서 바로 뛸 수 있게 했다.

## event.html
이제 **안내 + 자동 이동 페이지**(`v1.2.0-ADMIN`)다. 주소에 `key` 가 있으면 그대로 넘겨
`admin.html?key=…#event` 로 보내고, 자동 이동이 막힌 환경을 위해 수동 링크와
`<meta http-equiv="refresh" content="2; url=admin.html#event">` 를 함께 둔다.
빌드는 `compile_event.py` → `games_backup/event-redirect.html`.
옛 전체 콘솔 평문은 `games_backup/event.html.full.before_integration-2026-11-24` 에 보관했다.
관리자 화면의 「🎁 이벤트 관리 웹 열기」 링크는 제거했다.

## 서버 데이터
지급 경로·저장소는 **한 글자도 바꾸지 않았다.**
`event_config` · `event_pending` · `event_claims` · `spirit-cheats/queue/<아이디>`(add_gems / add_gold / add_trial 7일) ·
`duel_save_*` · `registry` 그대로이고, 그래서 예전에 쌓인 설정·내역이 그대로 이어진다.
빌드·검증 과정에서 실서버에 쓴 요청은 **0건**(테스트는 전부 가짜 fetch).

## 검증
- `test_admin_event_integration_2026-11-24.py` — **배포본 그대로(root admin.html)** 를 XOR 복호화해
  QuickJS + DOM/fetch 스텁에서 실행. 60여 항목 전부 통과
  (설정 저장·보상 5종·대기 5초 갱신·행별 지급/무시·직접 지급 5종·내역·리셋·치트 발송·치트 ON/OFF·유저 관리·인증).
- `python3 -m compileall` 수준의 빌드 검증: 복호화 결과 == 평문 소스.
