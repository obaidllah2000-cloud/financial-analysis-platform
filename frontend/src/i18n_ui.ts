// Arabic for every piece of interface text. Applied to the rendered page (text, placeholders, titles) when Arabic is selected.
// Server data (ratios, findings, interpretations) arrives already translated through ?lang=ar.
export const AR_UI: Record<string, string> = {
  // shell & navigation
  "Financial Analysis Platform": "منصة التحليل المالي", "AI-assisted, analyst-controlled": "بمساعدة الذكاء الاصطناعي وتحت سيطرة المحلل",
  Companies: "الشركات", Tools: "الأدوات", "Multi-company comparison": "مقارنة الشركات", Benchmarks: "المعايير المرجعية", Methodology: "المنهجية",
  User: "المستخدم", Language: "اللغة", English: "English", "تسجيل الخروج · Sign out": "تسجيل الخروج",
  Overview: "نظرة عامة", "Upload & Data Review": "الرفع ومراجعة البيانات", Classification: "تصنيف الحسابات", Assumptions: "الافتراضات",
  Statements: "القوائم المالية", Ratios: "النسب المالية", "Year comparison": "مقارنة السنوات", "Sources & Uses": "المصادر والاستخدامات",
  "Forecasting & Planning": "التنبؤ والتخطيط المالي", "AI Analyst": "المحلل الذكي", "Evaluation & Reports": "التقييم والتقارير", "Audit trail": "سجل التدقيق",
  "Loading…": "جارٍ التحميل…", "Search…": "بحث…", Save: "حفظ", Delete: "حذف", Compare: "مقارنة", Apply: "تطبيق", Calculate: "احسب",
  // companies page
  "New company": "شركة جديدة", Name: "الاسم", Industry: "القطاع", Currency: "العملة", Country: "الدولة", Create: "إنشاء",
  "Download template": "تحميل القالب", "Download 5-year sample": "تحميل نموذج لخمس سنوات", Standalone: "منفصلة", Consolidated: "مجمعة",
  "Academic methodology (course)": "المنهجية الأكاديمية (المقرر)", "Professional methodology": "المنهجية المهنية",
  "Workflow: Excel data entry → upload → validation → classification review → assumption confirmation → approval → multi-year analysis → interpretation → reports. Nothing is approved automatically.":
    "مسار العمل: إدخال البيانات في Excel ← الرفع ← التحقق ← مراجعة التصنيف ← تأكيد الافتراضات ← الاعتماد ← التحليل متعدد السنوات ← التفسير ← التقارير. لا يُعتمد أي شيء تلقائياً.",
  Years: "السنوات", "Pending assumptions": "افتراضات معلقة", "Data errors": "أخطاء البيانات", Status: "الحالة", "awaiting upload": "بانتظار الرفع",
  ready: "جاهز", "in review": "قيد المراجعة", "no data": "لا توجد بيانات",
  // benchmarks / compare / methodology
  "Benchmarks are configurable per industry. If none are set, ratio risk relies on the company's own trend and the limitation is stated in reports. Presets are clearly labelled — the course figures are teaching examples, not real industry data.":
    "المعايير قابلة للضبط لكل قطاع. إن لم تُضبط يعتمد تقييم المخاطر على اتجاه الشركة نفسها ويُذكر هذا القيد في التقارير. القيم الجاهزة موضحة بوضوح — أرقام المقرر أمثلة تعليمية وليست بيانات صناعة حقيقية.",
  "Add / update": "إضافة / تحديث", Presets: "قيم جاهزة", "Import (CSV / Excel: industry, ratio_key, value, source)": "استيراد (CSV / Excel: القطاع، مفتاح النسبة، القيمة، المصدر)",
  Value: "القيمة", Ratio: "النسبة", Source: "المصدر", "Value (ratios as decimals, e.g. 0.45 for 45%)": "القيمة (النسب كعدد عشري، مثلاً 0.45 لـ 45%)",
  "Reporting currency, methodology, year-end and basis are compatible.": "عملة التقرير والمنهجية ونهاية السنة وأساس القوائم متوافقة.",
  "Financial Methodology Database": "قاعدة بيانات المنهجية المالية",
  "Generated from the same registry the calculation engine executes. Academic = lectures & solved exams (default); Professional = additional industry practice; differences are documented and configurable through assumptions.":
    "مولّدة من نفس السجل الذي ينفذه محرك الحسابات. أكاديمي = المحاضرات والامتحانات المحلولة (الافتراضي)؛ مهني = ممارسات إضافية؛ والفروق موثقة وقابلة للضبط عبر الافتراضات.",
  Formula: "المعادلة", "Required accounts": "الحسابات المطلوبة", Classifications: "التصنيفات", Interpretation: "التفسير", Application: "التطبيق العملي",
  // workspace header / overview
  "reviews complete": "اكتملت المراجعات", "review in progress": "المراجعة جارية", "academic methodology": "المنهجية الأكاديمية",
  "professional methodology": "المنهجية المهنية", "currency ?": "العملة ؟",
  "Upload financial statements first (Upload & Data Review tab).": "ارفع القوائم المالية أولاً (تبويب الرفع ومراجعة البيانات).",
  "No data yet": "لا توجد بيانات بعد", "Download the Excel template, enter the statements for each year, then upload it.": "حمّل قالب Excel، وأدخل القوائم لكل سنة، ثم ارفعه.",
  "Go to upload": "انتقل إلى الرفع", "Reporting period": "الفترة المالية", "Classification approval": "اعتماد التصنيف", "Data validation": "التحقق من البيانات",
  "No errors": "لا أخطاء", "Review workflow — Upload → Review → Confirm → Analyze → Interpret → Report": "مسار المراجعة — رفع ← مراجعة ← تأكيد ← تحليل ← تفسير ← تقرير",
  "Assumptions confirmed": "تأكيد الافتراضات", "Analysis approval": "اعتماد التحليل", done: "تم", "action needed": "يلزم إجراء",
  "ready to approve": "جاهز للاعتماد", "blocked by pending reviews": "متوقف بسبب مراجعات معلقة", "Company profile": "بيانات الشركة", "Source file": "الملف المصدر",
  "Academic (lectures & solved exams)": "أكاديمي (المحاضرات والامتحانات المحلولة)", Professional: "مهني",
  "Changing methodology re-proposes pending assumptions; approved decisions are kept.": "تغيير المنهجية يعيد اقتراح الافتراضات المعلقة؛ والقرارات المعتمدة تبقى.",
  industry: "القطاع", country: "الدولة", currency: "العملة", "fy end": "نهاية السنة المالية", "reporting type": "نوع التقرير", basis: "أساس القوائم", standards: "المعايير",
  // upload & review
  "Upload Excel": "رفع ملف Excel", Template: "القالب", "5-year sample": "نموذج 5 سنوات", "Processing…": "جارٍ المعالجة…",
  "Re-uploading a revised file creates a new version. Original values are stored verbatim and are never modified; analyst decisions carry over to accounts with the same name.":
    "إعادة رفع ملف معدّل تنشئ نسخة جديدة. القيم الأصلية تُحفظ كما هي ولا تُعدّل؛ وقرارات المحلل تنتقل للحسابات بنفس الاسم.",
  "Data versions": "نسخ البيانات", Version: "النسخة", File: "الملف", Uploaded: "تاريخ الرفع", "SHA-256": "البصمة", Activate: "تفعيل", active: "نشطة",
  "Validation issues": "مشكلات التحقق", "No issues.": "لا توجد مشكلات.", Severity: "الخطورة", Code: "الكود", Message: "الرسالة", Location: "الموقع",
  Acknowledge: "تأكيد الاطلاع", acknowledged: "تم الاطلاع", "Reconciliation checks (depend on current classifications)": "فحوص المطابقة (تعتمد على التصنيفات الحالية)",
  "Search account…": "ابحث عن حساب…", "Sheet / row": "الورقة / الصف", "Original account": "الحساب الأصلي", "Original value": "القيمة الأصلية", Year: "السنة",
  "Suggested category": "التصنيف المقترح", Group: "المجموعة", Confidence: "الثقة", Validation: "التحقق", "Analyst decision": "قرار المحلل", "(opening)": "(أول المدة)",
  all: "الكل", valid: "سليم", warning: "تحذير", error: "خطأ", info: "معلومة", pending: "معلّق", approved: "معتمد", modified: "معدّل", rejected: "مرفوض",
  // classification
  "The engine suggests a category with its reasoning and confidence. Only approved/modified classifications are final; pending ones are used provisionally and every dependent result is labelled “provisional”. Rejected accounts are excluded from all calculations.":
    "يقترح المحرك تصنيفاً مع سببه ودرجة الثقة. التصنيفات المعتمدة/المعدلة فقط نهائية؛ والمعلقة تُستخدم مبدئياً وتُوسم كل نتيجة تعتمد عليها بأنها «مبدئية». الحسابات المرفوضة تُستبعد من كل الحسابات.",
  "Needs answer": "تحتاج إجابة", "All statements": "كل القوائم", "Balance sheet": "الميزانية", "Income statement": "قائمة الدخل", "Cash flow": "التدفقات النقدية",
  "Approve all high-confidence (≥85%, no open question) in view": "اعتماد كل المقترحات عالية الثقة (≥85% وبلا سؤال مفتوح) في العرض",
  "Nothing in this view.": "لا يوجد شيء في هذا العرض.", "carried over from previous version": "منقول من النسخة السابقة", Suggestion: "المقترح",
  Why: "السبب", "Approved classification": "التصنيف المعتمد", "Used in": "يُستخدم في", Question: "سؤال", Approve: "اعتماد", "Modify…": "تعديل…",
  Reject: "رفض", "Request info": "طلب معلومات", "Approve + Apply to similar": "اعتماد + تطبيق على المشابه", Reopen: "إعادة فتح",
  "Reconciliation only (subtotal — never added to aggregates)": "للمطابقة فقط (إجمالي فرعي — لا يُضاف للمجاميع)", "No ratio directly": "لا يدخل في نسبة مباشرة",
  // assumptions
  "Every assumption is explicit: proposed value, reason, supporting data, alternatives, and the numerical impact of each alternative on the latest year. Results that use an unconfirmed assumption are labelled provisional.":
    "كل افتراض معروض صراحة: القيمة المقترحة، والسبب، والبيانات الداعمة، والبدائل، والأثر الرقمي لكل بديل على آخر سنة. النتائج التي تستخدم افتراضاً غير مؤكد توسم بأنها مبدئية.",
  "Show assumptions not relevant to this data set": "إظهار الافتراضات غير المطلوبة لهذه البيانات", critical: "جوهري", "not needed for this data": "غير مطلوب لهذه البيانات",
  "Proposed value": "القيمة المقترحة", "Current value": "القيمة الحالية", Reason: "السبب", "Supporting data": "البيانات الداعمة", "Analyst note": "ملاحظة المحلل",
  Decided: "تاريخ القرار", Alternative: "البديل", Effect: "الأثر", "Use this": "استخدم هذا", "Accept proposed": "قبول المقترح", accepted: "مقبول",
  // statements / ratios / comparison
  "Balance Sheet": "الميزانية", "Income Statement": "قائمة الدخل", "Cash Flow": "التدفقات النقدية", Values: "القيم", "% change (YoY)": "التغير السنوي %",
  "% of total assets": "% من إجمالي الأصول", "% of sales": "% من المبيعات", "Filter accounts…": "تصفية الحسابات…",
  "Accounts as uploaded (original names) — click a row to drill down": "الحسابات كما رُفعت (بأسمائها الأصلية) — اضغط على أي صف للتفاصيل",
  Account: "الحساب", Trend: "الاتجاه", CAGR: "معدل النمو المركب", "AI notes": "ملاحظات الذكاء الاصطناعي", "n/m": "غير ذي معنى",
  "Subtotals are shown in italics; they are used to reconcile, never added. “n/m” = not meaningful (zero base or non-positive values); “±” = sign change.":
    "الإجماليات الفرعية بخط مائل؛ للمطابقة فقط ولا تُضاف. «غير ذي معنى» = أساس صفري أو قيم غير موجبة؛ «±» = تغير الإشارة.",
  "Standardised lines (computed from approved classifications)": "البنود الموحدة (محسوبة من التصنيفات المعتمدة)", Line: "البند",
  "Used in calculations": "يُستخدم في الحسابات", Normalization: "التعديل", "AI observations": "ملاحظات المحلل الذكي", Original: "الأصلية", Normalized: "المعدّلة",
  "Common size": "النسبة الرأسية", Highest: "الأعلى", Lowest: "الأدنى", Average: "المتوسط", "Cumulative change": "التغير التراكمي", Yes: "نعم", No: "لا",
  All: "الكل", Liquidity: "السيولة", "Activity & efficiency": "النشاط والكفاءة", Profitability: "الربحية", DuPont: "ديبونت",
  "Solvency & financial structure": "الملاءة والهيكل المالي", "Modern techniques & market": "الأساليب الحديثة والسوق", "Break-even & operating leverage": "التعادل والرافعة التشغيلية",
  "Click any value to see the formula, inputs, original accounts, assumptions and status. Status legend:": "اضغط على أي قيمة لرؤية المعادلة والمدخلات والحسابات الأصلية والافتراضات والحالة. دلالات الحالة:",
  Method: "المنهج", YoY: "التغير السنوي", Benchmark: "المعيار", Risk: "المخاطر", Assessment: "التقييم", "Risk basis": "أساس المخاطر", "Suggested action": "الإجراء المقترح",
  academic: "أكاديمي", professional: "مهني", both: "كلاهما", verified: "مُتحقق", "approved assumption": "افتراض معتمد", provisional: "مبدئي",
  "needs info": "يحتاج معلومات", invalid: "غير صالح", "info requested": "طلب معلومات", Low: "منخفض", Medium: "متوسط", High: "مرتفع", "n/a": "غير متاح",
  "Academic interpretation (professor's method)": "التفسير الأكاديمي (منهج الأستاذ)", "Show 7-step interpretation": "عرض التفسير بالخطوات السبع",
  "Hide interpretation": "إخفاء التفسير", favorable: "إيجابي", unfavorable: "سلبي", mixed: "مختلط", neutral: "محايد",
  "Multi-year comparison — horizontal analysis": "مقارنة متعددة السنوات — التحليل الأفقي", Item: "البند", Cumulative: "تراكمي", Trend_: "الاتجاه",
  "Percentage change = (current − previous) / |previous|. CAGR is shown only when the first and last values are positive. Gaps and sign changes are flagged rather than shown as misleading growth.":
    "التغير % = (الحالي − السابق) / |السابق|. معدل النمو المركب يظهر فقط عندما تكون القيمتان الأولى والأخيرة موجبتين. الفجوات وتغير الإشارة يُنبَّه عليها بدل إظهار نمو مضلل.",
  "Vertical analysis — financial structure": "التحليل الرأسي — الهيكل المالي", Base: "الأساس", "Revenue & profit": "الإيرادات والأرباح",
  "Financial structure": "الهيكل المالي", "Working capital items": "بنود رأس المال العامل", Leverage: "الرافعة", Days: "الأيام", Efficiency: "الكفاءة",
  Sales: "المبيعات", "Gross profit": "مجمل الربح", "Net profit": "صافي الربح",
  // sources & uses
  "At least two years of balance sheets are needed.": "يلزم وجود ميزانيتين لسنتين على الأقل.", "Short-term sources / uses": "المصادر / الاستخدامات قصيرة الأجل",
  "Long-term sources / uses": "المصادر / الاستخدامات طويلة الأجل", "Golden-rule deviation": "الانحراف عن القاعدة الذهبية", "|ST sources% − ST uses%|": "|المصادر قصيرة الأجل% − الاستخدامات قصيرة الأجل%|",
  "Internal / external finance": "التمويل الداخلي / الخارجي", Sources: "المصادر", Uses: "الاستخدامات", Movement: "الحركة", Term: "الأجل", Amount: "المبلغ",
  "Full movement table": "جدول الحركة الكامل", Change: "التغير", "Source / use": "مصدر / استخدام", "no change": "لا تغيير", source: "مصدر", use: "استخدام",
  short: "قصير", long: "طويل", internal: "داخلي", external: "خارجي",
  "Rules (Lecture 2, Q3): asset increase = use, asset decrease = source; liability/equity increase = source, decrease = use; accumulated depreciation increase = source.":
    "القواعد (المحاضرة 2، السؤال 3): زيادة الأصل = استخدام، ونقصه = مصدر؛ زيادة الخصوم/حقوق الملكية = مصدر، ونقصها = استخدام؛ زيادة مجمع الإهلاك = مصدر.",
  "Analysis (professor's method)": "التحليل (منهج الأستاذ)",
  // AI analyst
  "The analyst reviews the uploaded company's actual data at three levels. All numbers come from the deterministic engine; explanations are labelled as hypotheses until confirmed.":
    "يراجع المحلل بيانات الشركة الفعلية على ثلاثة مستويات. كل الأرقام من محرك الحسابات؛ والتفسيرات توسم كفرضيات حتى تتأكد.",
  "Level 1 — accounts": "المستوى 1 — الحسابات", "Level 2 — relationships": "المستوى 2 — العلاقات", "Level 3 — overall": "المستوى 3 — الصورة الكلية",
  "No observations at this level.": "لا توجد ملاحظات في هذا المستوى.", "Comparison period": "فترة المقارنة", Reasoning: "التعليل", "Possible explanation": "التفسير المحتمل",
  "(unverified)": "(غير مؤكد)", "Financial impact": "الأثر المالي", "Required action": "الإجراء المطلوب", "Ask the financial analyst": "اسأل المحلل المالي",
  "Answers are written by Claude from the verified results only.": "يكتب Claude الإجابات من النتائج المُتحقق منها فقط.",
  "Claude is not configured (set ANTHROPIC_API_KEY on the server). Answers fall back to the matching deterministic findings.": "Claude غير مفعّل على الخادم. ستُعرض الملاحظات المطابقة من محرك التحليل بدلاً منه.",
  "e.g. Why did liquidity weaken in the last year?": "مثال: لماذا ضعفت السيولة في السنة الأخيرة؟", Ask: "اسأل", "Thinking…": "جارٍ التفكير…",
  // evaluation & reports
  "Approval & export": "الاعتماد والتصدير", "Approve analysis": "اعتماد التحليل", "Report content": "محتوى التقرير", "Export Excel": "تصدير Excel", "Export PDF": "تصدير PDF",
  "Report language": "لغة التقرير", "Final financial evaluation": "التقييم المالي النهائي", Area: "المجال", Rating: "التقييم", "Key indicators (latest)": "المؤشرات الرئيسية (آخر سنة)",
  "Historical performance": "الأداء التاريخي", Strengths: "نقاط القوة", Weaknesses: "نقاط الضعف", Risks: "المخاطر", Recommendations: "التوصيات", Limitations: "القيود",
  "None identified.": "لا يوجد.", "Analysis approved and frozen as a snapshot.": "تم اعتماد التحليل وحفظه كنسخة ثابتة.",
  " — results below are not final until approved.": " — النتائج أدناه ليست نهائية حتى الاعتماد.",
  "The report always reflects the current approved data, classifications and assumptions; it is regenerated on every download.":
    "يعكس التقرير دائماً البيانات والتصنيفات والافتراضات المعتمدة الحالية؛ ويُعاد إنشاؤه عند كل تحميل.",
  profile: "بيانات الشركة", statements: "القوائم المالية", horizontal: "التحليل الأفقي", vertical: "التحليل الرأسي", ratios: "النسب المالية",
  interpretation_academic: "التفسير الأكاديمي", comparison: "المقارنة", "sources uses": "المصادر والاستخدامات", interpretation: "التقييم والتفسير",
  risks: "المخاطر", recommendations: "التوصيات", assumptions: "الافتراضات", "interpretation academic": "التفسير الأكاديمي",
  // audit
  Time: "الوقت", Action: "الإجراء", Entity: "الكيان", Before: "قبل", After: "بعد", Detail: "التفاصيل",
  // trace modal
  Result: "النتيجة", "Why this status": "سبب الحالة", "Calculation notes": "ملاحظات الحساب", "Assumptions applied": "الافتراضات المطبقة",
  "No assumptions involved in this calculation.": "لا توجد افتراضات في هذا الحساب.", "Inputs and underlying accounts": "المدخلات والحسابات الأساسية",
  "Original account / component": "الحساب الأصلي / المكوّن", "Classification used": "التصنيف المستخدم", aggregate: "مجموع", Additional_Info: "معلومات إضافية",
  // forecasting
  "Forecasted financial position": "المركز المالي المتوقع", "% of sales (AFN)": "نسبة من المبيعات (AFN)", "Cash budget": "الموازنة النقدية",
  "Forecasted financial position method (Lecture 5, Q4)": "طريقة المركز المالي المتوقع (المحاضرة 5، السؤال 4)",
  "Stage 1 grows the sales-related lines; the gap between assets and liabilities + equity is financed by the hierarchy; the new interest and dividends are fed back, and stages repeat until the gap is about zero.":
    "في المرحلة الأولى تنمو البنود المرتبطة بالمبيعات؛ والفجوة بين الأصول والخصوم + حقوق الملكية تُمول بالهيكل التمويلي؛ ثم تُضاف الفوائد والتوزيعات الجديدة وتتكرر المراحل حتى تقترب الفجوة من الصفر.",
  "Sales growth %": "نمو المبيعات %", "Tax rate %": "معدل الضريبة %", "Preferred dividends": "توزيعات الأسهم الممتازة", "Common shares outstanding": "عدد الأسهم العادية",
  "Last dividend per share": "آخر توزيع للسهم", "Promised DPS growth %": "نمو التوزيع الموعود للسهم %", "Share price for new issue": "سعر السهم للإصدار الجديد",
  "EVA opportunity rate on R/E %": "معدل تكلفة الفرصة على الأرباح المحتجزة %", "Financial hierarchy": "الهيكل التمويلي", "Share %": "النسبة %",
  "Annual interest %": "الفائدة السنوية %", Total: "الإجمالي", "Semi-annual rates: enter twice the rate (Q4: 4.5% twice yearly = 9%).": "المعدلات نصف السنوية: أدخل ضعف المعدل (السؤال 4: 4.5% مرتين سنوياً = 9%).",
  "Round every line to whole units at each stage (like the hand-worked solutions)": "تقريب كل بند لأعداد صحيحة في كل مرحلة (مثل الحلول اليدوية)",
  "Run forecast": "تشغيل التنبؤ", "First-stage financing need": "الاحتياج التمويلي في المرحلة الأولى", "Net profit: actual → forecast": "صافي الربح: الفعلي ← المتوقع",
  "EVA: before → after": "القيمة الاقتصادية المضافة: قبل ← بعد", "New shares issued": "الأسهم الجديدة المصدرة", "Income statement by stage": "قائمة الدخل حسب المرحلة",
  Actual: "الفعلي", Rule: "القاعدة", "Financial position by stage": "المركز المالي حسب المرحلة", "Rule (last stage)": "القاعدة (آخر مرحلة)",
  "Total assets": "إجمالي الأصول", "Total liabilities & equity": "إجمالي الخصوم وحقوق الملكية", "Financing need": "الاحتياج التمويلي",
  "How each stage's need is financed": "كيف يُمول احتياج كل مرحلة", Stage: "المرحلة", "New interest": "الفوائد الجديدة", "New shares": "الأسهم الجديدة",
  "Short-term debt / N/P": "ديون قصيرة الأجل / أوراق دفع", "Long-term bonds / loans": "سندات / قروض طويلة الأجل", "Common shares": "الأسهم العادية",
  "Percentage of sales method (Lecture 6)": "طريقة نسبة من المبيعات (المحاضرة 6)", "Actual sales S1": "المبيعات الفعلية S1", "Proposed sales S2": "المبيعات المقترحة S2",
  "Net profit margin %": "هامش صافي الربح %", "Dividend payout %": "نسبة التوزيع %", "AFN financed by": "يُمول الاحتياج عن طريق", "Short-term debt": "ديون قصيرة الأجل",
  "Long-term debt": "ديون طويلة الأجل", Equity: "حقوق الملكية", "Financial sources needed (AFN)": "المصادر المالية المطلوبة (AFN)",
  "Sales with no external finance (AFN = 0)": "المبيعات بلا تمويل خارجي (AFN = 0)", "Current ratio before → after": "نسبة التداول قبل ← بعد",
  "Debt ratio before → after": "نسبة المديونية قبل ← بعد", "% of S1": "% من S1", Projected: "المتوقع", "Liabilities & equity before new finance": "الخصوم وحقوق الملكية قبل التمويل الجديد",
  "Break-even & operating leverage (Lecture 8)": "التعادل والرافعة التشغيلية (المحاضرة 8)", "Total fixed costs": "إجمالي التكاليف الثابتة", "Selling price per unit": "سعر بيع الوحدة",
  "Average variable cost per unit": "متوسط التكلفة المتغيرة للوحدة", "Current units produced": "الوحدات المنتجة حالياً", "Total variable costs": "إجمالي التكاليف المتغيرة",
  "Break-even units": "وحدات التعادل", "Break-even sales": "مبيعات التعادل", "Operating profit at current level": "ربح التشغيل عند المستوى الحالي",
  "Margin of safety": "هامش الأمان", "Degree of operating leverage": "درجة الرافعة التشغيلية", "Break-even chart": "خريطة التعادل",
  "High fixed costs relative to total costs mean high operating leverage: a small change in sales causes a large change in operating profit.":
    "ارتفاع التكاليف الثابتة نسبةً للتكاليف الكلية يعني رافعة تشغيلية مرتفعة: تغير صغير في المبيعات يسبب تغيراً كبيراً في ربح التشغيل.",
  "Cash-flow forecast / master budget (Lecture 7)": "التنبؤ بالتدفقات النقدية / الموازنة الشاملة (المحاضرة 7)", "Cash sales %": "المبيعات النقدية %",
  "Credit collected after 1 month %": "تحصيل الآجل بعد شهر %", "after 2 months %": "بعد شهرين %", "Opening cash": "نقدية أول المدة", "Minimum cash": "الحد الأدنى للنقدية",
  "History months": "أشهر سابقة", Input: "المدخل", "Other receipts (e.g. asset sales)": "متحصلات أخرى (مثل بيع أصول)", "+ Month": "+ شهر", "+ Payment line": "+ بند مدفوعات",
  "Forecasted cash-flow statement": "قائمة التدفقات النقدية المتوقعة", "Cash sales": "المبيعات النقدية", "Other receipts": "متحصلات أخرى", "Revenues (receipts)": "الإيرادات (المتحصلات)",
  Expenditures: "المصروفات", Net: "الصافي", Balance: "الرصيد", "Surplus / (deficit)": "الفائض / (العجز)", BEP: "نقطة التعادل",
  Purchases: "المشتريات", Salaries: "الرواتب", Overheads: "المصروفات العامة", "Capital investment": "الاستثمار الرأسمالي", Dividends: "التوزيعات", Taxes: "الضرائب",
  EBIT: "EBIT", Interest: "الفوائد", EBT: "EBT", "P.S. dividends": "توزيعات الأسهم الممتازة", "Net distributable profit": "صافي الربح القابل للتوزيع",
  "C.S. dividends": "توزيعات الأسهم العادية", "Retained earnings for the year": "الأرباح المحتجزة للعام", EVA: "القيمة الاقتصادية المضافة",
  Side: "الجانب", "Latest value": "آخر قيمة", "Grows with sales": "ينمو مع المبيعات", Role: "الدور", Type: "النوع", Asset: "أصل", Liability: "التزام",
  "Short-term debt (financing target)": "ديون قصيرة الأجل (هدف التمويل)", "Long-term debt (financing target)": "ديون طويلة الأجل (هدف التمويل)",
  "Common shares (financing target)": "أسهم عادية (هدف التمويل)", "Retained earnings": "الأرباح المحتجزة", "Total revenue": "الإيرادات الكلية", "Total cost": "التكلفة الكلية", "Fixed cost": "التكلفة الثابتة",
  "Units: Q = FC / (P − AVC)": "بالوحدات: Q = FC / (P − AVC)", "Value: TFC / (1 − VC / Sales)": "بالقيمة: TFC / (1 − VC / المبيعات)",
  "financial years · data v": "سنوات مالية · نسخة البيانات",
  "Validation issues (": "مشكلات التحقق (",
  "Data Review Center — extracted items (v": "مركز مراجعة البيانات — البنود المستخرجة (نسخة ",
  "Impact on": "الأثر على",
  "Affects:": "يؤثر على:",
  "Values shown use": "القيم المعروضة تستخدم",
  "assumptions.": "افتراضات.",
  "Audit trail (": "سجل التدقيق (",
  "Opening (": "أول المدة (",
  "Closing (": "آخر المدة (",
  "Line (": "البند (",
  "balance sheet": "الميزانية",
  "income statement": "قائمة الدخل",
  "Current interest (": "الفوائد الحالية (",
  "Some starting accounts are not yet approved, so the starting point itself is provisional.": "بعض حسابات البداية لم تُعتمد بعد، لذا فنقطة البداية نفسها مبدئية.",
  "Scenarios are planning tools: they start from the": "السيناريوهات أدوات تخطيط: تبدأ من أرقام",
  "figures but never change the uploaded or approved data.": "لكنها لا تغير البيانات المرفوعة أو المعتمدة أبداً.",
  "Starting lines from": "بنود البداية من",
  "(edit growth rules, roles or values)": "(عدّل قواعد النمو أو الأدوار أو القيم)",
  "approved ·": "معتمد ·",
  "modified ·": "معدّل ·",
  "rejected ·": "مرفوض ·",
  "open warnings ·": "تحذيرات مفتوحة ·",
  "warnings": "تحذيرات",
  "errors ·": "أخطاء ·",
  "Level": "المستوى",
  "confidence:": "الثقة:",
  "· confidence": "· الثقة",
  "— results below are not final until approved.": "— النتائج أدناه ليست نهائية حتى الاعتماد.",
  "methodology": "المنهجية",
  "(uploaded": "(تاريخ الرفع",
  "revenue": "إيراد",
  "expense": "مصروف",
  "other_income": "إيراد آخر",
  "computed": "محسوب",
  "derived": "مشتق",
  "Subtotal": "إجمالي فرعي",
  "Revenue": "إيرادات",
  "Expense": "مصروفات",
  "Other": "أخرى",
  "CashFlow": "تدفقات نقدية",
  "All years": "كل السنوات",
  "Current": "متداول",
  "Non-Current": "غير متداول",
  "Operating": "تشغيلي",
  "Non-Operating": "غير تشغيلي",
  "Financing": "تمويلي",
  "Investing": "استثماري",
  "upload": "رفع",
  "create": "إنشاء",
  "company": "شركة",
  "approve": "اعتماد",
  "modify": "تعديل",
  "reject": "رفض",
  "classification": "تصنيف",
  "assumption": "افتراض",
  "Lead Analyst": "المحلل الرئيسي",
  "Financial Analyst": "محلل مالي",
  "Reviewer": "المراجع",
  "Management (view only)": "الإدارة (عرض فقط)",
  "admin": "مسؤول",
  "analyst": "محلل",
  "reviewer": "مراجع",
  "viewer": "مشاهد",
  "Manufacturing": "الصناعة التحويلية",
  "Retail": "التجزئة",
  "Services": "الخدمات",
  "Construction": "المقاولات",
  "Technology": "التكنولوجيا",
  "Trading": "التجارة",
  "Egypt": "مصر",
  "Audited financial statements": "قوائم مالية مدققة",
  "Cost of goods sold.": "تكلفة المبيعات.",
  "Income tax expense.": "مصروف ضريبة الدخل.",
  "Lecture 3, slide 2.": "المحاضرة 3، الشريحة 2.",
  Password: "كلمة المرور", "Years:": "السنوات:", "Modules:": "المحتويات:", "Industry:": "القطاع:",
};

// Sentences with numbers or names
export const AR_UI_PATTERNS: [RegExp, string][] = [
  [/^Pending \((\d+)\)$/, "قيد الانتظار ($1)"], [/^Approved \((\d+)\)$/, "معتمد ($1)"], [/^Modified \((\d+)\)$/, "معدّل ($1)"],
  [/^Rejected \((\d+)\)$/, "مرفوض ($1)"], [/^All \((\d+)\)$/, "الكل ($1)"],
  [/^(\d+) financial years · data v(\d+)$/, "$1 سنوات مالية · نسخة البيانات $2"],
  [/^(\d+) approved · (\d+) modified · (\d+) rejected · (\d+) pending$/, "$1 معتمد · $2 معدّل · $3 مرفوض · $4 معلّق"],
  [/^(\d+)\/(\d+) decided$/, "تم البت في $1 من $2"], [/^(\d+) pending$/, "$1 معلّق"], [/^(\d+) errors · (\d+) warnings$/, "$1 أخطاء · $2 تحذيرات"],
  [/^(\d+) open warnings · (\d+) info$/, "$1 تحذيرات مفتوحة · $2 معلومات"], [/^(\d+) errors$/, "$1 أخطاء"], [/^(\d+) rows$/, "$1 صف"],
  [/^Stage (\d+)$/, "المرحلة $1"], [/^After stage (\d+)$/, "بعد المرحلة $1"], [/^Level (\d+)$/, "المستوى $1"], [/^confidence: (.+)$/, "الثقة: $1"],
  [/^Δ% (\d{4})$/, "التغير % $1"], [/^Impact on (\d{4})$/, "الأثر على $1"], [/^Affects: (.*)$/, "يؤثر على: $1"], [/^Excel hint: (.+)$/, "مؤشر Excel: $1"],
  [/^Opening \((\d{4})\)$/, "أول المدة ($1)"], [/^Closing \((\d{4})\)$/, "آخر المدة ($1)"], [/^Status (\d{4})$/, "الحالة $1"],
  [/^DuPont (\d{4})$/, "ديبونت $1"],
  [/^Total sources (.+) = total uses (.+) — reconciled\.$/, "إجمالي المصادر $1 = إجمالي الاستخدامات $2 — متطابق."],
  [/^Total sources (.+) ≠ total uses (.+) \(difference (.+)\) — check classifications\.$/, "إجمالي المصادر $1 ≠ إجمالي الاستخدامات $2 (الفرق $3) — راجع التصنيفات."],
  [/^Uploaded as version (\d+): years (.+), (\d+) new accounts, issues (.*)$/, "رُفع كنسخة $1: السنوات $2، $3 حساب جديد، المشكلات $4"],
  [/^Starting lines from (\d{4}) \(edit growth rules, roles or values\)$/, "بنود البداية من $1 (عدّل قواعد النمو أو الأدوار أو القيم)"],
  [/^Balance-sheet lines from (\d{4})$/, "بنود الميزانية من $1"],
  [/^Blocked: (\d+) pending classifications, (\d+) pending assumptions, (\d+) data errors\.$/, "متوقف: $1 تصنيفات معلقة، $2 افتراضات معلقة، $3 أخطاء بيانات."],
  [/^Largest deficit: (.+) — the short-term financing to arrange in advance\.$/, "أكبر عجز: $1 — التمويل قصير الأجل الذي يجب ترتيبه مسبقاً."],
  [/^Pre-filled from Additional_Info \((\d{4})\)\.$/, "معبأ مسبقاً من المعلومات الإضافية ($1)."],
  [/^Scenarios are planning tools: they start from the (\d{4}) figures but never change the uploaded or approved data\.(.*)$/,
    "السيناريوهات أدوات تخطيط: تبدأ من أرقام $1 لكنها لا تغير البيانات المرفوعة أو المعتمدة أبداً."],
  [/^Balanced after (\d+) stage\(s\): total assets (.+) = liabilities \+ equity (.+)\.$/, "توازن بعد $1 مرحلة: إجمالي الأصول $2 = الخصوم + حقوق الملكية $3."],
];

export function translateText(s: string): string | null {
  const core = s.trim();
  if (!core) return null;
  const hit = AR_UI[core];
  if (hit !== undefined) return s.replace(core, hit);
  for (const [rx, rep] of AR_UI_PATTERNS) if (rx.test(core)) return s.replace(core, core.replace(rx, rep));
  return null;
}

const ATTRS = ["placeholder", "title", "aria-label"];

function translateNode(n: Node) {
  if (n.nodeType === Node.TEXT_NODE) {
    const p = (n as Text).parentElement;
    if (p && (p.closest("[data-no-translate]") || ["SCRIPT", "STYLE", "TEXTAREA"].includes(p.tagName))) return;
    const t = translateText(n.nodeValue || "");
    if (t !== null && t !== n.nodeValue) n.nodeValue = t;
    return;
  }
  if (n.nodeType !== Node.ELEMENT_NODE) return;
  const el = n as Element;
  if (el.closest("[data-no-translate]")) return;
  for (const a of ATTRS) {
    const v = el.getAttribute(a);
    if (v) { const t = translateText(v); if (t !== null && t !== v) el.setAttribute(a, t); }
  }
  if (el.tagName === "OPTION") { const t = translateText(el.textContent || ""); if (t !== null) el.textContent = t; return; }
  el.childNodes.forEach(translateNode);
}

let observer: MutationObserver | null = null;
/** Translate the whole page now and keep translating whatever React renders next. */
export function startArabic(root: HTMLElement) {
  stopArabic();
  translateNode(root);
  observer = new MutationObserver((muts) => {
    for (const m of muts) {
      if (m.type === "characterData") translateNode(m.target);
      else if (m.type === "attributes") translateNode(m.target);
      else m.addedNodes.forEach(translateNode);
    }
  });
  observer.observe(root, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ATTRS });
}
export function stopArabic() { observer?.disconnect(); observer = null; }
