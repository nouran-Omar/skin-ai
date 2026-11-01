"""Final evaluation on the held-out TEST split + probability calibration (temperature scaling on VAL).

  python -m ml.evaluate
Outputs: reports/metrics.json, reports/confusion_matrix.png, reports/training_curves.png, models/meta.json
"""
from __future__ import annotations
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, classification_report,
                             confusion_matrix, precision_recall_fscore_support, roc_auc_score)
from .config import DATA_PROCESSED, MODELS_DIR, REPORTS_DIR
from .dataset import make_loaders
from .models import build_model


@torch.no_grad()
def collect_logits(model, loader, device):
    model.eval()
    logits, labels = [], []
    for x, y in loader:
        logits.append(model(x.to(device)).cpu()); labels.append(y)
    return torch.cat(logits), torch.cat(labels)


def fit_temperature(logits: torch.Tensor, labels: torch.Tensor) -> float:
    log_t = torch.zeros(1, requires_grad=True)
    opt = torch.optim.LBFGS([log_t], lr=0.1, max_iter=100)
    nll = nn.CrossEntropyLoss()

    def closure():
        opt.zero_grad()
        loss = nll(logits / log_t.exp(), labels)
        loss.backward()
        return loss
    opt.step(closure)
    return float(log_t.exp())


def expected_calibration_error(probs: np.ndarray, labels: np.ndarray, bins: int = 15) -> float:
    conf, pred = probs.max(1), probs.argmax(1)
    edges, ece = np.linspace(0, 1, bins + 1), 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            ece += m.mean() * abs((pred[m] == labels[m]).mean() - conf[m].mean())
    return float(ece)


def plot_confusion(cm, classes, path):
    cmn = cm / cm.sum(1, keepdims=True).clip(min=1)
    fig, ax = plt.subplots(figsize=(1.1 * len(classes) + 3, 1.0 * len(classes) + 2.5))
    im = ax.imshow(cmn, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(classes)), classes, rotation=45, ha="right"); ax.set_yticks(range(len(classes)), classes)
    for i in range(len(classes)):
        for j in range(len(classes)):
            ax.text(j, i, f"{cm[i, j]}\n{cmn[i, j]:.0%}", ha="center", va="center", fontsize=8,
                    color="white" if cmn[i, j] > 0.5 else "#16324F")
    ax.set_xlabel("Predicted"); ax.set_ylabel("True"); ax.set_title("Confusion matrix (test set)")
    fig.colorbar(im, ax=ax, fraction=0.046); fig.tight_layout(); fig.savefig(path, dpi=160); plt.close(fig)


def plot_history(path_json, path_png):
    if not path_json.exists():
        return
    h = json.loads(path_json.read_text())
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].plot([r["train_loss"] for r in h], label="train"); ax[0].plot([r["val_loss"] for r in h], label="val")
    ax[0].set_title("Loss"); ax[0].legend()
    ax[1].plot([r["train_f1"] for r in h], label="train"); ax[1].plot([r["val_f1"] for r in h], label="val")
    ax[1].set_title("Macro-F1"); ax[1].legend()
    fig.tight_layout(); fig.savefig(path_png, dpi=140); plt.close(fig)


def main() -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(MODELS_DIR / "best.pt", map_location=device, weights_only=False)
    classes, arch, size = ckpt["class_names"], ckpt["arch"], ckpt["img_size"]
    model = build_model(arch, len(classes), pretrained=False).to(device)
    model.load_state_dict(ckpt["state_dict"])
    loaders, _, _ = make_loaders(DATA_PROCESSED, size, 32, workers=2)

    val_logits, val_y = collect_logits(model, loaders["val"], device)
    temp = fit_temperature(val_logits, val_y)
    test_logits, test_y = collect_logits(model, loaders["test"], device)
    probs = torch.softmax(test_logits / temp, 1).numpy()
    y, pred = test_y.numpy(), probs.argmax(1)

    p, r, f1, _ = precision_recall_fscore_support(y, pred, average="macro", zero_division=0)
    try:
        auc = float(roc_auc_score(y, probs, multi_class="ovr", average="macro"))
    except ValueError:
        auc = None
    metrics = dict(
        accuracy=accuracy_score(y, pred), balanced_accuracy=balanced_accuracy_score(y, pred),
        macro_precision=p, macro_recall=r, macro_f1=f1, macro_auc_ovr=auc,
        ece_calibrated=expected_calibration_error(probs, y),
        ece_uncalibrated=expected_calibration_error(torch.softmax(test_logits, 1).numpy(), y),
        temperature=temp,
        per_class=classification_report(y, pred, target_names=classes, output_dict=True, zero_division=0))
    cm = confusion_matrix(y, pred)

    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2, default=float))
    plot_confusion(cm, classes, REPORTS_DIR / "confusion_matrix.png")
    plot_history(REPORTS_DIR / "history.json", REPORTS_DIR / "training_curves.png")
    (MODELS_DIR / "meta.json").write_text(json.dumps(dict(
        arch=arch, class_names=classes, img_size=size, temperature=temp,
        test_accuracy=metrics["accuracy"], test_macro_f1=f1), indent=2))

    print(classification_report(y, pred, target_names=classes, digits=3, zero_division=0))
    print(f"Accuracy {metrics['accuracy']:.4f} | Balanced acc {metrics['balanced_accuracy']:.4f} | "
          f"Macro-F1 {f1:.4f} | AUC {auc} | ECE {metrics['ece_uncalibrated']:.3f} -> {metrics['ece_calibrated']:.3f} "
          f"(T={temp:.2f})")
    print("Clinically important: check RECALL (sensitivity) of 'mel' and 'bcc' in the table above.")


if __name__ == "__main__":
    main()
