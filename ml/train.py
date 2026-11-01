"""Two-phase transfer learning:
  Phase 1  backbone frozen, train the new classifier head (fast, stable)
  Phase 2  unfreeze everything, fine-tune with a small LR + cosine schedule
Model selection is on VALIDATION macro-F1 (robust to class imbalance); the test set is never touched here.

  python -m ml.train --arch efficientnet_b3 --epochs-ft 25
"""
from __future__ import annotations
import argparse, json, random
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, f1_score
from tqdm import tqdm
from .config import DATA_PROCESSED, IMG_SIZE, MEAN, MODELS_DIR, REPORTS_DIR, SEED, STD
from .dataset import make_loaders
from .models import build_model, set_backbone_trainable


def seed_everything(seed: int) -> None:
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)


def run_epoch(model, loader, criterion, device, optimizer=None, scaler=None, use_amp=False, freeze_bn=False):
    train = optimizer is not None
    model.train(train)
    if train and freeze_bn:
        for m in model.modules():
            if isinstance(m, nn.BatchNorm2d):
                m.eval()
    loss_sum, preds, labels = 0.0, [], []
    with torch.set_grad_enabled(train):
        for x, y in tqdm(loader, leave=False, desc="train" if train else "val"):
            x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
            with torch.autocast(device_type=device.type, enabled=use_amp):
                out = model(x)
                loss = criterion(out, y)
            if train:
                optimizer.zero_grad(set_to_none=True)
                if scaler is not None and use_amp:
                    scaler.scale(loss).backward()
                    scaler.unscale_(optimizer)
                    nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    loss.backward()
                    nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    optimizer.step()
            loss_sum += loss.item() * x.size(0)
            preds.append(out.argmax(1).cpu()); labels.append(y.cpu())
    p, l = torch.cat(preds).numpy(), torch.cat(labels).numpy()
    return loss_sum / len(l), accuracy_score(l, p), f1_score(l, p, average="macro", zero_division=0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(DATA_PROCESSED))
    ap.add_argument("--arch", default="efficientnet_b3")
    ap.add_argument("--img-size", type=int, default=IMG_SIZE)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--epochs-head", type=int, default=3)
    ap.add_argument("--epochs-ft", type=int, default=25)
    ap.add_argument("--lr-head", type=float, default=1e-3)
    ap.add_argument("--lr-ft", type=float, default=1e-4)
    ap.add_argument("--patience", type=int, default=6)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()

    seed_everything(SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    use_amp = device.type == "cuda"
    loaders, classes, counts = make_loaders(a.data, a.img_size, a.batch, a.workers)
    print(f"device={device} classes={classes} train_counts={counts}")

    # sqrt-inverse-frequency weights: counter imbalance without exploding gradients on rare classes
    w = (np.sum(counts) / (len(counts) * np.array(counts))) ** 0.5
    criterion = nn.CrossEntropyLoss(weight=torch.tensor(w, dtype=torch.float32, device=device), label_smoothing=0.1)

    model = build_model(a.arch, len(classes)).to(device)
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)
    MODELS_DIR.mkdir(exist_ok=True); REPORTS_DIR.mkdir(exist_ok=True)
    best_f1, bad, history = -1.0, 0, []

    def fit(epochs, optimizer, scheduler, phase, freeze_bn, patience=None):
        nonlocal best_f1, bad
        for ep in range(1, epochs + 1):
            tr = run_epoch(model, loaders["train"], criterion, device, optimizer, scaler, use_amp, freeze_bn)
            va = run_epoch(model, loaders["val"], criterion, device, use_amp=use_amp)
            if scheduler: scheduler.step()
            history.append(dict(phase=phase, epoch=ep, train_loss=tr[0], train_acc=tr[1], train_f1=tr[2],
                                val_loss=va[0], val_acc=va[1], val_f1=va[2]))
            print(f"[{phase} {ep:02d}/{epochs}] train loss {tr[0]:.3f} acc {tr[1]:.3f} | "
                  f"val loss {va[0]:.3f} acc {va[1]:.3f} macroF1 {va[2]:.3f}")
            if va[2] > best_f1:
                best_f1, bad = va[2], 0
                torch.save(dict(state_dict=model.state_dict(), arch=a.arch, class_names=classes,
                                img_size=a.img_size, mean=MEAN, std=STD, val_macro_f1=best_f1),
                           MODELS_DIR / "best.pt")
                print(f"  ✓ saved best.pt (val macro-F1 {best_f1:.4f})")
            else:
                bad += 1
                if patience and bad >= patience:
                    print("  early stopping"); break

    # Phase 1: head only
    set_backbone_trainable(model, False)
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=a.lr_head, weight_decay=1e-4)
    fit(a.epochs_head, opt, None, "head", freeze_bn=True)

    # Phase 2: full fine-tune (differential LR: head learns 10x faster than the backbone)
    set_backbone_trainable(model, True)
    head_ids = {id(p) for n, p in model.named_parameters() if n.startswith(("classifier", "fc"))}
    groups = [dict(params=[p for p in model.parameters() if id(p) not in head_ids], lr=a.lr_ft),
              dict(params=[p for p in model.parameters() if id(p) in head_ids], lr=a.lr_ft * 10)]
    opt = torch.optim.AdamW(groups, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=a.epochs_ft, eta_min=1e-6)
    bad = 0
    fit(a.epochs_ft, opt, sched, "finetune", freeze_bn=False, patience=a.patience)

    (REPORTS_DIR / "history.json").write_text(json.dumps(history, indent=2))
    print(f"Training finished. Best validation macro-F1 = {best_f1:.4f}. Next: python -m ml.evaluate")


if __name__ == "__main__":
    main()
