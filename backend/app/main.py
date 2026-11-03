from __future__ import annotations
import asyncio
import base64
import hashlib
import hmac
import io
import json, logging, os, re, secrets, time, uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Request, Response as FastAPIResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from ml.classes import info
from . import assistant, quiz
from . import records
from .config import (
    ALLOWED_ORIGINS,
    ANALYZE_RATE_LIMIT,
    ASSISTANT_RATE_LIMIT,
    AUTH_RATE_LIMIT,
    DISCLAIMER,
    LOW_CONFIDENCE_THRESHOLD,
    MAX_IMAGE_PIXELS,
    MAX_UPLOAD_MB,
    RETENTION_HOURS,
    STORAGE_DIR,
)
from .inference import get_predictor, overlay_cam, to_b64_png
from .report import build_pdf, build_acne_guide
from .schemas import AssistantIn, AuthIn, ProgressIn
from .security import rate_limit

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    records.initialize()
    purge_old()
    get_predictor()          # load the model once at startup
    cleanup_task = asyncio.create_task(_retention_worker())
    try:
        yield
    finally:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="SkinAI API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_methods=["*"], allow_headers=["*"], allow_credentials=True)
UUID_RE = re.compile(r"^[0-9a-f]{32}$")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
COOKIE_NAME = "skinai_session"
JWT_SECRET = os.getenv("SKINAI_JWT_SECRET")
if not JWT_SECRET:
    secret_path = STORAGE_DIR / ".jwt-secret"
    if os.getenv("SKINAI_ENV", "development").lower() in ("production", "prod"):
        raise RuntimeError("SKINAI_JWT_SECRET must be configured in production.")
    if secret_path.exists():
        JWT_SECRET = secret_path.read_text().strip()
    else:
        JWT_SECRET = secrets.token_urlsafe(48)
        secret_path.write_text(JWT_SECRET)
        try: secret_path.chmod(0o600)
        except OSError: pass
PBKDF2_ROUNDS = 600_000


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _jwt_encode(user_id: str) -> str:
    now = int(time.time())
    header = _b64(b'{"alg":"HS256","typ":"JWT"}')
    payload = _b64(json.dumps({"sub": user_id, "iat": now, "exp": now + 60 * 60 * 24 * 7}, separators=(",", ":")).encode())
    body = f"{header}.{payload}"
    sig = hmac.new(JWT_SECRET.encode(), body.encode(), hashlib.sha256).digest()
    return f"{body}.{_b64(sig)}"


def _jwt_decode(token: str) -> str | None:
    try:
        head, body, signature = token.split(".")
        if json.loads(base64.urlsafe_b64decode(head + "==")).get("alg") != "HS256": return None
        expected = _b64(hmac.new(JWT_SECRET.encode(), f"{head}.{body}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(expected, signature): return None
        claims = json.loads(base64.urlsafe_b64decode(body + "=="))
        return claims["sub"] if claims["exp"] > int(time.time()) else None
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None


def _current_user(request: Request) -> dict:
    user_id = _jwt_decode(request.cookies.get(COOKIE_NAME, ""))
    user = records.find_user(user_id) if user_id else None
    if not user: raise HTTPException(401, "Please sign in to continue.")
    return user


def _cookie_secure() -> bool:
    default = "true" if os.getenv("SKINAI_ENV", "development").lower() in ("production", "prod") else "false"
    return os.getenv("SKINAI_COOKIE_SECURE", default).lower() == "true"


def _session_cookie(response: FastAPIResponse, user_id: str):
    response.set_cookie(COOKIE_NAME, _jwt_encode(user_id), httponly=True,
        secure=_cookie_secure(), samesite="lax", max_age=60 * 60 * 24 * 7, path="/api")


def _password_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ROUNDS)
    return f"pbkdf2_sha256${PBKDF2_ROUNDS}${_b64(salt)}${_b64(digest)}"


def _password_valid(password: str, encoded: str) -> bool:
    try:
        scheme, rounds, salt, digest = encoded.split("$")
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.urlsafe_b64decode(salt + "=="), int(rounds))
        return scheme == "pbkdf2_sha256" and hmac.compare_digest(_b64(actual), digest)
    except (ValueError, TypeError): return False


@app.post("/api/auth/register")
def register(payload: AuthIn, response: FastAPIResponse, request: Request):
    rate_limit(request, "auth", AUTH_RATE_LIMIT)
    email = str(payload.email).strip().lower()
    password = payload.password
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or len(email) > 254:
        raise HTTPException(422, "Enter a valid email address.")
    if not isinstance(password, str) or not 12 <= len(password) <= 128:
        raise HTTPException(422, "Password must be between 12 and 128 characters.")
    user = records.create_user(email, _password_hash(password))
    if not user: raise HTTPException(409, "An account with that email already exists.")
    _session_cookie(response, user["id"])
    return user


@app.post("/api/auth/login")
def login(payload: AuthIn, response: FastAPIResponse, request: Request):
    rate_limit(request, "auth", AUTH_RATE_LIMIT)
    email = str(payload.email).strip().lower()
    password = payload.password
    user = records.find_user_by_email(email)
    if not user or not isinstance(password, str) or not _password_valid(password, user["password_hash"]):
        raise HTTPException(401, "Email or password is incorrect.")
    _session_cookie(response, user["id"])
    return {"id": user["id"], "email": user["email"], "created_at": user["created_at"]}


@app.get("/api/auth/me")
def me(request: Request): return _current_user(request)


@app.post("/api/auth/logout")
def logout(response: FastAPIResponse):
    response.delete_cookie(COOKIE_NAME, path="/api", httponly=True, samesite="lax", secure=_cookie_secure())
    return {"ok": True}


@app.delete("/api/auth/me")
def delete_account(request: Request, response: FastAPIResponse):
    user = _current_user(request)
    if not records.delete_user(user["id"]):
        raise HTTPException(404, "Account not found.")
    response.delete_cookie(COOKIE_NAME, path="/api", httponly=True, samesite="lax", secure=_cookie_secure())
    return {"ok": True}


@app.get("/api/history")
def history(request: Request): return records.list_analyses(_current_user(request)["id"])


@app.post("/api/history/{analysis_id}")
def save_history(analysis_id: str, request: Request):
    if not UUID_RE.match(analysis_id): raise HTTPException(400, "Invalid report id.")
    path = STORAGE_DIR / f"{analysis_id}.json"
    if not path.exists(): raise HTTPException(404, "Report not found or expired.")
    result = records.save_analysis(_current_user(request)["id"], json.loads(path.read_text()))
    if not result: raise HTTPException(409, "This analysis is already saved to another account.")
    return result


@app.delete("/api/history/{analysis_id}")
def remove_history(analysis_id: str, request: Request):
    if not UUID_RE.match(analysis_id): raise HTTPException(400, "Invalid report id.")
    if not records.delete_analysis(_current_user(request)["id"], analysis_id): raise HTTPException(404, "Saved analysis not found.")
    return {"ok": True}


@app.get("/api/progress")
def progress(request: Request, lesion_id: str | None = None): return records.list_progress(_current_user(request)["id"], lesion_id)


@app.post("/api/progress")
def add_progress(payload: ProgressIn, request: Request):
    user = _current_user(request)
    lesion = str(payload.lesion_id).strip()
    note = str(payload.note).strip()
    recorded_at = str(payload.recorded_at or datetime.now(timezone.utc).date().isoformat())
    try: datetime.strptime(recorded_at, "%Y-%m-%d")
    except ValueError: raise HTTPException(422, "Date must use YYYY-MM-DD format.")
    if not lesion or len(lesion) > 60: raise HTTPException(422, "Enter a lesion label of up to 60 characters.")
    if len(note) > 1000: raise HTTPException(422, "Progress note must be 1000 characters or fewer.")
    analysis_id = payload.analysis_id
    if analysis_id is not None and (not isinstance(analysis_id, str) or not UUID_RE.match(analysis_id)):
        raise HTTPException(422, "Analysis id is invalid.")
    try: return records.add_progress(user["id"], lesion, recorded_at, note, analysis_id)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc


@app.delete("/api/progress/{entry_id}")
def remove_progress(entry_id: str, request: Request):
    if not records.delete_progress(_current_user(request)["id"], entry_id): raise HTTPException(404, "Progress entry not found.")
    return {"ok": True}


@app.post("/api/assistant/chat")
def assistant_chat(payload: AssistantIn, request: Request):
    rate_limit(request, "assistant", ASSISTANT_RATE_LIMIT)
    question = str(payload.message).strip()
    if not question or len(question) > 1000: raise HTTPException(422, "Message must be between 1 and 1000 characters.")
    language = "ar" if re.search(r"[\u0600-\u06ff]", question) else ("ar" if payload.language == "ar" else "en")
    history = [
        {"role": turn.role, "content": turn.content.strip()}
        for turn in payload.history[-6:]
        if turn.content.strip()
    ]
    return assistant.reply(
        question,
        language,
        history=history,
        allow_generation=payload.allow_generation is True,
    )


@app.get("/api/assistant/guide/{topic}")
def assistant_guide(topic: str, language: str = "en"):
    if language not in ("en", "ar"):
        raise HTTPException(422, "Language must be en or ar.")
    guide = assistant.guide(topic, language)
    if guide is None:
        raise HTTPException(404, "Educational guide not found.")
    return guide


def purge_old() -> None:
    cutoff = time.time() - RETENTION_HOURS * 3600
    for f in STORAGE_DIR.glob("*.json"):
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink(missing_ok=True)
        except OSError:
            logger.warning("Could not purge expired report %s", f.name, exc_info=True)


async def _retention_worker() -> None:
    while True:
        await asyncio.sleep(60 * 60)
        purge_old()


@app.get("/api/health")
def health():
    p = get_predictor()
    return dict(status="ok", demo=p.demo, model=p.info())


@app.get("/api/quiz")
def get_quiz():
    return quiz.public_quiz()


@app.get("/api/reports/acne-guide")
def acne_guide(language: str = "en"):
    if language not in ("en", "ar"): raise HTTPException(422, "Language must be en or ar.")
    pdf = build_acne_guide(language)
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="skinai-acne-guide-{language}.pdf"'})


def predict_rgb(rgb: np.ndarray, mode: str = "full") -> dict:
    """Predict an RGB image; the Hugging Face Space wrapper replaces this with ZeroGPU."""
    return get_predictor().predict(rgb)


@app.post("/api/analyze")
async def analyze(request: Request, image: UploadFile = File(...), answers: str = Form("{}")):
    rate_limit(request, "analyze", ANALYZE_RATE_LIMIT)
    if image.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(415, "Upload a JPEG, PNG or WebP image.")
    max_upload_bytes = MAX_UPLOAD_MB * 1024 * 1024
    data = await image.read(max_upload_bytes + 1)
    if len(data) > max_upload_bytes:
        raise HTTPException(413, f"Image is larger than {MAX_UPLOAD_MB} MB.")
    try:
        with Image.open(io.BytesIO(data)) as decoded:
            width, height = decoded.size
            if width < 64 or height < 64:
                raise HTTPException(422, "Upload an image that is at least 64x64 pixels.")
            if width * height > MAX_IMAGE_PIXELS:
                raise HTTPException(413, "Image dimensions are too large to analyze safely.")
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, ValueError):
        raise HTTPException(422, "This file could not be read as a supported image.")
    try:
        bgr = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    except cv2.error:
        bgr = None
    if bgr is None or min(bgr.shape[:2]) < 64:
        raise HTTPException(422, "This file could not be read as an image of at least 64x64 pixels.")
    try:
        raw = json.loads(answers)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(422, "Answers must be a JSON object.")
    if not isinstance(raw, dict):
        raise HTTPException(422, "Answers must be a JSON object.")

    ans = quiz.clean_answers(raw)
    p = get_predictor()
    try:
        out = predict_rgb(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), "full")
    except Exception as exc:
        logger.exception("SkinAI inference failed")
        raise HTTPException(503, "Image analysis is temporarily unavailable. Please try again later.") from exc
    raw_probs = [float(x) for x in out["probs"]]
    if (
        not raw_probs
        or not np.isfinite(raw_probs).all()
        or any(probability < 0.0 or probability > 1.0 for probability in raw_probs)
        or not np.isclose(sum(raw_probs), 1.0, atol=1e-3)
        or len(raw_probs) != len(p.classes)
    ):
        logger.error("Predictor returned invalid class probabilities")
        raise HTTPException(503, "Image analysis is temporarily unavailable. Please try again later.")
    model_confidence = max(raw_probs, default=0.0)
    if not p.demo and model_confidence < LOW_CONFIDENCE_THRESHOLD:
        raise HTTPException(
            422,
            "The image could not be matched confidently to the supported skin-lesion classes. "
            "It may be unclear or outside the model's scope. Upload a clear close-up of one lesion, "
            "or consult a clinician.",
        )
    adj_probs, fired = quiz.apply_context(raw_probs, p.classes, ans)
    urgency = quiz.assess_urgency(adj_probs, p.classes, ans)

    preds = sorted(({**info(c), "label": c, "probability": r, "adjusted_probability": a}
                    for c, r, a in zip(p.classes, raw_probs, adj_probs)), key=lambda x: -x["adjusted_probability"])
    preds = [dict(label=x["label"], name=x["name"], risk=x["risk"], description=x["desc"],
                  probability=round(x["probability"], 4), adjusted_probability=round(x["adjusted_probability"], 4)) for x in preds]

    d, warnings = out["details"], []
    if p.demo: warnings.append("Demo mode: no trained model is loaded. Results are placeholders.")
    if model_confidence < 0.5:
        warnings.append(
            "Low confidence: the image may be unclear or outside the supported skin-lesion classes. "
            "Treat these results with extra caution."
        )
    if d["sharpness_score"] < 8:
        raise HTTPException(422, "The photo is too blurry to analyze. Retake it in focus and try again.")
    if d["sharpness_score"] < 25: warnings.append("The photo looks blurry. Retake it in focus for a more reliable result.")
    if d["mean_brightness"] < 40 or d["mean_brightness"] > 215: warnings.append("The photo is very dark or over-exposed.")
    if min(bgr.shape[:2]) < 200: warnings.append("Low resolution image. Fine detail may be lost.")
    if d["hair_coverage_pct"] > 8: warnings.append("Heavy hair coverage was detected and digitally removed; details may be affected.")
    if ans.get("skin_tone") in ("V", "VI"):
        warnings.append("Public skin-image datasets under-represent dark skin tones, so accuracy may be lower for your skin type. "
                        "Please rely on a clinician's assessment.")

    result = dict(
        id=uuid.uuid4().hex, created_at=datetime.now(timezone.utc).isoformat(), demo=p.demo, model=p.info(),
        predictions=preds, urgency=urgency, context_factors=fired, warnings=warnings, preprocessing=d,
        answers_summary=quiz.summarize(ans),
        images=dict(processed=to_b64_png(out["processed"]), gradcam=to_b64_png(overlay_cam(out["processed"], out["cam"]))),
        disclaimer=DISCLAIMER)
    (STORAGE_DIR / f"{result['id']}.json").write_text(json.dumps(result))
    purge_old()
    return result


@app.get("/api/report/{analysis_id}")
def report(analysis_id: str, language: str = "en"):
    if not UUID_RE.match(analysis_id):
        raise HTTPException(400, "Invalid report id.")
    if language not in ("en", "ar"):
        raise HTTPException(422, "Language must be en or ar.")
    f = STORAGE_DIR / f"{analysis_id}.json"
    if not f.exists():
        raise HTTPException(404, "Report not found or expired. Run the analysis again.")
    pdf = build_pdf(json.loads(f.read_text()), language)
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="skin-report-{analysis_id[:8]}-{language}.pdf"'})
