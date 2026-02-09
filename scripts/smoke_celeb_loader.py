import numpy as np

# 프로젝트 구조에 맞게 loader import 경로만 맞추면 됨
from backend.app.infra.celeb_store import loader

# loader.py에 있는 “실제 로딩 함수명”으로 맞춰야 함
# 예: load(), load_celeb_store(), load_store() 등
store = loader.load_celeb_store()  # <- 여기 이름이 다르면 loader.py 보고 바꾸기

# dict 반환 / 객체 반환 둘 다 대응
if isinstance(store, dict):
    emb = store.get("embeddings")
    ids = store.get("ids")
    names = store.get("names")
else:
    emb = getattr(store, "embeddings", None)
    ids = getattr(store, "ids", None)
    names = getattr(store, "names", None)

print("[OK] embeddings shape:", np.array(emb).shape)
print("[OK] ids len:", len(ids))
print("[OK] names len:", len(names) if names is not None else None)
print("sample:", ids[:3], (names[:3] if names is not None else None))
