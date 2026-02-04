# Beauty Inside - Backend

닮은 연예인 찾기 서비스의 백엔드 서버입니다.

---

## 📋 목차

- [아키텍처](#아키텍처)
- [디렉토리 구조](#디렉토리-구조)
- [핵심 모듈 설명](#핵심-모듈-설명)
- [설치 및 실행](#설치-및-실행)
- [API 사용법](#api-사용법)
- [환경 설정](#환경-설정)
- [테스트](#테스트)

---

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                      클라이언트 (Browser)                    │
└─────────────────────────────┬───────────────────────────────┘
                              │ WebSocket (ws://)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         API Layer                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  WebSocket Handler (api/ws.py)                        │  │
│  │  - 연결 관리 (ConnectionManager)                       │  │
│  │  - 메시지 라우팅 (analyze_request, ping)               │  │
│  │  - 진행 상태 콜백                                      │  │
│  └───────────────────────────┬───────────────────────────┘  │
└──────────────────────────────┼──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                       Domain Layer                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Analyze Pipeline (domain/pipeline/)                  │  │
│  │                                                        │  │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────┐│  │
│  │  │ 1.Decode │ → │ 2.Detect │ → │ 3.Embed  │ → │4.Match││  │
│  │  │ 이미지   │   │ 얼굴감지 │   │ 특징추출 │   │ 매칭 ││  │
│  │  └──────────┘   └──────────┘   └──────────┘   └──────┘│  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌───────────────────┐    │
│  │ Expression  │  │  Embedding  │  │     Ranking       │    │
│  │ ─────────── │  │ ─────────── │  │ ───────────────── │    │
│  │ MediaPipe   │  │ DeepFace    │  │ Cosine Similarity │    │
│  │ 표정 분석   │  │ 얼굴 임베딩 │  │ Top-K 선정        │    │
│  └─────────────┘  └─────────────┘  └───────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                        Infra Layer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌───────────────────┐    │
│  │ Celeb Store │  │  Firestore  │  │      Images       │    │
│  │ 연예인 DB   │  │   (선택)    │  │   이미지 처리     │    │
│  └─────────────┘  └─────────────┘  └───────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 디렉토리 구조

```
backend/
├── app/
│   ├── main.py                 # FastAPI 앱 엔트리포인트
│   ├── api/
│   │   └── ws.py               # WebSocket 엔드포인트
│   ├── core/
│   │   ├── config.py           # 환경 설정 (Pydantic Settings)
│   │   ├── errors.py           # 에러 코드 정의
│   │   └── logger.py           # 구조화된 로깅
│   ├── domain/
│   │   ├── embedding/
│   │   │   ├── deepface_embedder.py  # DeepFace 얼굴 임베딩
│   │   │   └── face_crop.py          # 얼굴 크롭 유틸
│   │   ├── expression/
│   │   │   ├── mp_landmarker.py      # MediaPipe 랜드마크
│   │   │   ├── expression_map.py     # 표정 분류 로직
│   │   │   └── quality_gate.py       # 이미지 품질 검사
│   │   ├── pipeline/
│   │   │   └── analyze_pipeline.py   # 분석 파이프라인 조율
│   │   └── ranking/
│   │       ├── similarity.py         # 코사인 유사도 계산
│   │       ├── score_scale.py        # 점수 스케일링
│   │       └── topk.py               # Top-K 선정
│   ├── infra/
│   │   ├── celeb_store/
│   │   │   ├── paths.py              # 경로 관리
│   │   │   ├── loader.py             # 연예인 데이터 로더
│   │   │   └── index.py              # 표정별 인덱스
│   │   ├── firestore/
│   │   │   ├── client.py             # Firebase 클라이언트
│   │   │   └── repo.py               # 저장소 패턴
│   │   └── images/
│   │       └── decode.py             # Base64 이미지 디코딩
│   ├── schemas/
│   │   ├── ws_messages.py            # WebSocket 메시지 모델
│   │   ├── result_models.py          # 결과 도메인 모델
│   │   └── firestore_models.py       # Firestore DTO
│   └── utils/
│       ├── ids.py                    # ID 생성/검증
│       └── timeit.py                 # 성능 측정
├── tests/
│   ├── test_quality_gate.py          # 품질 검사 테스트
│   ├── test_ranking.py               # 랭킹 테스트
│   └── test_ws_contract.py           # WebSocket 스키마 테스트 -
├── requirements.txt
└── README.md
```

---

## 🔧 핵심 모듈 설명

### 1. 분석 파이프라인 (`domain/pipeline/analyze_pipeline.py`)

4단계 분석 워크플로우를 조율합니다:

```python
# 분석 흐름
1. decode()   → Base64 이미지를 numpy 배열로 변환
2. detect()   → 얼굴 감지 + 품질 검사 + 표정 분석
3. embed()    → DeepFace로 512차원 얼굴 특징 벡터 추출
4. match()    → 연예인 임베딩과 유사도 비교 → Top-3 선정
```

### 2. 표정 분석 (`domain/expression/`)

| 모듈 | 역할 |
|------|------|
| `mp_landmarker.py` | MediaPipe로 얼굴 랜드마크 + 블렌드쉐이프 추출 |
| `expression_map.py` | 블렌드쉐이프 → 표정 분류 (smile, sad, surprise, neutral) |
| `quality_gate.py` | 흐림/밝기/얼굴크기 품질 검사 |

### 3. 얼굴 임베딩 (`domain/embedding/`)

| 모듈 | 역할 |
|------|------|
| `deepface_embedder.py` | Facenet512 모델로 512차원 벡터 추출 |
| `face_crop.py` | 얼굴 영역 크롭 및 정렬 |

### 4. 랭킹 시스템 (`domain/ranking/`)

| 모듈 | 역할 |
|------|------|
| `similarity.py` | 배치 코사인 유사도 계산 |
| `score_scale.py` | 0~1 유사도 → 50~99 표시 점수 변환 |
| `topk.py` | Gold/Silver/Bronze 선정 |

### 5. WebSocket API (`api/ws.py`)

```
클라이언트                        서버
    │                              │
    │── analyze_request ──────────>│
    │                              │ (분석 시작)
    │<────── analyze_progress ─────│ (10% 수신완료)
    │<────── analyze_progress ─────│ (25% 얼굴감지)
    │<────── analyze_progress ─────│ (40% 표정분석)
    │<────── analyze_progress ─────│ (60% 임베딩)
    │<────── analyze_progress ─────│ (80% 매칭중)
    │<────── analyze_result ───────│ (100% 완료 + 결과)
    │                              │
```

---

## 🚀 설치 및 실행

### 요구 사항

- Python 3.9+
- 4GB RAM 이상
- (선택) CUDA GPU - 성능 향상

### 1. 가상 환경 생성

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. AI 모델 다운로드 (자동)

서버 첫 실행 시 자동으로 다운로드됩니다:
- **MediaPipe Face Landmarker** (~4MB) → `backend/app/models/`
- **DeepFace Facenet512** (~95MB) → `~/.deepface/weights/`

수동 다운로드:
```bash
python -c "from app.core.model_loader import initialize_all_models; initialize_all_models()"
```

### 4. 서버 실행

```bash
# 개발 모드 (자동 재시작)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 모드
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. 접속 확인

- 서버: http://localhost:8000
- API 문서: http://localhost:8000/docs
- 헬스체크: http://localhost:8000/health

---

## 📡 API 사용법

### WebSocket 연결

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/analyze');

ws.onopen = () => {
  console.log('연결됨');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('메시지:', data);
};
```

### 분석 요청

```javascript
// 이미지 캡처 후 전송
const imageData = canvas.toDataURL('image/jpeg', 0.8);

ws.send(JSON.stringify({
  type: 'analyze_request',
  image_data: imageData
}));
```

### 응답 처리

```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch (data.type) {
    case 'analyze_progress':
      // 진행 상태 업데이트
      console.log(`${data.progress_percent}% - ${data.message}`);
      break;
      
    case 'analyze_result':
      // 결과 표시
      console.log('표정:', data.detected_expression);
      data.matches.forEach(match => {
        console.log(`${match.rank}위: ${match.name} (${match.similarity_score}점)`);
      });
      break;
      
    case 'error':
      // 에러 처리
      console.error(`[${data.error_code}] ${data.message}`);
      break;
  }
};
```

---

## ⚙️ 환경 설정

### 환경 변수 (.env)

```env
# 서버 설정
DEBUG=true
LOG_LEVEL=INFO

# 얼굴 분석
FACE_DETECTION_CONFIDENCE=0.7
FACE_EMBEDDING_MODEL=Facenet512
FACE_DETECTOR_BACKEND=retinaface

# 품질 검사
MIN_FACE_SIZE=80
BLUR_THRESHOLD=100
BRIGHTNESS_MIN=40
BRIGHTNESS_MAX=250

# 랭킹
TOP_K=3
SIMILARITY_THRESHOLD=0.4

# 데이터 경로
CELEB_DATA_PATH=../data/celebs

# Firebase (선택)
FIREBASE_ENABLED=false
FIREBASE_CREDENTIALS_PATH=
```

---

## 🧪 테스트

### 단위 테스트 실행

```bash
# 전체 테스트
pytest tests/ -v

# 특정 테스트
pytest tests/test_quality_gate.py -v
pytest tests/test_ranking.py -v
pytest tests/test_ws_contract.py -v

# 커버리지
pytest tests/ --cov=app --cov-report=html
```

### 연결 테스트

```bash
# 모듈 임포트 테스트
python -c "from app.main import app; print('✓ main.py')"
python -c "from app.api.ws import router; print('✓ ws.py')"
python -c "from app.domain.pipeline.analyze_pipeline import AnalyzePipeline; print('✓ pipeline')"
```

---

## 📊 성능 참고

| 단계 | 예상 시간 |
|------|----------|
| 이미지 디코딩 | ~10ms |
| 얼굴 감지 (MediaPipe) | ~50ms |
| 표정 분석 | ~20ms |
| 임베딩 추출 (DeepFace) | ~200ms |
| 유사도 매칭 | ~30ms |
| **총합** | **~300-500ms** |

> GPU 사용 시 임베딩 추출 시간이 크게 단축됩니다.

---

## 🔗 관련 문서

- [API Contract](../docs/api_contract.md) - WebSocket 메시지 규격
- [Error Codes](../docs/error_codes.md) - 에러 코드 정의
- [Scoring Rules](../docs/scoring_rules.md) - 점수 계산 규칙
- [Architecture](../docs/architecture.md) - 전체 아키텍처

---

## 📝 라이선스

이 프로젝트는 내부 사용 목적으로 제작되었습니다.
