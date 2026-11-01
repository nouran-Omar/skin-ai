"""Clinical pre-assessment questionnaire + context fusion.

The questionnaire is served as DATA (GET /api/quiz) so the React UI renders it dynamically
(branching via `show_if`). Answers re-weight the model's probabilities with small, bounded,
literature-inspired priors (age, change over time, bleeding, family history ...) and drive the
rule-based urgency level.  These priors are heuristics -- NOT clinically validated -- and are
tempered by CONTEXT_STRENGTH. Raw model probabilities are always returned alongside.
"""
from __future__ import annotations
import math
from ml.classes import info
from .config import CONTEXT_STRENGTH

def _o(value, label, **kw): return dict(value=value, label=label, **kw)
YN = [_o("yes", "Yes"), _o("no", "No")]

QUIZ: list[dict] = [
    dict(id="age", type="number", section="About you", text="How old are you?", min=0, max=120, unit="years", required=True),
    dict(id="sex", type="single", section="About you", text="What is your sex at birth?", required=True,
         options=[_o("female", "Female"), _o("male", "Male"), _o("na", "Prefer not to say")]),
    dict(id="skin_tone", type="single", section="About you", text="How does your skin react to the sun?", required=True,
         help="This helps us judge how reliable the result is for your skin type.",
         options=[_o("I", "Always burns, never tans", hint="Very fair"), _o("II", "Burns easily, tans a little", hint="Fair"),
                  _o("III", "Sometimes burns, tans gradually", hint="Medium"), _o("IV", "Rarely burns, tans easily", hint="Olive"),
                  _o("V", "Very rarely burns, tans deeply", hint="Brown"), _o("VI", "Never burns", hint="Dark brown / black")]),
    dict(id="location", type="single", section="The spot", text="Where on the body is it?", required=True,
         options=[_o("head_neck", "Head or neck"), _o("trunk", "Chest, back or belly"), _o("arms", "Arm"), _o("hands", "Hand"),
                  _o("legs", "Leg"), _o("feet_soles", "Foot or sole"), _o("other", "Somewhere else")]),
    dict(id="duration", type="single", section="The spot", text="How long has it been there?", required=True,
         options=[_o("lt_2w", "Less than 2 weeks"), _o("w2_8", "2 to 8 weeks"), _o("m2_6", "2 to 6 months"),
                  _o("gt_6m", "More than 6 months"), _o("birth", "Since birth or childhood")]),
    dict(id="change", type="single", section="The spot", required=True,
         text="In the last 3 months, has it changed in size, shape or colour?",
         options=[_o("none", "No change"), _o("slow", "Changed slowly"), _o("rapid", "Changed quickly")]),
    dict(id="symptoms", type="multi", section="Symptoms", required=True, text="Which of these do you notice? Select all that apply.",
         options=[_o("itching", "Itching"), _o("pain", "Pain or tenderness"), _o("bleeding", "Bleeding"), _o("crusting", "Crusting or oozing"),
                  _o("scaling", "Scaling or flaking"), _o("dry_cracked", "Dry or cracked skin"), _o("none", "None of these", exclusive=True)]),
    dict(id="itch_severity", type="scale", section="Symptoms", required=True, min=0, max=10,
         text="How strong is the itching, from 0 (barely) to 10 (unbearable)?",
         show_if=dict(question="symptoms", includes="itching")),
    dict(id="non_healing", type="single", section="Symptoms", required=True, options=YN,
         text="Has the spot bled or stayed open for more than 4 weeks?", show_if=dict(question="symptoms", includes="bleeding")),
    dict(id="extent", type="single", section="Symptoms", required=True, text="How many areas of your body are affected?",
         options=[_o("one", "Just one spot"), _o("few", "A few areas"), _o("widespread", "Many areas")],
         show_if=dict(question="symptoms", includes_any=["itching", "scaling", "dry_cracked"])),
    dict(id="flares", type="single", section="Symptoms", required=True, options=YN,
         text="Does it come and go in flare-ups?", show_if=dict(question="extent", in_=["few", "widespread"])),
    dict(id="history", type="multi", section="Your history", required=True,
         text="Do any of these apply to you or your close family?",
         options=[_o("atopy", "Asthma, hay fever or food allergies"), _o("eczema_family", "Eczema in the family"),
                  _o("psoriasis_family", "Psoriasis in the family"), _o("none", "None of these", exclusive=True)]),
    dict(id="family_melanoma", type="single", section="Your history", required=True, text="Has a close relative had melanoma?",
         options=[_o("yes", "Yes"), _o("no", "No"), _o("unknown", "I don't know")]),
    dict(id="sunburn", type="single", section="Your history", required=True, text="How many blistering sunburns have you had in your life?",
         options=[_o("many", "5 or more"), _o("few", "1 to 4"), _o("none", "None")]),
    dict(id="prior_cancer", type="single", section="Your history", required=True, options=YN, text="Have you ever had a skin cancer before?"),
    dict(id="immuno", type="single", section="Your history", required=True, options=YN,
         text="Do you take medicine that weakens your immune system (for example after a transplant)?"),
]

def public_quiz() -> list[dict]:
    """JSON-safe copy for the frontend (renames `in_` -> `in`)."""
    out = []
    for q in QUIZ:
        q = dict(q)
        if "show_if" in q and "in_" in q["show_if"]:
            q["show_if"] = {("in" if k == "in_" else k): v for k, v in q["show_if"].items()}
        out.append(q)
    return out

# ---------------------------------------------------------------- visibility & validation
def _visible(q: dict, a: dict) -> bool:
    s = q.get("show_if")
    if not s:
        return True
    v = a.get(s["question"])
    if "equals" in s: return v == s["equals"]
    if "includes" in s: return isinstance(v, list) and s["includes"] in v
    if "includes_any" in s: return isinstance(v, list) and any(x in v for x in s["includes_any"])
    if "in_" in s: return v in s["in_"]
    return True

def clean_answers(raw: dict) -> dict:
    """Keep only valid answers to currently-visible questions."""
    out: dict = {}
    for q in QUIZ:
        if not _visible(q, out) or q["id"] not in raw:
            continue
        v, t = raw[q["id"]], q["type"]
        opts = {o["value"] for o in q.get("options", [])}
        if t == "single" and isinstance(v, str) and v in opts: out[q["id"]] = v
        elif t == "multi" and isinstance(v, list) and v and all(x in opts for x in v): out[q["id"]] = v
        elif t in ("number", "scale") and isinstance(v, (int, float)) and q["min"] <= v <= q["max"]: out[q["id"]] = v
    return out

def summarize(answers: dict) -> list[dict]:
    rows = []
    for q in QUIZ:
        if q["id"] not in answers:
            continue
        v, lab = answers[q["id"]], {o["value"]: o["label"] for o in q.get("options", [])}
        text = ", ".join(lab.get(x, x) for x in v) if isinstance(v, list) else lab.get(v, f"{v} {q.get('unit', '')}".strip())
        rows.append(dict(question=q["text"], answer=text))
    return rows

# ---------------------------------------------------------------- context rules
def _has(a, key, val): return isinstance(a.get(key), list) and val in a[key]

RULES = [
    ("Age 50 or older", lambda a: a.get("age", 0) >= 50, dict(mel=1.2, bcc=1.4, akiec=1.5, bkl=1.3, nv=0.85)),
    ("Age 25 or younger", lambda a: a.get("age", 99) <= 25, dict(nv=1.2, mel=0.8, bcc=0.6, akiec=0.5, eczema=1.2)),
    ("Rapid change in the last 3 months", lambda a: a.get("change") == "rapid", dict(mel=1.6, bcc=1.2, nv=0.6, bkl=0.8)),
    ("Slow change in the last 3 months", lambda a: a.get("change") == "slow", dict(mel=1.2, nv=0.85)),
    ("Bleeding or crusting", lambda a: _has(a, "symptoms", "bleeding") or _has(a, "symptoms", "crusting"),
     dict(mel=1.3, bcc=1.5, akiec=1.2, nv=0.7, bkl=0.8, df=0.8)),
    ("Non-healing for over 4 weeks", lambda a: a.get("non_healing") == "yes", dict(bcc=1.6, akiec=1.3, mel=1.2)),
    ("Close relative with melanoma", lambda a: a.get("family_melanoma") == "yes", dict(mel=1.3)),
    ("5+ blistering sunburns", lambda a: a.get("sunburn") == "many", dict(mel=1.2, bcc=1.3, akiec=1.4)),
    ("Previous skin cancer", lambda a: a.get("prior_cancer") == "yes", dict(mel=1.3, bcc=1.4, akiec=1.3)),
    ("Weakened immune system", lambda a: a.get("immuno") == "yes", dict(akiec=1.3, bcc=1.2, mel=1.1)),
    ("Present since birth or childhood", lambda a: a.get("duration") == "birth", dict(nv=1.4, mel=0.7, vasc=1.2)),
    ("Lesion on foot or sole", lambda a: a.get("location") == "feet_soles", dict(mel=1.2)),
    ("Scaling in several areas", lambda a: _has(a, "symptoms", "scaling") and a.get("extent") in ("few", "widespread"),
     dict(psoriasis=1.6, eczema=1.3)),
    ("Strong itch, dryness or allergy history",
     lambda a: a.get("itch_severity", 0) >= 7 or _has(a, "symptoms", "dry_cracked") or _has(a, "history", "atopy"),
     dict(eczema=1.6)),
    ("Comes and goes in flare-ups", lambda a: a.get("flares") == "yes", dict(eczema=1.2, psoriasis=1.2)),
    ("Psoriasis in the family", lambda a: _has(a, "history", "psoriasis_family"), dict(psoriasis=1.4)),
    ("Eczema in the family", lambda a: _has(a, "history", "eczema_family"), dict(eczema=1.3)),
]

def apply_context(probs: list[float], classes: list[str], answers: dict):
    """Returns (adjusted_probs, fired_rules)."""
    mult = {c: 1.0 for c in classes}
    fired = []
    for reason, cond, effects in RULES:
        if cond(answers):
            eff = {c: f for c, f in effects.items() if c in mult}
            if eff:
                for c, f in eff.items():
                    mult[c] *= f ** CONTEXT_STRENGTH
                fired.append(dict(reason=reason, effects=eff))
    adj = [p * min(2.5, max(0.5, mult[c])) for p, c in zip(probs, classes)]
    s = sum(adj) or 1.0
    return [p / s for p in adj], fired

def assess_urgency(probs: list[float], classes: list[str], answers: dict) -> dict:
    risky = sum(p for p, c in zip(probs, classes) if info(c)["risk"] in ("malignant", "premalignant"))
    mel = next((p for p, c in zip(probs, classes) if c == "mel"), 0.0)
    top_c = classes[max(range(len(probs)), key=probs.__getitem__)]
    red_flags = answers.get("change") == "rapid" or (answers.get("non_healing") == "yes") \
        or (_has(answers, "symptoms", "bleeding") and answers.get("change") in ("slow", "rapid"))
    if mel >= 0.2 or risky >= 0.5 or red_flags and risky >= 0.2:
        return dict(level="urgent", title="See a doctor soon", message="Features that need a professional check were found. "
                    "Book a dermatology appointment within the next 1-2 weeks, and sooner if the spot keeps changing.")
    if risky >= 0.2 or red_flags or info(top_c)["risk"] == "inflammatory" and answers.get("itch_severity", 0) >= 7:
        return dict(level="soon", title="Book a routine appointment", message="This result is not alarming, but a clinician "
                    "should confirm it. Book a visit in the next few weeks and keep photos to track changes.")
    return dict(level="routine", title="Low concern, keep watching", message="Nothing in this analysis suggests urgency. "
                "Re-check monthly and see a doctor if it grows, changes colour, bleeds or starts to hurt.")
