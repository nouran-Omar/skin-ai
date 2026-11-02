import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import type { Question } from "./types";

export type Language = "en" | "ar";

const AR: Record<string, string> = {
  "Could not connect to the SkinAI service. It may be starting, or the API URL or browser access settings may need checking. Please try again shortly.": "تعذر الاتصال بخدمة SkinAI. قد تكون الخدمة قيد التشغيل، أو قد يحتاج عنوان API أو إعدادات الوصول من المتصفح إلى المراجعة. يُرجى المحاولة بعد قليل.",
  "The request took too long. The screening service may be waking up; wait a moment and try again.": "استغرق الطلب وقتاً طويلاً. قد تكون خدمة الفحص قيد التشغيل؛ انتظر قليلاً ثم حاول مجدداً.",
  "The SkinAI service is starting or temporarily unavailable. Please wait a minute and try again.": "خدمة SkinAI قيد التشغيل أو غير متاحة مؤقتاً. انتظر دقيقة ثم حاول مجدداً.",
  "The SkinAI service encountered a problem. Please try again shortly. If it keeps happening, contact support with the error code.": "واجهت خدمة SkinAI مشكلة. يُرجى المحاولة بعد قليل. إذا استمرت المشكلة، تواصل مع الدعم واذكر رمز الخطأ.",
  "SkinAI | Skin lesion pre-screening": "SkinAI | الفحص الأولي لآفات الجلد",
  "Skin lesion pre-screening": "الفحص الأولي لآفات الجلد",
  "Main navigation": "التنقل الرئيسي",
  "Footer navigation": "روابط التذييل",
  "Skin lesion check": "فحص آفة جلدية",
  "SkinAI Assistant": "مساعد SkinAI",
  "Switch to English": "التبديل إلى الإنجليزية",
  "Skin lesion checker": "أداة فحص آفات الجلد",
  "AI Dermatologist Assistant": "مساعد SkinAI للعناية بالبشرة",
  "Progress tracker": "متابعة الجلد",
  "SkinAI provides educational pre-screening support and general skin-care information. It does not diagnose or replace a qualified clinician.": "يقدم SkinAI معلومات تعليمية للفحص الأولي والعناية العامة بالبشرة. لا يشخّص الحالات ولا يحل محل الطبيب المختص.",
  "Built to make skin-health education more accessible.": "نعمل على إتاحة التثقيف الصحي للبشرة للجميع.",
  "Explore SkinAI": "استكشف SkinAI",
  "Find out more": "اكتشف المزيد",
  "AI-supported skin health": "صحة الجلد بدعم الذكاء الاصطناعي",
  "SkinAI | Smart skin lesion pre-screening": "SkinAI | الفحص الأولي الذكي لآفات البشرة",
  "Explore a skin concern with AI-supported pre-screening, receive a clear clinical-style report to discuss with a clinician, and build awareness for earlier care.": "استكشف مشكلة جلدية عبر فحص أولي مدعوم بالذكاء الاصطناعي، واحصل على تقرير واضح لمناقشته مع الطبيب، وعزّز الوعي لاتخاذ خطوات الرعاية مبكراً.",
  "Start screening": "ابدأ الفحص",
  "A clearer place to start": "خطوة أوضح نحو العناية ببشرتك",
  "Primary feature": "الميزة الرئيسية",
  "Optional features": "مزايا إضافية",
  "Explore at your own pace": "استكشف وفقاً لوقتك",
  "Helpful tools and education are here when you want them.": "أدوات مفيدة ومعلومات تثقيفية متاحة لك متى احتجتها.",
  "A friendly place to ask": "مساحة ودودة لأسئلتك",
  "Analysis": "التحليل",
  "Features": "المزايا",
  "Account": "الحساب",
  "Resources": "الموارد",
  "Chatbot": "المحادثة الذكية",
  "Acne Care": "العناية بحب الشباب",
  "Sign In": "تسجيل الدخول",
  "Journal": "السجل",
  "About": "عن SkinAI",
  "Limits": "الحدود الطبية",
  "Start Free Chat": "ابدأ المحادثة مجاناً",
  "A welcoming space for everyday skin questions, with trusted sources and gentle guidance.": "مساحة ودودة لأسئلتك اليومية عن البشرة، مع إرشادات لطيفة ومصادر موثوقة.",
  "Medical safety notice": "تنبيه طبي",
  "I understand SkinAI is educational and cannot diagnose or replace a clinician.": "أفهم أن SkinAI يقدم معلومات تعليمية ولا يشخّص ولا يحل محل الطبيب.",
  "I understand my photo is processed on the server and the report is temporarily available for up to 24 hours.": "أفهم أن صورتي تُعالج على الخادم وأن التقرير متاح مؤقتاً لمدة تصل إلى 24 ساعة.",
  "Sign in to continue your skin journal.": "سجّل الدخول لمتابعة سجل بشرتك.",
  "Welcome back": "مرحباً بعودتك",
  "Create your SkinAI account": "أنشئ حساب SkinAI الخاص بك",
  "Choose sign in or create account": "اختر تسجيل الدخول أو إنشاء حساب",
  "Email address": "عنوان البريد الإلكتروني",
  "Password": "كلمة المرور",
  "Your account is private to you.": "حسابك خاص بك.",
  "Educational use only": "للاستخدام التعليمي فقط",
  "A thoughtful place to start": "بداية هادئة لأسئلتك",
  "Your SkinAI Assistant": "مساعد SkinAI الخاص بك",
  "Ask naturally in English or Arabic about everyday skin care, acne, or general skin-health questions. The assistant shares educational guidance and helps you find trusted sources.": "اسأل بالعربية أو الإنجليزية عن العناية اليومية بالبشرة أو حب الشباب أو الصحة الجلدية عموماً. يقدم المساعد إرشادات تعليمية ويساعدك في الوصول إلى مصادر موثوقة.",
  "Back to SkinAI": "العودة إلى SkinAI",
  "If a skin spot is changing, bleeding, or worrying you, arrange an in-person medical assessment. Chat cannot examine skin or diagnose a condition.": "إذا كانت بقعة جلدية تتغير أو تنزف أو تثير قلقك، فرتب تقييماً طبياً حضورياً. لا تستطيع المحادثة فحص الجلد أو تشخيص حالة.",
  "Sources": "المصادر",
  "Generated using retrieved references": "تمت صياغة الإجابة بالاستناد إلى المصادر المسترجعة",
  "Allow optional Hugging Face generation": "السماح بالصياغة الاختيارية عبر Hugging Face",
  "When enabled and configured, your message and recent chat turns are sent to the selected Hugging Face model. Avoid personal or identifying details.": "عند تفعيل الخيار وإعداد الخدمة، تُرسل رسالتك وبعض رسائل المحادثة الأخيرة إلى نموذج Hugging Face المحدد. تجنب مشاركة بيانات شخصية أو تعريفية.",
  "Acne care": "العناية بحب الشباب",
  "History & progress": "السجل والمتابعة",
  "Your SkinAI dashboard": "لوحة SkinAI الخاصة بك",
  "Explore the assistant, practical skin-care education, and your optional progress journal.": "استكشف المساعد ومعلومات العناية بالبشرة وسجل المتابعة الاختياري.",
  "Interactive SkinAI Assistant": "مساعد SkinAI التفاعلي",
  "Ask about general skin health or acne care. Guided educational responses; not a dermatologist, diagnosis, or treatment plan.": "اسأل عن صحة الجلد أو العناية بحب الشباب. إجابات تعليمية موجّهة وليست بديلاً عن طبيب الجلدية أو التشخيص أو خطة العلاج.",
  "Try asking about gentle acne care, or when to get a spot checked.": "يمكنك السؤال عن العناية اللطيفة بحب الشباب أو متى ينبغي فحص بقعة جلدية.",
  "Acne care guide": "دليل العناية بحب الشباب",
  "General education for gentle, over-the-counter skin care. Acne is not a class supported by this image model.": "معلومات عامة عن العناية اللطيفة ومنتجات العناية دون وصفة. حب الشباب ليس من الفئات التي يدعمها نموذج الصور.",
  "Wash gently and avoid scrubbing or picking.": "اغسل البشرة بلطف وتجنب الفرك أو عصر البثور.",
  "If suitable, try one OTC active such as benzoyl peroxide or salicylic acid gradually and follow its product label.": "إذا كان مناسباً، جرّب مكوّناً واحداً دون وصفة مثل البنزويل بيروكسيد أو حمض الساليسيليك تدريجياً واتبع ملصق المنتج.",
  "Avoid adapalene during pregnancy or when trying to conceive unless a clinician advises otherwise.": "تجنب الأدابالين أثناء الحمل أو التخطيط له إلا إذا أوصى الطبيب بخلاف ذلك.",
  "AAD self-care guidance": "إرشادات الأكاديمية الأمريكية للأمراض الجلدية",
  "Educational information only. Seek medical advice for painful nodules, scarring, severe irritation, or persistent concerns.": "معلومات تعليمية فقط. اطلب المشورة الطبية عند وجود عُقيدات مؤلمة أو ندبات أو تهيج شديد أو استمرار المشكلة.",
  "Sign in or create an account to save analysis summaries and use skin progress tracking.": "سجّل الدخول أو أنشئ حساباً لحفظ ملخصات التحليل واستخدام متابعة الجلد.",
  "Skin progress journal": "سجل متابعة الجلد",
  "Save summaries and progress notes. Uploaded photos are not stored in your account.": "احفظ ملخصات التحليل وملاحظات المتابعة. لا تُحفظ الصور المرفوعة في حسابك.",
  "Sign out": "تسجيل الخروج", "Email": "البريد الإلكتروني", "Password (12+ characters)": "كلمة المرور (12 حرفاً على الأقل)",
  "Sign in": "تسجيل الدخول", "Create account": "إنشاء حساب", "Need an account? Create one": "ليس لديك حساب؟ أنشئ حساباً", "Already have an account? Sign in": "لديك حساب؟ سجّل الدخول",
  "Saved summary to your account. Images are not saved.": "تم حفظ ملخص التحليل في حسابك. لم يتم حفظ الصور.", "Save this analysis summary": "احفظ ملخص هذا التحليل",
  "Saved summaries": "الملخصات المحفوظة", "No saved analyses yet.": "لا توجد تحليلات محفوظة بعد.", "Skin progress": "متابعة الجلد", "Spot label, e.g. left arm": "اسم للبقعة، مثل الذراع اليسرى", "Optional progress note": "ملاحظة متابعة اختيارية", "Add dated entry": "أضف إدخالاً بتاريخ اليوم", "Delete": "حذف",
  "Only save information you are comfortable keeping in this account. Use a nickname for each spot; avoid names or other identifying details.": "احفظ فقط المعلومات التي ترغب في الاحتفاظ بها في هذا الحساب. استخدم اسماً مستعاراً لكل بقعة وتجنب الأسماء أو البيانات التعريفية.",
  "Skin information assistant": "مساعد المعلومات الجلدية", "Ask a general question. This assistant does not diagnose or prescribe.": "اطرح سؤالاً عاماً. يقدم المساعد معلومات موجّهة ولا يشخّص أو يصف العلاج.", "Download acne care guide (English)": "تنزيل دليل العناية بحب الشباب (بالإنجليزية)", "You:": "أنت:", "Ask about general skin or acne care": "اسأل عن العناية العامة بالجلد أو حب الشباب", "Sending…": "جارٍ الإرسال…", "Ask": "اسأل", "Could not reach assistant. Please try again.": "تعذر الاتصال بالمساعد. حاول مرة أخرى.", "Educational information only; not a diagnosis or a substitute for a clinician. Do not share identifying or sensitive personal details.": "معلومات تعليمية فقط، وليست تشخيصاً أو بديلاً عن الطبيب. لا تشارك بيانات شخصية أو حساسة.", "Do not share identifying or sensitive personal details.": "لا تشارك بيانات شخصية أو حساسة.",
  "Switch to Arabic": "التبديل إلى العربية",
  "Check a skin spot, with context a camera can't see.": "افحص بقعة جلدية بمعلومات لا تستطيع الكاميرا رؤيتها.",
  "Answer a few questions about the spot, add a photo, and get a ranked list of likely conditions, an urgency level and a PDF summary you can bring to your doctor.": "أجب عن بعض الأسئلة وأضف صورة لتحصل على احتمالات مرتبة ومستوى الاستعجال وملخص يمكنك عرضه على طبيبك.",
  "This tool supports, and never replaces, a clinician. It cannot diagnose. Photos are processed on the server, kept for 24 hours so you can download your report, then deleted.": "تساعدك هذه الأداة ولا تحل محل الطبيب، ولا تقدم تشخيصاً. تُعالج الصور على الخادم وتُحفظ لمدة 24 ساعة لإتاحة تنزيل التقرير، ثم تُحذف.",
  "I understand this is not a medical diagnosis and I will see a doctor about anything that worries me.": "أفهم أن هذه الأداة لا تقدم تشخيصاً طبياً، وسأراجع الطبيب بشأن أي أمر يقلقني.",
  "Start questions": "ابدأ الأسئلة",
  "of": "من",
  "How old are you?": "كم عمرك؟",
  "What is your sex at birth?": "ما الجنس المسجل عند الولادة؟",
  "How does your skin react to the sun?": "كيف تتفاعل بشرتك مع الشمس؟",
  "This helps us judge how reliable the result is for your skin type.": "يساعدنا ذلك على تقدير مدى ملاءمة النتيجة لدرجة بشرتك.",
  "Where on the body is it?": "أين تقع البقعة؟",
  "How long has it been there?": "منذ متى ظهرت؟",
  "In the last 3 months, has it changed in size, shape or colour?": "هل تغير حجمها أو شكلها أو لونها خلال الأشهر الثلاثة الماضية؟",
  "Which of these do you notice? Select all that apply.": "ما الأعراض التي تلاحظها؟ اختر كل ما ينطبق.",
  "How strong is the itching, from 0 (barely) to 10 (unbearable)?": "ما شدة الحكة من 0 (خفيفة جداً) إلى 10 (لا تُحتمل)؟",
  "Has the spot bled or stayed open for more than 4 weeks?": "هل نزفت البقعة أو بقيت مفتوحة لأكثر من 4 أسابيع؟",
  "How many areas of your body are affected?": "كم منطقة من الجسم متأثرة؟",
  "Does it come and go in flare-ups?": "هل تظهر الأعراض وتختفي على شكل نوبات؟",
  "Do any of these apply to you or your close family?": "هل ينطبق أي مما يلي عليك أو على عائلتك المقربة؟",
  "Has a close relative had melanoma?": "هل أُصيب أحد أقاربك المقربين بالميلانوما؟",
  "How many blistering sunburns have you had in your life?": "كم مرة تعرضت لحروق شمسية سببت فقاعات؟",
  "Have you ever had a skin cancer before?": "هل أُصبت بسرطان الجلد من قبل؟",
  "Do you take medicine that weakens your immune system (for example after a transplant)?": "هل تتناول دواءً يضعف جهاز المناعة، مثل أدوية ما بعد زراعة الأعضاء؟",
  "Yes": "نعم",
  "No": "لا",
  "Prefer not to say": "أفضل عدم الإجابة",
  "Very fair": "فاتحة جداً",
  "Fair": "فاتحة",
  "Medium": "متوسطة",
  "Olive": "زيتونية",
  "Brown": "بنية",
  "Dark brown / black": "بنية داكنة أو سوداء",
  "Head or neck": "الرأس أو الرقبة",
  "Chest, back or belly": "الصدر أو الظهر أو البطن",
  "Arm": "الذراع",
  "Hand": "اليد",
  "Leg": "الساق",
  "Foot or sole": "القدم أو باطنها",
  "Somewhere else": "مكان آخر",
  "Less than 2 weeks": "أقل من أسبوعين",
  "2 to 8 weeks": "من أسبوعين إلى 8 أسابيع",
  "2 to 6 months": "من شهرين إلى 6 أشهر",
  "More than 6 months": "أكثر من 6 أشهر",
  "Since birth or childhood": "منذ الولادة أو الطفولة",
  "No change": "لم تتغير",
  "Changed slowly": "تغيرت ببطء",
  "Changed quickly": "تغيرت بسرعة",
  "Itching": "حكة",
  "Pain or tenderness": "ألم أو حساسية عند اللمس",
  "Bleeding": "نزيف",
  "Crusting or oozing": "قشور أو إفرازات",
  "Scaling or flaking": "تقشر",
  "Dry or cracked skin": "جفاف أو تشقق",
  "None of these": "لا شيء مما سبق",
  "Just one spot": "بقعة واحدة فقط",
  "A few areas": "عدة مناطق",
  "Many areas": "مناطق كثيرة",
  "Asthma, hay fever or food allergies": "الربو أو حمى القش أو حساسية الطعام",
  "Eczema in the family": "إكزيما في العائلة",
  "Psoriasis in the family": "صدفية في العائلة",
  "I don't know": "لا أعلم",
  "5 or more": "5 مرات أو أكثر",
  "1 to 4": "من مرة إلى 4 مرات",
  "None": "لم يحدث",
  "Cannot reach the server. Start the backend on port 8000 and refresh.": "تعذّر الاتصال بالخادم. شغّل خدمة التطبيق ثم حدّث الصفحة.",
  "Something went wrong.": "حدث خطأ غير متوقع.",
  "Consent": "الموافقة",
  "Questions": "الأسئلة",
  "Photo": "الصورة",
  "Result": "النتيجة",
  "Progress": "التقدم",
  "Switch to light mode": "التبديل إلى الوضع الفاتح",
  "Switch to dark mode": "التبديل إلى الوضع الداكن",
  "Analysing your photo": "جارٍ تحليل الصورة",
  "Cleaning the image and removing hair": "تحسين الصورة وإزالة الشعر",
  "Balancing colour and lighting": "موازنة الألوان والإضاءة",
  "Running the classification model": "تشغيل نموذج التصنيف",
  "Mapping the areas that influenced the result": "تحديد المناطق التي أثرت في النتيجة",
  "Combining with your answers": "دمج النتيجة مع إجاباتك",
  "Back": "رجوع",
  "Continue to photo": "المتابعة إلى الصورة",
  "Next": "التالي",
  "Use a JPEG, PNG or WebP photo.": "استخدم صورة بصيغة JPEG أو PNG أو WebP.",
  "Upload a photo. Drop a file here or press Enter to browse.": "ارفع صورة. أفلت الملف هنا أو اضغط Enter لاختياره.",
  "Natural light, in focus, the spot centred and filling about half the frame. Dermoscopy images work best.": "استخدم إضاءة طبيعية، واجعل البقعة واضحة وفي منتصف الصورة وتشغل نحو نصف الإطار. صور منظار الجلد تعطي أفضل النتائج.",
  "Choose a smaller photo.": "اختر صورة أصغر حجماً.",
  "The photo is over {size} MB. Choose a smaller one.": "حجم الصورة أكبر من {size} ميغابايت. اختر صورة أصغر.",
  "Add a photo of the spot": "أضف صورة للبقعة",
  "Drop a photo here": "أفلت الصورة هنا",
  "or click to browse. JPEG, PNG or WebP, up to {size} MB.": "أو انقر لاختيارها. JPEG أو PNG أو WebP، حتى {size} ميغابايت.",
  "Take a photo": "التقط صورة",
  "Selected skin photo": "صورة الجلد المحددة",
  "Remove photo": "إزالة الصورة",
  "Analyse photo": "حلّل الصورة",
  "Confidence": "مستوى الثقة",
  "confidence": "الثقة",
  "Malignant": "خبيث",
  "Pre-malignant": "محتمل التحول إلى خبيث",
  "Benign": "حميد",
  "Inflammatory": "التهابي",
  "Vascular": "وعائي",
  "Unclassified": "غير مصنف",
  "Other possibilities": "احتمالات أخرى",
  "Probability source": "مصدر الاحتمالات",
  "With your answers": "مع إجاباتك",
  "Image only": "الصورة فقط",
  "What the model looked at": "ما الذي ركّز عليه النموذج؟",
  "Preprocessed photo": "الصورة بعد المعالجة",
  "Attention heat map": "خريطة المناطق المؤثرة",
  "Slide to compare photo and heat map": "حرّك المؤشر لمقارنة الصورة بخريطة التأثير",
  "Warm colours mark the regions that pushed the model towards its top answer.": "تشير الألوان الدافئة إلى المناطق التي أثّرت في الاحتمال الأعلى للنموذج.",
  "Things to know": "معلومات مهمة",
  "How your answers changed the result": "كيف أثّرت إجاباتك في النتيجة",
  "Image processing details": "تفاصيل معالجة الصورة",
  "Original size": "الحجم الأصلي",
  "Model input": "حجم الصورة للنموذج",
  "Hair removed": "الشعر الذي أُزيل",
  "Sharpness": "الوضوح",
  "Brightness": "الإضاءة",
  "Model": "النموذج",
  "Calibration (T)": "معايرة الثقة (T)",
  "Start over": "ابدأ من جديد",
  "Download PDF report": "تنزيل التقرير بصيغة PDF",
  "Demo mode.": "الوضع التجريبي.",
  "No trained model is installed, so these numbers are placeholders.": "لا يوجد نموذج مدرّب؛ هذه الأرقام للتوضيح فقط.",
  "Demo mode: no trained model is loaded. Results are placeholders.": "الوضع التجريبي: لم يتم تحميل نموذج مدرّب، والنتائج للتوضيح فقط.",
  "Low confidence: the image may be unclear or outside the supported skin-lesion classes. Treat these results with extra caution.": "الثقة منخفضة: قد تكون الصورة غير واضحة أو خارج فئات آفات الجلد التي يدعمها النموذج. تعامل مع النتائج بحذر شديد.",
  "The photo looks blurry. Retake it in focus for a more reliable result.": "تبدو الصورة ضبابية. أعد التقاطها بوضوح للحصول على نتيجة أفضل.",
  "The photo is very dark or over-exposed.": "الصورة مظلمة جداً أو شديدة السطوع.",
  "Low resolution image. Fine detail may be lost.": "دقة الصورة منخفضة وقد لا تظهر التفاصيل الدقيقة.",
  "Heavy hair coverage was detected and digitally removed; details may be affected.": "تم رصد شعر كثيف وإزالته رقمياً؛ قد تتأثر بعض التفاصيل.",
  "Public skin-image datasets under-represent dark skin tones, so accuracy may be lower for your skin type. Please rely on a clinician's assessment.": "تمثّل درجات البشرة الداكنة بنسبة أقل في مجموعات الصور العامة، لذلك قد تقل الدقة لهذه الدرجة. يُرجى الاعتماد على تقييم الطبيب.",
  "This output is generated by an experimental AI system for educational and decision-support purposes only. It is not a diagnosis and does not replace examination by a qualified dermatologist. If a lesion is changing, bleeding or worrying you, seek medical care regardless of this result.": "أنتج نظام الذكاء الاصطناعي التجريبي هذه النتيجة لأغراض تعليمية ومساندة القرار فقط. وهي ليست تشخيصاً ولا تغني عن فحص طبيب جلدية مؤهل. إذا كانت الآفة تتغير أو تنزف أو تثير قلقك، فاطلب الرعاية الطبية بصرف النظر عن هذه النتيجة.",
  "See a doctor soon": "راجع الطبيب قريباً",
  "Features that need a professional check were found. Book a dermatology appointment within the next 1-2 weeks, and sooner if the spot keeps changing.": "ظهرت سمات تستدعي تقييماً طبياً. احجز موعداً لدى طبيب الجلدية خلال أسبوع إلى أسبوعين، أو أسرع إذا استمرت البقعة في التغير.",
  "Book a routine appointment": "احجز موعداً طبياً قريباً",
  "This result is not alarming, but a clinician should confirm it. Book a visit in the next few weeks and keep photos to track changes.": "لا تبدو النتيجة مقلقة، لكن ينبغي للطبيب تأكيدها. احجز موعداً خلال الأسابيع القادمة واحتفظ بصور لمتابعة التغيرات.",
  "Low concern, keep watching": "مؤشرات الاستعجال منخفضة؛ واصل المتابعة",
  "Nothing in this analysis suggests urgency. Re-check monthly and see a doctor if it grows, changes colour, bleeds or starts to hurt.": "لا تشير هذه النتيجة إلى حاجة عاجلة. أعد الفحص شهرياً وراجع الطبيب إذا كبرت البقعة أو تغير لونها أو نزفت أو بدأت تؤلمك.",
  "Age 50 or older": "العمر 50 عاماً أو أكثر",
  "Age 25 or younger": "العمر 25 عاماً أو أقل",
  "Rapid change in the last 3 months": "تغير سريع خلال الأشهر الثلاثة الماضية",
  "Slow change in the last 3 months": "تغير تدريجي خلال الأشهر الثلاثة الماضية",
  "Bleeding or crusting": "نزيف أو تقشر",
  "Non-healing for over 4 weeks": "عدم الالتئام لأكثر من 4 أسابيع",
  "Close relative with melanoma": "إصابة قريب من الدرجة الأولى بالميلانوما",
  "5+ blistering sunburns": "خمس حروق شمسية فقاعية أو أكثر",
  "Previous skin cancer": "إصابة سابقة بسرطان الجلد",
  "Weakened immune system": "ضعف جهاز المناعة",
  "Present since birth or childhood": "موجودة منذ الولادة أو الطفولة",
  "Lesion on foot or sole": "آفة في القدم أو باطنها",
  "Scaling in several areas": "تقشر في عدة مناطق",
  "Strong itch, dryness or allergy history": "حكة شديدة أو جفاف أو تاريخ من الحساسية",
  "Comes and goes in flare-ups": "تظهر وتختفي على شكل نوبات",
  "Actinic keratosis / intraepithelial carcinoma": "التقرّن السفعي / سرطان داخل الظهارة",
  "Rough, scaly patch caused by long-term sun damage. Can progress to squamous cell carcinoma.": "بقعة خشنة ومتقشرة بسبب التعرض الطويل للشمس، وقد تتطور إلى سرطان الخلايا الحرشفية.",
  "Basal cell carcinoma": "سرطان الخلايا القاعدية",
  "Most common skin cancer. Grows slowly and rarely spreads, but needs treatment.": "أكثر أنواع سرطان الجلد شيوعاً. ينمو ببطء ونادراً ما ينتشر، لكنه يحتاج إلى علاج.",
  "Benign keratosis-like lesion": "آفة شبيهة بالتقرّن الحميد",
  "Includes seborrheic keratosis and solar lentigo. Harmless waxy or pigmented growths.": "تشمل التقرّن الدهني والنمش الشمسي؛ وهي زوائد مصطبغة أو شمعية حميدة.",
  "Dermatofibroma": "ورم ليفي جلدي",
  "Firm, harmless skin nodule, often after a minor injury or insect bite.": "عقدة جلدية صلبة وحميدة، وقد تظهر بعد إصابة بسيطة أو لدغة حشرة.",
  "Melanoma": "الميلانوما",
  "Serious skin cancer arising from pigment cells. Early detection is critical for survival.": "سرطان جلدي خطير ينشأ من الخلايا الصبغية. يساهم اكتشافه المبكر في تحسين فرص العلاج.",
  "Melanocytic nevus (mole)": "وحمة صبغية (شامة)",
  "Common benign mole. Should be monitored for changes in size, shape or colour.": "شامة حميدة شائعة. تجب مراقبتها لأي تغير في الحجم أو الشكل أو اللون.",
  "Vascular lesion": "آفة وعائية",
  "Includes angiomas and angiokeratomas. Usually benign blood-vessel growths.": "تشمل الأورام الوعائية والورم الوعائي المتقرّن، وغالباً ما تكون زوائد حميدة للأوعية الدموية.",
  "Eczema (atopic dermatitis)": "الإكزيما (التهاب الجلد التأتبي)",
  "Chronic itchy, dry and inflamed skin that comes and goes in flares.": "حالة مزمنة تسبب حكة وجفافاً والتهاباً جلدياً وقد تظهر على شكل نوبات.",
  "Psoriasis": "الصدفية",
  "Autoimmune condition causing thick, silvery-scaled red plaques.": "حالة مناعية تسبب لويحات حمراء سميكة مغطاة بقشور فضية.",
  "Upload a JPEG, PNG or WebP image.": "ارفع صورة بصيغة JPEG أو PNG أو WebP.",
  "Image dimensions are too large to analyze safely.": "أبعاد الصورة أكبر من الحد الآمن للتحليل.",
  "This file could not be read as a supported image.": "تعذرت قراءة الملف كصورة مدعومة.",
  "This file could not be read as an image of at least 64x64 pixels.": "تعذرت قراءة الصورة أو أن أبعادها أصغر من 64×64 بكسل.",
  "Upload an image that is at least 64x64 pixels.": "ارفع صورة بأبعاد لا تقل عن 64×64 بكسل.",
  "Answers must be a JSON object.": "يجب إرسال الإجابات بتنسيق JSON صالح.",
  "Image analysis is temporarily unavailable. Please try again later.": "تحليل الصور غير متاح مؤقتاً. يُرجى المحاولة لاحقاً.",
  "The image could not be matched confidently to the supported skin-lesion classes. It may be unclear or outside the model's scope. Upload a clear close-up of one lesion, or consult a clinician.": "تعذر مطابقة الصورة بثقة مع فئات آفات الجلد التي يدعمها النموذج. قد تكون الصورة غير واضحة أو خارج نطاقه. ارفع صورة قريبة وواضحة لآفة واحدة أو استشر طبيباً.",
  "The photo is too blurry to analyze. Retake it in focus and try again.": "الصورة ضبابية جداً للتحليل. أعد التقاطها بوضوح ثم حاول مجدداً.",
  "Hair artefact removal (black-hat + inpainting)": "إزالة الشعر من الصورة باستخدام المعالجة الرقمية",
  "Colour constancy (Shades of Gray, p=6)": "موازنة الألوان والإضاءة",
};

const QUESTION_AR: Record<string, { section: string; text: string; help?: string; unit?: string; options?: Record<string, { label: string; hint?: string }> }> = {
  age: { section: "عن معلوماتك", text: "كم عمرك؟", unit: "سنة" },
  sex: { section: "عن معلوماتك", text: "ما الجنس المسجل عند الولادة؟", options: { female: { label: "أنثى" }, male: { label: "ذكر" }, na: { label: "أفضل عدم الإجابة" } } },
  skin_tone: { section: "عن معلوماتك", text: "كيف تتفاعل بشرتك مع الشمس؟", help: "يساعدنا ذلك على تقدير مدى ملاءمة النتيجة لدرجة بشرتك.", options: {
    I: { label: "تحترق دائماً ولا تسمر أبداً", hint: "فاتحة جداً" }, II: { label: "تحترق بسهولة وتسمر قليلاً", hint: "فاتحة" },
    III: { label: "تحترق أحياناً وتسمر تدريجياً", hint: "متوسطة" }, IV: { label: "نادراً ما تحترق وتسمر بسهولة", hint: "زيتونية" },
    V: { label: "نادراً جداً ما تحترق وتسمر بعمق", hint: "بنية" }, VI: { label: "لا تحترق أبداً", hint: "بنية داكنة أو سوداء" },
  } },
  location: { section: "البقعة الجلدية", text: "أين تقع البقعة؟", options: { head_neck: { label: "الرأس أو الرقبة" }, trunk: { label: "الصدر أو الظهر أو البطن" }, arms: { label: "الذراع" }, hands: { label: "اليد" }, legs: { label: "الساق" }, feet_soles: { label: "القدم أو باطنها" }, other: { label: "مكان آخر" } } },
  duration: { section: "البقعة الجلدية", text: "منذ متى ظهرت؟", options: { lt_2w: { label: "أقل من أسبوعين" }, w2_8: { label: "من أسبوعين إلى 8 أسابيع" }, m2_6: { label: "من شهرين إلى 6 أشهر" }, gt_6m: { label: "أكثر من 6 أشهر" }, birth: { label: "منذ الولادة أو الطفولة" } } },
  change: { section: "البقعة الجلدية", text: "هل تغير حجمها أو شكلها أو لونها خلال الأشهر الثلاثة الماضية؟", options: { none: { label: "لم تتغير" }, slow: { label: "تغيرت ببطء" }, rapid: { label: "تغيرت بسرعة" } } },
  symptoms: { section: "الأعراض", text: "ما الأعراض التي تلاحظها؟ اختر كل ما ينطبق.", options: { itching: { label: "حكة" }, pain: { label: "ألم أو حساسية عند اللمس" }, bleeding: { label: "نزيف" }, crusting: { label: "قشور أو إفرازات" }, scaling: { label: "تقشر" }, dry_cracked: { label: "جفاف أو تشقق" }, none: { label: "لا شيء مما سبق" } } },
  itch_severity: { section: "الأعراض", text: "ما شدة الحكة من 0 (خفيفة جداً) إلى 10 (لا تُحتمل)؟" },
  non_healing: { section: "الأعراض", text: "هل نزفت البقعة أو بقيت مفتوحة لأكثر من 4 أسابيع؟", options: { yes: { label: "نعم" }, no: { label: "لا" } } },
  extent: { section: "الأعراض", text: "كم منطقة من الجسم متأثرة؟", options: { one: { label: "بقعة واحدة فقط" }, few: { label: "عدة مناطق" }, widespread: { label: "مناطق كثيرة" } } },
  flares: { section: "الأعراض", text: "هل تظهر الأعراض وتختفي على شكل نوبات؟", options: { yes: { label: "نعم" }, no: { label: "لا" } } },
  history: { section: "تاريخك الصحي", text: "هل ينطبق أي مما يلي عليك أو على عائلتك المقربة؟", options: { atopy: { label: "الربو أو حمى القش أو حساسية الطعام" }, eczema_family: { label: "إكزيما في العائلة" }, psoriasis_family: { label: "صدفية في العائلة" }, none: { label: "لا شيء مما سبق" } } },
  family_melanoma: { section: "تاريخك الصحي", text: "هل أُصيب أحد أقاربك المقربين بالميلانوما؟", options: { yes: { label: "نعم" }, no: { label: "لا" }, unknown: { label: "لا أعلم" } } },
  sunburn: { section: "تاريخك الصحي", text: "كم مرة تعرضت لحروق شمسية سببت فقاعات؟", options: { many: { label: "5 مرات أو أكثر" }, few: { label: "من مرة إلى 4 مرات" }, none: { label: "لم يحدث" } } },
  prior_cancer: { section: "تاريخك الصحي", text: "هل أُصبت بسرطان الجلد من قبل؟", options: { yes: { label: "نعم" }, no: { label: "لا" } } },
  immuno: { section: "تاريخك الصحي", text: "هل تتناول دواءً يضعف جهاز المناعة (مثل أدوية ما بعد زراعة الأعضاء)؟", options: { yes: { label: "نعم" }, no: { label: "لا" } } },
};

interface LanguageContextValue { language: Language; setLanguage: (language: Language) => void; t: (text: string) => string }
const LanguageContext = createContext<LanguageContextValue | null>(null);

function initialLanguage(): Language {
  try {
    const saved = localStorage.getItem("skinai-language");
    if (saved === "ar" || saved === "en") return saved;
  } catch { /* local storage may be unavailable */ }
  return navigator.language.toLowerCase().startsWith("ar") ? "ar" : "en";
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>(initialLanguage);
  useEffect(() => {
    const direction = language === "ar" ? "rtl" : "ltr";
    document.documentElement.lang = language;
    document.documentElement.dir = direction;
    const title = language === "ar" ? AR["SkinAI | Skin lesion pre-screening"] : "SkinAI | Skin lesion pre-screening";
    const description = language === "ar"
      ? "أداة تعليمية ثنائية اللغة للفحص الأولي لآفات الجلد، تساعدك على مناقشة ملخص مع الطبيب. لا تقدم تشخيصاً طبياً."
      : "Bilingual educational skin-lesion pre-screening. Review an image with questionnaire context and prepare a summary to discuss with a clinician. Not a medical diagnosis.";
    document.title = title;
    document.querySelector('meta[name="description"]')?.setAttribute("content", description);
    document.querySelector('meta[property="og:title"]')?.setAttribute("content", title);
    document.querySelector('meta[property="og:description"]')?.setAttribute("content", description);
    document.querySelector('meta[property="og:locale"]')?.setAttribute("content", language === "ar" ? "ar_EG" : "en_US");
    document.querySelector('meta[name="twitter:title"]')?.setAttribute("content", title);
    document.querySelector('meta[name="twitter:description"]')?.setAttribute("content", description);
    try { localStorage.setItem("skinai-language", language); } catch { /* local storage may be unavailable */ }
  }, [language]);
  const value = useMemo(() => ({
    language,
    setLanguage,
    t: (text: string) => language === "ar" ? AR[text] ?? text : text,
  }), [language]);
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) throw new Error("useLanguage must be used inside LanguageProvider");
  return context;
}

export function localizeQuestion(question: Question, language: Language): Question {
  if (language === "en") return question;
  const translation = QUESTION_AR[question.id];
  if (!translation) return question;
  return {
    ...question,
    section: translation.section,
    text: translation.text,
    help: translation.help ?? question.help,
    unit: translation.unit ?? question.unit,
    options: question.options?.map((option) => ({
      ...option,
      ...translation.options?.[option.value],
    })),
  };
}

export function localizeApiError(message: string, language: Language): string {
  if (language !== "ar") return message;
  const dynamic = message.match(/^Image is larger than (\d+(?:\.\d+)?) MB\.$/);
  if (dynamic) return `حجم الصورة أكبر من ${dynamic[1]} ميغابايت.`;
  const localSize = message.match(/^The photo is over (\d+(?:\.\d+)?) MB\. Choose a smaller one\.$/);
  if (localSize) return `حجم الصورة أكبر من ${localSize[1]} ميغابايت. اختر صورة أصغر.`;
  const translated = AR[message];
  if (translated) return translated;
  if (message.startsWith("Request failed (")) return "تعذر إكمال الطلب. يُرجى المحاولة مرة أخرى.";
  const apiErrors: Record<string, string> = {
    "Please sign in to continue.": "يرجى تسجيل الدخول للمتابعة.",
    "Enter a valid email address.": "أدخل عنوان بريد إلكتروني صالحاً.",
    "Password must be between 12 and 128 characters.": "يجب أن تتراوح كلمة المرور بين 12 و128 حرفاً.",
    "An account with that email already exists.": "يوجد حساب بهذا البريد الإلكتروني بالفعل.",
    "Email or password is incorrect.": "البريد الإلكتروني أو كلمة المرور غير صحيحة.",
    "Invalid report id.": "معرّف التقرير غير صالح.",
    "Report not found or expired.": "لم يُعثر على التقرير أو انتهت صلاحيته.",
    "Report not found or expired. Run the analysis again.": "لم يُعثر على التقرير أو انتهت صلاحيته. أعد التحليل من فضلك.",
    "This analysis is already saved to another account.": "هذا التحليل محفوظ بالفعل في حساب آخر.",
    "Saved analysis not found.": "لم يُعثر على التحليل المحفوظ.",
    "Date must use YYYY-MM-DD format.": "يجب إدخال التاريخ بالتنسيق YYYY-MM-DD.",
    "Enter a lesion label of up to 60 characters.": "أدخل اسماً للبقعة لا يتجاوز 60 حرفاً.",
    "Progress note must be 1000 characters or fewer.": "يجب ألا تتجاوز ملاحظة المتابعة 1000 حرف.",
    "Analysis id is invalid.": "معرّف التحليل غير صالح.",
    "Progress entry not found.": "لم يُعثر على إدخال المتابعة.",
    "Analysis is not in this account's saved history.": "هذا التحليل غير موجود في السجل المحفوظ لهذا الحساب.",
    "Could not reach assistant. Please try again.": "تعذر الاتصال بالمساعد. حاول مرة أخرى من فضلك.",
    "Could not save": "تعذر الحفظ. حاول مرة أخرى من فضلك.",
  };
  return apiErrors[message] ?? "حدث خطأ أثناء تنفيذ الطلب. يُرجى المحاولة مرة أخرى.";
}

export function translatedContent(text: string, language: Language): string {
  if (language !== "ar") return text;
  const translated = AR[text];
  if (translated) return translated;
  if (text.endsWith(" years")) return `${text.slice(0, -6)} سنة`;
  if (text.startsWith("Aspect-preserving resize + pad to ")) return `تغيير الحجم مع الحفاظ على التناسب وإضافة حواف إلى ${text.match(/\d+x\d+/)?.[0] ?? ""}`;
  if (text.startsWith("ImageNet mean=")) return "قيم التطبيع: متوسط ImageNet وانحرافه المعياري";
  return text;
}
