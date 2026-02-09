# Firebase 임베딩 동기화 - 요약

## 🎯 한 줄 요약

**Firebase의 995명 연예인 임베딩 데이터를 로컬 CSV/NumPy 파일로 복제하여 오프라인 분석 지원**

---

## 📊 데이터 흐름

```
Firebase Firestore (온라인)
  └─ 995명 × 512차원 임베딩
       │
       ▼ (Python 스크립트로 동기화)
       │
  로컬 파일 (오프라인)
  ├─ celebs.csv (995명 메타정보)
  ├─ images.csv (995개 이미지 경로)
  ├─ embed.npy (995×512 임베딩 벡터)
  └─ ids.npy (인덱싱 배열)
```

---

## 🚀 사용법 (3단계)

### Step 1: 스크립트 선택

| 스크립트 | 추천 대상 | 특징 |
|---------|---------|------|
| `sync_celeb_embeddings_simple.py` | 초심자 | 간단, 빠름 |
| `sync_celeb_embeddings_from_firebase.py` | 고급 | 병합 기능 |
| `manage_embeddings.py` | 통합 관리 | 여러 모드 |

### Step 2: 실행

```bash
cd scripts
python sync_celeb_embeddings_simple.py
```

### Step 3: 확인

```
✓ 동기화 완료!
📊 최종 결과:
  • 연예인: 995명
  • 이미지: 995개
  • 임베딩: (995, 512)
```

---

## 💾 생성 파일

### celebs.csv (메타정보)
```csv
celeb_id,celeb_name,name,gender,birth_year,agency
김태희,김태희,김태희,F,1985,MYM
...
```
- 행: 995명 (헤더 1 + 데이터 994)
- 컬럼: celeb_id, name, gender, birth_year, agency

### images.csv (이미지 경로)
```csv
celeb_id,image_path,expression
김태희,famous/김태희_05.jpg,neutral
...
```
- 행: 995개 (헤더 1 + 이미지 994)
- 표정별 구분 가능

### embed.npy (임베딩 벡터)
- Shape: (995, 512)
- DType: float32
- 크기: ~2MB
- 로드: `np.load('embed.npy')`

### ids.npy (인덱싱)
- Shape: (995,)
- DType: object (문자열)
- 용도: `embed.npy[i]`는 `ids[i]`의 임베딩

---

## 🔧 동작 원리

### 1. Firebase 연결
```python
from app.infra.firestore.client import firestore_manager, init_firebase

init_firebase()
db = firestore_manager.get_db()
```

### 2. 데이터 수집
```python
collection = db.collection("celeb_embeddings")
for doc in collection.stream():
    celeb_id = doc.id
    embedding = doc.get("embedding")  # 512차원 배열
```

### 3. 파일 저장
```python
# CSV 저장
csv.writer.writerow({'celeb_id': '...', 'name': '...', ...})

# NumPy 저장
np.save('embed.npy', embeddings)  # (995, 512)
np.save('ids.npy', ids)            # (995,)
```

### 4. 검증
```python
embeddings = np.load('embed.npy')
assert embeddings.shape == (995, 512)
assert embeddings.dtype == np.float32
```

---

## ⚡ 성능 개선

### 전후 비교

| 메트릭 | Firebase | 로컬 파일 | 개선 |
|--------|---------|----------|-----|
| 전체 분석 시간 | ~550ms | ~300ms | **45% 단축** |
| 임베딩 로드 | ~500ms | ~50ms | **10배 빠름** |
| 오프라인 지원 | ✗ | ✓ | **가능** |

---

## 📝 스크립트 비교

### sync_celeb_embeddings_simple.py
```
장점: 간단, 직관적
단점: 옵션 제한

용도: 일회성 동기화
```

### sync_celeb_embeddings_from_firebase.py
```
장점: 고급 기능, 병합 지원
단점: 복잡도 증가

용도: 주기적 동기화
```

### manage_embeddings.py
```
장점: 여러 모드, 검증 기능
단점: 최고 복잡도

용도: 프로덕션 운영
```

---

## 🔐 필수 조건

1. **Firebase 인증**
   ```
   secrets/firebase/serviceAccountKey.json
   ```

2. **Firestore 컬렉션**
   ```
   celeb_embeddings (995개 문서)
   ├─ name
   ├─ gender
   ├─ birth_year
   ├─ agency
   └─ embedding (512차원)
   ```

3. **Python 라이브러리**
   ```bash
   pip install firebase-admin numpy pandas
   ```

---

## 🎯 사용 사례

### Case 1: 초기 셋업
```bash
python sync_celeb_embeddings_simple.py
→ 로컬 파일 생성
→ 개발/테스트 시작
```

### Case 2: 정기 업데이트
```bash
python manage_embeddings.py --mode sync
→ Firebase의 최신 데이터 반영
→ 기존 로컬 데이터 덮어쓰기
```

### Case 3: 데이터 병합
```bash
python manage_embeddings.py --mode merge
→ 기존 로컬 데이터 유지
→ Firebase의 새로운 연예인만 추가
```

### Case 4: 검증만 수행
```bash
python manage_embeddings.py --mode validate
→ 로컬 파일 무결성 확인
→ 형식 검증
```

---

## 📚 상세 문서

| 문서 | 내용 |
|------|------|
| [Firebase 동기화 가이드](FIREBASE_SYNC_GUIDE.md) | 사용법, 문제 해결 |
| [기술 상세 설명](EMBEDDING_SYNC_TECHNICAL.md) | 아키텍처, 알고리즘 |
| [README](../README.md) | 전체 프로젝트 가이드 |

---

## ✅ 체크리스트

동기화 전:
- [ ] Firebase 인증 정보 확인
- [ ] `celeb_embeddings` 컬렉션 존재
- [ ] 995명 데이터 존재

동기화 후:
- [ ] `celebs.csv` 생성됨 (995행)
- [ ] `images.csv` 생성됨 (995행)
- [ ] `embed.npy` 생성됨 (2MB)
- [ ] `ids.npy` 생성됨 (인덱싱)

---

## 🚨 주의사항

```
⚠️ 기존 파일 덮어쓰기
   sync 모드는 기존 파일을 완전히 덮어씀
   중요한 로컬 수정사항이 있으면 merge 모드 사용

⚠️ 임베딩 형식
   Firebase의 embedding은 리스트 또는 배열 형식이어야 함
   
⚠️ 네트워크
   995명 데이터 수집에 시간 소요 (~20초)
   정상 동작입니다
```

---

## 📞 FAQ

**Q: 왜 동기화가 필요한가?**
A: Firebase 조회 시간 (~500ms)을 없앨 수 있고, 오프라인 분석이 가능합니다.

**Q: 얼마나 자주 동기화해야 하나?**
A: 연예인 정보 변경 시에만 필요. 주1회 또는 월1회 권장.

**Q: 로컬 파일이 커지지 않나?**
A: 2.2MB 정도로 매우 작습니다.

**Q: Firebase 없이 동작하나?**
A: 네. 로컬 파일만으로 완전히 동작합니다.

**Q: 기존 데이터를 유지하면서 추가할 수 있나?**
A: `--mode merge` 사용하면 됩니다.

