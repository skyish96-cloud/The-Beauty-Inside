# Overview - 프로젝트 개요

## 소개
**Beauty Inside**는 사용자의 얼굴 사진을 분석하여 닮은 연예인을 찾아주는 실시간 웹 서비스입니다.

---

## 주요 기능

### 1. 실시간 얼굴 분석
- 웹캠 캡처 → 즉시 분석
- WebSocket 기반 실시간 통신
- 평균 분석 시간: 1-2초

### 2. 표정 기반 매칭
- 4가지 표정 지원 (무표정, 웃음, 슬픔, 놀람)
- 같은 표정의 연예인 이미지와 매칭
- 더 정확한 비교 결과

### 3. AI 기반 유사도 측정
- MediaPipe: 얼굴 랜드마크 검출
- DeepFace: 얼굴 특징 벡터 추출
- 코사인 유사도 기반 매칭

### 4. Top-3 결과 제공
- Gold (1위): 가장 닮은 연예인
- Silver (2위): 두 번째로 닮은 연예인
- Bronze (3위): 세 번째로 닮은 연예인

---

## 사용 흐름

```
1. 웹사이트 접속
       ↓
2. 웹캠 활성화
       ↓
3. 표정 선택 (선택사항)
       ↓
4. 촬영 버튼 클릭
       ↓
5. 분석 진행 (로딩 화면)
       ↓
6. 결과 확인
       ↓
7. 공유 또는 재시도
```

---

## 기술 특징

### 프라이버시 우선
- ❌ 사용자 사진 서버 저장 안함
- ❌ 얼굴 데이터 클라우드 전송 안함
- ✅ 분석 후 즉시 데이터 삭제
- ✅ 브라우저 세션 종료 시 모든 데이터 삭제

### 실시간 처리
- WebSocket 양방향 통신
- 분석 진행 상태 실시간 업데이트
- 낮은 지연시간

### 품질 보장
- 이미지 품질 자동 검사
- 흐림/밝기/얼굴 크기 확인
- 명확한 에러 메시지

---

## 시스템 요구사항

### 서버
- Python 3.9+
- 4GB RAM 이상
- CUDA GPU (선택, 성능 향상)

### 클라이언트
- 모던 웹 브라우저 (Chrome, Firefox, Safari, Edge)
- 웹캠 접근 권한
- WebSocket 지원

---

## 디렉토리 구조

```
The_Beauty_Inside/
├── backend/           # 백엔드 서버
│   ├── app/          # 애플리케이션 코드
│   │   ├── api/      # API 엔드포인트
│   │   ├── core/     # 핵심 설정
│   │   ├── domain/   # 비즈니스 로직
│   │   ├── infra/    # 인프라 연동
│   │   └── schemas/  # 데이터 모델
│   └── tests/        # 테스트 코드
├── frontend/         # 프론트엔드
│   ├── public/       # 정적 파일
│   └── src/          # 소스 코드
├── data/             # 데이터 파일
│   ├── celebs/       # 연예인 데이터
│   └── cache/        # 캐시
├── docs/             # 문서
├── infra/            # 인프라 설정
└── scripts/          # 유틸리티 스크립트
```

---

## 빠른 시작

### 1. 환경 설정
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 서버 실행
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 접속
브라우저에서 `http://localhost:8000` 접속

---

## 관련 문서

- [API Contract](api_contract.md): WebSocket API 규격
- [Architecture](architecture.md): 시스템 아키텍처
- [Scoring Rules](scoring_rules.md): 점수 계산 규칙
- [Error Codes](error_codes.md): 에러 코드 정의
- [Firestore Schema](firestore_schema.md): 데이터베이스 구조
- [Privacy](privacy.md): 개인정보 처리 방침
