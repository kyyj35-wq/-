## 🪙 이벤트 보상을 보석·코인 중 선택 — event v1.1.0-EVENT · duel v1.4.15-DUEL (2026-11-23)

- 대상: 이벤트 웹(`event.html`) · 스피릿 듀얼(`duel.html`/`duel-core.html`, v1.4.15-DUEL) · 어드민(`admin.html`)
- 링크: https://kyyj35-wq.github.io/-/event.html · /duel.html · /admin.html
- 사용자 요청: "보석이랑 코인 고를 수 있게 바꿔줘 보석이랑 코인. 이벤트 만들 때. 바꿀 수 있게 해 줘. 아니 고를 수 있게 해 줘."

### 1. 무엇이 바뀌었나

이벤트 보상 재화를 **💎 보석(`gems`) / 🪙 코인(`gold`)** 중에서 고를 수 있게 됐다. 설정·사람별 지급·직접 지급 어디서든 고를 수 있다.

| 위치 | 바뀐 것 |
|---|---|
| `event_config` | `rewardType: 'gems' \| 'gold'` 추가(기본 `'gems'`). 기존 `rewardGems` 는 '기본 지급 수량'으로 그대로 쓴다 |
| event.html ① 이벤트 설정 | **보상 재화** 라디오(`fieldset`/`legend` + 진짜 `input[type=radio]`, 보이스오버가 "라디오 버튼"으로 읽음) + **기본 지급 수량 (개)** |
| event.html ② 대기 목록 | 행마다 **지급 재화** 선택(`select`) + **지급 수량** 칸. 기본값은 그 행에 기록된 재화(없으면 이벤트 설정값)와 수량 |
| event.html ③ 직접 지급 | **지급 재화** 선택 + 수량 |
| 버튼 | 선택에 따라 `💎 보석 지급` / `🪙 코인 지급`, `aria-label` 도 "…님에게 코인 지급" / "…에게 지급할 코인 개수" 로 함께 바뀐다 |
| 지급 큐 | 보석이면 `action:'add_gems'`, 코인이면 `action:'add_gold'` (+ `rewardType` 필드) |
| `event_claims` | `{ user, rewardType, amount, gems(호환), at, source, opponent, eventId }` — 내역에 `💎 N` / `🪙 N` 으로 구분. 옛 기록(rewardType 없음)은 💎 로 표시 |
| admin.html | 이벤트 요약 한 줄이 `기본 💎1,000` / `기본 🪙1,000` 로 표시, 카드 제목·안내·링크 낭독 문구도 보상 기준으로 정리 |
| duel v1.4.15 | `cheatApply` 에 `add_gold` 추가(`ST.gold` 증가, `goldNow()` 경유). 홈 배너·PvP 승리 문구·토스트가 `rewardType` 에 맞춰 `🪙 코인 N개` / `💎 보석 N개`. `event_pending` 항목·문서에 `rewardType` 저장 |

### 2. 지급 사슬 (그대로 유지)

1. 듀얼 PvP에서 `hostIds`(kyyj35·dev)를 이기면 → `event_pending` 에 **기록만** (자동 지급 없음)
2. 운영자가 `event.html` 에서 재화·수량을 고르고 **[보상 지급]** → `spirit-cheats/queue/<아이디>` 에 `add_gems`/`add_gold` 예약 + `event_claims` 기록 + 대기 목록에서 제거
3. 그 계정이 다음에 듀얼을 열 때 `cheatApply` 가 실제 재화로 더한다

이벤트가 꺼져 있으면 기록도 네트워크 요청도 없다(기존 규칙 그대로).

### 3. 안전장치

- 화면에서 재화를 못 읽는 경우(선택값이 비었거나 이상값)에는 **그 행에 기록된 재화 → 이벤트 설정값** 순으로 따른다. 잘못 읽었다고 보석으로 조용히 바뀌지 않는다.
- 기존 보석 이벤트·기존 큐·기존 `event_claims` 와 호환된다(`add_gems`·`gems`·`rewardGems` 모두 그대로 동작).
- `event_config` 에 `rewardType` 이 없으면 보석으로 동작하므로, 배포만으로 기존 이벤트 설정이 바뀌지 않는다.

### 4. 검증

- `test_event_reward_choice_2026-11-23.py` (QuickJS, 실소스): 설정 정규화·gold 저장 / 설정 렌더(코인 라디오·직접 지급 기본값) / 대기 행(코인 선택·버튼·aria, 행 기록 우선) / 재화 변경 시 버튼 문구 / 코인 지급 → `add_gold` + claims `rewardType` / 보석 경로 `add_gems` 회귀 / 직접 지급 코인 / 내역 `💎`·`🪙`·옛 기록 / 듀얼 `duelEventNormalize`·`duelEventRewardLabel` / `cheatApply add_gold` 로 골드 200→1,100·다이아 불변 / 배너·PvP 문구·`event_pending` rewardType. 전 항목 통과.
- `test_event_reward_e2e_2026-11-23.py` (실소스 2개를 이어 붙인 E2E): event.html 설정 gold 저장 → duel PvP 승리 기록 → event.html 대기 행 자동 코인 → 지급 `add_gold` → duel `cheatApply` 로 골드 500→1,300. 보석 경로도 100→900. 전 항목 통과.
- 기존 회귀: `test_event_page_2026-11-23.py`, `test_duel_event_cheats_2026-11-23.py` 전 항목 통과.
- 컴파일 산출물(event.html·admin.html·duel-core.html) 복호화 왕복 일치 확인.
- 실서버 확인: `/event.html` — 보상 재화 라디오(기본 보석)·직접 지급 재화 선택·버튼/낭독 문구가 재화에 따라 바뀌는 것 확인. `/admin.html` — `기본 💎1,000 · 지급 대기 0명`. `/duel.html` — v1.4.15 본체 정상 로드(홈·골드 표시).
- 실서버 상태는 그대로: `event_config` `enabled:false`(rewardType 없음 → 보석), `event_pending`·`event_claims` 빈 목록, `queue/kyyj35` 미변경.
