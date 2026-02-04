# Frontend (A 역할) README — Beauty Inside (표정 기반 닮은꼴 Top3)

이 폴더(`frontend/`)는 **A(Front) 담당 범위**입니다.  
A의 목표는 한 줄로 끝납니다:

> **카메라로 한 장 찍어서 WS로 보내고 → 결과(Top3/에러)를 보기 좋게 렌더 → 합성 이미지로 다운로드까지**. :contentReference[oaicite:0]{index=0}

---

## 1) 무엇을 만드는가

브라우저에서 사용자의 얼굴(1명)을 웹캠으로 촬영하고,  
서버가 분석한 **표정 라벨 + 닮은꼴 Top3(금/은/동) + 점수**를 받아 화면에 보여주는 웹 앱입니다.  
원본 이미지는 저장하지 않고 분석에만 쓰며, **다운로드는 사용자가 원할 때만** 합성 이미지로 저장합니다. :contentReference[oaicite:1]{index=1}

---

## 2) 사용자 흐름 (프론트 기준)

1. 홈 화면: 웹캠 권한 요청 → 실시간 미리보기
2. “촬영/분석” 클릭: 현재 프레임 1장을 캡처
3. 로딩 화면: 2~3초(또는 서버 처리시간) 동안 단계 문구 노출
4. 결과 화면: 사용자 캡처 + Top3 카드 + 유사도(0~100) 표시
5. “다운로드”: 사용자 캡처 + Top3 카드를 **한 장으로 합성**해 저장(로컬) :contentReference[oaicite:2]{index=2}

---

## 3) 기술 스택 / 구성

- Front: **HTML / CSS / JS** (필요 시 jQuery) :contentReference[oaicite:3]{index=3}  
- 웹캠: `getUserMedia()`  
- 캡처: `canvas.drawImage()` → `toBlob()` → **JPEG base64**  
- 통신: **WebSocket** (`/ws/analyze`)  
- 다운로드: 캔버스 합성 후 `toBlob()`로 파일 저장 :contentReference[oaicite:4]{index=4}

---

## 4) 디렉토리 구조 (A 담당 지도)

(상위 트리 기준, 프론트는 여기만 보면 됩니다) :contentReference[oaicite:5]{index=5}

- `public/`
  - `index.html` : 엔트리
  - `assets/` : 아이콘/스티커 등(연예인 원본 사진은 제외)
- `src/pages/`
  - `home.html` : 촬영 전(미리보기/버튼)
  - `loading.html` : 로딩 단계 표시
  - `result.html` : Top3 카드/다운로드
- `src/partials/`
  - `privacy_badge.html` : “사진 저장 안함” 안내 고정 컴포넌트
  - `celeb_card.html` : 카드 템플릿(선택)
- `src/styles/`
  - `base.css`, `components.css`, `pages.css`
- `src/js/`
  - `app.js` : 라우팅/상태 전환(홈→로딩→결과/에러)
  - `config.js` : WS URL/타임아웃/옵션
  - `core/` : dom/state/timers 등 공용 유틸
  - `features/`
    - `webcam.js` : 카메라 연결/해제, 권한 실패 UX
    - `capture.js` : 캡처/리사이즈/JPEG base64 생성
    - `ws_client.js` : WS 연결/재시도/요청-응답 분기
    - `render_loading.js` : “표정 확인→비교→정리” 타이밍
    - `render_result.js` : Top3 카드 렌더 + 점수 표시
    - `export_image.js` : 합성 이미지 다운로드
    - `filters_overlay.js` : 랜드마크 스티커(옵션)

---

## 5) Front 상태 머신 (화면이 안 흔들리게)

프론트는 아래 4상태만 유지합니다. :contentReference[oaicite:6]{index=6}

- `HOME` : 카메라 미리보기 + 촬영 버튼
- `LOADING` : 로딩 단계 문구
- `RESULT` : Top3 카드
- `ERROR` : 에러 문구 + “다시 시도”

이벤트는 딱 5개로만(권장):
- `CAM_READY`, `CAPTURED`, `WS_OPEN`, `GOT_RESULT`, `GOT_ERROR` :contentReference[oaicite:7]{index=7}

---

## 6) WebSocket 계약 요약 (프론트가 지켜야 하는 것)

계약(Contract) v1은 **/docs**와 백엔드 스키마가 SSOT이며, 프론트는 **형식 그대로** 보냅니다. :contentReference[oaicite:8]{index=8}

### 6-1) Endpoint
- `/ws/analyze` :contentReference[oaicite:9]{index=9}

### 6-2) Request (client → server)
- `type="analyze"` 고정
- `image_format="jpeg"` 고정
- **image_b64는 raw base64만** (❌ `data:image/jpeg;base64,` prefix 금지) :contentReference[oaicite:10]{index=10}

예시:
```json
{
  "type": "analyze",
  "session_id": "s_9f12ab",
  "seq": 1,
  "ts_ms": 1730000000000,
  "image_format": "jpeg",
  "image_b64": "...."
}
```

## 6-3) Response (server → client)

### 성공 (type="result")
- `type`: `"result"`
- `expression_label`: `"smile" | "sad" | "surprise" | "neutral"` (**4개 고정**)
- `results`: **길이 3** (`rank` 1..3)
- `similarity_100`: **0..100**

> 출처: 팀지침

### 에러 (type="error")
- `type`: `"error"`
- `error_code`: **7개 고정**
  - `FACE_NOT_FOUND`
  - `MULTIPLE_FACES`
  - `TOO_DARK`
  - `TOO_BLURRY`
  - `EXPRESSION_WEAK`
  - `DECODE_FAIL`
  - `TIMEOUT`

> 출처: 팀지침

---

## 7) 이미지 캡처 규칙 (성능/지연 방지)

- 캡처는 **촬영 버튼 눌렀을 때만** (매 프레임 캡처 금지)
- 리사이즈 고정 권장: **긴 변 640px(또는 720px)**
- JPEG 품질: **0.7 ~ 0.85 권장**
- 큰 이미지를 base64로 보내면 **WS 지연/타임아웃**이 쉽게 납니다.

> 출처: A역할_팀지침활용법

---

## 8) 에러 처리 원칙 (팀 멘탈 보호 룰)

- 백엔드는 `error_code`만 정확히 보내면 됩니다.
- 프론트는 `error_code → 문구/CTA`만 **1:1 매핑**합니다.
- “프론트에서 로직으로 해결하려고” 들면 통합이 흔들리기 쉬워서 **금지에 가깝습니다.**

> 출처: 팀지침

---

## 9) 협업/충돌 방지 규칙 (프론트가 지켜야 할 것)

다음 파일들은 **충돌 위험이 큰 SSOT/계약 영역**이라 A가 직접 수정하기보다,  
필요 시 **근거(왜 필요한지 + 프론트에서 막히는 지점)**를 붙여 제안하는 방식이 안전합니다.

- `docs/api_contract.md`
- `backend/app/schemas/ws_messages.py`

> 출처: A역할_팀지침활용법 / 팀지침

---

## 10) 로컬 실행 (프론트만 먼저 UI 개발)

프론트 UI는 **백엔드가 mock을 보내는 동안 먼저 완성**해도 됩니다(전략적으로 안전).

### A안) 프론트만 정적 서빙 (UI/카메라/캡처까지)
```bash
cd frontend
python -m http.server 5173

## 10) 로컬 실행 (프론트만 먼저 UI 개발)

브라우저에서:
- `http://localhost:5173/public/index.html`

참고:
- 카메라는 환경에 따라 **HTTPS 보안 컨텍스트**에서만 정상 동작하는 경우가 있어,
  홈 화면에서 권한/디바이스/환경 안내 UX를 반드시 제공합니다.

> 출처: A역할_팀지침활용법
```

### B안) 백엔드와 함께 통합
- 백엔드가 같은 host로 서빙/프록시되면 `/ws/analyze`로 바로 연결됩니다.
- 다른 host라면 `config.js`에서 WS URL 구성을 조정합니다(프로토콜 `ws/wss` 포함).

> 출처: A역할_팀지침활용법

---

## 11) 프론트 개발 순서 

1. `webcam.js` : `getUserMedia` 연결 + 실패 UX(권한/장치/HTTPS)
2. `capture.js` : 640 리사이즈 + JPEG(base64 prefix 제거)
3. `ws_client.js` : 연결→요청→응답 분기(result/error) + 재시도(2회)
4. `render_loading.js` : 3단계 로딩 문구 타이밍
5. `render_result.js` : Top3 카드 3장 렌더
6. `export_image.js` : 합성 캔버스 → 다운로드

> 출처: A역할_팀지침활용법

---

## 12) 5분 디버깅 체크리스트

1. 카메라가 안 뜬다 → 권한/HTTPS/디바이스 연결부터 확인
2. WS가 안 붙는다 → URL, `ws/wss`, endpoint `/ws/analyze` 확인
3. `DECODE_FAIL`이 잦다 → `image_b64`에 prefix가 붙었는지 확인(최빈 원인)
4. `TIMEOUT`이 뜬다 → 이미지 크기(리사이즈) 먼저 줄이기(즉효)

> 출처: A역할_팀지침활용법

---

## 13) 프라이버시 표시 (프론트가 지켜야 하는 문구)

- “원본 사용자 이미지 저장 없음”
- “다운로드는 사용자 선택”

이 문구는 `privacy_badge`, 푸터/툴팁 등에 **항상 노출**하는 것을 기본으로 합니다.
