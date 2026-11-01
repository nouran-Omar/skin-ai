"""Professional A4 PDF medical summary (ReportLab)."""
from __future__ import annotations
import base64, io
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

INK, BLUE, MINT = colors.HexColor("#16324F"), colors.HexColor("#2C62A2"), colors.HexColor("#1FB58A")
MUTED, LINE, WASH = colors.HexColor("#5B6B7C"), colors.HexColor("#D9E2EC"), colors.HexColor("#F2F6FA")
URGENCY = {"urgent": colors.HexColor("#C0392B"), "soon": colors.HexColor("#C98A0B"), "routine": colors.HexColor("#12926F")}
RISK_LABEL = dict(malignant="Malignant", premalignant="Pre-malignant", benign="Benign", inflammatory="Inflammatory",
                  vascular="Vascular", unknown="-")

ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=20, textColor=INK, alignment=0, spaceAfter=2)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=12, textColor=BLUE, spaceBefore=12, spaceAfter=5)
BODY = ParagraphStyle("B", parent=ss["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13, textColor=INK)
SMALL = ParagraphStyle("S", parent=BODY, fontSize=8, leading=10.5, textColor=MUTED)


def _bar(p: float, w=150, h=8, color=BLUE) -> Drawing:
    d = Drawing(w, h)
    d.add(Rect(0, 0, w, h, fillColor=WASH, strokeColor=None))
    d.add(Rect(0, 0, max(1, w * p), h, fillColor=color, strokeColor=None))
    return d


def _img(data_uri: str, size: float) -> Image:
    return Image(io.BytesIO(base64.b64decode(data_uri.split(",", 1)[1])), width=size, height=size)


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5); canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 10 * mm, f"SkinAI decision-support report  |  ID {doc.report_id}  |  Not a medical diagnosis")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {doc.page}")
    canvas.setStrokeColor(LINE); canvas.line(18 * mm, 14 * mm, A4[0] - 18 * mm, 14 * mm)
    canvas.restoreState()


def _table(rows, widths, header=True, zebra=True):
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
    st = [("FONTNAME", (0, 0), (-1, -1), "Helvetica"), ("FONTSIZE", (0, 0), (-1, -1), 9), ("TEXTCOLOR", (0, 0), (-1, -1), INK),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
          ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE)]
    if header:
        st += [("BACKGROUND", (0, 0), (-1, 0), INK), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    if zebra:
        st += [("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1), [colors.white, WASH])]
    t.setStyle(TableStyle(st))
    return t


def build_pdf(r: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=20 * mm,
                            title="SkinAI Analysis Report", author="SkinAI")
    doc.report_id = r["id"][:8].upper()
    W = A4[0] - 36 * mm
    P = lambda t, s=BODY: Paragraph(t, s)
    s: list = [P("Skin lesion analysis report", H1),
               P(f"Report {r['id'][:8].upper()}  |  Generated {r['created_at'][:19].replace('T', ' ')} UTC  |  Model: {r['model']['arch']}", SMALL),
               Spacer(1, 8)]

    if r["demo"]:
        s += [P("<b>DEMO MODE</b> - no trained model is installed. Values below are placeholders and carry no clinical meaning.", BODY), Spacer(1, 6)]

    u = r["urgency"]; col = URGENCY[u["level"]]
    box = Table([[P(f"<font color='white'><b>{u['title']}</b></font>", BODY)], [P(f"<font color='white'>{u['message']}</font>", BODY)]], colWidths=[W])
    box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), col), ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                             ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    s += [box, P("Most likely findings", H2)]

    rows = [["Condition", "Category", "Model", "Context-adjusted", ""]]
    for p in r["predictions"][:5]:
        rows.append([p["name"], RISK_LABEL.get(p["risk"], "-"), f"{p['probability'] * 100:.1f}%", f"{p['adjusted_probability'] * 100:.1f}%",
                     _bar(p["adjusted_probability"], 90)])
    s.append(_table(rows, [W * .34, W * .16, W * .13, W * .17, W * .20]))
    top = r["predictions"][0]
    s += [Spacer(1, 5), P(f"<b>{top['name']}.</b> {top['description']}", BODY)]

    s.append(P("Images", H2))
    side = (W - 10 * mm) / 2
    s.append(KeepTogether([Table([[_img(r["images"]["processed"], side), _img(r["images"]["gradcam"], side)],
                                  [P("Preprocessed input", SMALL), P("Grad-CAM attention (areas that drove the prediction)", SMALL)]],
                                 colWidths=[side + 5 * mm] * 2)]))

    s.append(P("Clinical questionnaire", H2))
    if r["answers_summary"]:
        s.append(_table([["Question", "Answer"]] + [[P(x["question"], SMALL), P(x["answer"], SMALL)] for x in r["answers_summary"]], [W * .62, W * .38]))
    if r["context_factors"]:
        s += [P("Context factors applied to the probabilities", H2),
              P("; ".join(f["reason"] for f in r["context_factors"]) + ".", BODY),
              P("These are heuristic priors, not clinically validated rules. Raw model probabilities are shown in the 'Model' column.", SMALL)]

    s.append(P("Preprocessing & image quality", H2))
    d = r["preprocessing"]
    pre = [["Original size", d["original_size"]], ["Model input", d["model_input_size"]], ["Hair coverage removed", f"{d['hair_coverage_pct']}%"],
           ["Sharpness score", d["sharpness_score"]], ["Mean brightness", d["mean_brightness"]], ["Normalisation", P(d["normalisation"], SMALL)],
           ["Pipeline", P(" > ".join(d["steps"]), SMALL)], ["Probability calibration", f"Temperature scaling, T = {r['model']['temperature']}"]]
    s.append(_table(pre, [W * .3, W * .7], header=False))

    if r["warnings"]:
        s += [P("Warnings", H2)] + [P(f"- {w}", BODY) for w in r["warnings"]]

    s += [Spacer(1, 10), P("Disclaimer", H2), P(r["disclaimer"], SMALL)]
    doc.build(s, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()


def build_acne_guide(language: str = "en") -> bytes:
    """Create an educational, non-diagnostic acne self-care handout."""
    ar = language == "ar"
    title = "دليل العناية العامة بحب الشباب" if ar else "Acne care: a gentle starting guide"
    lines = ([
        "اغسل المنطقة بلطف مرة أو مرتين يومياً، وتجنب الفرك وعصر البثور.",
        "اختر مرطباً وواقياً شمسياً مكتوباً عليهما غير مسببيْن لانسداد المسام.",
        "يمكن تجربة منتج واحد دون وصفة مثل البنزويل بيروكسيد أو حمض الساليسيليك؛ ابدأ تدريجياً واتبع ملصق المنتج.",
        "قد يسبب البنزويل بيروكسيد تهيجاً وقد يبهت الأقمشة. أوقف المنتج إذا حدث تهيج شديد أو تورم.",
        "تجنب الأدابالين أثناء الحمل أو التخطيط للحمل إلا إذا وجّهك طبيبك. اطلب تقييماً طبياً عند وجود عقد مؤلمة أو ندبات أو استمرار المشكلة.",
    ] if ar else [
        "Wash gently once or twice daily; avoid scrubbing and picking.",
        "Choose moisturizer and sunscreen labeled non-comedogenic.",
        "If appropriate, try one OTC active such as benzoyl peroxide or salicylic acid; start gradually and follow the product label.",
        "Benzoyl peroxide can irritate skin and bleach fabrics. Stop and seek advice for severe irritation or swelling.",
        "Avoid adapalene while pregnant or trying to conceive unless your clinician advises it. Seek care for painful nodules, scarring, or persistent acne.",
    ])
    disclaimer = "معلومات تعليمية عامة وليست تشخيصاً أو خطة علاج شخصية. استشر طبيباً أو صيدلياً عند الشك." if ar else "General education only, not a diagnosis or personal treatment plan. Ask a clinician or pharmacist if unsure."
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=22*mm, bottomMargin=22*mm, title=title, author="SkinAI")
    story = [Paragraph("SkinAI", H2), Paragraph(title, H1), Spacer(1, 10)]
    story.extend(Paragraph(f"• {line}", BODY) for line in lines)
    story += [Spacer(1, 14), Paragraph(disclaimer, SMALL), Spacer(1, 10), Paragraph("Sources: American Academy of Dermatology; NHS. Review product labels and local clinical advice.", SMALL)]
    doc.build(story)
    return buf.getvalue()
