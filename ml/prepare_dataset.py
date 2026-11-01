"""Build leakage-free train/val/test splits and a preprocessed copy of the dataset.

Usage
  HAM10000 : python -m ml.prepare_dataset --source ham10000
             (expects data/raw/HAM10000_metadata.csv + images anywhere under data/raw/)
  Folders  : python -m ml.prepare_dataset --source folders
             (expects data/raw/<label>/*.jpg  e.g. eczema/, psoriasis/, mel/ ...)

Leakage control
  * Split is done on GROUPS, never on single images:
      - HAM10000: group = lesion_id (same lesion photographed several times stays in ONE split)
      - folders : group = perceptual dHash (exact / near-exact duplicates stay together)
  * StratifiedGroupKFold keeps class proportions in every split.
  * Preprocessing has no fitted statistics (nothing learnt from the data) -> cannot leak.
  * Augmentation is applied online and ONLY to the training split (see ml/dataset.py).
"""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import cv2
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.model_selection import StratifiedGroupKFold
from tqdm import tqdm
from .config import DATA_PROCESSED, DATA_RAW, IMG_SIZE, SEED, SPLITS_CSV
from .preprocessing import preprocess_image, read_image_rgb

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def dhash(path: Path, hash_size: int = 8) -> str:
    im = Image.open(path).convert("L").resize((hash_size + 1, hash_size), Image.LANCZOS)
    a = np.asarray(im, dtype=np.int16)
    bits = (a[:, 1:] > a[:, :-1]).flatten()
    return f"{int(''.join('1' if b else '0' for b in bits), 2):016x}"


def index_ham10000(raw: Path) -> pd.DataFrame:
    meta = pd.read_csv(next(raw.rglob("HAM10000_metadata.csv")))
    files = {p.stem: p for p in raw.rglob("*") if p.suffix.lower() in IMG_EXT}
    meta = meta[meta.image_id.isin(files)].copy()
    meta["path"] = meta.image_id.map(lambda i: str(files[i]))
    return meta.rename(columns={"dx": "label", "lesion_id": "group_id"})[["image_id", "path", "label", "group_id"]]


def index_folders(raw: Path) -> pd.DataFrame:
    rows = []
    for cls_dir in sorted(d for d in raw.iterdir() if d.is_dir()):
        for p in sorted(cls_dir.rglob("*")):
            if p.suffix.lower() in IMG_EXT:
                rows.append(dict(image_id=f"{cls_dir.name}_{p.stem}", path=str(p), label=cls_dir.name,
                                 group_id=dhash(p)))
    return pd.DataFrame(rows)


def make_splits(df: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    """~72% train / 14% val / 14% test, grouped + stratified."""
    df = df.reset_index(drop=True)
    df["split"] = "train"
    outer = StratifiedGroupKFold(n_splits=7, shuffle=True, random_state=seed)
    trainval_idx, test_idx = next(outer.split(df, df.label, df.group_id))
    df.loc[test_idx, "split"] = "test"
    tv = df.loc[trainval_idx]
    inner = StratifiedGroupKFold(n_splits=6, shuffle=True, random_state=seed)
    _, val_rel = next(inner.split(tv, tv.label, tv.group_id))
    df.loc[tv.index[val_rel], "split"] = "val"
    return df


def assert_no_leakage(df: pd.DataFrame) -> None:
    g = {s: set(df[df.split == s].group_id) for s in ("train", "val", "test")}
    for a, b in (("train", "val"), ("train", "test"), ("val", "test")):
        overlap = g[a] & g[b]
        assert not overlap, f"DATA LEAKAGE: {len(overlap)} groups shared between {a} and {b}"
    assert not set(df[df.split == "train"].path) & set(df[df.split != "train"].path)
    print("Leakage check passed: no lesion/group appears in more than one split.")


def _process(args):
    path, out_path, size = args
    out_path = Path(out_path)
    if out_path.exists():
        return True
    try:
        img, _ = preprocess_image(read_image_rgb(path), size=size)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out_path), cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 95])
        return True
    except Exception as exc:  # corrupt file: report, don't crash the whole run
        print(f"skip {path}: {exc}")
        return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["ham10000", "folders"], default="folders")
    ap.add_argument("--raw", type=Path, default=DATA_RAW)
    ap.add_argument("--out", type=Path, default=DATA_PROCESSED)
    ap.add_argument("--size", type=int, default=IMG_SIZE)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--min-per-class", type=int, default=30, help="drop classes with fewer images")
    a = ap.parse_args()

    df = index_ham10000(a.raw) if a.source == "ham10000" else index_folders(a.raw)
    counts = df.label.value_counts()
    df = df[df.label.isin(counts[counts >= a.min_per_class].index)]
    print("Images per class:\n", df.label.value_counts().to_string())

    df = make_splits(df)
    assert_no_leakage(df)
    print("\nSplit sizes:\n", pd.crosstab(df.label, df.split).to_string())

    df["out_path"] = [str(a.out / r.split / r.label / f"{r.image_id}.jpg") for r in df.itertuples()]
    SPLITS_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SPLITS_CSV, index=False)

    jobs = [(r.path, r.out_path, a.size) for r in df.itertuples()]
    with ProcessPoolExecutor(a.workers) as ex:
        ok = list(tqdm(ex.map(_process, jobs, chunksize=32), total=len(jobs), desc="Preprocessing"))
    print(f"Done: {sum(ok)}/{len(ok)} images -> {a.out}")


if __name__ == "__main__":
    main()
