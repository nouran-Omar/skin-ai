"""Clinical metadata for every label the system can predict.
Adding a new disease = drop a folder with that label into data/raw/ and add an entry here
(unknown labels still work, they just fall back to a generic description)."""

CLASS_INFO = {
    "akiec": dict(name="Actinic keratosis / intraepithelial carcinoma", risk="premalignant",
                  desc="Rough, scaly patch caused by long-term sun damage. Can progress to squamous cell carcinoma."),
    "bcc": dict(name="Basal cell carcinoma", risk="malignant",
                desc="Most common skin cancer. Grows slowly and rarely spreads, but needs treatment."),
    "bkl": dict(name="Benign keratosis-like lesion", risk="benign",
                desc="Includes seborrheic keratosis and solar lentigo. Harmless waxy or pigmented growths."),
    "df": dict(name="Dermatofibroma", risk="benign",
               desc="Firm, harmless skin nodule, often after a minor injury or insect bite."),
    "mel": dict(name="Melanoma", risk="malignant",
                desc="Serious skin cancer arising from pigment cells. Early detection is critical for survival."),
    "nv": dict(name="Melanocytic nevus (mole)", risk="benign",
               desc="Common benign mole. Should be monitored for changes in size, shape or colour."),
    "vasc": dict(name="Vascular lesion", risk="vascular",
                 desc="Includes angiomas and angiokeratomas. Usually benign blood-vessel growths."),
    "eczema": dict(name="Eczema (atopic dermatitis)", risk="inflammatory",
                   desc="Chronic itchy, dry and inflamed skin that comes and goes in flares."),
    "psoriasis": dict(name="Psoriasis", risk="inflammatory",
                      desc="Autoimmune condition causing thick, silvery-scaled red plaques."),
}

DEMO_CLASSES = ["akiec", "bcc", "bkl", "df", "eczema", "mel", "nv", "psoriasis", "vasc"]


def info(label: str) -> dict:
    return CLASS_INFO.get(label, dict(name=label.replace("_", " ").title(), risk="unknown", desc=""))
