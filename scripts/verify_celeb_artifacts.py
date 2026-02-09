import json, os
import numpy as np
import pandas as pd

ROOT = "data/celebs"
EMB = f"{ROOT}/embeddings"
META = f"{ROOT}/meta"

paths = {
    "embed": f"{EMB}/embed.npy",
    "ids": f"{EMB}/ids.npy",
    "expr": f"{EMB}/expr_index.json",
    "celebs": f"{META}/celebs.csv",
    "images": f"{META}/images.csv",
}

for k, p in paths.items():
    if not os.path.exists(p):
        raise SystemExit(f"[FAIL] missing: {k} -> {p}")
    if os.path.getsize(p) <= 0:
        raise SystemExit(f"[FAIL] 0-byte: {k} -> {p}")

embed = np.load(paths["embed"])
ids = np.load(paths["ids"], allow_pickle=False)

if embed.shape[0] != len(ids):
    raise SystemExit(f"[FAIL] len(ids) != embed.shape[0] : {len(ids)} vs {embed.shape[0]}")

celebs = pd.read_csv(paths["celebs"])

if "celeb_id" not in celebs.columns:
    raise SystemExit("[FAIL] celebs.csv must contain 'celeb_id' column")

if "name" not in celebs.columns:
    raise SystemExit("[FAIL] celebs.csv must contain 'name' column")
if (celebs["name"].astype(str).str.strip() == "").any():
    raise SystemExit("[FAIL] celebs.csv has empty 'name' values")

celeb_id_set = set(celebs["celeb_id"].astype(str).tolist())
missing = [x for x in ids.astype(str).tolist() if x not in celeb_id_set]
if missing:
    raise SystemExit(f"[FAIL] ids not in celebs.csv: sample={missing[:10]} (total {len(missing)})")

expr = json.load(open(paths["expr"], "r", encoding="utf-8"))
N = embed.shape[0]
for label, idxs in expr.items():
    for i in idxs:
        if not (0 <= int(i) < N):
            raise SystemExit(f"[FAIL] expr_index out of range: label={label}, idx={i}, N={N}")

print("[OK] artifacts validated")
print("N =", N, "D =", embed.shape[1])
