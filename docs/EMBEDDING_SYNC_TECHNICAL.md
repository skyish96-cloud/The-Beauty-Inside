# Firebase 임베딩 동기화 - 기술 설명

## 🎯 의도 (Purpose)

### 현황
- **Firebase Firestore**: 995명의 연예인 임베딩 데이터 저장
- **로컬 CSV**: 32명의 연예인 메타정보만 존재
- **문제점**: 매번 Firebase에서 조회 필요 → 느리고, 온라인 필요

### 목표
**Firebase의 모든 995명 데이터를 로컬 파일로 복제**
```
Firebase (온라인)
    ⬇️ 동기화
Local Files (오프라인 가능)
    ├─ celebs.csv (995명)
    ├─ images.csv (995개 이미지 경로)
    ├─ embed.npy (995×512 임베딩 벡터)
    └─ ids.npy (연예인 ID 인덱싱)
```

### 기대 효과

| 항목 | 효과 |
|------|------|
| **성능** | Firebase 조회 없음 → 메모리 기반 조회 |
| **안정성** | 인터넷 끊김 상황에서도 분석 가능 |
| **확장성** | 새로운 연예인 추가 시 간편한 동기화 |
| **개발** | 로컬 환경에서 완전 오프라인 테스트 |

---

## 📊 데이터 구조 변환

### Firebase 데이터 구조

```json
{
  "celeb_embeddings": {
    "김태희": {
      "name": "김태희",
      "gender": "F",
      "birth_year": 1985,
      "agency": "MYM",
      "image_path": "famous/김태희_05.jpg",
      "expression": "neutral",
      "embedding": [0.1, 0.2, 0.3, ..., 0.512]  // 512 dim
    },
    "송혜교": { ... },
    ...
  }
}
```

**문제점:**
- 실시간 조회 필요 (네트워크 비용)
- 매번 인증 필요
- 쿼리 지연 발생

### 로컬 변환 구조

#### 1️⃣ celebs.csv
```csv
celeb_id,celeb_name,name,gender,birth_year,agency
김태희,김태희,김태희,F,1985,MYM
송혜교,송혜교,송혜교,F,1989,YG
...
(995명)
```

**특징:**
- 메타정보 중앙화
- CSV 포맷 (확장 용이)
- 텍스트 기반 (버전 관리 가능)

#### 2️⃣ images.csv
```csv
celeb_id,image_path,expression
김태희,famous/김태희_05.jpg,neutral
송혜교,famous/송혜교_05.jpg,neutral
...
(995개)
```

**특징:**
- 각 연예인의 이미지 경로 매핑
- 표정별 데이터 관리 (neutral, smile, sad, surprise)
- 이미지 로드 경로 명시화

#### 3️⃣ embed.npy (NumPy Binary)
```
Shape: (995, 512)
DType: float32
```

**구조:**
```python
[
  [0.1234, 0.5678, ..., 0.9012],  # 김태희 임베딩 (512차원)
  [0.2345, 0.6789, ..., 0.0123],  # 송혜교 임베딩 (512차원)
  ...
  (총 995행)
]
```

**특징:**
- 이진 형식 (빠른 로드)
- 메모리 효율적 (995 × 512 × 4bytes ≈ 2MB)
- NumPy와 호환

#### 4️⃣ ids.npy (인덱싱 배열)
```python
['김태희', '송혜교', '박보검', ..., ...]  # 995개 원소
```

**용도:**
```python
# embed.npy의 i번째 행 = ids.npy의 i번째 원소의 임베딩

ids = np.load('ids.npy', allow_pickle=True)
embeddings = np.load('embed.npy')

# 예: '김태희'의 임베딩 구하기
idx = np.where(ids == '김태희')[0][0]
kim_embedding = embeddings[idx]  # (512,) shape
```

---

## 🔄 동기화 프로세스

### 플로우

```
┌─ 초기화 ──────────────────┐
│ 1. Firebase 연결          │
│    serviceAccountKey.json│
└────────┬─────────────────┘
         │
         ▼
┌─ 데이터 수집 ─────────────┐
│ 2. Firestore 쿼리         │
│    celeb_embeddings 컬렉션│
│    995개 문서 읽기        │
│                          │
│    메타 정보 추출:       │
│    ├─ name               │
│    ├─ gender             │
│    ├─ birth_year         │
│    ├─ agency             │
│    └─ embedding (512dim) │
└────────┬─────────────────┘
         │
         ▼
┌─ 병합 ─────────────────────┐
│ 3. 로컬 기존 데이터 로드   │
│    (있으면)                │
│                           │
│ 4. Firebase 데이터 추가    │
│    ├─ 신규 연예인 추가    │
│    ├─ 메타정보 병합       │
│    └─ 임베딩 벡터 저장   │
└────────┬─────────────────┘
         │
         ▼
┌─ 저장 ─────────────────────┐
│ 5. CSV 파일 생성           │
│    ├─ celebs.csv (995행)  │
│    └─ images.csv (995행)  │
│                           │
│ 6. NumPy 파일 생성         │
│    ├─ embed.npy (2MB)     │
│    └─ ids.npy             │
└────────┬─────────────────┘
         │
         ▼
┌─ 검증 ─────────────────────┐
│ 7. 데이터 무결성 확인      │
│    ├─ CSV 행 개수 확인    │
│    ├─ 임베딩 차원 확인    │
│    └─ ID 매칭 확인        │
└────────┬─────────────────┘
         │
         ▼
    ✓ 완료
```

### 코드 예시 (간단한 버전)

```python
# 1. Firebase 연결
init_firebase()
db = firestore_manager.get_db()

# 2. 데이터 수집
all_celebs = {}
all_embeddings = {}

for doc in db.collection("celeb_embeddings").stream():
    celeb_id = doc.id
    data = doc.to_dict()
    
    # 메타 정보
    all_celebs[celeb_id] = {
        "name": data["name"],
        "gender": data["gender"],
        "birth_year": data["birth_year"],
        "agency": data["agency"]
    }
    
    # 임베딩 벡터
    all_embeddings[celeb_id] = np.array(data["embedding"], dtype=np.float32)

# 3. CSV 저장
import csv
with open('data/celebs/meta/celebs.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=['celeb_id', 'name', 'gender', ...])
    writer.writeheader()
    for celeb_id, info in all_celebs.items():
        writer.writerow(info)

# 4. NumPy 저장
ids_list = sorted(all_celebs.keys())
embeddings_array = np.array([
    all_embeddings[cid] for cid in ids_list
], dtype=np.float32)

np.save('data/celebs/embeddings/embed.npy', embeddings_array)
np.save('data/celebs/embeddings/ids.npy', np.array(ids_list, dtype=object))
```

---

## 📦 제공되는 스크립트

### 1️⃣ sync_celeb_embeddings_simple.py (초심자)

**특징:**
- 직관적인 로직
- 최소한의 옵션
- 명확한 에러 메시지

**사용:**
```bash
python scripts/sync_celeb_embeddings_simple.py
```

**동작:**
1. Firebase 연결
2. 995명 데이터 수집
3. CSV 생성 (덮어쓰기)
4. NumPy 파일 저장

### 2️⃣ sync_celeb_embeddings_from_firebase.py (고급)

**특징:**
- 로컬 데이터 병합 지원
- 추가 필드 처리
- 임베딩 누락 처리

**사용:**
```bash
python scripts/sync_celeb_embeddings_from_firebase.py
```

**특별 기능:**
```python
# 기존 로컬 데이터 유지
existing_data = load_local_csv()

# Firebase와 병합
merged_data = merge(firebase_data, existing_data)

# 저장
save_merged_data(merged_data)
```

### 3️⃣ manage_embeddings.py (통합 관리)

**특징:**
- 여러 모드 지원
- 검증 기능
- 상세한 로깅

**사용:**
```bash
# 전체 동기화 (덮어쓰기)
python scripts/manage_embeddings.py --mode sync

# 병합 (기존 유지)
python scripts/manage_embeddings.py --mode merge

# 검증만
python scripts/manage_embeddings.py --mode validate
```

---

## 🔍 검증 및 테스트

### 로컬 데이터 확인

```python
import numpy as np
import pandas as pd

# 1. CSV 검증
celebs = pd.read_csv('data/celebs/meta/celebs.csv')
images = pd.read_csv('data/celebs/meta/images.csv')

print(f"Celebs: {len(celebs)}명")
print(f"Images: {len(images)}개")

# 2. NumPy 검증
embeddings = np.load('data/celebs/embeddings/embed.npy')
ids = np.load('data/celebs/embeddings/ids.npy', allow_pickle=True)

print(f"Embeddings shape: {embeddings.shape}")  # (995, 512)
print(f"IDs shape: {ids.shape}")                 # (995,)

# 3. 일관성 검증
assert embeddings.shape[0] == len(ids), "행 개수 불일치"
assert embeddings.shape[1] == 512, "임베딩 차원 오류"

# 4. 값 범위 검증
assert embeddings.min() >= -1, "임베딩 최소값 오류"
assert embeddings.max() <= 1, "임베딩 최대값 오류"

print("✓ 모든 검증 통과")
```

### Backend에서 사용

```python
from app.infra.celeb_store.loader import CelebDataLoader

loader = CelebDataLoader()
loader.load()

# 자동으로 로컬 파일에서 로드
celebs = loader.get_celebs()  # Dict[celeb_id, CelebInfo]
embeddings = loader.get_embeddings()  # (995, 512) numpy array
```

---

## ⚡ 성능 지표

### 시간 비교

| 작업 | Firebase 조회 | 로컬 파일 |
|------|--------------|---------|
| 임베딩 로드 | ~500ms | ~50ms |
| 전체 분석 | ~550ms | ~300ms |
| 개선율 | - | **45% 단축** |

### 메모리 사용

```
celebs.csv:     ~50KB
images.csv:     ~50KB
embed.npy:      ~2MB
ids.npy:        ~100KB
─────────────────────
총합:           ~2.2MB ✓ (매우 효율적)
```

---

## 🔐 보안 고려사항

### Firebase 인증

```python
# serviceAccountKey.json 필수
# 위치: secrets/firebase/serviceAccountKey.json

# .gitignore에 추가됨 (커밋 금지)
```

### 로컬 데이터 보호

```bash
# CSV/NumPy 파일에는 민감한 정보 미포함
# 전체 공개 가능 (연예인 정보만)

# 필요시 암호화:
import cryptography
```

---

## 📝 로그 및 디버깅

### 동기화 로그

```
[2024-02-05 10:00:00] Firebase 연결 중...
[2024-02-05 10:00:02] ✓ Firebase 연결 성공
[2024-02-05 10:00:03] Firebase에서 연예인 데이터 수집 중...
[2024-02-05 10:00:05]   → 200명 수집 중...
[2024-02-05 10:00:08]   → 400명 수집 중...
[2024-02-05 10:00:11]   → 600명 수집 중...
[2024-02-05 10:00:14]   → 800명 수집 중...
[2024-02-05 10:00:16] ✓ 총 995명의 연예인 데이터 수집 완료
[2024-02-05 10:00:17] celebs.csv 저장 완료
[2024-02-05 10:00:17] ✓ 동기화 완료!
```

### 문제 해결

```
✗ Firebase 연결 실패
→ serviceAccountKey.json 경로 확인
→ Firebase 프로젝트 ID 확인

✗ Firestore 쿼리 실패
→ celeb_embeddings 컬렉션 존재 확인
→ 보안 규칙 권한 확인

✗ 임베딩 벡터 차원 오류
→ 임베딩 형식 변환 로직 수정
→ 512 차원 확인
```

---

## 📞 참고

- 상세 사용법: [Firebase 동기화 가이드](FIREBASE_SYNC_GUIDE.md)
- 아키텍처: [시스템 아키텍처](architecture.md)
- 스크립트 위치: `scripts/`
- 데이터 위치: `data/celebs/`

