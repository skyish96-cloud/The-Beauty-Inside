# Architecture - 시스템 아키텍처

## 개요
Beauty Inside는 클린 아키텍처 기반의 실시간 얼굴 분석 시스템입니다.

---

## 전체 구조

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐ │
│  │   Webcam   │──│  Capture   │──│   WebSocket Client     │ │
│  └────────────┘  └────────────┘  └───────────┬────────────┘ │
└──────────────────────────────────────────────┼──────────────┘
                                               │ ws://
                                               ▼
┌─────────────────────────────────────────────────────────────┐
│                         Backend                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                     API Layer                            ││
│  │  ┌──────────────────────────────────────────────────┐   ││
│  │  │               WebSocket Handler                   │   ││
│  │  │  - Connection Management                         │   ││
│  │  │  - Message Routing                               │   ││
│  │  │  - Progress Callbacks                            │   ││
│  │  └────────────────────────┬─────────────────────────┘   ││
│  └───────────────────────────┼─────────────────────────────┘│
│                              ▼                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                   Domain Layer                           ││
│  │  ┌───────────────────────────────────────────────────┐  ││
│  │  │              Analyze Pipeline                      │  ││
│  │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │  ││
│  │  │  │ Decode  │→│ Detect  │→│  Embed  │→│  Match  │  │  ││
│  │  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘  │  ││
│  │  └───────────────────────────────────────────────────┘  ││
│  │                                                          ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  ││
│  │  │ Expression  │  │  Embedding  │  │     Ranking     │  ││
│  │  │ mp_landmarker│  │ deepface    │  │ similarity     │  ││
│  │  │ expression_map│ │ face_crop   │  │ score_scale    │  ││
│  │  │ quality_gate │  │             │  │ topk           │  ││
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  ││
│  └─────────────────────────────────────────────────────────┘│
│                              │                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                   Infra Layer                            ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  ││
│  │  │ Celeb Store │  │  Firestore  │  │     Images      │  ││
│  │  │ paths       │  │  client     │  │     decode      │  ││
│  │  │ loader      │  │  repo       │  │                 │  ││
│  │  │ index       │  │             │  │                 │  ││
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Embeddings  │  │   Images    │  │      Metadata       │  │
│  │ embed.npy   │  │ neutral/    │  │   celebs.csv        │  │
│  │ ids.npy     │  │ smile/      │  │   images.csv        │  │
│  │             │  │ sad/        │  │   expr_index.json   │  │
│  │             │  │ surprise/   │  │                     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 레이어 설명

### 1. API Layer (`app/api/`)
클라이언트와의 통신 담당

- **ws.py**: WebSocket 엔드포인트
  - 연결 관리
  - 메시지 라우팅
  - 진행 상태 콜백

### 2. Domain Layer (`app/domain/`)
비즈니스 로직 담당

#### Pipeline
- **analyze_pipeline.py**: 분석 워크플로우 조율

#### Expression
- **mp_landmarker.py**: MediaPipe 얼굴 감지
- **expression_map.py**: 블렌드쉐이프 → 표정 매핑
- **quality_gate.py**: 이미지 품질 검사

#### Embedding
- **deepface_embedder.py**: 얼굴 임베딩 추출
- **face_crop.py**: 얼굴 영역 크롭

#### Ranking
- **similarity.py**: 코사인 유사도 계산
- **score_scale.py**: 점수 스케일링
- **topk.py**: Top-K 선정

### 3. Infra Layer (`app/infra/`)
외부 시스템과의 인터페이스

#### Celeb Store
- **paths.py**: 경로 관리
- **loader.py**: 연예인 데이터 로딩
- **index.py**: 표정 인덱스

#### Firestore
- **client.py**: Firebase 클라이언트
- **repo.py**: 저장소 패턴

#### Images
- **decode.py**: Base64 디코딩

### 4. Core Layer (`app/core/`)
공통 기능

- **config.py**: 환경 설정
- **logger.py**: 로깅
- **errors.py**: 에러 정의

### 5. Schemas (`app/schemas/`)
데이터 모델

- **ws_messages.py**: WebSocket 메시지
- **result_models.py**: 결과 모델
- **firestore_models.py**: Firestore DTO

---

## 분석 파이프라인

```
[이미지 수신]
     │
     ▼
┌─────────────────┐
│  1. Decode      │  Base64 디코딩 → numpy 배열
│  (이미지 디코딩) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  2. Detect      │  얼굴 감지 + 품질 검사 + 표정 분석
│  (얼굴 감지)    │
└────────┬────────┘
         │ (통과 시)
         ▼
┌─────────────────┐
│  3. Embed       │  DeepFace로 512차원 벡터 추출
│  (임베딩 추출)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  4. Match       │  유사도 계산 → 스케일링 → Top-K 선정
│  (매칭)         │
└────────┬────────┘
         │
         ▼
   [결과 반환]
```

---

## 기술 스택

| 카테고리 | 기술 |
|---------|------|
| 프레임워크 | FastAPI |
| 얼굴 감지 | MediaPipe Face Landmarker |
| 얼굴 임베딩 | DeepFace (Facenet512) |
| 이미지 처리 | OpenCV, NumPy |
| 유사도 계산 | SciPy, NumPy |
| 데이터베이스 | Firebase Firestore (선택) |
| 검증 | Pydantic v2 |

---

## 데이터 흐름

### 요청 흐름
```
Client → WebSocket → analyze_request
  ↓
Pipeline.decode() → numpy.ndarray
  ↓
Pipeline.detect() → Expression, QualityResult
  ↓
Pipeline.embed() → vector(512)
  ↓
Pipeline.match() → [RankingResult × 3]
  ↓
WebSocket ← analyze_result
```

### 진행 상태 흐름
```
각 단계 완료 시 → Progress Callback → analyze_progress 메시지 전송
```

---

## 확장 포인트

1. **새 표정 추가**: `expression_map.py` 수정
2. **새 임베딩 모델**: `deepface_embedder.py` 수정
3. **새 스케일링 방식**: `score_scale.py`에 추가
4. **새 저장소**: `infra/` 하위에 모듈 추가
