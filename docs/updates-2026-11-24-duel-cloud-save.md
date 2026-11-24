## ☁️ 듀얼 클라우드 세이브 + 복원 버튼 제거 — duel v1.4.17-DUEL (2026-11-24)

- 대상: 스피릿 듀얼(`duel.html`/`duel-core.html`, v1.4.17-DUEL)
- 링크: https://kyyj35-wq.github.io/-/duel.html
- 사용자 지시: "이제 복원 버튼 지워도 될 것 같아" · "서버 데이터를 써버에도 올리게 이거를 세이브 데이터를 서버 해도 올라가게 바꾸라고"

### 1. 「📖 스토리 진행도」 복원 버튼 제거

| 지점 | 처리 |
|---|---|
| 설정 화면 | `#story-restore-card` 카드(「📖 스토리 진행도」·「📖 스토리 1~40단계로 되돌리기」·안내 문구) 삭제 |
| 스크립트 | `restoreStoryTo40()` 삭제 |
| 렌더 | `renderSettings()` 의 표시 조건(`cheatAccountName() !== 'dev' && storyCleared.length > 40`)과 안내 줄 갱신 삭제 |
| 유지 | 스토리 순차 잠금(`isStageUnlocked`/`isStageCleared`/`nextOpenStage`) · 치트 대기열 `set_story_max` 처리 그대로 |

남은 참조 0건(grep 확인). `set_story_max` 치트는 서버 대기열 방식으로 계속 동작한다.

### 2. 계정별 클라우드 세이브

- 저장소: `https://mantledb.sh/v2/spirit-duel-pvp/duel_save_<소문자아이디>` — 최강자들의 `spirit-universe/save_<id>` 와 절대 겹치지 않는다(이벤트 서버와 같은 네임스페이스라 요청 한도 여유도 크다).
- 문서 형태: `{ v, game:'duel', account, updatedAt, summary{storyCleared, cards, diamonds, gold, savedAt}, save:ST }`
- 동작 조건: `cheatAccountName()` 이 있는 로그인 계정에서만. 게스트는 기기 저장만 하고 설정 카드도 숨긴다.
- 업로드: `saveNow()` 뒤 **2.5초 디바운스**. 내용 지문(`savedAt` 제외)이 그대로면 요청하지 않는다. 치트 적용·전투 종료·뽑기·한정 패키지 구매 직후에는 디바운스 없이 바로 반영한다.
- 시작·계정 전환(`spirit-account-changed`) 시 서버와 한 번 맞춘다.

| 상황 | 처리 |
|---|---|
| 서버 404 + 기기에 진행 있음 | 기기 세이브를 서버로 첫 업로드 |
| 기기가 새 세이브(진행 0) | 서버 세이브로 기기를 갱신 |
| 서버가 더 진행됐거나(진행 무게) 같으면 더 최신 | 서버 세이브로 기기를 갱신 — 서버를 덮지 않는다 |
| 기기가 더 진행됨 | 기기 세이브를 서버로 올린다 |
| 내용이 같음 | 아무것도 하지 않는다(불필요한 안내·렌더 없음) |

- 갱신할 때 기기 진행은 지우지 않는다 — `spirit-duel-save__bak` 과 `spirit-duel-save-cloud-prev` 에 남긴다.
- **계정 격리(2026-11-23 규칙 유지)**: `saveScopeSwitching()` 이거나 `saveScopeReady()` 가 아니면 업로드·다운로드 모두 하지 않는다. 문서의 `account` 가 지금 계정과 다르면 그 세이브는 읽지도 쓰지도 않는다.
- **페이지-계정 바인딩**: 한 번 열린 화면은 처음 본 계정에 묶인다. 계정 이름이 그 뒤에 바뀌면(코어가 화면을 새로 고치기 전 잠깐 사이) 클라우드 업로드·다운로드를 모두 막는다 — 이전 계정의 진행이 새 계정의 `duel_save_<id>` 로 새는 일을 막는 두 번째 안전장치다.

### 3. ⚙️ 설정 → 「☁️ 클라우드 세이브」 카드 (로그인 계정에서만)

- `☁️ 클라우드 지금 저장` — 사용자가 누르면 서버가 더 최신이어도 기기 세이브를 올린다(force). 진행이 없는 새 세이브로는 올리지 않는다.
- `☁️ 클라우드에서 불러오기` — 확인 창(요약·저장 시각)을 거쳐 서버 세이브로 맞춘다. 기기 진행은 백업. 대전 중에는 막는다.
- 마지막 클라우드 저장 시각 + 이 기기 마지막 저장 시각 표시. 두 버튼 모두 `aria-label` 을 두어 보이스오버가 그대로 읽는다.

### 4. 검증

- `test_duel_story_restore_removed_2026-11-24.py` — 43검사 전부 통과: 설정 카드·버튼·함수·문구(innerText·aria) 부재(게스트·kyyj35), 스토리 순차 잠금(1~40 → 41 열림·42 잠김), `set_story_max` 적용·저장·대기열 DELETE, 이벤트 상수·함수 6종 존재.
- `test_duel_cloud_save_2026-11-24.py` — 60검사 전부 통과(가짜 서버): 게스트 요청 0건, 새 기기 이어받기, 404 첫 업로드, 서버 우선·기기 우선 판정, `saveScopeReady=false`·전환 중 요청 0건, 다른 `account` 문서 무시, **계정 이름만 바뀐 위험한 순간에도 새 계정 키로 요청 0건**, 설정 카드·두 버튼·aria, 디바운스·중복 방지·치트 즉시 반영, 「지금 저장」·「불러오기」.
- `e2e_duel_cloud_live_2026-11-24.py` — 17검사 전부 통과(실서버): 테스트 전용 계정 `test_duel_cloud_tmp` 로 업로드(200·account·33단계·summary) → 빈 기기에서 이어받기 → 설정 카드·aria·버전 → **키 DELETE 200 · 재조회 404**. 실계정(kyyj35·gral·dev) 키는 건드리지 않았다.
- `test_event_sync_2026-11-24.py` — PvP↔이벤트 동기화 회귀 전부 통과.

### 5. 배포

- 빌드: `python3 compile_duel.py` (VERSION `1.4.17`) → `duel-core.html` / `duel.html` / `duel-version.json`.
- 평문 `games_backup/duel.html.bak` 은 커밋하지 않는다.
