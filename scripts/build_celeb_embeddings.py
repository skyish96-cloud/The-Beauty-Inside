import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, default=30)
    ap.add_argument("--D", type=int, default=512)
    args = ap.parse_args()

    out_root = Path("data/celebs")
    out_emb = out_root / "embeddings"
    out_meta = out_root / "meta"
    out_emb.mkdir(parents=True, exist_ok=True)
    out_meta.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(42)
    embed = rng.normal(size=(args.N, args.D)).astype("float32")
    ids = np.array([f"id_{i:04d}" for i in range(args.N)], dtype=str)

    np.save(out_emb / "embed.npy", embed)
    np.save(out_emb / "ids.npy", ids)

    pd.DataFrame({"celeb_id": ids, "celeb_name": [f"celeb_{i:04d}" for i in range(args.N)]}) \
      .to_csv(out_meta / "celebs.csv", index=False, encoding="utf-8")

    pd.DataFrame(columns=["celeb_id","image_path","expression"]) \
      .to_csv(out_meta / "images.csv", index=False, encoding="utf-8")

    expr = {k: list(range(args.N)) for k in ["smile","sad","surprise","neutral"]}
    (out_emb / "expr_index.json").write_text(json.dumps(expr, ensure_ascii=False), encoding="utf-8")

    print(f"[OK] bootstrapped artifacts: N={args.N} D={args.D}")

if __name__ == "__main__":
    main()
