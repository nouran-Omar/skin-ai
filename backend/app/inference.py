"""Model loading, prediction, Grad-CAM. If no trained checkpoint exists the service starts in DEMO mode
(deterministic pseudo-predictions) so the whole pipeline can be tested before training finishes."""
from __future__ import annotations
import base64, hashlib, json, threading
from collections.abc import Mapping
import cv2
import numpy as np
from ml.classes import DEMO_CLASSES
from ml.preprocessing import normalize_array, preprocess_image
from .config import META_PATH, MODEL_PATH


def to_b64_png(rgb: np.ndarray) -> str:
    ok, buf = cv2.imencode(".png", cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    return "data:image/png;base64," + base64.b64encode(buf.tobytes()).decode()


def overlay_cam(rgb: np.ndarray, cam: np.ndarray, alpha: float = 0.45) -> np.ndarray:
    cam = cv2.resize(cam, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_CUBIC).clip(0, 1)
    heat = cv2.cvtColor(cv2.applyColorMap((cam * 255).astype(np.uint8), cv2.COLORMAP_JET), cv2.COLOR_BGR2RGB)
    return cv2.addWeighted(rgb, 1 - alpha, heat, alpha, 0)


def _load_safetensors_cpu(path) -> tuple[dict, dict]:
    """Load safetensors as CPU tensors without touching CUDA.

    Hugging Face ZeroGPU patches `torch.cuda.is_available()` to True at startup,
    but no GPU is attached yet. `safetensors.torch.load_file(..., device="cuda")`
    allocates pinned CUDA memory and crashes with "No CUDA GPUs are available".
    """
    import torch
    from safetensors import safe_open

    state_dict: dict = {}
    with safe_open(str(path), framework="numpy") as handle:
        metadata = dict(handle.metadata() or {})
        for key in handle.keys():
            state_dict[key] = torch.from_numpy(np.array(handle.get_tensor(key), copy=True))
    return state_dict, metadata


class Predictor:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.demo = not MODEL_PATH.exists()
        self.temperature, self.test_f1 = 1.0, None
        if self.demo:
            self.arch, self.classes, self.img_size = "demo (no trained model)", DEMO_CLASSES, 300
            return
        import torch
        from ml.models import build_model, gradcam_layer
        self.torch = torch
        try:
            if MODEL_PATH.suffix == ".safetensors":
                state_dict, checkpoint_meta = _load_safetensors_cpu(MODEL_PATH)
                ckpt = {
                    "state_dict": state_dict,
                    "arch": checkpoint_meta.get("arch"),
                    "class_names": json.loads(checkpoint_meta.get("class_names", "[]")),
                    "img_size": int(checkpoint_meta.get("img_size", "0")),
                    "val_macro_f1": float(checkpoint_meta["val_macro_f1"]) if checkpoint_meta.get("val_macro_f1") else None,
                }
            else:
                ckpt = torch.load(MODEL_PATH, map_location="cpu", weights_only=True)
            if not isinstance(ckpt, Mapping):
                raise ValueError("checkpoint must contain a mapping")
            arch = ckpt.get("arch")
            classes = ckpt.get("class_names")
            img_size = ckpt.get("img_size")
            state_dict = ckpt.get("state_dict")
            self.test_f1 = ckpt.get("val_macro_f1")
            if not isinstance(classes, list) or not classes or not all(
                isinstance(name, str) and name for name in classes
            ):
                raise ValueError("checkpoint class_names must be a non-empty list of names")
            if len(set(classes)) != len(classes):
                raise ValueError("checkpoint class_names contains duplicates")
            if not isinstance(img_size, int) or isinstance(img_size, bool) or img_size < 64:
                raise ValueError("checkpoint img_size must be an integer of at least 64")
            if not isinstance(state_dict, Mapping):
                raise ValueError("checkpoint state_dict is missing or invalid")

            self.arch, self.classes, self.img_size = arch, classes, img_size
            self.model = build_model(self.arch, len(self.classes), pretrained=False).cpu().eval()
            self.model.load_state_dict(state_dict, strict=True)
            self.target_layer = gradcam_layer(self.model, self.arch)
            # Keep weights on CPU here. ZeroGPU only intercepts `.to("cuda")` at
            # module scope (see deploy/huggingface-space/app.py). A real GPU is
            # attached later inside `@spaces.GPU`.
            self.device = torch.device("cpu")
            if META_PATH.exists():
                meta = json.loads(META_PATH.read_text())
                temperature = float(meta.get("temperature", 1.0))
                if not np.isfinite(temperature) or temperature <= 0:
                    raise ValueError("model metadata temperature must be a finite positive number")
                self.temperature = temperature
                self.test_f1 = meta.get("test_macro_f1")
        except Exception as exc:
            raise RuntimeError(f"Unable to load trained checkpoint at {MODEL_PATH}: {exc}") from exc

    def info(self) -> dict:
        return dict(arch=self.arch, classes=len(self.classes), test_macro_f1=self.test_f1, temperature=round(self.temperature, 3))

    def predict(self, rgb: np.ndarray) -> dict:
        processed, details = preprocess_image(rgb, size=self.img_size)
        probs, cam = self._demo(processed) if self.demo else self._real(processed)
        return dict(processed=processed, details=details, probs=probs, cam=cam)

    # -- demo ---------------------------------------------------------------------------------
    def _demo(self, processed):
        seed = int(hashlib.md5(processed.tobytes()).hexdigest()[:8], 16)
        probs = np.random.default_rng(seed).dirichlet(np.ones(len(self.classes)) * 0.35)
        yy, xx = np.mgrid[0:32, 0:32]
        cam = np.exp(-(((xx - 16) ** 2 + (yy - 16) ** 2) / 90.0)).astype(np.float32)
        return probs, cam

    # -- real model ---------------------------------------------------------------------------
    def _real(self, processed):
        torch = self.torch
        store: dict = {}

        def fwd_hook(_m, _i, out):
            store["a"] = out
            out.register_hook(lambda g: store.__setitem__("g", g))

        with self.lock:                                   # hooks + backward are not re-entrant
            device = next(self.model.parameters()).device
            if torch.cuda.is_available() and device.type != "cuda":
                self.model.to("cuda")
                device = torch.device("cuda")
            self.device = device
            x = torch.from_numpy(normalize_array(processed)).unsqueeze(0).to(device)
            handle = self.target_layer.register_forward_hook(fwd_hook)
            try:
                self.model.zero_grad(set_to_none=True)
                with torch.enable_grad():
                    logits = self.model(x)
                    probs_t = torch.softmax(logits / self.temperature, 1)
                    logits[0, int(probs_t.argmax())].backward()
            finally:
                handle.remove()
            weights = store["g"].mean(dim=(2, 3), keepdim=True)
            cam = torch.relu((weights * store["a"]).sum(1)).squeeze(0).detach().cpu().numpy()
            probs = probs_t.detach().cpu().numpy()[0]
        cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
        return probs, cam.astype(np.float32)


predictor: Predictor | None = None

def get_predictor() -> Predictor:
    global predictor
    if predictor is None:
        predictor = Predictor()
    return predictor
