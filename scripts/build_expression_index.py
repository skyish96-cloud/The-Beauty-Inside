import json
from pathlib import Path
import numpy as np

EMB = Path("data/celebs/embeddings")
EMB.mkdir(parents=True, exist_ok=True)

embed = np.load(EMB / "embed.npy")
N = int(embed.shape[0])

expr = {k: list(range(N)) for k in ["smile", "sad", "surprise", "neutral"]}
(EMB / "expr_index.json").write_text(json.dumps(expr, ensure_ascii=False), encoding="utf-8")

print("[OK] expr_index.json written. N =", N)
