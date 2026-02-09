# 📚 문서 인덱스

## 🚀 빠른 시작

### Firebase 임베딩 동기화 가이드

| 수준 | 문서 | 내용 |
|------|------|------|
| **초급** | [동기화 요약](EMBEDDING_SYNC_SUMMARY.md) | 한눈에 이해하기 |
| **중급** | [사용 가이드](FIREBASE_SYNC_GUIDE.md) | 단계별 사용법 |
| **고급** | [기술 설명](EMBEDDING_SYNC_TECHNICAL.md) | 아키텍처 및 알고리즘 |

---

## 📖 전체 문서 목록

### 프로젝트 개요
- **[overview.md](overview.md)** - 프로젝트 소개 및 목표

### 시스템 설계
- **[architecture.md](architecture.md)** - 시스템 아키텍처
- **[execution_flow.md](execution_flow.md)** - 요청-응답 흐름
- **[firestore_schema.md](firestore_schema.md)** - Firebase 스키마

### 분석 로직
- **[scoring_rules.md](scoring_rules.md)** - 점수 계산 규칙
- **[api_contract.md](api_contract.md)** - API 명세

### 데이터 관리
- **[FIREBASE_SYNC_GUIDE.md](FIREBASE_SYNC_GUIDE.md)** - Firebase 동기화 (사용 가이드)
- **[EMBEDDING_SYNC_TECHNICAL.md](EMBEDDING_SYNC_TECHNICAL.md)** - 임베딩 동기화 (기술)
- **[EMBEDDING_SYNC_SUMMARY.md](EMBEDDING_SYNC_SUMMARY.md)** - 임베딩 동기화 (요약)

### 정책 및 보안
- **[privacy.md](privacy.md)** - 개인정보 보호 정책
- **[error_codes.md](error_codes.md)** - 에러 코드 목록

---

## 🎯 시나리오별 읽을 문서

### 👤 새로운 개발자
1. [overview.md](overview.md) - 프로젝트 이해
2. [architecture.md](architecture.md) - 구조 파악
3. [EMBEDDING_SYNC_SUMMARY.md](EMBEDDING_SYNC_SUMMARY.md) - 데이터 동기화

### 🚀 배포 담당자
1. [execution_flow.md](execution_flow.md) - 실행 흐름
2. [firestore_schema.md](firestore_schema.md) - 데이터베이스 설정
3. [FIREBASE_SYNC_GUIDE.md](FIREBASE_SYNC_GUIDE.md) - 동기화 운영

### 🔧 데이터 엔지니어
1. [EMBEDDING_SYNC_TECHNICAL.md](EMBEDDING_SYNC_TECHNICAL.md) - 기술 상세
2. [firestore_schema.md](firestore_schema.md) - 스키마
3. [scoring_rules.md](scoring_rules.md) - 알고리즘

### 🐛 문제 해결
1. [error_codes.md](error_codes.md) - 에러 코드
2. [FIREBASE_SYNC_GUIDE.md](FIREBASE_SYNC_GUIDE.md#-문제-해결) - 문제 해결
3. [architecture.md](architecture.md) - 구조 분석

---

## 📊 Firebase 동기화 문서 구조

### 계층 1: 입문자
```
EMBEDDING_SYNC_SUMMARY.md
  ├─ 한 줄 요약
  ├─ 데이터 흐름
  ├─ 사용법 (3단계)
  └─ FAQ
```

### 계층 2: 실무자
```
FIREBASE_SYNC_GUIDE.md
  ├─ 개요
  ├─ 사용법
  ├─ 프로세스
  ├─ 검증 방법
  └─ 문제 해결
```

### 계층 3: 전문가
```
EMBEDDING_SYNC_TECHNICAL.md
  ├─ 의도 분석
  ├─ 데이터 구조
  ├─ 동기화 프로세스
  ├─ 성능 지표
  └─ 보안 고려
```

---

## 🔍 주요 개념

### 동기화 (Sync)
Firebase의 데이터를 로컬에 복제하는 과정
- **목표**: 오프라인 분석 지원, 성능 향상
- **대상**: 995명의 연예인 임베딩 (512차원)
- **결과**: CSV 파일 + NumPy 배열

### 임베딩 (Embedding)
연예인 얼굴을 512차원의 수치 벡터로 표현
- **생성**: DeepFace (FaceNet512) 모델
- **저장**: embed.npy (995×512 float32)
- **사용**: 코사인 유사도 계산으로 닮은꼴 찾기

### 메타데이터 (Metadata)
연예인의 기본 정보
- **구성**: 이름, 성별, 생년, 소속사 등
- **저장**: celebs.csv
- **사용**: 결과 표시 시 활용

---

## 💡 핵심 파일 위치

```
scripts/
├─ setup_check.py                      ← 검사 도구
├─ sync_celeb_embeddings_simple.py    ← 간단한 동기화
├─ sync_celeb_embeddings_from_firebase.py  ← 고급 동기화
└─ manage_embeddings.py                ← 통합 관리

data/celebs/
├─ meta/
│  ├─ celebs.csv      ← 메타정보
│  └─ images.csv      ← 이미지 경로
└─ embeddings/
   ├─ embed.npy       ← 임베딩 벡터
   └─ ids.npy         ← 인덱싱

docs/
├─ EMBEDDING_SYNC_SUMMARY.md        ← 요약 (입문)
├─ FIREBASE_SYNC_GUIDE.md          ← 가이드 (실무)
├─ EMBEDDING_SYNC_TECHNICAL.md     ← 기술 (전문)
└─ INDEX.md                        ← 이 파일
```

---

## 🎓 학습 로드맵

### Phase 1: 이해 (30분)
1. [EMBEDDING_SYNC_SUMMARY.md](EMBEDDING_SYNC_SUMMARY.md) 읽기
2. 데이터 흐름 다이어그램 파악
3. 스크립트 3개 비교

### Phase 2: 실행 (10분)
1. `scripts/setup_check.py` 실행
2. 조건 확인
3. 동기화 스크립트 선택

### Phase 3: 운영 (5분)
1. 동기화 실행
2. 로그 확인
3. 데이터 검증

### Phase 4: 심화 (1시간)
1. [FIREBASE_SYNC_GUIDE.md](FIREBASE_SYNC_GUIDE.md) 상세 읽기
2. [EMBEDDING_SYNC_TECHNICAL.md](EMBEDDING_SYNC_TECHNICAL.md) 기술 이해
3. 커스터마이징 검토

---

## 🚀 빠른 명령어

### 환경 확인
```bash
python scripts/setup_check.py
```

### 동기화 실행 (간단)
```bash
python scripts/sync_celeb_embeddings_simple.py
```

### 동기화 실행 (병합)
```bash
python scripts/manage_embeddings.py --mode merge
```

### 데이터 검증
```bash
python scripts/manage_embeddings.py --mode validate
```

---

## 📞 문의 및 지원

### 문제 해결
→ [FIREBASE_SYNC_GUIDE.md - 문제 해결](FIREBASE_SYNC_GUIDE.md#-문제-해결)

### 기술 지원
→ [EMBEDDING_SYNC_TECHNICAL.md - 디버깅](EMBEDDING_SYNC_TECHNICAL.md#-로그-및-디버깅)

### FAQ
→ [EMBEDDING_SYNC_SUMMARY.md - FAQ](EMBEDDING_SYNC_SUMMARY.md#-faq)

---

## 📊 문서 통계

| 카테고리 | 문서 수 | 페이지 |
|---------|--------|--------|
| 프로젝트 | 2 | overview, execution_flow |
| 아키텍처 | 2 | architecture, firestore_schema |
| 분석 | 2 | scoring_rules, api_contract |
| 동기화 | 3 | SUMMARY, GUIDE, TECHNICAL |
| 정책 | 2 | privacy, error_codes |
| **합계** | **11** | - |

---

## ✨ 개선 피드백

각 문서를 읽고 다음 사항을 참고하세요:

- ❓ 불명확한 부분 → [FIREBASE_SYNC_GUIDE.md](FIREBASE_SYNC_GUIDE.md) 참고
- 🔧 기술 깊이 필요 → [EMBEDDING_SYNC_TECHNICAL.md](EMBEDDING_SYNC_TECHNICAL.md) 참고
- 🚀 빠르게 시작 → [EMBEDDING_SYNC_SUMMARY.md](EMBEDDING_SYNC_SUMMARY.md) 참고
- 🐛 에러 발생 → [error_codes.md](error_codes.md) 참고

---

**마지막 업데이트**: 2024년 2월
**작성자**: The Beauty Inside 팀
