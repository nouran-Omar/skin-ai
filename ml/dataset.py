from __future__ import annotations

from collections import Counter
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from .config import MEAN, STD


def build_transforms(size: int, train: bool) -> transforms.Compose:
    if size < 1:
        raise ValueError("Image size must be a positive integer.")

    normalize = transforms.Normalize(MEAN, STD)
    if not train:
        return transforms.Compose(
            [transforms.Resize((size, size)), transforms.ToTensor(), normalize]
        )

    return transforms.Compose(
        [
            transforms.RandomResizedCrop(size, scale=(0.75, 1.0), ratio=(0.9, 1.1)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(),
            transforms.RandomRotation(180),
            transforms.ColorJitter(
                brightness=0.2, contrast=0.2, saturation=0.15, hue=0.02
            ),
            transforms.ToTensor(),
            normalize,
        ]
    )


def make_loaders(
    data_dir: str | Path, size: int, batch: int, workers: int = 4
) -> tuple[dict[str, DataLoader], list[str], list[int]]:
    if batch < 1:
        raise ValueError("Batch size must be a positive integer.")
    if workers < 0:
        raise ValueError("DataLoader workers cannot be negative.")

    root = Path(data_dir)
    split_dirs = {split: root / split for split in ("train", "val", "test")}
    missing = [str(path) for path in split_dirs.values() if not path.is_dir()]
    if missing:
        raise FileNotFoundError(
            "Expected ImageFolder directories for train, val, and test; missing: "
            + ", ".join(missing)
        )

    datasets_by_split = {
        split: datasets.ImageFolder(
            str(path), transform=build_transforms(size, split == "train")
        )
        for split, path in split_dirs.items()
    }
    classes = datasets_by_split["train"].classes
    if not classes:
        raise ValueError(f"No class folders containing images were found in {split_dirs['train']}.")
    for split, dataset in datasets_by_split.items():
        if dataset.class_to_idx != datasets_by_split["train"].class_to_idx:
            raise ValueError(
                f"Class folders in {split_dirs[split]} do not match the training split. "
                "Each split must use the same class names."
            )
        if not dataset.samples:
            raise ValueError(f"No supported images were found in {split_dirs[split]}.")

    counts = Counter(datasets_by_split["train"].targets)
    class_counts = [counts[index] for index in range(len(classes))]
    empty_classes = [name for name, count in zip(classes, class_counts) if count == 0]
    if empty_classes:
        raise ValueError(
            "The training split has no images for these classes: "
            + ", ".join(empty_classes)
        )

    pin_memory = torch.cuda.is_available()
    loaders = {
        split: DataLoader(
            dataset,
            batch_size=batch,
            shuffle=split == "train",
            num_workers=workers,
            pin_memory=pin_memory,
            # Keep every training example, including when the split is smaller than a batch.
            drop_last=False,
            persistent_workers=workers > 0,
        )
        for split, dataset in datasets_by_split.items()
    }
    return loaders, classes, class_counts
