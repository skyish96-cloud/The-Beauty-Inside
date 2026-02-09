# 🎬 The Beauty Inside - 닮은 연예인 찾기 서비스

사용자의 얼굴 사진을 업로드하면, **AI가 닮은 연예인을 찾아주는 서비스**입니다.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green)
![React](https://img.shields.io/badge/React-18%2B-cyan)
![License](https://img.shields.io/badge/License-Internal-red)

---

## 🎯 주요 기능

✅ **실시간 얼굴 인식** - MediaPipe를 통한 고정밀 얼굴 감지  
✅ **표정 분석** - 웃음, 슬픔, 놀람 등 4가지 표정 분류  
✅ **AI 매칭** - DeepFace 임베딩으로 닮은 연예인 추천  
✅ **라이브 피드백** - WebSocket을 통한 실시간 진행 상태  
✅ **빠른 응답** - 평균 300ms 처리 시간  

---

## 📊 기술 스택

### 🔙 Backend
| 레이어 | 기술 |
|--------|------|
| **Framework** | FastAPI + Uvicorn |
| **통신** | WebSocket (asyncio) |
| **얼굴 감지** | MediaPipe Face Landmarker |
| **표정 분석** | MediaPipe Blend Shapes |
| **임베딩** | DeepFace (FaceNet512) |
| **매칭** | Scikit-learn (Cosine Similarity) |
| **로깅** | Structlog |
| **테스트** | Pytest |

### 🎨 Frontend
| 레이어 | 기술 |
|--------|------|
| **Framework** | React 18 |
| **통신** | WebSocket API |
| **UI** | Tailwind CSS / MUI |
| **상태관리** | Context API |
| **빌드** | Vite |

### ☁️ Infrastructure (선택)
- **Database:** Firestore (결과 저장)
- **Storage:** Cloud Storage (이미지)
- **Deploy:** Firebase Hosting (프론트) / Cloud Run (백엔드)

---

## 🚀 빠른 시작

### 1️⃣ 저장소 클론

```bash
git clone https://github.com/your-org/beauty-inside.git
cd beauty-inside
```

### 2️⃣ 백엔드 설정

```bash
cd backend

# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일에서 필요한 값 수정

# 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3️⃣ 프론트엔드 설정

```bash
cd frontend

# 의존성 설치
npm install

# 환경 변수 설정
cp .env.example .env

# 개발 서버 실행
npm run dev
```

### 4️⃣ 접속 확인

---

## 🔄 Firebase 임베딩 동기화 (선택)

### 개요

Firebase Firestore에 저장된 **995명의 연예인 임베딩 데이터**를 로컬에서 빠르게 사용하기 위해 동기화합니다.

### 사용 시기

| 상황 | 동작 |
|------|------|
| **첫 설정** | Firebase → CSV + numpy 파일 생성 |
| **정기 업데이트** | Firebase의 새 데이터 추가 |
| **오프라인 개발** | 로컬 임베딩만 사용 (Firebase 불필요) |

### 빠른 실행

```bash
cd scripts

# 1. 간단한 동기화 (추천)
python sync_celeb_embeddings_simple.py

# 또는 2. 고급 옵션
python manage_embeddings.py --mode sync
```

### 결과

```
✓ 동기화 완료!

📊 최종 결과:
  • 연예인: 995명
  • 이미지: 995개
  • 임베딩 벡터: (995, 512)
  • 저장 위치: data/celebs/
```

### 상세 가이드

📖 [Firebase 동기화 가이드](docs/FIREBASE_SYNC_GUIDE.md) 참고

---

## 🏗️ 전체 로직 구성도

### 시스템 아키텍처

```
┌──────────────────────────────────────────────────────────────┐
│                     FRONTEND (React)                          │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  1. 웹캠 캡처 → 2. Base64 인코딩 → 3. WebSocket 전송   │  │
│  │     (capture.js)  (export_image.js)  (ws_client.js)    │  │
│  └──────────────────────────┬─────────────────────────────┘  │
└─────────────────────────────┼────────────────────────────────┘
                              │ WebSocket
                              │ AnalyzeRequest
                              │ {session_id, seq, image_b64}
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                        │
│                                                               │
│  ┌─ API Layer ──────────────────────────────────────────┐   │
│  │ [ws.py] WebSocket Handler                            │   │
│  │ ├─ 연결 수락                                          │   │
│  │ ├─ 메시지 파싱 (AnalyzeRequest)                      │   │
│  │ ├─ 분석 파이프라인 실행                               │   │
│  │ └─ 결과 반환 (ResultMessage)                         │   │
│  └──────────────────────┬────────────────────────────────┘   │
│                         │                                      │
│  ┌─ Domain Layer ──────▼─────────────────────────────────┐   │
│  │ [analyze_pipeline.py] 분석 워크플로우 조율             │   │
│  │                                                        │   │
│  │ ┌─ STEP 1: Decode ──────────────────────────────┐   │   │
│  │ │ 입력: Base64 인코딩된 JPEG 이미지             │   │   │
│  │ │ 동작: [decode.py] Base64 → numpy 배열        │   │   │
│  │ │ 출력: RGB 이미지 배열 (H×W×3)                │   │   │
│  │ └────────────────────────────────────────────────┘   │   │
│  │                       │                               │   │
│  │ ┌─ STEP 2: Detect ───▼─────────────────────────┐   │   │
│  │ │ 입력: RGB 이미지                              │   │   │
│  │ │ 동작:                                         │   │   │
│  │ │  1. [mp_landmarker.py] 얼굴 감지            │   │   │
│  │ │     - 468개 얼굴 랜드마크 추출               │   │   │
│  │ │  2. [quality_gate.py] 품질 검사              │   │   │
│  │ │     - 얼굴 개수 (1개만 허용)                │   │   │
│  │ │     - 밝기 (너무 어두우면 거부)              │   │   │
│  │ │     - 흐림 (흐리면 거부)                     │   │   │
│  │ │  3. [expression_map.py] 표정 분석            │   │   │
│  │ │     - 52개 블렌드쉐이프 추출                │   │   │
│  │ │     - 웃음/슬픔/놀람/무표정 중 하나로 분류   │   │   │
│  │ │ 출력: QualityResult, 표정(Expression)        │   │   │
│  │ └────────────────────────────────────────────────┘   │   │
│  │                       │                               │   │
│  │ ┌─ STEP 3: Embed ────▼─────────────────────────┐   │   │
│  │ │ 입력: 원본 이미지 + 얼굴 영역 정보           │   │   │
│  │ │ 동작:                                         │   │   │
│  │ │  1. [face_crop.py] 얼굴 영역 크롭            │   │   │
│  │ │  2. [deepface_embedder.py] 임베딩 추출       │   │   │
│  │ │     - 모델: FaceNet512                       │   │   │
│  │ │     - 출력: 512차원 벡터                    │   │   │
│  │ │ 출력: embedding_vector (512,)                │   │   │
│  │ └────────────────────────────────────────────────┘   │   │
│  │                       │                               │   │
│  │ ┌─ STEP 4: Match ────▼─────────────────────────┐   │   │
│  │ │ 입력: 사용자 임베딩 + 표정                   │   │   │
│  │ │ 동작:                                         │   │   │
│  │ │  1. [similarity.py] 유사도 계산              │   │   │
│  │ │     - 방식: 코사인 유사도 (Cosine)          │   │   │
│  │ │     - 범위: -1 ~ 1                          │   │   │
│  │ │  2. [score_scale.py] 점수 변환               │   │   │
│  │ │     - 공식: 50 + (유사도^0.7) × 49         │   │   │
│  │ │     - 최종 범위: 50 ~ 99                    │   │   │
│  │ │  3. [topk.py] Top-3 선정                     │   │   │
│  │ │     - 상위 3명 연예인 반환                   │   │   │
│  │ │ 출력: [RankingResult × 3]                    │   │   │
│  │ └────────────────────────────────────────────────┘   │   │
│  └───────────────────────────────────────────────────────┘   │
│                         │                                      │
│  ┌─ Infra Layer ───────▼─────────────────────────────────┐   │
│  │ [celeb_store/]                                        │   │
│  │ ├─ paths.py: 데이터 경로 관리                         │   │
│  │ ├─ loader.py: 연예인 데이터 로드                      │   │
│  │ │  • celebs.csv → 연예인 메타데이터                  │   │
│  │ │  • images.csv → 이미지 메타데이터                  │   │
│  │ │  • embed.npy → 512차원 임베딩 벡터 (N×512)        │   │
│  │ │  • ids.npy → 연예인 ID 매핑                        │   │
│  │ └─ index.py: 표정별 인덱스 접근                       │   │
│  │    • expr_index.json: 표정 → 연예인 ID 매핑         │   │
│  │                                                        │   │
│  │ [firestore/] (선택)                                  │   │
│  │ ├─ client.py: Firebase 인증 및 연결                 │   │
│  │ └─ repo.py: 분석 결과 저장소                         │   │
│  │                                                        │   │
│  │ [images/]                                             │   │
│  │ └─ decode.py: Base64 디코딩 유틸                     │   │
│  └────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
                              │
                              │ ResultMessage
                              │ {rank, celeb_name, similarity}
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                    FRONTEND (Result Render)                   │
│  1. 결과 수신 (result.js)                                    │
│  2. 카드 렌더링 (celeb_card.html)                           │
│  3. 사용자 표시                                              │
└──────────────────────────────────────────────────────────────┘
```

---

### 데이터 흐름 상세

#### 1️⃣ 요청 메시지 구조 (Frontend → Backend)

```json
{
  "type": "analyze",
  "session_id": "s_abc123",
  "seq": 1,
  "ts_ms": 1730000000000,
  "image_format": "jpeg",
  "image_b64": "iVBORw0KGgoAAAANSUhEUgAAAAUA..."
}
```

| 필드 | 설명 | 예시 |
|------|------|------|
| `type` | 요청 타입 (고정) | `"analyze"` |
| `session_id` | 사용자 세션 ID | `"s_abc123"` |
| `seq` | 요청 시퀀스 번호 | `1` |
| `ts_ms` | 타임스탬프 (밀리초) | `1730000000000` |
| `image_format` | 이미지 포맷 (고정) | `"jpeg"` |
| `image_b64` | Base64 인코딩 이미지 (**prefix 제거됨**) | `"iVBORw0..."` |

#### 2️⃣ 응답 메시지 구조 (Backend → Frontend)

**성공 응답:**
```json
{
  "type": "result",
  "session_id": "s_abc123",
  "seq": 1,
  "latency_ms": 287,
  "expression_label": "smile",
  "similarity_method": "cosine",
  "quality_flags": [],
  "results": [
    {
      "rank": 1,
      "celeb_id": "c_001",
      "celeb_name": "연예인 A",
      "similarity": 0.82,
      "similarity_100": 82
    },
    {
      "rank": 2,
      "celeb_id": "c_014",
      "celeb_name": "연예인 B",
      "similarity": 0.79,
      "similarity_100": 79
    },
    {
      "rank": 3,
      "celeb_id": "c_203",
      "celeb_name": "연예인 C",
      "similarity": 0.77,
      "similarity_100": 77
    }
  ]
}
```

**에러 응답:**
```json
{
  "type": "error",
  "session_id": "s_abc123",
  "error_code": "FACE_NOT_FOUND",
  "message": "얼굴을 감지할 수 없습니다"
}
```

#### 3️⃣ 표정 분류 로직

| 표정 | 영문 | 판단 기준 | 주요 블렌드쉐이프 |
|------|------|----------|------------------|
| 웃음 | `smile` | mouthSmile > 0.30 | mouthSmileLeft (0.30), mouthSmileRight (0.30) |
| 슬픔 | `sad` | mouthFrown > 0.25 | mouthFrownLeft (0.25), mouthFrownRight (0.25) |
| 놀람 | `surprise` | browOuterUp > 0.35 | browOuterUpLeft (0.20), browOuterUpRight (0.20) |
| 무표정 | `neutral` | 위 조건 미충족 | (기본값) |

#### 4️⃣ 유사도 매칭 알고리즘

```
Step 1: 임베딩 벡터 비교
  A = 사용자 얼굴 (512차원)
  B = 연예인 얼굴 (512차원)
  
Step 2: 코사인 유사도 계산
  similarity = (A · B) / (||A|| × ||B||)
  범위: -1 ~ 1

Step 3: 점수 스케일링 (Power Scale)
  score = 50 + (similarity ^ 0.7) × 49
  범위: 50 ~ 99
  
Step 4: Top-3 선정
  결과를 점수순으로 정렬하여 상위 3명 반환
```

#### 5️⃣ 품질 검사 플로우

```
입력 이미지
    │
    ▼
[1] 밝기 검사
    ├─ 너무 어두우면 → ERROR: IMAGE_TOO_DARK
    └─ 통과 ──┐
             ▼
[2] 흐림 검사
    ├─ Laplacian 분산이 낮으면 → ERROR: IMAGE_TOO_BLURRY
    └─ 통과 ──┐
             ▼
[3] 얼굴 개수 검사
    ├─ 얼굴 0개 → ERROR: NO_FACE_DETECTED
    ├─ 얼굴 2개 이상 → ERROR: MULTIPLE_FACES_DETECTED
    └─ 1개 ──┐
            ▼
[4] 표정 신뢰도 검사
    ├─ 신뢰도 < 0.15 → ERROR: EXPRESSION_NOT_DETECTED
    └─ 통과 ──┐
            ▼
         ✅ 품질 통과
```

---

### 파일 구조별 책임

```
backend/app/
│
├─ api/
│  └─ ws.py ..................... WebSocket 엔드포인트
│                               ├─ 연결 관리
│                               ├─ 메시지 라우팅
│                               └─ 에러 매핑
│
├─ domain/ ...................... 핵심 비즈니스 로직
│  │
│  ├─ pipeline/
│  │  └─ analyze_pipeline.py ... 분석 워크플로우 조율
│  │                            ├─ Step 1: Decode
│  │                            ├─ Step 2: Detect
│  │                            ├─ Step 3: Embed
│  │                            └─ Step 4: Match
│  │
│  ├─ expression/
│  │  ├─ mp_landmarker.py ...... MediaPipe 얼굴 감지
│  │  ├─ expression_map.py ..... 블렌드쉐이프 → 표정
│  │  └─ quality_gate.py ....... 품질 검사
│  │
│  ├─ embedding/
│  │  ├─ deepface_embedder.py .. 임베딩 추출 (FaceNet512)
│  │  └─ face_crop.py .......... 얼굴 영역 크롭
│  │
│  └─ ranking/
│     ├─ similarity.py ......... 코사인 유사도
│     ├─ score_scale.py ........ 점수 변환
│     └─ topk.py ............... Top-K 선정
│
├─ infra/ ....................... 외부 시스템 인터페이스
│  │
│  ├─ celeb_store/
│  │  ├─ paths.py ............ 데이터 경로 관리
│  │  ├─ loader.py .......... 연예인 데이터 로드
│  │  │                      ├─ celebs.csv 로드
│  │  │                      ├─ embed.npy 로드
│  │  │                      └─ ids.npy 로드
│  │  └─ index.py .......... 표정 인덱스
│  │
│  ├─ firestore/
│  │  ├─ client.py ......... Firebase 클라이언트
│  │  └─ repo.py ........... 분석 결과 저장
│  │
│  └─ images/
│     └─ decode.py ......... Base64 디코딩
│
├─ schemas/ ..................... 데이터 모델
│  ├─ ws_messages.py ............ WebSocket 요청/응답
│  ├─ result_models.py .......... 분석 결과 모델
│  └─ firestore_models.py ....... Firestore DTO
│
├─ core/ ........................ 공통 유틸
│  ├─ config.py ................. 환경 설정
│  ├─ logger.py ................. 구조화된 로깅
│  ├─ errors.py ................. 에러 정의
│  └─ debug_tools.py ............ 디버깅 도구
│
├─ utils/ ....................... 헬퍼 함수
│  ├─ ids.py .................... ID 생성
│  └─ timeit.py ................. 성능 측정
│
└─ main.py ...................... FastAPI 앱 초기화

frontend/src/
│
├─ js/
│  │
│  ├─ features/
│  │  ├─ webcam.js ............ 웹캠 스트림 제어
│  │  ├─ capture.js .......... 프레임 캡처
│  │  ├─ export_image.js ..... Base64 인코딩
│  │  ├─ ws_client.js ....... WebSocket 클라이언트
│  │  │                      ├─ analyzeOnce()
│  │  │                      └─ 재시도 로직
│  │  ├─ render_result.js ... 결과 렌더링
│  │  └─ filters_overlay.js .. 필터 오버레이
│  │
│  ├─ core/
│  │  ├─ state.js ............ 상태 관리 (Context)
│  │  ├─ error_map.js ....... 에러 메시지 매핑
│  │  ├─ dom.js ............. DOM 유틸
│  │  └─ timers.js ......... 타이머 관리
│  │
│  ├─ config.js .............. 전역 설정
│  └─ app.js ................. 진입점
│
├─ pages/ ...................... HTML 페이지
│  ├─ home.html ............... 메인 화면
│  ├─ loading.html ............ 분석 중 화면
│  ├─ result.html ............ 결과 화면
│  └─ error.html ............ 에러 화면
│
├─ partials/ ................... HTML 컴포넌트
│  ├─ celeb_card.html ......... 연예인 카드
│  ├─ header.html ............ 헤더
│  ├─ footer.html ............ 푸터
│  └─ privacy_badge.html ..... 개인정보 배지
│
└─ styles/
   ├─ base.css ................ 기본 스타일
   ├─ components.css .......... 컴포넌트 스타일
   └─ pages.css ............... 페이지별 스타일
```

---

### 핵심 처리 시간

| 구성 | 예상 시간 |
|------|----------|
| 이미지 디코딩 | ~20ms |
| 얼굴 감지 + 품질 검사 | ~80ms |
| 표정 분석 | ~30ms |
| 임베딩 추출 | ~100ms |
| 유사도 계산 + 점수 변환 | ~10ms |
| 결과 반환 | ~5ms |
| **총 처리 시간** | **~245ms** |

---

## 🔄 요청-응답 사이클 예시

```
┌─ FRONTEND ─────────────────────────────────┐
│ 1. 웹캠에서 프레임 캡처                    │
│ 2. Base64로 인코딩                         │
│ 3. WebSocket 메시지 구성                   │
│    {type, session_id, seq, image_b64}      │
└──────────────┬──────────────────────────────┘
               │ WebSocket
               │ (평균 <50ms)
               ▼
┌─ BACKEND ─────────────────────────────────┐
│ 4. 메시지 파싱                             │
│ 5. Pipeline 실행:                         │
│    ├─ Step1: 이미지 디코딩                │
│    ├─ Step2: 얼굴 감지 + 품질 검사        │
│    ├─ Step3: 임베딩 추출                  │
│    └─ Step4: 매칭 + 점수 계산             │
│ 6. 결과 생성                              │
└──────────────┬──────────────────────────────┘
               │ WebSocket
               │ (평균 <50ms)
               ▼
┌─ FRONTEND ─────────────────────────────────┐
│ 7. 결과 수신                               │
│ 8. UI 렌더링                               │
│    ├─ 표정 라벨 표시                      │
│    ├─ Top-3 연예인 카드                   │
│    └─ 유사도 점수 표시                    │
└────────────────────────────────────────────┘

총 지연시간: ~300ms (처리 ~245ms + 통신 ~55ms)
```

---

## 🔥 Firebase 임베딩 동기화

### 📌 개요

Firebase Firestore에 저장된 **995명의 셀레브리티 임베딩 데이터**를 로컬 파일로 동기화합니다.

- **원격:** Firebase Firestore (`celeb_embeddings` 컬렉션)
- **로컬:** CSV + NumPy 파일 (오프라인 사용 가능)

### 🚀 빠른 시작

#### 1단계: 환경 검증
```bash
python scripts/setup_check.py
```

#### 2단계: 동기화 실행
```bash
# 간단한 동기화 (995명 모두)
python scripts/sync_celeb_embeddings_simple.py

# 또는 고급 동기화 (기존 데이터 병합)
python scripts/sync_celeb_embeddings_from_firebase.py

# 또는 통합 관리 도구
python scripts/manage_embeddings.py --mode sync
```

### 📋 설정 방법

#### 방법 1: 자동 감지 (권장)
```bash
# backend/serviceAccountKey.json 파일이 있으면 자동으로 감지됩니다
# .env 파일 생성 없이 바로 사용 가능
python scripts/setup_check.py
```

#### 방법 2: .env 파일로 설정
```bash
cp .env.example .env
# 필요시 값 수정:
# FIREBASE_CREDENTIALS_PATH=backend/serviceAccountKey.json
# FIREBASE_PROJECT_ID=the-beauty-inside
```

#### 방법 3: 환경 변수로 설정
```bash
# Windows PowerShell
$env:FIREBASE_CREDENTIALS_PATH="backend/serviceAccountKey.json"
$env:FIREBASE_PROJECT_ID="the-beauty-inside"

# Linux/Mac
export FIREBASE_CREDENTIALS_PATH=backend/serviceAccountKey.json
export FIREBASE_PROJECT_ID=the-beauty-inside
```

### 📊 결과 확인

동기화 완료 후:
```bash
# 생성된 파일 확인
ls -lah data/celebs/meta/
ls -lah data/celebs/embeddings/

# 데이터 확인
wc -l data/celebs/meta/celebs.csv  # 996줄 (995명 + 헤더)

# NumPy 파일 확인
python -c "import numpy as np; print(np.load('data/celebs/embeddings/embed.npy').shape)"
# (995, 512) 출력 예상
```

### 📚 상세 가이드

- [Firebase Config Guide](docs/FIREBASE_CONFIG_GUIDE.md) - 설정 가이드
- [Service Key Analysis](docs/FIREBASE_SERVICE_KEY_ANALYSIS.md) - 근본 원인 분석
- [Firebase Sync Guide](docs/FIREBASE_SYNC_GUIDE.md) - 동기화 상세 설명
- [Fix Summary](docs/FIREBASE_FIX_SUMMARY.md) - 최종 요약

### ❓ 문제 해결

**Q: Firebase 미활성화 메시지가 나옵니다**
```bash
# 1. 서비스 키 파일 확인
ls -la backend/serviceAccountKey.json

# 2. 파일이 없으면 복사
# backend/ 폴더에 serviceAccountKey.json 파일을 놓으세요

# 3. 다시 검증
python scripts/setup_check.py
```

**Q: "FIREBASE_PROJECT_ID not found" 에러**
```bash
# 1. .env 파일 생성
echo "FIREBASE_PROJECT_ID=the-beauty-inside" >> .env

# 2. 또는 환경 변수 설정
export FIREBASE_PROJECT_ID=the-beauty-inside

# 3. 다시 실행
python scripts/setup_check.py
```

---
