"""Academic interpretation engine — reproduces the professor's interpretation method (Q1, Q3, Q5 solutions, Lecture 3).

His pattern for every ratio:
  ratio = formula = numbers = result
  Interpretation: "Every unit of <denominator> generates / covers / backs up <result> units of <numerator>"
  Analysis:       "∵ ratio(firm) </> ratio(industry average or previous year)  ∴ <meaning>"
  Conclusion:     "Accordingly, … we do recommend <firm> to …"

The 7 steps required by the platform (result, comparison, direction, meaning, favourable?, impact, conclusion) follow that
sequence. Only calculated values are used. Ratios not covered in the lectures are labelled 'professional interpretation'.
"""
from __future__ import annotations

from .engine.analysis import fmt
from .engine.ratios import BY_KEY as RATIO_BY_KEY

# ------------------------------------------------------------------ the professor's "every unit of …" sentences
# (en, ar) with {v} = formatted value
UNIT_SENTENCE = {
    "current_ratio": ("Every 1 unit of current liabilities is covered (backed up) by {v} units of current assets.",
                      "كل وحدة واحدة من الخصوم المتداولة مغطاة (مدعومة) بـ {v} وحدة من الأصول المتداولة."),
    "quick_ratio": ("Excluding inventory, every 1 unit of current liabilities is covered by {v} units of quick assets.",
                    "باستبعاد المخزون، كل وحدة من الخصوم المتداولة مغطاة بـ {v} وحدة من الأصول سريعة التحويل لنقدية."),
    "cash_ratio": ("Every 1 unit of current liabilities is covered by {v} units of cash in kind.",
                   "كل وحدة من الخصوم المتداولة مغطاة بـ {v} وحدة من النقدية وما في حكمها."),
    "working_capital": ("Net short-term resources (current assets − current liabilities) amount to {v}.",
                        "صافي الموارد قصيرة الأجل (الأصول المتداولة − الخصوم المتداولة) يبلغ {v}."),
    "acp": ("The firm collects its receivables on average every {v}.", "تحصّل الشركة مديونياتها في المتوسط كل {v}."),
    "asp": ("The firm sells its inventory on average every {v}.", "تبيع الشركة مخزونها في المتوسط كل {v}."),
    "liquidity_of_inventory": ("The total time needed to purchase, manufacture, sell the finished products and collect what has been sold is {v}.",
                               "الوقت الكلي اللازم للشراء والتصنيع وبيع المنتج التام وتحصيل قيمة ما تم بيعه هو {v}."),
    "debt_ratio": ("{v} of the firm's total assets are financed by debts.", "{v} من إجمالي أصول الشركة ممولة بالديون."),
    "debt_equity": ("There are {v} units of debt for every 1 unit of equity.", "يوجد {v} وحدة من الديون مقابل كل وحدة من حقوق الملكية."),
    "capital_structure_ratio": ("{v} of the long-term capital comes from long-term liabilities.",
                                "{v} من رأس المال طويل الأجل مصدره الخصوم طويلة الأجل."),
    "interest_coverage": ("EBIT covers the interest expense {v} times.", "الربح قبل الفوائد والضرائب يغطي مصروف الفوائد {v} مرة."),
    "tato": ("Every unit of total assets yields (generates) {v} units of sales.", "كل وحدة من إجمالي الأصول تولّد {v} وحدة من المبيعات."),
    "tato_credit": ("Every unit of total assets generates {v} units of credit sales.", "كل وحدة من إجمالي الأصول تولّد {v} وحدة من المبيعات الآجلة."),
    "tato_cash": ("Every unit of total assets generates {v} units of cash sales.", "كل وحدة من إجمالي الأصول تولّد {v} وحدة من المبيعات النقدية."),
    "fato": ("Every unit of fixed assets generates {v} units of sales.", "كل وحدة من الأصول الثابتة تولّد {v} وحدة من المبيعات."),
    "cato": ("Every unit of current assets generates {v} units of sales.", "كل وحدة من الأصول المتداولة تولّد {v} وحدة من المبيعات."),
    "cash_turnover": ("Sales are {v} times the cash balance.", "المبيعات تعادل {v} مرة رصيد النقدية."),
    "ar_turnover": ("Receivables are collected and renewed {v} times a year.", "تُحصَّل المديونيات وتتجدد {v} مرة في السنة."),
    "inventory_turnover": ("Inventory is sold and replaced {v} times a year.", "يُباع المخزون ويُستبدل {v} مرة في السنة."),
    "gpm": ("Every unit of sales generates {v} of gross profit.", "كل وحدة من المبيعات تحقق {v} مجمل ربح."),
    "oim": ("Every unit of sales generates {v} of operating income (EBIT).", "كل وحدة من المبيعات تحقق {v} دخلاً تشغيلياً (EBIT)."),
    "nim": ("Every unit of sales leaves {v} of net income.", "كل وحدة من المبيعات تترك {v} صافي ربح."),
    "roi": ("Every unit invested in total assets earns {v} before interest and tax.", "كل وحدة مستثمرة في إجمالي الأصول تحقق {v} قبل الفوائد والضرائب."),
    "roe": ("Every unit of owners' equity earns {v}.", "كل وحدة من حقوق الملكية تحقق عائداً قدره {v}."),
    "robf": ("Borrowed funds add {v} to the return on equity.", "الأموال المقترضة تضيف {v} إلى العائد على حقوق الملكية."),
    "eva": ("After charging the cost of every source of finance, the firm created economic value of {v}.",
            "بعد خصم تكلفة كل مصادر التمويل، حققت الشركة قيمة اقتصادية مضافة قدرها {v}."),
    "mva": ("The market values the owners' equity at {v} above its book value.", "يقيّم السوق حقوق الملكية بـ {v} فوق قيمتها الدفترية."),
    "best_liquidity_measure": ("{v} is the most reliable liquidity measure for this year.", "{v} هي أفضل مقياس للسيولة في هذه السنة."),
    "roe_identity": ("ROI + ROBF = {v}; this equals EBT / equity exactly when BF = total liabilities and OE = total equity.",
                     "ROI + ROBF = {v}؛ ويساوي EBT / حقوق الملكية تماماً عندما BF = إجمالي الخصوم وOE = إجمالي حقوق الملكية."),
    "dupont_roi": ("ROI of {v} = profitability (OIM) × efficiency (TATO).", "العائد على الاستثمار {v} = الربحية (هامش التشغيل) × الكفاءة (دوران الأصول)."),
    "bvps": ("Book value per share is {v}.", "القيمة الدفترية للسهم {v}."), "eps": ("Each common share earned {v}.", "كل سهم عادي حقق ربحاً قدره {v}."),
    "ocf": ("Operations generated {v} in cash.", "ولّدت العمليات التشغيلية نقدية قدرها {v}."),
    "icf": ("Investing activities produced {v}.", "صافي التدفق من الأنشطة الاستثمارية {v}."),
    "fincf": ("Financing activities produced {v}.", "صافي التدفق من الأنشطة التمويلية {v}."),
    "fcf": ("After investing in fixed assets, {v} of cash remains.", "بعد الاستثمار في الأصول الثابتة يتبقى {v} نقدية حرة."),
    "ocf_ratio": ("Operating cash flow covers current liabilities {v} times.", "التدفق النقدي التشغيلي يغطي الخصوم المتداولة {v} مرة."),
    "ocf_to_np": ("Each unit of net profit is backed by {v} units of operating cash.", "كل وحدة من صافي الربح مدعومة بـ {v} وحدة نقدية تشغيلية."),
    "ocf_to_debt": ("Operating cash flow covers {v} of total debts per year.", "التدفق النقدي التشغيلي يغطي {v} من إجمالي الديون سنوياً."),
    "bep_sales": ("Sales of {v} are needed to cover all costs.", "يلزم تحقيق مبيعات قدرها {v} لتغطية كل التكاليف."),
    "margin_of_safety": ("Sales can fall {v} before losses begin.", "يمكن أن تنخفض المبيعات {v} قبل أن تبدأ الخسائر."),
    "dol": ("A 1% change in sales changes operating profit by {v}%.", "تغير المبيعات بنسبة 1% يغير ربح التشغيل بنسبة {v}%."),
    "equity_ratio": ("{v} of assets are financed by owners.", "{v} من الأصول ممولة من الملاك."),
    "financial_leverage": ("Each unit of equity supports {v} units of assets.", "كل وحدة من حقوق الملكية تدعم {v} وحدة من الأصول."),
    "lt_debt_ratio": ("{v} of assets are financed by long-term liabilities.", "{v} من الأصول ممولة بخصوم طويلة الأجل."),
    "payables_turnover": ("Suppliers are paid {v} times a year.", "يُسدَّد للموردين {v} مرة في السنة."),
    "app": ("Suppliers are paid on average after {v}.", "يُسدَّد للموردين في المتوسط بعد {v}."),
    "ccc": ("Cash is tied up in operations for {v} after paying suppliers.", "تبقى النقدية محتجزة في العمليات {v} بعد السداد للموردين."),
    "operating_margin": ("Core operations earn {v} per unit of sales before non-operating items.", "العمليات الأساسية تحقق {v} لكل وحدة مبيعات قبل البنود غير التشغيلية."),
    "roa": ("Assets earn {v} after interest and tax.", "الأصول تحقق {v} بعد الفوائد والضرائب."),
    "roce": ("Long-term capital earns {v} before interest and tax.", "رأس المال طويل الأجل يحقق {v} قبل الفوائد والضرائب."),
}

# meaning of a rise / fall: (en_up, en_down, ar_up, ar_down)
MEANING = {
    "liquidity": ("the firm's ability to meet its short-term obligations has improved",
                  "the firm's ability to meet its short-term obligations has weakened",
                  "تحسّنت قدرة الشركة على سداد التزاماتها قصيرة الأجل", "ضعفت قدرة الشركة على سداد التزاماتها قصيرة الأجل"),
    "days": ("cash is tied up for a longer period before it returns to the firm",
             "cash returns to the firm faster",
             "النقدية تبقى محتجزة مدة أطول قبل أن تعود للشركة", "النقدية تعود للشركة بسرعة أكبر"),
    "debt": ("the firm relies more on borrowed money, so its financial risk is higher",
             "the firm relies less on borrowed money, so its financial risk is lower",
             "الشركة تعتمد أكثر على الأموال المقترضة، فترتفع مخاطرها المالية", "الشركة تعتمد أقل على الأموال المقترضة، فتنخفض مخاطرها المالية"),
    "coverage": ("profits cover the cost of debt more comfortably", "profits cover the cost of debt less comfortably",
                 "الأرباح تغطي تكلفة الديون بارتياح أكبر", "الأرباح تغطي تكلفة الديون بارتياح أقل"),
    "activity": ("the firm uses its assets more efficiently to generate sales", "the firm uses its assets less efficiently to generate sales",
                 "الشركة تستخدم أصولها بكفاءة أعلى لتوليد المبيعات", "الشركة تستخدم أصولها بكفاءة أقل لتوليد المبيعات"),
    "profitability": ("the firm earns more from each unit of sales / investment", "the firm earns less from each unit of sales / investment",
                      "الشركة تحقق ربحاً أكبر من كل وحدة مبيعات / استثمار", "الشركة تحقق ربحاً أقل من كل وحدة مبيعات / استثمار"),
    "value": ("the firm created more value for its owners", "the firm created less value for its owners",
              "الشركة حققت قيمة أكبر لملاكها", "الشركة حققت قيمة أقل لملاكها"),
    "cashflow": ("operations generate more cash", "operations generate less cash",
                 "العمليات تولّد نقدية أكبر", "العمليات تولّد نقدية أقل"),
}
GROUP = {"acp": "days", "asp": "days", "liquidity_of_inventory": "days", "app": "days", "ccc": "days",
         "interest_coverage": "coverage", "eva": "value", "mva": "value", "bvps": "value", "eps": "value"}
CAT_GROUP = {"liquidity": "liquidity", "debt": "debt", "activity": "activity", "profitability": "profitability",
             "dupont": "profitability", "market": "value", "cashflow": "cashflow", "breakeven": "profitability"}

IMPACT = {  # (en_good, en_bad, ar_good, ar_bad)
    "liquidity": ("lower risk of failing to pay suppliers and short-term lenders", "higher risk of a liquidity squeeze and need for short-term borrowing",
                  "انخفاض خطر العجز عن سداد الموردين والمقرضين قصيري الأجل", "ارتفاع خطر أزمة سيولة والحاجة إلى اقتراض قصير الأجل"),
    "days": ("less need for cash to finance operations", "greater need for cash to finance operations (Lecture 3: the larger the liquidity of inventory, the greater the need for cash)",
             "حاجة أقل للنقدية لتمويل العمليات", "حاجة أكبر للنقدية لتمويل العمليات (المحاضرة 3: كلما زادت سيولة المخزون زادت الحاجة للنقدية)"),
    "debt": ("more borrowing capacity and lower bankruptcy risk", "higher fixed interest burden and higher bankruptcy risk",
             "قدرة أكبر على الاقتراض ومخاطر إفلاس أقل", "عبء فوائد ثابت أكبر ومخاطر إفلاس أعلى"),
    "coverage": ("creditors are safer and new borrowing is easier", "creditors are less safe; new borrowing becomes harder and more expensive",
                 "الدائنون أكثر أماناً والاقتراض الجديد أسهل", "الدائنون أقل أماناً والاقتراض الجديد أصعب وأغلى"),
    "activity": ("higher sales from the same asset base, which supports profitability (DuPont: ROI = OIM × TATO)",
                 "idle or under-used assets that drag down ROI (DuPont: ROI = OIM × TATO)",
                 "مبيعات أعلى من نفس الأصول مما يدعم الربحية (ديبونت: ROI = OIM × TATO)", "أصول عاطلة أو غير مستغلة تخفض العائد على الاستثمار (ديبونت)"),
    "profitability": ("more internally generated funds (retained earnings) and higher return for owners",
                      "fewer internal funds and lower return for owners",
                      "أموال داخلية أكثر (أرباح محتجزة) وعائد أعلى للملاك", "أموال داخلية أقل وعائد أقل للملاك"),
    "value": ("owners' wealth increases", "owners' wealth decreases", "ثروة الملاك تزداد", "ثروة الملاك تنخفض"),
    "cashflow": ("profits are backed by cash; less dependence on external finance", "profits are not turning into cash; more dependence on external finance",
                 "الأرباح مدعومة بنقدية فعلية واعتماد أقل على التمويل الخارجي", "الأرباح لا تتحول إلى نقدية واعتماد أكبر على التمويل الخارجي"),
}

RECOMMEND = {  # (en_keep, en_fix, ar_keep, ar_fix)
    "liquidity": ("keep current assets in line with current liabilities and avoid financing long-term assets with short-term funds (golden rule)",
                  "lengthen debt maturities, convert short-term borrowing to long-term, and build current assets from retained profit",
                  "الحفاظ على توازن الأصول المتداولة مع الخصوم المتداولة وتجنب تمويل الأصول طويلة الأجل بأموال قصيرة الأجل (القاعدة الذهبية)",
                  "إطالة آجال الديون وتحويل الاقتراض قصير الأجل إلى طويل الأجل وبناء الأصول المتداولة من الأرباح المحتجزة"),
    "days": ("keep the current credit and inventory policy; it can take credit facilities from suppliers longer than its collection period",
             "tighten credit terms, follow up overdue customers and review slow-moving inventory",
             "الاستمرار في سياسة الائتمان والمخزون الحالية، ويمكنها الحصول على تسهيلات من الموردين أطول من فترة التحصيل",
             "تشديد شروط الائتمان ومتابعة العملاء المتأخرين ومراجعة المخزون بطيء الحركة"),
    "debt": ("use the available borrowing capacity only for projects whose ROI exceeds the cost of debt",
             "retain more earnings or raise equity before adding new debt",
             "استخدام القدرة المتاحة على الاقتراض فقط لمشروعات يزيد عائدها على تكلفة الدين",
             "احتجاز مزيد من الأرباح أو زيادة رأس المال قبل الاقتراض الجديد"),
    "coverage": ("maintain the current debt level", "reduce interest-bearing debt or refinance at a lower cost",
                 "الحفاظ على مستوى الديون الحالي", "تخفيض الديون ذات الفوائد أو إعادة تمويلها بتكلفة أقل"),
    "activity": ("keep using the asset base efficiently and expand sales on it",
                 "dispose of idle assets or grow sales on the existing asset base (restructure the asset distribution)",
                 "الاستمرار في استغلال الأصول بكفاءة والتوسع في المبيعات عليها",
                 "التخلص من الأصول العاطلة أو زيادة المبيعات على الأصول الحالية (إعادة هيكلة توزيع الأصول)"),
    "profitability": ("maintain pricing and cost control", "review pricing, cost of sales and operating expenses",
                      "الحفاظ على سياسة التسعير والرقابة على التكاليف", "مراجعة التسعير وتكلفة المبيعات والمصروفات التشغيلية"),
    "value": ("continue with the current investment policy", "invest only where returns exceed the cost of capital",
              "الاستمرار في سياسة الاستثمار الحالية", "الاستثمار فقط حيث يزيد العائد على تكلفة رأس المال"),
    "cashflow": ("keep converting profits into cash", "investigate working-capital movements (receivables, inventory) absorbing cash",
                 "الاستمرار في تحويل الأرباح إلى نقدية", "فحص تحركات رأس المال العامل (المدينين والمخزون) التي تمتص النقدية"),
}

T = {
    "title_acad": ("Academic interpretation (professor's method — {src})", "تفسير أكاديمي (منهج الأستاذ — {src})"),
    "title_prof": ("Professional interpretation (not covered in the lectures)", "تفسير مهني (غير مشروح في المحاضرات)"),
    "s1": ("1. Result", "١. النتيجة"), "s2": ("2. Comparison", "٢. المقارنة"), "s3": ("3. Direction of change", "٣. اتجاه التغير"),
    "s4": ("4. Financial meaning", "٤. المعنى المالي"), "s5": ("5. Favourable or unfavourable", "٥. إيجابي أم سلبي"),
    "s6": ("6. Impact on the company", "٦. الأثر على الشركة"), "s7": ("7. Conclusion and recommendation", "٧. الاستنتاج والتوصية"),
    "result": ("{name} ({y}) = {formula} = {v}.", "{name} ({y}) = {formula} = {v}."),
    "prev": ("Previous year ({py}): {pv}.", "السنة السابقة ({py}): {pv}."),
    "noprev": ("No previous year is available for comparison.", "لا توجد سنة سابقة للمقارنة."),
    "bench": ("∵ {name} (company) = {v} {rel} {name} (benchmark: {b}, {src}).", "∵ {name} (الشركة) = {v} {rel} {name} (المعيار: {b}، {src})."),
    "nobench": ("No industry benchmark is set, so the assessment relies on the company's own history (professional note).",
                "لا يوجد معيار صناعي محدد، لذا يعتمد التقييم على تاريخ الشركة نفسها (ملاحظة مهنية)."),
    "up": ("{name} increased from {pv} to {v} ({d}).", "ارتفعت قيمة {name} من {pv} إلى {v} ({d})."),
    "down": ("{name} decreased from {pv} to {v} ({d}).", "انخفضت قيمة {name} من {pv} إلى {v} ({d})."),
    "same": ("{name} remained unchanged at {v}.", "بقيت قيمة {name} دون تغيير عند {v}."),
    "nodir": ("Direction cannot be determined (single year or missing value).", "لا يمكن تحديد الاتجاه (سنة واحدة أو قيمة ناقصة)."),
    "meaning_up": ("This means that {m}.", "وهذا يعني أن {m}."), "meaning_down": ("This means that {m}.", "وهذا يعني أن {m}."),
    "fav": ("Favourable.", "إيجابي (في صالح الشركة)."),
    "mixed": ("Mixed: the trend is favourable, but the level is still weak.", "مختلط: الاتجاه إيجابي لكن المستوى ما زال ضعيفاً."), "unfav": ("Unfavourable.", "سلبي (في غير صالح الشركة)."),
    "neutral": ("Neither favourable nor unfavourable by itself; it must be read with related ratios.",
                "ليس إيجابياً أو سلبياً في حد ذاته؛ يجب قراءته مع النسب المرتبطة."),
    "vs_bench_good": ("Compared with the benchmark, the firm's performance is above the industry average.",
                      "مقارنةً بالمعيار، أداء الشركة أعلى من متوسط الصناعة."),
    "vs_bench_bad": ("Compared with the benchmark, the firm's performance is below the industry average and it has to improve it.",
                     "مقارنةً بالمعيار، أداء الشركة أقل من متوسط الصناعة وعليها تحسينه."),
    "impact": ("Expected impact: {i}.", "الأثر المتوقع: {i}."),
    "conclude_good": ("∴ The firm is performing well in this aspect. Accordingly, we do recommend the firm to {r}.",
                      "∴ الشركة تؤدي بشكل جيد في هذا الجانب. وعليه نوصي الشركة ب{r}."),
    "conclude_bad": ("∴ The firm's performance in this aspect needs improvement. Accordingly, we do recommend the firm to {r}.",
                     "∴ أداء الشركة في هذا الجانب يحتاج إلى تحسين. وعليه نوصي الشركة ب{r}."),
    "status_note": ("Note: this result is {st} — {why}.", "ملاحظة: هذه النتيجة {st} — {why}."),
    "na": ("Not available for {y}: {why}.", "غير متاحة لسنة {y}: {why}."),
    "gt": (">", ">"), "lt": ("<", "<"), "eq": ("=", "="),
}
STATUS_AR = {"verified": "مُتحقق منها", "approved_assumption": "مبنية على افتراضات معتمدة", "provisional": "مبدئية",
             "needs_info": "تحتاج معلومات إضافية", "invalid": "غير صالحة"}


FORMULA_AR = [("Current liabilities", "الخصوم المتداولة"), ("Current assets", "الأصول المتداولة"), ("Total assets", "إجمالي الأصول"),
              ("Total debts", "إجمالي الديون"), ("Fixed assets", "الأصول الثابتة"), ("Credit sales", "المبيعات الآجلة"),
              ("Cash sales", "المبيعات النقدية"), ("credit purchases", "المشتريات الآجلة"), ("ST investments", "الاستثمارات قصيرة الأجل"),
              ("Inventory", "المخزون"), ("Gross profit", "مجمل الربح"), ("Net income", "صافي الدخل"), ("Net profit", "صافي الربح"),
              ("Interest", "الفوائد"), ("Equity", "حقوق الملكية"), ("Sales", "المبيعات"), ("COGS", "تكلفة المبيعات"), ("Cash", "النقدية"),
              ("No. of shares", "عدد الأسهم"), ("market price", "سعر السوق"), ("Total O/E", "إجمالي حقوق الملكية"),
              ("Academic", "أكاديمي"), ("Professional", "مهني"), ("course", "المقرر"), ("professional option", "خيار مهني"),
              ("opportunity rate", "معدل تكلفة الفرصة"), ("CS dividends", "توزيعات الأسهم العادية"), ("PS dividends", "توزيعات الأسهم الممتازة"),
              ("Fixed costs", "التكاليف الثابتة"), ("Variable costs", "التكاليف المتغيرة"), ("Break-even sales", "مبيعات التعادل")]


def formula_text(formula: str, lang: str) -> str:
    if lang != "ar":
        return formula
    for en, ar in FORMULA_AR:
        formula = formula.replace(en, ar)
    return formula


def _t(key, lang, **kw):
    en, ar = T[key]
    return (ar if lang == "ar" else en).format(**kw)


def _group(r):
    return GROUP.get(r["key"], CAT_GROUP.get(r["category"], "profitability"))


def _change_text(cur, prev, unit, lang="en"):
    if cur is None or prev is None or not isinstance(cur, (int, float)) or not isinstance(prev, (int, float)):
        return None
    d = cur - prev
    if unit == "%":
        s = f"{d * 100:+.2f} " + ("نقطة مئوية" if lang == "ar" else "pp")
    elif unit == "days":
        s = f"{d:+.1f} " + ("يوماً" if lang == "ar" else "days")
    elif unit == "ccy":
        s = f"{d:+,.0f}"
    else:
        s = f"{d:+.2f}"
    if prev:
        s += f", {d / abs(prev) * 100:+.1f}%"
    return s


def interpret_ratio(r: dict, year: int, lang: str = "en", ccy: str = "") -> dict:
    """r = one ratio entry from Analysis.ratios() (with cells, benchmark, higher_is_better, unit, category, source)."""
    cells = {c["year"]: c for c in r["cells"]}
    years = sorted(cells)
    c = cells[year]
    name = r["name_ar"] if lang == "ar" else r["name_en"]
    academic = r["methodology"] in ("academic", "both")
    head = _t("title_acad", lang, src=r["source"]) if academic else _t("title_prof", lang)
    steps = []
    if c["value"] is None or r["unit"] == "text":
        if r["key"] == "best_liquidity_measure" and c["value"]:
            return {"key": r["key"], "year": year, "basis": "academic", "heading": head, "verdict": "n/a",
                    "steps": [{"title": _t("s1", lang), "text": _best_liq_text(c["value"], lang)}], "status": c["status"]}
        why = "; ".join(c["reasons"]) or c["status"]
        return {"key": r["key"], "year": year, "basis": "academic" if academic else "professional", "heading": head,
                "verdict": "n/a", "steps": [{"title": _t("s1", lang), "text": _t("na", lang, y=year, why=why)}], "status": c["status"]}
    v = c["display"]
    formula = formula_text(r["formula"], lang)
    s1 = _t("result", lang, name=name, y=year, formula=formula, v=v)
    us = UNIT_SENTENCE.get(r["key"])
    if us:
        s1 += " " + (us[1] if lang == "ar" else us[0]).format(v=v)
    if c["status"] not in ("verified", "approved_assumption"):
        st = STATUS_AR.get(c["status"], c["status"]) if lang == "ar" else c["status"].replace("_", " ")
        s1 += " " + _t("status_note", lang, st=st, why="; ".join(c["reasons"]) or "-")
    steps.append({"title": _t("s1", lang), "text": s1})

    # 2. comparison
    idx = years.index(year)
    prev = cells[years[idx - 1]] if idx > 0 else None
    comp = []
    comp.append(_t("prev", lang, py=prev["year"], pv=prev["display"]) if prev and prev["value"] is not None else _t("noprev", lang))
    bench = r.get("benchmark")
    hib = r.get("higher_is_better")
    bench_good = None
    if bench and bench.get("value") is not None:
        bv = bench["value"]
        rel = _t("gt" if c["value"] > bv else "lt" if c["value"] < bv else "eq", lang)
        bfmt = fmt(bv, r["unit"], ccy)
        comp.append(_t("bench", lang, name=name, v=v, rel=rel, b=bfmt.replace(" days", " يوماً") if lang == "ar" else bfmt,
                       src=bench.get("source", "")))
        if hib is not None and c["value"] != bv:
            bench_good = (c["value"] > bv) == bool(hib)
    else:
        comp.append(_t("nobench", lang))
    steps.append({"title": _t("s2", lang), "text": " ".join(comp)})

    # 3. direction
    direction = None
    if prev and prev["value"] is not None:
        ch = _change_text(c["value"], prev["value"], r["unit"], lang)
        if c["value"] > prev["value"]:
            direction = "up"
        elif c["value"] < prev["value"]:
            direction = "down"
        else:
            direction = "same"
        steps.append({"title": _t("s3", lang), "text": _t(direction, lang, name=name, pv=prev["display"], v=v, d=ch)})
    else:
        steps.append({"title": _t("s3", lang), "text": _t("nodir", lang)})

    # 4. meaning
    g = _group(r)
    en_up, en_dn, ar_up, ar_dn = MEANING[g]
    if direction in ("up", "down"):
        m = (ar_up if direction == "up" else ar_dn) if lang == "ar" else (en_up if direction == "up" else en_dn)
        steps.append({"title": _t("s4", lang), "text": _t("meaning_up", lang, m=m)})
    else:
        base = (us[1] if lang == "ar" else us[0]).format(v=v) if us else r["interpretation"]
        steps.append({"title": _t("s4", lang), "text": base})

    # 5. favourable?
    if hib is None:
        verdict = "neutral"
        fav_text = _t("neutral", lang)
    else:
        good_trend = None if direction not in ("up", "down") else ((direction == "up") == bool(hib))
        if good_trend is None and bench_good is None:
            verdict = "neutral"
        elif bench_good is not None and good_trend is not None and bench_good != good_trend:
            verdict = "mixed"
        else:
            verdict = "favorable" if (good_trend if good_trend is not None else bench_good) else "unfavorable"
        if r.get("risk") == "High" and good_trend is not True:  # threshold breached and not improving
            verdict = "unfavorable"
        elif r.get("risk") == "High" and good_trend:  # improving, but still weak
            verdict = "mixed"
        fav_text = {"favorable": _t("fav", lang), "unfavorable": _t("unfav", lang), "neutral": _t("neutral", lang),
                    "mixed": _t("mixed", lang)}[verdict]
        if bench_good is not None:
            fav_text += " " + _t("vs_bench_good" if bench_good else "vs_bench_bad", lang)
    steps.append({"title": _t("s5", lang), "text": fav_text})

    # 6. impact
    ig, ib, aig, aib = IMPACT[g]
    good = verdict in ("favorable", "neutral")  # 'mixed' keeps the corrective recommendation
    steps.append({"title": _t("s6", lang), "text": _t("impact", lang, i=(aig if good else aib) if lang == "ar" else (ig if good else ib))})

    # 7. conclusion
    rk, rf, ark, arf = RECOMMEND[g]
    rec = (ark if good else arf) if lang == "ar" else (rk if good else rf)
    steps.append({"title": _t("s7", lang), "text": _t("conclude_good" if good else "conclude_bad", lang, r=rec)})
    return {"key": r["key"], "year": year, "basis": "academic" if academic else "professional", "heading": head,
            "verdict": verdict, "steps": steps, "status": c["status"]}


def _best_liq_text(value, lang):
    if lang == "ar":
        m = {"Current ratio": "نسبة التداول", "Quick ratio": "نسبة السيولة السريعة", "Cash ratio": "نسبة النقدية"}.get(value, value)
        return (f"أفضل مقياس للسيولة هو {m}. ∵ مدة تحويل المدينين والمخزون إلى نقدية (ACP + ASP) "
                f"{'أقل من 360 يوماً' if value == 'Current ratio' else 'تتجاوز 360 يوماً'} ∴ "
                f"{'يُعتبر المدينون والمخزون أصولاً متداولة' if value == 'Current ratio' else 'لا يُعتمد عليها كاملة كأصول متداولة'} (المحاضرة 3، الشريحة 4؛ السؤال 5).")
    return (f"The best measure of liquidity is the {value.lower()}. ∵ The time needed to turn receivables and inventory into cash (ACP + ASP) "
            f"{'is less than 360 days' if value == 'Current ratio' else 'exceeds 360 days'} ∴ "
            f"{'AR and inventory are considered current assets' if value == 'Current ratio' else 'they cannot all be relied on as current assets'} "
            "(Lecture 3, slide 4; Q5 solution).")


def interpret_dupont(ratios: list[dict], year: int, lang: str) -> str | None:
    """Q3 style: 'ROI has been increased by increasing both profitability and efficiency'."""
    rm = {r["key"]: r for r in ratios}
    if not all(k in rm for k in ("roi", "oim", "tato")):
        return None
    def val(k, y):
        c = next((c for c in rm[k]["cells"] if c["year"] == y), None)
        return c["value"] if c else None
    ys = sorted(c["year"] for c in rm["roi"]["cells"])
    if year not in ys or ys.index(year) == 0:
        return None
    py = ys[ys.index(year) - 1]
    vals = {k: (val(k, py), val(k, year)) for k in ("roi", "oim", "tato")}
    if any(a is None or b is None for a, b in vals.values()):
        return None
    d = {k: (b > a) - (b < a) for k, (a, b) in vals.items()}
    en = {1: "increasing", -1: "decreasing", 0: "unchanged"}
    ar = {1: "ارتفاع", -1: "انخفاض", 0: "ثبات"}
    roi_word_en = {1: "increased", -1: "decreased", 0: "remained unchanged"}[d["roi"]]
    roi_word_ar = {1: "ارتفع", -1: "انخفض", 0: "ثبت"}[d["roi"]]
    f = lambda x: f"{x * 100:.2f}%"  # noqa: E731
    if lang == "ar":
        return (f"نظام ديبونت: ROI = OIM × TATO. في {py}: {f(vals['roi'][0])} = {f(vals['oim'][0])} × {vals['tato'][0]:.3f}؛ "
                f"وفي {year}: {f(vals['roi'][1])} = {f(vals['oim'][1])} × {vals['tato'][1]:.3f}. "
                f"وعليه {roi_word_ar} العائد على الاستثمار نتيجة {ar[d['oim']]} الربحية (هامش التشغيل) و{ar[d['tato']]} الكفاءة (دوران الأصول) "
                f"من {py} إلى {year}" + ("، مما يدل على أن أداء الشركة أفضل." if d["roi"] > 0 else "، مما يستدعي مراجعة مصدر التراجع." if d["roi"] < 0 else "."))
    return (f"DuPont system: ROI = OIM × TATO. {py}: {f(vals['roi'][0])} = {f(vals['oim'][0])} × {vals['tato'][0]:.3f}; "
            f"{year}: {f(vals['roi'][1])} = {f(vals['oim'][1])} × {vals['tato'][1]:.3f}. "
            f"Accordingly, ROI has {roi_word_en} with {en[d['oim']]} profitability (OIM) and {en[d['tato']]} efficiency (TATO) from {py} to {year}"
            + (", which indicates that the firm is performing well and better." if d["roi"] > 0 else
               ", which calls for a review of the source of the decline." if d["roi"] < 0 else "."))


def interpret_sources_uses(su: dict, lang: str) -> list[str]:
    """Q3 style overall analysis of sources and uses of money."""
    if not su or not su.get("rows"):
        return []
    srcs = sorted([r for r in su["rows"] if r["type"] == "source"], key=lambda r: -r["amount"])
    uses = sorted([r for r in su["rows"] if r["type"] == "use"], key=lambda r: -r["amount"])
    p = lambda x: "n/a" if x is None else f"{x * 100:.1f}%"  # noqa: E731
    out = []
    if lang == "ar":
        uses = [dict(r, description=su_desc_ar(r)) for r in uses]
        srcs = [dict(r, description=su_desc_ar(r)) for r in srcs]
        if uses:
            out.append(f"وجّهت الشركة {p(uses[0]['pct'])} من استخداماتها إلى: {uses[0]['description']}.")
        if srcs:
            out.append(f"أكبر مصدر للأموال: {srcs[0]['description']} بنسبة {p(srcs[0]['pct'])} من إجمالي المصادر.")
        out.append(f"{p(su['short_term_sources_pct'])} من المصادر قصيرة الأجل مقابل {p(su['short_term_uses_pct'])} من الاستخدامات قصيرة الأجل، "
                   f"و{p(su['long_term_sources_pct'])} من المصادر طويلة الأجل مقابل {p(su['long_term_uses_pct'])} من الاستخدامات طويلة الأجل "
                   f"(أي أن الانحراف عن القاعدة الذهبية = {p(su['golden_rule_deviation'])}).")
        out.append(f"{p(su['internal_sources_pct'])} من مصادر التمويل داخلية، بينما {p(su['external_sources_pct'])} مصادر خارجية.")
        dev = su.get("golden_rule_deviation") or 0
        out.append("وعليه فإن الشركة " + ("لم تنحرف انحرافاً كبيراً عن القاعدة الذهبية" if dev <= 0.10 else "انحرفت عن القاعدة الذهبية بتمويل استخدامات بمصادر ذات آجال غير مناسبة")
                   + "، و" + ("تعتمد أساساً على مصادرها الداخلية." if (su["internal_sources_pct"] or 0) >= 0.5 else "تعتمد أساساً على مصادر خارجية."))
    else:
        if uses:
            out.append(f"The company has directed {p(uses[0]['pct'])} of its uses to: {uses[0]['description']}.")
        if srcs:
            out.append(f"The largest source of funds: {srcs[0]['description']} ({p(srcs[0]['pct'])} of total sources).")
        out.append(f"{p(su['short_term_sources_pct'])} of its sources come from short-term items compared to {p(su['short_term_uses_pct'])} of its uses; "
                   f"{p(su['long_term_sources_pct'])} of its sources come from long-term items compared to {p(su['long_term_uses_pct'])} of its uses "
                   f"(i.e. deviation from the golden rule is {p(su['golden_rule_deviation'])}).")
        out.append(f"{p(su['internal_sources_pct'])} of the sources of finance come from internal sources, while {p(su['external_sources_pct'])} are obtained from external sources.")
        dev = su.get("golden_rule_deviation") or 0
        out.append("Therefore, the firm " + ("works without a great deviation from the golden rule" if dev <= 0.10 else "deviates from the golden rule by financing uses with sources of unsuitable maturity")
                   + " and " + ("relies mainly on internal sources of finance." if (su["internal_sources_pct"] or 0) >= 0.5 else "relies mainly on external sources of finance."))
    return out


def su_desc_ar(r: dict) -> str:
    up = (r.get("change") or 0) > 0
    a = r["account"]
    if r.get("category") == "bs.nca.acc_depreciation":
        return f"زيادة {a} (عبء غير نقدي محتجز في الشركة)" if up else f"انخفاض {a}"
    if r["element"] == "Asset":
        return f"زيادة {a}" if up else (f"تسييل / تخفيض {a}" if r.get("group") == "Non-Current" else f"انخفاض {a}")
    if r["element"] == "Liability":
        return f"زيادة {a} (تمويل جديد)" if up else f"سداد / تخفيض {a}"
    return f"زيادة {a}" if up else f"انخفاض {a}"


def interpret_all(ratios: list[dict], lang: str, ccy: str = "") -> dict:
    """{ratio_key: [interpretation per year]} for every ratio."""
    return {r["key"]: [interpret_ratio(r, c["year"], lang, ccy) for c in r["cells"]] for r in ratios}
