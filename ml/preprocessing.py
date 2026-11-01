"""Single source of truth for image preprocessing.
The SAME function runs in dataset preparation AND at inference time -> no train/serve skew."""
from __future__ import annotations
import cv2
import numpy as np
from .config import IMG_SIZE, MEAN, STD


def read_image_rgb(path) -> np.ndarray:
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Cannot read image: {path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def color_constancy(img: np.ndarray, power: int = 6) -> np.ndarray:
    """Shades-of-Gray illuminant normalisation: removes camera / lighting colour cast."""
    x = img.astype(np.float32)
    rgb = np.power(np.mean(np.power(x, power), axis=(0, 1)), 1.0 / power)
    rgb = rgb / (np.sqrt(np.sum(rgb ** 2)) + 1e-8)
    gain = 1.0 / (rgb * np.sqrt(3) + 1e-8)
    return np.clip(x * gain, 0, 255).astype(np.uint8)


def remove_hair(img: np.ndarray) -> tuple[np.ndarray, float]:
    """DullRazor-style hair removal (black-hat morphology + inpainting). Returns image and hair coverage %."""
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
    _, mask = cv2.threshold(blackhat, 10, 255, cv2.THRESH_BINARY)
    mask = cv2.dilate(mask, np.ones((3, 3), np.uint8))
    coverage = float(mask.mean() / 255.0 * 100)
    if coverage < 0.2:
        return img, coverage
    return cv2.inpaint(img, mask, 1, cv2.INPAINT_TELEA), coverage


def letterbox(img: np.ndarray, size: int) -> np.ndarray:
    """Aspect-ratio preserving resize + pad to square (never crops the lesion)."""
    h, w = img.shape[:2]
    scale = size / max(h, w)
    interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC
    resized = cv2.resize(img, (max(1, round(w * scale)), max(1, round(h * scale))), interpolation=interp)
    rh, rw = resized.shape[:2]
    top, left = (size - rh) // 2, (size - rw) // 2
    fill = tuple(int(v) for v in resized.reshape(-1, 3).mean(0))
    return cv2.copyMakeBorder(resized, top, size - rh - top, left, size - rw - left,
                              cv2.BORDER_CONSTANT, value=fill)


def preprocess_image(img: np.ndarray, size: int = IMG_SIZE, hair: bool = True,
                     colour: bool = True) -> tuple[np.ndarray, dict]:
    """RGB uint8 -> (RGB uint8 size x size, details dict used in the API + PDF report)."""
    h, w = img.shape[:2]
    steps = [f"Aspect-preserving resize + pad to {size}x{size}"]
    out = letterbox(img, size)
    hair_pct = 0.0
    if hair:
        out, hair_pct = remove_hair(out)
        steps.append("Hair artefact removal (black-hat + inpainting)")
    if colour:
        out = color_constancy(out)
        steps.append("Colour constancy (Shades of Gray, p=6)")
    gray = cv2.cvtColor(out, cv2.COLOR_RGB2GRAY)
    details = {
        "original_size": f"{w}x{h}",
        "model_input_size": f"{size}x{size}",
        "steps": steps,
        "hair_coverage_pct": round(hair_pct, 2),
        "sharpness_score": round(float(cv2.Laplacian(gray, cv2.CV_64F).var()), 1),
        "mean_brightness": round(float(gray.mean()), 1),
        "normalisation": f"ImageNet mean={list(MEAN)} std={list(STD)}",
    }
    return out, details


def normalize_array(img: np.ndarray) -> np.ndarray:
    """RGB uint8 HxWx3 -> float32 CxHxW, ImageNet-normalised."""
    x = img.astype(np.float32) / 255.0
    x = (x - np.array(MEAN, dtype=np.float32)) / np.array(STD, dtype=np.float32)
    return np.ascontiguousarray(x.transpose(2, 0, 1))
