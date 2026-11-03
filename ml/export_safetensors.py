"""Convert a trusted SkinAI PyTorch checkpoint to a safe deployment artifact."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from safetensors.torch import save_file


def export_checkpoint(source: Path, destination: Path) -> None:
    # Checkpoints are pickle containers: only convert files produced and
    # controlled by this project. Never disable weights_only for user uploads.
    checkpoint = torch.load(source, map_location="cpu", weights_only=True)
    required = ("state_dict", "arch", "class_names", "img_size")
    missing = [key for key in required if key not in checkpoint]
    if missing:
        raise ValueError(f"Checkpoint is missing required fields: {', '.join(missing)}")

    tensors = {
        name: tensor.detach().cpu().contiguous()
        for name, tensor in checkpoint["state_dict"].items()
    }
    metadata = {
        "arch": str(checkpoint["arch"]),
        "class_names": json.dumps(checkpoint["class_names"]),
        "img_size": str(int(checkpoint["img_size"])),
    }
    if checkpoint.get("val_macro_f1") is not None:
        metadata["val_macro_f1"] = str(float(checkpoint["val_macro_f1"]))

    destination.parent.mkdir(parents=True, exist_ok=True)
    save_file(tensors, str(destination), metadata=metadata)
    print(f"Exported {len(tensors)} tensors to {destination}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Trusted .pt checkpoint")
    parser.add_argument("destination", type=Path, help="Output .safetensors file")
    args = parser.parse_args()
    export_checkpoint(args.source, args.destination)


if __name__ == "__main__":
    main()
