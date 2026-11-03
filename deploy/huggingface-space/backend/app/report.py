"""Bilingual, printable A4 summaries and general acne-care handouts."""
from __future__ import annotations

import base64
import io
from pathlib import Path
from xml.sax.saxutils import escape

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

INK, BLUE, MINT = colors.HexColor("#16324F"), colors.HexColor("#2C62A2"), colors.HexColor("#1FB58A")
MUTED, LINE, WASH = colors.HexColor("#5B6B7C"), colors.HexColor("#D9E2EC"), colors.HexColor("#F2F6FA")
URGENCY = {"urgent": colors.HexColor("#C0392B"), "soon": colors.HexColor("#C98A0B"), "routine": colors.HexColor("#12926F")}
FONT_DIR = Path(__file__).with_name("fonts")
FONT_REGULAR, FONT_BOLD = "Helvetica", "Helvetica-Bold"

if (FONT_DIR / "Amiri-Regular.ttf").is_file() and (FONT_DIR / "Amiri-Bold.ttf").is_file():
    if "SkinAI-Amiri" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("SkinAI-Amiri", str(FONT_DIR / "Amiri-Regular.ttf")))
        pdfmetrics.registerFont(TTFont("SkinAI-Amiri-Bold", str(FONT_DIR / "Amiri-Bold.ttf")))
        pdfmetrics.registerFontFamily("SkinAI-Amiri", normal="SkinAI-Amiri", bold="SkinAI-Amiri-Bold")
    FONT_REGULAR, FONT_BOLD = "SkinAI-Amiri", "SkinAI-Amiri-Bold"


def _display(text: str, language: str) -> str:
    if language == "ar":
        return get_display(arabic_reshaper.reshape(text), base_dir="R")
    return text


def _paragraph(text: object, style: ParagraphStyle, language: str = "en") -> Paragraph:
    # Keep user-controlled strings as text, never as ReportLab markup.
    return Paragraph(_display(escape(str(text)), language), style)


def _styles(language: str) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    font = FONT_REGULAR if language == "ar" else "Helvetica"
    bold = FONT_BOLD if language == "ar" else "Helvetica-Bold"
    align = 2 if language == "ar" else 0
    return {
        "title": ParagraphStyle("SkinAI-title", parent=base["Title"], fontName=bold, fontSize=20, leading=26, textColor=INK, alignment=align, spaceAfter=2),
        "heading": ParagraphStyle("SkinAI-heading", parent=base["Heading2"], fontName=bold, fontSize=12, leading=17, textColor=BLUE, alignment=align, spaceBefore=12, spaceAfter=5),
        "body": ParagraphStyle("SkinAI-body", parent=base["BodyText"], fontName=font, fontSize=9.5, leading=14, textColor=INK, alignment=align),
        "small": ParagraphStyle("SkinAI-small", parent=base["BodyText"], fontName=font, fontSize=8, leading=11, textColor=MUTED, alignment=align),
        "header": ParagraphStyle("SkinAI-table-header", parent=base["BodyText"], fontName=bold, fontSize=8, leading=11, textColor=colors.white, alignment=align),
        "white": ParagraphStyle("SkinAI-white", parent=base["BodyText"], fontName=font, fontSize=9.5, leading=14, textColor=colors.white, alignment=align),
        "white_bold": ParagraphStyle("SkinAI-white-bold", parent=base["BodyText"], fontName=bold, fontSize=10, leading=14, textColor=colors.white, alignment=align),
    }


def _bar(p: float, w: float = 90, h: float = 8, color=BLUE) -> Drawing:
    d = Drawing(w, h)
    d.add(Rect(0, 0, w, h, fillColor=WASH, strokeColor=None))
    d.add(Rect(0, 0, max(1, w * p), h, fillColor=color, strokeColor=None))
    return d


def _img(data_uri: str, size: float) -> Image:
    return Image(io.BytesIO(base64.b64decode(data_uri.split(",", 1)[1])), width=size, height=size)


def _table(rows, widths, language: str, header: bool = True, zebra: bool = True):
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0, hAlign="RIGHT" if language == "ar" else "LEFT")
    st = [
        ("FONTNAME", (0, 0), (-1, -1), FONT_REGULAR if language == "ar" else "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9), ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
    ]
    if header:
        st += [("BACKGROUND", (0, 0), (-1, 0), INK), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
               ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD if language == "ar" else "Helvetica-Bold")]
    if zebra:
        st.append(("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1), [colors.white, WASH]))
    t.setStyle(TableStyle(st))
    return t


AR = {
    "Skin lesion analysis report": "تقرير معلوماتي عن آفة جلدية",
    "Generated": "تاريخ الإنشاء", "Model": "النموذج", "Most likely findings": "الاحتمالات التي رتّبها النموذج",
    "Condition": "الاحتمال", "Category": "الفئة", "Model score": "درجة النموذج",
    "Context-adjusted score": "بعد إضافة إجاباتك", "Images": "الصور",
    "Preprocessed input": "الصورة بعد المعالجة", "Grad-CAM attention map": "خريطة المناطق المؤثرة في نتيجة النموذج",
    "Clinical questionnaire": "إجابات الاستبيان", "Question": "السؤال", "Answer": "الإجابة",
    "Context factors applied to the scores": "العوامل السياقية المضافة إلى الدرجات",
    "Preprocessing & image quality": "معالجة الصورة وجودتها", "Original size": "الأبعاد الأصلية",
    "Model input": "أبعاد إدخال النموذج", "Hair coverage removed": "نسبة الشعر التي أزيلت",
    "Sharpness score": "حدة الصورة", "Mean brightness": "متوسط السطوع", "Normalisation": "التطبيع",
    "Pipeline": "خطوات المعالجة", "Probability calibration": "معايرة الدرجات",
    "Warnings": "تنبيهات", "Disclaimer": "تنويه", "Page": "صفحة",
    "Malignant": "خبيث", "Pre-malignant": "محتمل ما قبل سرطاني", "Benign": "حميد",
    "Inflammatory": "التهابي", "Vascular": "وعائي", "Unknown": "غير مصنف",
    "See a doctor soon": "يُنصح بطلب تقييم طبي قريباً",
    "Book a routine appointment": "احجز موعداً طبياً قريباً",
    "Low concern, keep watching": "لا تظهر مؤشرات استعجال، واستمر بالمراقبة",
    "Skin lesion analysis report disclaimer": "هذا ملخص تعليمي لدعم النقاش مع الطبيب، وليس تشخيصاً أو بديلاً عن الفحص الطبي.",
    "DEMO MODE - no trained model is installed. Values below are placeholders and carry no clinical meaning.": "وضع العرض: لا يوجد نموذج مدرّب؛ القيم أدناه تجريبية ولا تحمل معنى طبياً.",
    "This output is generated by an experimental AI system for educational and decision-support purposes only. It is not a diagnosis and does not replace examination by a qualified dermatologist. If a lesion is changing, bleeding or worrying you, seek medical care regardless of this result.": "هذا ناتج تجريبي لأغراض التثقيف ودعم النقاش فقط، وليس تشخيصاً ولا يغني عن فحص طبيب الجلدية. اطلب الرعاية الطبية إذا كانت الآفة تتغير أو تنزف أو تثير قلقك، بصرف النظر عن هذه النتيجة.",
    "Features that need a professional check were found. Book a dermatology appointment within the next 1-2 weeks, and sooner if the spot keeps changing.": "ظهرت سمات تستدعي تقييماً مختصاً. احجز موعداً لدى طبيب جلدية خلال أسبوع إلى أسبوعين، وبوقت أقرب إذا استمرت البقعة في التغير.",
    "This result is not alarming, but a clinician should confirm it. Book a visit in the next few weeks and keep photos to track changes.": "لا تشير النتيجة إلى حالة طارئة، لكن ينبغي أن يؤكدها مختص. احجز موعداً خلال الأسابيع القادمة واحتفظ بصور لمتابعة التغيرات.",
    "Nothing in this analysis suggests urgency. Re-check monthly and see a doctor if it grows, changes colour, bleeds or starts to hurt.": "لا تشير هذه النتيجة إلى استعجال. أعد التحقق شهرياً، وراجع الطبيب إذا كبرت البقعة أو تغير لونها أو نزفت أو بدأت تؤلمك.",
    "Rapid change in the last 3 months": "تغير سريع خلال الأشهر الثلاثة الماضية",
    "Slow change in the last 3 months": "تغير بطيء خلال الأشهر الثلاثة الماضية",
    "Bleeding or crusting": "نزيف أو تقشر",
    "Non-healing for over 4 weeks": "عدم الالتئام لأكثر من أربعة أسابيع",
    "Close relative with melanoma": "إصابة قريب من الدرجة الأولى بالميلانوما",
    "5+ blistering sunburns": "خمس حروق شمسية فقاعية أو أكثر",
    "Previous skin cancer": "إصابة سابقة بسرطان الجلد",
    "Weakened immune system": "ضعف جهاز المناعة",
    "Present since birth or childhood": "موجودة منذ الولادة أو الطفولة",
    "Lesion on foot or sole": "الآفة في القدم أو باطنها",
    "Scaling in several areas": "تقشر في عدة مناطق",
    "Strong itch, dryness or allergy history": "حكة شديدة أو جفاف أو تاريخ من الحساسية",
    "Comes and goes in flare-ups": "تظهر الأعراض وتختفي على شكل نوبات",
    "Psoriasis in the family": "وجود الصدفية في العائلة",
    "Eczema in the family": "وجود الإكزيما في العائلة",
    "Low confidence: the image may be unclear or outside the supported skin-lesion classes. Treat these results with extra caution.": "ثقة منخفضة: قد تكون الصورة غير واضحة أو خارج فئات آفات الجلد التي يدعمها النموذج. تعامل مع النتيجة بحذر شديد.",
    "The photo looks blurry. Retake it in focus for a more reliable result.": "تبدو الصورة غير واضحة. أعد التقاطها بتركيز أفضل للحصول على نتيجة أوثق.",
    "The photo is very dark or over-exposed.": "الصورة مظلمة جداً أو شديدة التعرض للضوء.",
    "Low resolution image. Fine detail may be lost.": "دقة الصورة منخفضة وقد لا تظهر التفاصيل الدقيقة.",
    "Heavy hair coverage was detected and digitally removed; details may be affected.": "اكتُشفت تغطية كثيفة بالشعر وأزيلت رقمياً؛ قد تتأثر بعض التفاصيل.",
    "Public skin-image datasets under-represent dark skin tones, so accuracy may be lower for your skin type. Please rely on a clinician's assessment.": "تمثيل درجات البشرة الداكنة محدود في مجموعات الصور العامة؛ لذلك قد تقل الدقة لهذا النوع من البشرة. اعتمد على تقييم الطبيب.",
    "How old are you?": "كم عمرك؟", "What is your sex at birth?": "ما الجنس المسجل عند الولادة؟",
    "How does your skin react to the sun?": "كيف تتفاعل بشرتك مع الشمس؟", "Where on the body is it?": "أين تقع البقعة؟",
    "How long has it been there?": "منذ متى ظهرت؟", "In the last 3 months, has it changed in size, shape or colour?": "هل تغير حجمها أو شكلها أو لونها خلال الأشهر الثلاثة الماضية؟",
    "Which of these do you notice? Select all that apply.": "ما الأعراض التي تلاحظها؟ اختر كل ما ينطبق.",
    "How strong is the itching, from 0 (barely) to 10 (unbearable)?": "ما شدة الحكة من 0 (خفيفة جداً) إلى 10 (لا تُحتمل)؟",
    "Has the spot bled or stayed open for more than 4 weeks?": "هل نزفت البقعة أو بقيت مفتوحة لأكثر من أربعة أسابيع؟",
    "How many areas of your body are affected?": "كم منطقة من الجسم متأثرة؟", "Does it come and go in flare-ups?": "هل تظهر الأعراض وتختفي على شكل نوبات؟",
    "Do any of these apply to you or your close family?": "هل ينطبق أي مما يلي عليك أو على عائلتك المقربة؟",
    "Has a close relative had melanoma?": "هل أُصيب أحد أقاربك المقربين بالميلانوما؟",
    "How many blistering sunburns have you had in your life?": "كم مرة تعرضت لحروق شمسية سببت فقاعات؟",
    "Have you ever had a skin cancer before?": "هل أُصبت بسرطان الجلد من قبل؟",
    "Do you take medicine that weakens your immune system (for example after a transplant)?": "هل تتناول دواءً يضعف جهاز المناعة، مثل أدوية ما بعد زراعة الأعضاء؟",
    "Female": "أنثى", "Male": "ذكر", "Prefer not to say": "أفضل عدم الإجابة",
    "Always burns, never tans": "تحترق دائماً ولا تسمر أبداً", "Burns easily, tans a little": "تحترق بسهولة وتسمر قليلاً",
    "Sometimes burns, tans gradually": "تحترق أحياناً وتسمر تدريجياً", "Rarely burns, tans easily": "نادراً ما تحترق وتسمر بسهولة",
    "Very rarely burns, tans deeply": "نادراً جداً ما تحترق وتسمر بعمق", "Never burns": "لا تحترق أبداً",
    "Head or neck": "الرأس أو الرقبة", "Chest, back or belly": "الصدر أو الظهر أو البطن", "Arm": "الذراع", "Hand": "اليد",
    "Leg": "الساق", "Foot or sole": "القدم أو باطنها", "Somewhere else": "مكان آخر",
    "Less than 2 weeks": "أقل من أسبوعين", "2 to 8 weeks": "من أسبوعين إلى 8 أسابيع", "2 to 6 months": "من شهرين إلى 6 أشهر",
    "More than 6 months": "أكثر من 6 أشهر", "Since birth or childhood": "منذ الولادة أو الطفولة",
    "No change": "لم تتغير", "Changed slowly": "تغيرت ببطء", "Changed quickly": "تغيرت بسرعة",
    "Itching": "حكة", "Pain or tenderness": "ألم أو حساسية عند اللمس", "Bleeding": "نزيف", "Crusting or oozing": "قشور أو إفرازات",
    "Scaling or flaking": "تقشر", "Dry or cracked skin": "جفاف أو تشقق", "None of these": "لا شيء مما سبق",
    "Yes": "نعم", "No": "لا", "Just one spot": "بقعة واحدة فقط", "A few areas": "عدة مناطق", "Many areas": "مناطق كثيرة",
    "Asthma, hay fever or food allergies": "الربو أو حمى القش أو حساسية الطعام", "Eczema in the family": "إكزيما في العائلة",
    "Psoriasis in the family": "صدفية في العائلة", "I don't know": "لا أعلم", "5 or more": "5 مرات أو أكثر", "1 to 4": "من مرة إلى 4 مرات",
}

CLASS_AR = {
    "Actinic keratosis / intraepithelial carcinoma": "التقرّن السفعي / سرطان داخل الظهارة",
    "Basal cell carcinoma": "سرطان الخلايا القاعدية", "Benign keratosis-like lesion": "آفة شبيهة بالتقرّن الحميد",
    "Dermatofibroma": "ورم ليفي جلدي", "Melanoma": "الميلانوما",
    "Melanocytic nevus (mole)": "وحمة ميلانينية (شامة)", "Vascular lesion": "آفة وعائية",
    "Eczema (atopic dermatitis)": "الإكزيما (التهاب الجلد التأتبي)", "Psoriasis": "الصدفية",
    "Rough, scaly patch caused by long-term sun damage. Can progress to squamous cell carcinoma.": "بقعة خشنة متقشرة قد تنتج عن التعرض الطويل للشمس، وقد تتطور إلى سرطان الخلايا الحرشفية.",
    "Most common skin cancer. Grows slowly and rarely spreads, but needs treatment.": "أشيع أنواع سرطان الجلد. ينمو ببطء ونادراً ما ينتشر، لكنه يحتاج إلى تقييم وعلاج طبي.",
    "Includes seborrheic keratosis and solar lentigo. Harmless waxy or pigmented growths.": "تشمل التقرّن الدهني والنمش الشمسي؛ وهي زوائد مصطبغة أو شمعية حميدة عادةً.",
    "Firm, harmless skin nodule, often after a minor injury or insect bite.": "عقدة جلدية متماسكة وحميدة غالباً، وقد تظهر بعد إصابة بسيطة أو لدغة حشرة.",
    "Serious skin cancer arising from pigment cells. Early detection is critical for survival.": "سرطان جلدي خطير ينشأ من الخلايا الصبغية. لا يمكن لهذا التقرير تأكيده أو استبعاده؛ اطلب تقييماً طبياً.",
    "Common benign mole. Should be monitored for changes in size, shape or colour.": "شامة حميدة شائعة؛ راقب أي تغير في الحجم أو الشكل أو اللون واطلب تقييماً طبياً عند حدوثه.",
    "Includes angiomas and angiokeratomas. Usually benign blood-vessel growths.": "تشمل أوراماً وعائية، وتكون غالباً زوائد حميدة للأوعية الدموية.",
    "Chronic itchy, dry and inflamed skin that comes and goes in flares.": "حالة مزمنة تسبب الحكة والجفاف والالتهاب وقد تظهر على شكل نوبات.",
    "Autoimmune condition causing thick, silvery-scaled red plaques.": "حالة مناعية قد تسبب لويحات حمراء سميكة مغطاة بقشور فضية.",
}

RISK_AR = {
    "malignant": "خبيث", "premalignant": "محتمل ما قبل سرطاني", "benign": "حميد",
    "inflammatory": "التهابي", "vascular": "وعائي", "unknown": "غير مصنف",
}


def _tr(text: str, language: str) -> str:
    if language != "ar":
        return text
    if text.endswith(" years") and text[:-6].isdigit():
        return f"{text[:-6]} سنة"
    return CLASS_AR.get(text, AR.get(text, text))


def _footer(canvas, doc):
    canvas.saveState()
    lang = doc.language
    font = FONT_REGULAR if lang == "ar" else "Helvetica"
    canvas.setFont(font, 7.5)
    canvas.setFillColor(MUTED)
    text = f"SkinAI | {doc.report_id} | " + ("ليس تشخيصاً طبياً" if lang == "ar" else "Not a medical diagnosis")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, _display(text, lang))
    canvas.drawString(18 * mm, 10 * mm, _display(f"{_tr('Page', lang)} {doc.page}", lang))
    canvas.setStrokeColor(LINE)
    canvas.line(18 * mm, 14 * mm, A4[0] - 18 * mm, 14 * mm)
    canvas.restoreState()


def build_pdf(r: dict, language: str = "en") -> bytes:
    if language not in ("en", "ar"):
        raise ValueError("language must be 'en' or 'ar'")
    styles = _styles(language)
    p = lambda text, style="body": _paragraph(text, styles[style], language)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm,
                            bottomMargin=20 * mm, title=_tr("Skin lesion analysis report", language), author="SkinAI")
    doc.report_id, doc.language = r["id"][:8].upper(), language
    w = A4[0] - 36 * mm
    sections: list = [p(_tr("Skin lesion analysis report", language), "title"),
                      p(f"{_tr('Generated', language)} {r['created_at'][:19].replace('T', ' ')} UTC | {_tr('Model', language)}: {r['model']['arch']}", "small"),
                      Spacer(1, 8)]
    if r["demo"]:
        sections += [p(_tr("DEMO MODE - no trained model is installed. Values below are placeholders and carry no clinical meaning.", language)), Spacer(1, 6)]

    urgency = r["urgency"]
    urgency_color = URGENCY.get(urgency.get("level"), URGENCY["routine"])
    urgency_title = p(_tr(urgency["title"], language), "white_bold")
    urgency_message = p(_tr(urgency["message"], language), "white")
    box = Table([[urgency_title], [urgency_message]], colWidths=[w], hAlign="RIGHT" if language == "ar" else "LEFT")
    box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), urgency_color), ("LEFTPADDING", (0, 0), (-1, -1), 10),
                             ("RIGHTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 6),
                             ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    sections += [box, p(_tr("Most likely findings", language), "heading")]

    headers = ["Condition", "Category", "Model score", "Context-adjusted score", ""]
    rows = [[p(_tr(x, language), "header") if x else "" for x in headers]
            for _ in [0]]
    for item in r["predictions"][:5]:
        risk = RISK_AR.get(item["risk"], "غير مصنف") if language == "ar" else item["risk"].replace("_", " ").title()
        bar_width = w * (0.17 if language == "ar" else 0.14)
        row = [p(_tr(item["name"], language), "small"), p(risk, "small"), p(f"{item['probability'] * 100:.1f}%", "small"),
               p(f"{item['adjusted_probability'] * 100:.1f}%", "small"), _bar(item["adjusted_probability"], w=bar_width)]
        rows.append(list(reversed(row)) if language == "ar" else row)
    if language == "ar":
        rows[0] = list(reversed(rows[0]))
    sections.append(_table(rows, [w * .31, w * .15, w * .15, w * .21, w * .18], language))
    top = r["predictions"][0]
    sections += [Spacer(1, 5), p(f"{_tr(top['name'], language)}. {_tr(top['description'], language)}")]

    sections.append(p(_tr("Images", language), "heading"))
    side = (w - 10 * mm) / 2
    captions = [p(_tr("Preprocessed input", language), "small"), p(_tr("Grad-CAM attention map", language), "small")]
    if language == "ar":
        image_cells = [_img(r["images"]["gradcam"], side), _img(r["images"]["processed"], side)]
        captions.reverse()
    else:
        image_cells = [_img(r["images"]["processed"], side), _img(r["images"]["gradcam"], side)]
    sections.append(KeepTogether([Table([image_cells, captions], colWidths=[side + 5 * mm] * 2)]))

    sections.append(p(_tr("Clinical questionnaire", language), "heading"))
    if r["answers_summary"]:
        qrows = [[p(_tr("Question", language), "header"), p(_tr("Answer", language), "header")]]
        qrows += [[p(_tr(item["question"], language), "small"), p(_tr(item["answer"], language), "small")] for item in r["answers_summary"]]
        if language == "ar":
            qrows = [list(reversed(row)) for row in qrows]
        sections.append(_table(qrows, [w * .62, w * .38] if language == "en" else [w * .38, w * .62], language))

    if r["context_factors"]:
        sections += [p(_tr("Context factors applied to the scores", language), "heading"),
                     p("; ".join(_tr(x["reason"], language) for x in r["context_factors"]) + "."),
                     p("These are heuristic rules, not clinically validated findings." if language == "en" else
                       "هذه قواعد تقديرية غير معتمدة سريرياً.", "small")]

    sections.append(p(_tr("Preprocessing & image quality", language), "heading"))
    details = r["preprocessing"]
    preprocess_rows = [
        ("Original size", details["original_size"]), ("Model input", details["model_input_size"]),
        ("Hair coverage removed", f"{details['hair_coverage_pct']}%"), ("Sharpness score", details["sharpness_score"]),
        ("Mean brightness", details["mean_brightness"]), ("Normalisation", details["normalisation"]),
        ("Pipeline", " > ".join(details["steps"])),
        ("Probability calibration", f"Temperature scaling, T = {r['model']['temperature']}"),
    ]
    prep_rows = [[p(_tr(label, language), "small"), p(value, "small")] for label, value in preprocess_rows]
    if language == "ar":
        prep_rows = [list(reversed(row)) for row in prep_rows]
    sections.append(_table(prep_rows, [w * .3, w * .7] if language == "en" else [w * .7, w * .3], language, header=False))

    if r["warnings"]:
        sections.append(p(_tr("Warnings", language), "heading"))
        sections.extend(p(f"• {_tr(warning, language)}") for warning in r["warnings"])
    sections += [Spacer(1, 10), p(_tr("Disclaimer", language), "heading"),
                 p(_tr("This output is generated by an experimental AI system for educational and decision-support purposes only. It is not a diagnosis and does not replace examination by a qualified dermatologist. If a lesion is changing, bleeding or worrying you, seek medical care regardless of this result.", language), "small")]
    doc.build(sections, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()


def build_acne_guide(language: str = "en") -> bytes:
    """Create an educational, non-diagnostic acne self-care handout."""
    if language not in ("en", "ar"):
        raise ValueError("language must be 'en' or 'ar'")
    styles = _styles(language)
    p = lambda text, style="body": _paragraph(text, styles[style], language)
    if language == "ar":
        title = "دليل العناية العامة بحب الشباب"
        lines = [
            "اغسل المنطقة بلطف مرة أو مرتين يومياً، وتجنب الفرك وعصر البثور.",
            "اختر مرطباً وواقياً شمسياً مكتوباً عليهما غير مسببيْن لانسداد المسام.",
            "يمكن تجربة منتج واحد دون وصفة مثل البنزويل بيروكسيد أو حمض الساليسيليك؛ ابدأ تدريجياً واتبع ملصق المنتج.",
            "قد يسبب البنزويل بيروكسيد تهيجاً وقد يبهت الأقمشة. أوقف المنتج إذا حدث تهيج شديد أو تورم.",
            "تجنب الأدابالين أثناء الحمل أو التخطيط للحمل إلا إذا وجّهك طبيبك. اطلب تقييماً طبياً عند وجود عقد مؤلمة أو ندبات أو استمرار المشكلة.",
        ]
        disclaimer = "معلومات تعليمية عامة وليست تشخيصاً أو خطة علاج شخصية. استشر طبيباً أو صيدلياً عند الشك."
        source = "المصادر: الأكاديمية الأمريكية للأمراض الجلدية وNHS. اتبع ملصق المنتج والإرشادات الطبية المحلية."
    else:
        title = "Acne care: a gentle starting guide"
        lines = [
            "Wash gently once or twice daily; avoid scrubbing and picking.",
            "Choose moisturizer and sunscreen labeled non-comedogenic.",
            "If appropriate, try one OTC active such as benzoyl peroxide or salicylic acid; start gradually and follow the product label.",
            "Benzoyl peroxide can irritate skin and bleach fabrics. Stop and seek advice for severe irritation or swelling.",
            "Avoid adapalene while pregnant or trying to conceive unless your clinician advises it. Seek care for painful nodules, scarring, or persistent acne.",
        ]
        disclaimer = "General education only, not a diagnosis or personal treatment plan. Ask a clinician or pharmacist if unsure."
        source = "Sources: American Academy of Dermatology; NHS. Review product labels and local clinical advice."

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=22 * mm,
                            bottomMargin=22 * mm, title=title, author="SkinAI")
    story = [p("SkinAI", "heading"), p(title, "title"), Spacer(1, 10)]
    story.extend(p(f"• {line}") for line in lines)
    story += [Spacer(1, 14), p(disclaimer, "small"), Spacer(1, 10), p(source, "small")]
    doc.build(story)
    return buf.getvalue()
