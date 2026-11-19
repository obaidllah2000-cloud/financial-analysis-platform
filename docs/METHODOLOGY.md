# Financial Methodology Database

Generated from the calculation engine's own registry (`backend/app/engine/ratios.py`) — the documentation and the code are the same source.

**Academic** = lectures & solved exams (default). **Professional** = additional industry-standard methods. **Both** = identical.

## Documented differences between academic and professional formulas

| Topic | Academic (course) | Professional | Where configured |
|---|---|---|---|
| ROE | EBT / Equity (Lecture 3, slide 7) — so ROE = ROI + ROBF holds | Net profit / Equity | Assumption `roe_definition` |
| ROI / ROA | EBIT / Total assets | NP / Total assets shown separately as ROA (net) | `roi_definition` |
| Balances | Closing balances (Q1, Q3, Q5) | Average (opening + closing)/2 | `inventory_basis`, `receivables_basis`, `asset_equity_basis` |
| Days | 360 | 365 | `days_in_year` |
| Cash ratio | (CA − Inv − AR − ST inv) / CL | (Cash + ST inv) / CL | `cash_ratio_definition` |
| OIM | EBIT / Sales (Q3 DuPont) | Operating profit before non-operating items / Sales (separate ratio) | Both shown |
| Operating cycle | 'Liquidity of inventory' = ASP + ACP | CCC = ASP + ACP − payment period | Both shown (professional only adds CCC) |
| EVA | NP − (I + PS div + CS div + r × R/E), r = 10% in Q3 | NOPAT − WACC × capital (not implemented: needs WACC) | `eva_opportunity_rate` |
| ROBF variables | BF = total debts, OE = monetary equity (Lecture 1 slides 29 & 31) | BF = interest-bearing debt | `bf_definition`, `oe_definition` |

## Indicators

### Current ratio — نسبة التداول

- **Category:** liquidity · **Methodology:** both
- **Formula:** Current assets / Current liabilities
- **Required accounts:** Total current assets, Current liabilities
- **Account classifications:** bs.ca.cash, bs.ca.inventory, bs.ca.notes_receivable, bs.ca.other, bs.ca.prepaid, bs.ca.receivables, bs.ca.st_investments, bs.cl.accrued, bs.cl.advance_revenue, bs.cl.notes_payable, bs.cl.other, bs.cl.payables, bs.cl.st_debt, bs.cl.tax_payable
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Every 1 unit of current liabilities is covered by X units of current assets. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Lecture 3 — Financial Ratios, slide 2
- **Practical application:** Lengthen debt maturities, convert short-term borrowing to long-term, or build current assets from retained profit.

### Quick (acid-test) ratio — نسبة السيولة السريعة

- **Category:** liquidity · **Methodology:** both
- **Formula:** (Current assets − Inventory) / Current liabilities
- **Required accounts:** Total current assets, Inventory, Current liabilities
- **Account classifications:** bs.ca.cash, bs.ca.inventory, bs.ca.notes_receivable, bs.ca.other, bs.ca.prepaid, bs.ca.receivables, bs.ca.st_investments, bs.cl.accrued, bs.cl.advance_revenue, bs.cl.notes_payable, bs.cl.other, bs.cl.payables, bs.cl.st_debt, bs.cl.tax_payable
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Excluding inventory, every 1 unit of current liabilities is covered by X units of liquid assets. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Lecture 3 — Financial Ratios, slide 2
- **Practical application:** Reduce dependence on inventory to meet obligations; accelerate collections.

### Cash ratio — نسبة النقدية

- **Category:** liquidity · **Methodology:** both
- **Formula:** Academic: (CA − Inventory − AR − ST investments) / CL · Professional: (Cash + ST investments) / CL
- **Required accounts:** Total current assets, Inventory, Receivables (A/R + N/R), Short-term investments, Cash & equivalents, Current liabilities
- **Account classifications:** bs.ca.cash, bs.ca.inventory, bs.ca.notes_receivable, bs.ca.other, bs.ca.prepaid, bs.ca.receivables, bs.ca.st_investments, bs.cl.accrued, bs.cl.advance_revenue, bs.cl.notes_payable, bs.cl.other, bs.cl.payables, bs.cl.st_debt, bs.cl.tax_payable
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Cash-in-kind covers X of current liabilities. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** Cash ratio definition
- **Source:** Lecture 3 — Financial Ratios, slide 2
- **Practical application:** Monitoring and comparison over time.

### Working capital — رأس المال العامل

- **Category:** liquidity · **Methodology:** both
- **Formula:** Current assets − Current liabilities
- **Required accounts:** Total current assets, Current liabilities
- **Account classifications:** bs.ca.cash, bs.ca.inventory, bs.ca.notes_receivable, bs.ca.other, bs.ca.prepaid, bs.ca.receivables, bs.ca.st_investments, bs.cl.accrued, bs.cl.advance_revenue, bs.cl.notes_payable, bs.cl.other, bs.cl.payables, bs.cl.st_debt, bs.cl.tax_payable
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Net short-term resources available: X. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Lecture 1 — Financial Management, slide 13
- **Practical application:** Monitoring and comparison over time.

### Average collection period (Liquidity of AR) — متوسط فترة التحصيل

- **Category:** liquidity · **Methodology:** academic
- **Formula:** (AR × 360) / Credit sales
- **Required accounts:** Receivables (A/R + N/R), Credit sales, Sales / revenue
- **Account classifications:** Additional_Info: credit_sales (or sales − cash_sales; or assumption), bs.ca.notes_receivable, bs.ca.receivables, is.revenue
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Receivables are collected on average every X days. Lower is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** Receivables balance for turnover / ACP; Credit sales when not provided; Days in the year
- **Source:** Lecture 3 — Financial Ratios, slide 3; Q1 & Q2 solutions
- **Practical application:** Tighten credit terms, offer early-payment discounts, review overdue customers.

### Average selling period (inventory days) — متوسط فترة البيع

- **Category:** liquidity · **Methodology:** academic
- **Formula:** (Inventory × 360) / COGS
- **Required accounts:** Inventory, Cost of goods sold
- **Account classifications:** bs.ca.inventory, is.cogs
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Inventory is sold on average every X days. Lower is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** Inventory balance for turnover / ASP; Days in the year
- **Source:** Lecture 3 — Financial Ratios, slide 3; Q1 & Q5 solutions
- **Practical application:** Review slow-moving items, align purchasing with demand.

### Liquidity of inventory (operating cycle) — سيولة المخزون (الدورة التشغيلية)

- **Category:** liquidity · **Methodology:** academic
- **Formula:** ASP + ACP
- **Required accounts:** Inventory, Cost of goods sold, Receivables (A/R + N/R), Credit sales
- **Account classifications:** Additional_Info: credit_sales (or sales − cash_sales; or assumption), bs.ca.inventory, bs.ca.notes_receivable, bs.ca.receivables, is.cogs
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** It takes X days to sell inventory and collect the cash. The larger it is, the more cash is needed to finance operations. Lower is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** Inventory balance for turnover / ASP; Receivables balance for turnover / ACP; Credit sales when not provided; Days in the year
- **Source:** Lecture 3 — Financial Ratios, slide 3; Q1 & Q5 solutions
- **Practical application:** Monitoring and comparison over time.

### Best measure of liquidity (course rule) — أفضل مقياس للسيولة

- **Category:** liquidity · **Methodology:** academic
- **Formula:** If ACP+ASP < 360 → current ratio; if ACP < 360 but ACP+ASP ≥ 360 → quick ratio; if ACP ≥ 360 → cash ratio
- **Required accounts:** Receivables (A/R + N/R), Inventory, Cost of goods sold, Credit sales
- **Account classifications:** Additional_Info: credit_sales (or sales − cash_sales; or assumption), bs.ca.inventory, bs.ca.notes_receivable, bs.ca.receivables, is.cogs
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** X is the most reliable liquidity measure for this year, because of how quickly receivables and inventory turn into cash.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** Inventory balance for turnover / ASP; Receivables balance for turnover / ACP; Credit sales when not provided; Days in the year
- **Source:** Lecture 3 — Financial Ratios, slide 4; Q5 solution
- **Practical application:** Monitoring and comparison over time.

### Debt ratio — نسبة المديونية

- **Category:** debt · **Methodology:** both
- **Formula:** Total debts / Total assets
- **Required accounts:** Total debts (liabilities), Total assets
- **Account classifications:** bs.ca.cash, bs.ca.inventory, bs.ca.notes_receivable, bs.ca.other, bs.ca.prepaid, bs.ca.receivables, bs.ca.st_investments, bs.cl.accrued, bs.cl.advance_revenue, bs.cl.notes_payable, bs.cl.other, bs.cl.payables, bs.cl.st_debt, bs.cl.tax_payable, bs.nca.acc_depreciation, bs.nca.intangibles, bs.nca.land, bs.nca.lt_investments, bs.nca.other, bs.nca.ppe_gross, bs.nca.ppe_net, bs.ncl.bonds, bs.ncl.lt_loans, bs.ncl.other
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** X of assets are financed by debt. The higher the ratio, the riskier the company. Lower is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Lecture 3 — Financial Ratios, slide 5
- **Practical application:** Retain more earnings or raise equity before adding new debt.

### Debt / equity — الديون إلى حقوق الملكية

- **Category:** debt · **Methodology:** both
- **Formula:** Total debts / Equity
- **Required accounts:** Total debts (liabilities), Monetary equity (O/E incl. preferred)
- **Account classifications:** bs.cl.accrued, bs.cl.advance_revenue, bs.cl.notes_payable, bs.cl.other, bs.cl.payables, bs.cl.st_debt, bs.cl.tax_payable, bs.eq.common, bs.eq.other, bs.eq.preferred, bs.eq.reserves, bs.eq.retained, bs.ncl.bonds, bs.ncl.lt_loans, bs.ncl.other
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** There are X units of debt for every unit of equity. Lower is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Lecture 3 — Financial Ratios, slide 5
- **Practical application:** Monitoring and comparison over time.

### Capital structure ratio (CSR) — نسبة هيكل رأس المال

- **Category:** debt · **Methodology:** academic
- **Formula:** LTL / (LTL + ME)
- **Required accounts:** Long-term liabilities (LTL), Monetary equity (O/E incl. preferred)
- **Account classifications:** bs.eq.common, bs.eq.other, bs.eq.preferred, bs.eq.reserves, bs.eq.retained, bs.ncl.bonds, bs.ncl.lt_loans, bs.ncl.other
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** X of long-term capital comes from long-term debt. Lower is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Lecture 3 — Financial Ratios, slide 5
- **Practical application:** Monitoring and comparison over time.

### Interest coverage — معدل تغطية الفوائد

- **Category:** debt · **Methodology:** both
- **Formula:** EBIT / Interest
- **Required accounts:** EBIT, Interest expense
- **Account classifications:** (is.finance_income per assumption), is.cogs, is.interest, is.opex.*, is.other_expense, is.other_income, is.revenue
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** EBIT covers interest X times. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Lecture 3 — Financial Ratios, slide 5
- **Practical application:** Reduce interest-bearing debt or refinance at lower cost.

### Equity ratio — نسبة الملكية

- **Category:** debt · **Methodology:** professional
- **Formula:** Equity / Total assets
- **Required accounts:** Monetary equity (O/E incl. preferred), Total assets
- **Account classifications:** bs.ca.cash, bs.ca.inventory, bs.ca.notes_receivable, bs.ca.other, bs.ca.prepaid, bs.ca.receivables, bs.ca.st_investments, bs.eq.common, bs.eq.other, bs.eq.preferred, bs.eq.reserves, bs.eq.retained, bs.nca.acc_depreciation, bs.nca.intangibles, bs.nca.land, bs.nca.lt_investments, bs.nca.other, bs.nca.ppe_gross, bs.nca.ppe_net
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** X of assets are financed by owners. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Professional (complement of the debt ratio)
- **Practical application:** Monitoring and comparison over time.

### Financial leverage (equity multiplier) — الرافعة المالية (مضاعف الملكية)

- **Category:** debt · **Methodology:** professional
- **Formula:** Total assets / Equity
- **Required accounts:** Total assets, Monetary equity (O/E incl. preferred)
- **Account classifications:** bs.ca.cash, bs.ca.inventory, bs.ca.notes_receivable, bs.ca.other, bs.ca.prepaid, bs.ca.receivables, bs.ca.st_investments, bs.eq.common, bs.eq.other, bs.eq.preferred, bs.eq.reserves, bs.eq.retained, bs.nca.acc_depreciation, bs.nca.intangibles, bs.nca.land, bs.nca.lt_investments, bs.nca.other, bs.nca.ppe_gross, bs.nca.ppe_net
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Each unit of equity supports X units of assets.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** Total assets / equity balance for returns & turnover
- **Source:** Professional (DuPont 3-step)
- **Practical application:** Monitoring and comparison over time.

### Long-term debt ratio — نسبة الديون طويلة الأجل

- **Category:** debt · **Methodology:** professional
- **Formula:** LTL / Total assets
- **Required accounts:** Long-term liabilities (LTL), Total assets
- **Account classifications:** bs.ca.cash, bs.ca.inventory, bs.ca.notes_receivable, bs.ca.other, bs.ca.prepaid, bs.ca.receivables, bs.ca.st_investments, bs.nca.acc_depreciation, bs.nca.intangibles, bs.nca.land, bs.nca.lt_investments, bs.nca.other, bs.nca.ppe_gross, bs.nca.ppe_net, bs.ncl.bonds, bs.ncl.lt_loans, bs.ncl.other
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** X of assets are financed by long-term liabilities. Lower is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Professional
- **Practical application:** Monitoring and comparison over time.

### Total assets turnover (TATO) — معدل دوران الأصول

- **Category:** activity · **Methodology:** both
- **Formula:** Sales / Total assets
- **Required accounts:** Sales / revenue, Total assets
- **Account classifications:** bs.ca.cash, bs.ca.inventory, bs.ca.notes_receivable, bs.ca.other, bs.ca.prepaid, bs.ca.receivables, bs.ca.st_investments, bs.nca.acc_depreciation, bs.nca.intangibles, bs.nca.land, bs.nca.lt_investments, bs.nca.other, bs.nca.ppe_gross, bs.nca.ppe_net, is.revenue
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Every unit of total assets generates X units of sales. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** Total assets / equity balance for returns & turnover
- **Source:** Lecture 3 — Financial Ratios, slide 6; Q1 & Q3 solutions
- **Practical application:** Dispose of idle assets or grow sales on the existing asset base.

### TATO — credit sales — معدل دوران الأصول — المبيعات الآجلة

- **Category:** activity · **Methodology:** academic
- **Formula:** Credit sales / Total assets
- **Required accounts:** Credit sales, Total assets
- **Account classifications:** Additional_Info: credit_sales (or sales − cash_sales; or assumption), bs.ca.cash, bs.ca.inventory, bs.ca.notes_receivable, bs.ca.other, bs.ca.prepaid, bs.ca.receivables, bs.ca.st_investments, bs.nca.acc_depreciation, bs.nca.intangibles, bs.nca.land, bs.nca.lt_investments, bs.nca.other, bs.nca.ppe_gross, bs.nca.ppe_net
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Every unit of total assets generates X units of credit sales. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** Credit sales when not provided
- **Source:** Q1 solution (detailed TATO)
- **Practical application:** Monitoring and comparison over time.

### TATO — cash sales — معدل دوران الأصول — المبيعات النقدية

- **Category:** activity · **Methodology:** academic
- **Formula:** Cash sales / Total assets
- **Required accounts:** Sales / revenue, Credit sales, Total assets
- **Account classifications:** Additional_Info: credit_sales (or sales − cash_sales; or assumption), bs.ca.cash, bs.ca.inventory, bs.ca.notes_receivable, bs.ca.other, bs.ca.prepaid, bs.ca.receivables, bs.ca.st_investments, bs.nca.acc_depreciation, bs.nca.intangibles, bs.nca.land, bs.nca.lt_investments, bs.nca.other, bs.nca.ppe_gross, bs.nca.ppe_net, is.revenue
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Every unit of total assets generates X units of cash sales. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** Credit sales when not provided
- **Source:** Q1 solution (detailed TATO)
- **Practical application:** Monitoring and comparison over time.

### Fixed assets turnover (FATO) — معدل دوران الأصول الثابتة

- **Category:** activity · **Methodology:** both
- **Formula:** Sales / Fixed assets
- **Required accounts:** Sales / revenue, Fixed (non-current) assets
- **Account classifications:** bs.nca.acc_depreciation, bs.nca.intangibles, bs.nca.land, bs.nca.lt_investments, bs.nca.other, bs.nca.ppe_gross, bs.nca.ppe_net, is.revenue
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Every unit of fixed assets generates X units of sales. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Lecture 3 — Financial Ratios, slide 6; Q1 solution
- **Practical application:** Monitoring and comparison over time.

### Current assets turnover (CATO) — معدل دوران الأصول المتداولة

- **Category:** activity · **Methodology:** academic
- **Formula:** Sales / Current assets
- **Required accounts:** Sales / revenue, Total current assets
- **Account classifications:** bs.ca.cash, bs.ca.inventory, bs.ca.notes_receivable, bs.ca.other, bs.ca.prepaid, bs.ca.receivables, bs.ca.st_investments, is.revenue
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Every unit of current assets generates X units of sales. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Lecture 3 — Financial Ratios, slide 6; Q1 solution
- **Practical application:** Monitoring and comparison over time.

### Cash turnover — معدل دوران النقدية

- **Category:** activity · **Methodology:** academic
- **Formula:** Sales / Cash
- **Required accounts:** Sales / revenue, Cash & equivalents
- **Account classifications:** bs.ca.cash, is.revenue
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Sales are X times the cash balance.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Lecture 3 — Financial Ratios, slide 6; Q1 solution
- **Practical application:** Monitoring and comparison over time.

### Receivables turnover — معدل دوران المدينين

- **Category:** activity · **Methodology:** both
- **Formula:** Credit sales / AR
- **Required accounts:** Credit sales, Receivables (A/R + N/R)
- **Account classifications:** Additional_Info: credit_sales (or sales − cash_sales; or assumption), bs.ca.notes_receivable, bs.ca.receivables
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Receivables are collected X times a year. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** Receivables balance for turnover / ACP; Credit sales when not provided
- **Source:** Lecture 3 — Financial Ratios, slide 6; Q1 & Q5 solutions
- **Practical application:** Monitoring and comparison over time.

### Inventory turnover — معدل دوران المخزون

- **Category:** activity · **Methodology:** both
- **Formula:** COGS / Inventory
- **Required accounts:** Cost of goods sold, Inventory
- **Account classifications:** bs.ca.inventory, is.cogs
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Inventory is sold and replaced X times a year. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** Inventory balance for turnover / ASP
- **Source:** Lecture 3 — Financial Ratios, slide 6; Q1, Q2 & Q5 solutions
- **Practical application:** Review slow-moving stock and purchasing policy.

### Payables turnover — معدل دوران الدائنين

- **Category:** activity · **Methodology:** professional
- **Formula:** COGS (or credit purchases) / AP
- **Required accounts:** Cost of goods sold, credit_purchases, Accounts payable / creditors
- **Account classifications:** Additional_Info, bs.cl.payables, is.cogs
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Suppliers are paid X times a year.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** Payables turnover driver; Payables balance for turnover / payment period
- **Source:** Professional — not covered in the lectures
- **Practical application:** Monitoring and comparison over time.

### Average payment period — متوسط فترة السداد

- **Category:** activity · **Methodology:** professional
- **Formula:** (AP × 360) / COGS (or credit purchases)
- **Required accounts:** Accounts payable / creditors, Cost of goods sold, credit_purchases
- **Account classifications:** Additional_Info, bs.cl.payables, is.cogs
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Suppliers are paid on average after X days.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** Payables turnover driver; Payables balance for turnover / payment period; Days in the year
- **Source:** Professional — not covered in the lectures
- **Practical application:** Monitoring and comparison over time.

### Cash conversion cycle — دورة التحويل النقدي

- **Category:** activity · **Methodology:** professional
- **Formula:** (ASP + ACP) − Average payment period
- **Required accounts:** Inventory, Receivables (A/R + N/R), Accounts payable / creditors, Cost of goods sold, Credit sales
- **Account classifications:** Additional_Info: credit_sales (or sales − cash_sales; or assumption), bs.ca.inventory, bs.ca.notes_receivable, bs.ca.receivables, bs.cl.payables, is.cogs
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Cash is tied up in operations for X days after paying suppliers. Lower is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** Inventory balance for turnover / ASP; Receivables balance for turnover / ACP; Payables balance for turnover / payment period; Payables turnover driver; Credit sales when not provided; Days in the year
- **Source:** Professional — extends the course's 'liquidity of inventory'
- **Practical application:** Monitoring and comparison over time.

### Gross profit margin (GPM) — هامش مجمل الربح

- **Category:** profitability · **Methodology:** both
- **Formula:** Gross profit / Sales
- **Required accounts:** Gross profit, Sales / revenue
- **Account classifications:** is.cogs, is.revenue
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Each unit of sales leaves X after cost of goods sold. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Lecture 3 — Financial Ratios, slide 7
- **Practical application:** Monitoring and comparison over time.

### Operating income margin (OIM) — هامش الدخل التشغيلي

- **Category:** profitability · **Methodology:** academic
- **Formula:** EBIT / Sales
- **Required accounts:** EBIT, Sales / revenue
- **Account classifications:** (is.finance_income per assumption), is.cogs, is.opex.*, is.other_expense, is.other_income, is.revenue
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Each unit of sales generates X of EBIT. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Lecture 3 — Financial Ratios, slides 7–8; Q3 & Q5 solutions
- **Practical application:** Monitoring and comparison over time.

### Operating profit margin (before non-operating items) — هامش ربح التشغيل

- **Category:** profitability · **Methodology:** professional
- **Formula:** (Sales − COGS − operating expenses) / Sales
- **Required accounts:** Operating income, Sales / revenue
- **Account classifications:** is.cogs, is.opex.*, is.revenue
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Core operations earn X per unit of sales before non-operating items. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Lecture 3 — Financial Ratios, slide 7 (OI definition)
- **Practical application:** Monitoring and comparison over time.

### Net income margin (NIM) — هامش صافي الربح

- **Category:** profitability · **Methodology:** both
- **Formula:** Net income / Sales
- **Required accounts:** Net profit, Sales / revenue
- **Account classifications:** EBT, is.revenue, is.tax
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Each unit of sales leaves X net profit. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Lecture 3 — Financial Ratios, slide 7
- **Practical application:** Monitoring and comparison over time.

### Return on investment (ROI / ROA academic) — العائد على الاستثمار

- **Category:** profitability · **Methodology:** academic
- **Formula:** EBIT / Total assets
- **Required accounts:** EBIT, Total assets
- **Account classifications:** (is.finance_income per assumption), bs.ca.cash, bs.ca.inventory, bs.ca.notes_receivable, bs.ca.other, bs.ca.prepaid, bs.ca.receivables, bs.ca.st_investments, bs.nca.acc_depreciation, bs.nca.intangibles, bs.nca.land, bs.nca.lt_investments, bs.nca.other, bs.nca.ppe_gross, bs.nca.ppe_net, is.cogs, is.opex.*, is.other_expense, is.other_income, is.revenue
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Every unit invested in assets earns X before interest and tax. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** ROI definition; Total assets / equity balance for returns & turnover
- **Source:** Lecture 3 — Financial Ratios, slide 7; Q3 & Q5 solutions
- **Practical application:** Monitoring and comparison over time.

### Return on equity (ROE) — العائد على حقوق الملكية

- **Category:** profitability · **Methodology:** academic
- **Formula:** EBT / Equity (course) · NP / Equity (professional option)
- **Required accounts:** EBT, Net profit, Monetary equity (O/E incl. preferred)
- **Account classifications:** EBIT, EBT, bs.eq.common, bs.eq.other, bs.eq.preferred, bs.eq.reserves, bs.eq.retained, is.interest, is.tax
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Owners earn X on each unit of equity. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** ROE definition; Total assets / equity balance for returns & turnover
- **Source:** Lecture 3 — Financial Ratios, slide 7; Q5 solution
- **Practical application:** Monitoring and comparison over time.

### Return on borrowed funds (ROBF) — العائد على الأموال المقترضة

- **Category:** profitability · **Methodology:** academic
- **Formula:** (ROI − Interest / BF) × (BF / OE)
- **Required accounts:** EBIT, Total assets, Interest expense, Total debts (liabilities), Interest-bearing debt, Monetary equity (O/E incl. preferred), Common owners' equity
- **Account classifications:** (is.finance_income per assumption), bs.ca.cash, bs.ca.inventory, bs.ca.notes_receivable, bs.ca.other, bs.ca.prepaid, bs.ca.receivables, bs.ca.st_investments, bs.cl.accrued, bs.cl.advance_revenue, bs.cl.notes_payable, bs.cl.other, bs.cl.payables, bs.cl.st_debt, bs.cl.tax_payable, bs.eq.common, bs.eq.other, bs.eq.preferred, bs.eq.reserves, bs.eq.retained, bs.nca.acc_depreciation, bs.nca.intangibles, bs.nca.land, bs.nca.lt_investments, bs.nca.other, bs.nca.ppe_gross, bs.nca.ppe_net, bs.ncl.bonds, bs.ncl.lt_loans, bs.ncl.other, is.cogs, is.interest, is.opex.*, is.other_expense, is.other_income, is.revenue
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Borrowing adds X to the return on equity. A negative value means debt costs more than it earns.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** ROI definition; BF (borrowed funds) in ROBF; OE (owners' equity) in ROBF / ROE; Total assets / equity balance for returns & turnover
- **Source:** Lecture 3 — Financial Ratios, slide 7; Q5 solution
- **Practical application:** Monitoring and comparison over time.

### ROE = ROI + ROBF (course identity check) — تحقق: العائد على الملكية = ROI + ROBF

- **Category:** profitability · **Methodology:** academic
- **Formula:** ROI + ROBF
- **Required accounts:** EBIT, Total assets, Interest expense, Total debts (liabilities), Monetary equity (O/E incl. preferred)
- **Account classifications:** (is.finance_income per assumption), bs.ca.cash, bs.ca.inventory, bs.ca.notes_receivable, bs.ca.other, bs.ca.prepaid, bs.ca.receivables, bs.ca.st_investments, bs.cl.accrued, bs.cl.advance_revenue, bs.cl.notes_payable, bs.cl.other, bs.cl.payables, bs.cl.st_debt, bs.cl.tax_payable, bs.eq.common, bs.eq.other, bs.eq.preferred, bs.eq.reserves, bs.eq.retained, bs.nca.acc_depreciation, bs.nca.intangibles, bs.nca.land, bs.nca.lt_investments, bs.nca.other, bs.nca.ppe_gross, bs.nca.ppe_net, bs.ncl.bonds, bs.ncl.lt_loans, bs.ncl.other, is.cogs, is.interest, is.opex.*, is.other_expense, is.other_income, is.revenue
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** ROI + ROBF = X. This equals EBT/Equity exactly only when BF = total liabilities and OE = total equity. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** ROI definition; BF (borrowed funds) in ROBF; OE (owners' equity) in ROBF / ROE; Total assets / equity balance for returns & turnover
- **Source:** Lecture 3 — Financial Ratios, slide 7 (D)
- **Practical application:** Monitoring and comparison over time.

### Return on assets (net) — العائد على الأصول (صافي)

- **Category:** profitability · **Methodology:** professional
- **Formula:** Net profit / Total assets
- **Required accounts:** Net profit, Total assets
- **Account classifications:** EBT, bs.ca.cash, bs.ca.inventory, bs.ca.notes_receivable, bs.ca.other, bs.ca.prepaid, bs.ca.receivables, bs.ca.st_investments, bs.nca.acc_depreciation, bs.nca.intangibles, bs.nca.land, bs.nca.lt_investments, bs.nca.other, bs.nca.ppe_gross, bs.nca.ppe_net, is.tax
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Assets earn X after interest and tax. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** Total assets / equity balance for returns & turnover
- **Source:** Professional
- **Practical application:** Monitoring and comparison over time.

### Return on capital employed (ROCE) — العائد على رأس المال المستخدم

- **Category:** profitability · **Methodology:** professional
- **Formula:** EBIT / (Total assets − Current liabilities)
- **Required accounts:** EBIT, Total assets, Current liabilities
- **Account classifications:** (is.finance_income per assumption), bs.ca.cash, bs.ca.inventory, bs.ca.notes_receivable, bs.ca.other, bs.ca.prepaid, bs.ca.receivables, bs.ca.st_investments, bs.cl.accrued, bs.cl.advance_revenue, bs.cl.notes_payable, bs.cl.other, bs.cl.payables, bs.cl.st_debt, bs.cl.tax_payable, bs.nca.acc_depreciation, bs.nca.intangibles, bs.nca.land, bs.nca.lt_investments, bs.nca.other, bs.nca.ppe_gross, bs.nca.ppe_net, is.cogs, is.opex.*, is.other_expense, is.other_income, is.revenue
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Long-term capital earns X before interest and tax. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Professional; capital = equity + LTL (Lecture 1, slide 13)
- **Practical application:** Monitoring and comparison over time.

### DuPont: OIM × TATO — نظام ديبونت: هامش التشغيل × دوران الأصول

- **Category:** dupont · **Methodology:** academic
- **Formula:** (EBIT / Sales) × (Sales / Total assets)
- **Required accounts:** EBIT, Sales / revenue, Total assets
- **Account classifications:** (is.finance_income per assumption), bs.ca.cash, bs.ca.inventory, bs.ca.notes_receivable, bs.ca.other, bs.ca.prepaid, bs.ca.receivables, bs.ca.st_investments, bs.nca.acc_depreciation, bs.nca.intangibles, bs.nca.land, bs.nca.lt_investments, bs.nca.other, bs.nca.ppe_gross, bs.nca.ppe_net, is.cogs, is.opex.*, is.other_expense, is.other_income, is.revenue
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** ROI of X = profitability (OIM) × efficiency (TATO). Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** Total assets / equity balance for returns & turnover
- **Source:** Lecture 3 — Financial Ratios, slide 8; Q3 solution
- **Practical application:** Monitoring and comparison over time.

### Market value added (MVA) — القيمة السوقية المضافة

- **Category:** market · **Methodology:** academic
- **Formula:** (No. of shares × market price) − Total O/E
- **Required accounts:** shares_outstanding, share_price, Monetary equity (O/E incl. preferred)
- **Account classifications:** Additional_Info, bs.eq.common, bs.eq.other, bs.eq.preferred, bs.eq.reserves, bs.eq.retained
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** The market values the equity X above its book value. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Lecture 3 — Financial Ratios, slide 9; Q3 solution
- **Practical application:** Monitoring and comparison over time.

### Economic value added (EVA — course method) — القيمة الاقتصادية المضافة

- **Category:** market · **Methodology:** academic
- **Formula:** NP − (Interest + PS dividends + CS dividends + opportunity rate × RE)
- **Required accounts:** Net profit, Interest expense, Preferred dividends, Common dividends, Retained earnings
- **Account classifications:** EBT, bs.eq.retained, is.dividends.common, is.dividends.preferred, is.interest, is.tax
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** After charging every source of capital, the company created X of economic value. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** Opportunity cost of retained earnings (EVA)
- **Source:** Lecture 3 — Financial Ratios, slide 9; Q3 solution (10% on R/E)
- **Practical application:** Monitoring and comparison over time.

### Book value per share — القيمة الدفترية للسهم

- **Category:** market · **Methodology:** academic
- **Formula:** O/E / Number of shares
- **Required accounts:** Monetary equity (O/E incl. preferred), shares_outstanding
- **Account classifications:** Additional_Info, bs.eq.common, bs.eq.other, bs.eq.preferred, bs.eq.reserves, bs.eq.retained
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Book value per share is X. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Lecture 1 — Financial Management, slide 33
- **Practical application:** Monitoring and comparison over time.

### Earnings per share — ربحية السهم

- **Category:** market · **Methodology:** professional
- **Formula:** (NP − preferred dividends) / Number of shares
- **Required accounts:** Net profit, Preferred dividends, shares_outstanding
- **Account classifications:** Additional_Info, EBT, is.dividends.preferred, is.tax
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Each common share earned X. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Professional
- **Practical application:** Monitoring and comparison over time.

### Operating cash flow — التدفق النقدي التشغيلي

- **Category:** cashflow · **Methodology:** professional
- **Formula:** Net cash from operating activities
- **Required accounts:** Operating cash flow
- **Account classifications:** cf.total.operating or Σ cf.op.item
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Operations generated X in cash. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Professional
- **Practical application:** Monitoring and comparison over time.

### Investing cash flow — التدفق النقدي الاستثماري

- **Category:** cashflow · **Methodology:** professional
- **Formula:** Net cash from investing activities
- **Required accounts:** Investing cash flow
- **Account classifications:** cf.total.investing
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Investing activities produced X.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Professional
- **Practical application:** Monitoring and comparison over time.

### Financing cash flow — التدفق النقدي التمويلي

- **Category:** cashflow · **Methodology:** professional
- **Formula:** Net cash from financing activities
- **Required accounts:** Financing cash flow
- **Account classifications:** cf.total.financing
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Financing activities produced X.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Professional
- **Practical application:** Monitoring and comparison over time.

### Free cash flow — التدفق النقدي الحر

- **Category:** cashflow · **Methodology:** professional
- **Formula:** OCF − capital expenditure
- **Required accounts:** Operating cash flow, Capital expenditure
- **Account classifications:** cf.inv.capex, cf.total.operating or Σ cf.op.item
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** After investing in fixed assets, X of cash remains. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Professional
- **Practical application:** Monitoring and comparison over time.

### Operating cash-flow ratio — نسبة التدفق النقدي التشغيلي

- **Category:** cashflow · **Methodology:** professional
- **Formula:** OCF / Current liabilities
- **Required accounts:** Operating cash flow, Current liabilities
- **Account classifications:** bs.cl.accrued, bs.cl.advance_revenue, bs.cl.notes_payable, bs.cl.other, bs.cl.payables, bs.cl.st_debt, bs.cl.tax_payable, cf.total.operating or Σ cf.op.item
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Operating cash flow covers current liabilities X times. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Professional
- **Practical application:** Monitoring and comparison over time.

### Cash quality of earnings — جودة الأرباح النقدية

- **Category:** cashflow · **Methodology:** professional
- **Formula:** OCF / Net profit
- **Required accounts:** Operating cash flow, Net profit
- **Account classifications:** EBT, cf.total.operating or Σ cf.op.item, is.tax
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Each unit of net profit is backed by X units of operating cash. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Professional
- **Practical application:** Monitoring and comparison over time.

### Cash-flow debt coverage — تغطية الديون بالتدفق النقدي

- **Category:** cashflow · **Methodology:** professional
- **Formula:** OCF / Total debts
- **Required accounts:** Operating cash flow, Total debts (liabilities)
- **Account classifications:** bs.cl.accrued, bs.cl.advance_revenue, bs.cl.notes_payable, bs.cl.other, bs.cl.payables, bs.cl.st_debt, bs.cl.tax_payable, bs.ncl.bonds, bs.ncl.lt_loans, bs.ncl.other, cf.total.operating or Σ cf.op.item
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Operating cash flow covers X of total debts per year. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Professional
- **Practical application:** Monitoring and comparison over time.

### Monetary break-even point — نقطة التعادل بالقيمة

- **Category:** breakeven · **Methodology:** academic
- **Formula:** Fixed costs / (1 − Variable costs / Sales)
- **Required accounts:** fixed_costs, variable_costs, Sales / revenue
- **Account classifications:** Additional_Info, is.revenue
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Sales of X are needed to cover all costs.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Lecture 8 — Break-even & Operating Leverage, slide 5
- **Practical application:** Monitoring and comparison over time.

### Margin of safety — هامش الأمان

- **Category:** breakeven · **Methodology:** professional
- **Formula:** (Sales − Break-even sales) / Sales
- **Required accounts:** fixed_costs, variable_costs, Sales / revenue
- **Account classifications:** Additional_Info, is.revenue
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** Sales can fall X before losses begin. Higher is better.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Professional (extends Lecture 8)
- **Practical application:** Monitoring and comparison over time.

### Degree of operating leverage — درجة الرافعة التشغيلية

- **Category:** breakeven · **Methodology:** professional
- **Formula:** (Sales − VC) / (Sales − VC − FC)
- **Required accounts:** fixed_costs, variable_costs, Sales / revenue
- **Account classifications:** Additional_Info, is.revenue
- **Calculation:** Closing balances unless the approved assumption selects averages; 360-day year by default; Decimal arithmetic.
- **Interpretation:** A 1% change in sales changes operating profit by X%.
- **Benchmarks:** Configurable per industry / company; otherwise historical trend (limitation stated).
- **Assumptions:** None
- **Source:** Professional (quantifies the Lecture 8 concept)
- **Practical application:** Monitoring and comparison over time.

### Sources & Uses statement

- **Category:** Sources & uses of money · **Methodology:** academic
- **Formula:** Change = closing − opening. Asset ↑ = use, asset ↓ = source; liability/equity ↑ = source, ↓ = use; accumulated depreciation ↑ = source. Σ sources = Σ uses.
- **Required accounts:** All balance-sheet accounts for two consecutive years
- **Account classifications:** bs.* (subtotals excluded)
- **Calculation:** —
- **Interpretation:** Rank sources and uses by %, split short-/long-term (golden rule deviation = |ST sources% − ST uses%|) and internal vs external finance.
- **Benchmarks:** Golden rule: short-term uses financed by short-term sources; long-term by long-term.
- **Assumptions:** Gross fixed assets and accumulated depreciation shown separately when available (Lecture 2).
- **Source:** Lecture 2 — Financial Analysis (XYZ Co. example, 49 = 49); Q3 solution (57,200; 6.8% deviation; 77.3% internal)
- **Practical application:** Explains where money came from and how it was used; tests financing discipline.

### Absolute / % change, CAGR

- **Category:** Horizontal analysis · **Methodology:** professional
- **Formula:** Δ = current − previous; %Δ = Δ / |previous|; CAGR = (end/begin)^(1/n) − 1
- **Required accounts:** Any line with ≥ 2 years
- **Account classifications:** All
- **Calculation:** —
- **Interpretation:** Zero base → not meaningful; sign change → flagged; CAGR only when begin and end > 0.
- **Benchmarks:** Company's own history
- **Assumptions:** None
- **Source:** Specification §8 (not in the lectures)
- **Practical application:** Trend detection across 3–5+ years.

### Common-size statements

- **Category:** Vertical analysis · **Methodology:** professional
- **Formula:** Balance-sheet item / total assets; income-statement item / sales
- **Required accounts:** Total assets, sales
- **Account classifications:** All
- **Calculation:** —
- **Interpretation:** Structure of assets, financing and costs.
- **Benchmarks:** Industry common-size if available
- **Assumptions:** None
- **Source:** Specification §9.2
- **Practical application:** Comparing structure across years and companies.

### Financial sources needed (% of sales)

- **Category:** Forecasting · **Methodology:** academic
- **Formula:** AFN = A/S1·ΔS − L/S1·ΔS − P·S2·(1 − D)
- **Required accounts:** Spontaneous assets & liabilities, sales, margin, payout
- **Account classifications:** Items with a direct relation to sales
- **Calculation:** —
- **Interpretation:** Positive = external finance needed (apply financial hierarchy).
- **Benchmarks:** —
- **Assumptions:** Spontaneous items move proportionally with sales
- **Source:** Lecture 6 — Percentage of Sales (231; S2 = 413)
- **Practical application:** Planning growth financing.

### Forecasted financial position

- **Category:** Forecasting · **Methodology:** academic
- **Formula:** Stage 1: grow sales-related IS and BS items by (1 + g); Stage 2: finance the gap per financial hierarchy; iterate for new interest and dividends until balanced.
- **Required accounts:** Full IS and BS
- **Account classifications:** All
- **Calculation:** —
- **Interpretation:** Determines required financing and its cost.
- **Benchmarks:** —
- **Assumptions:** Hierarchy %, interest rates, share price, DPS growth
- **Source:** Lecture 5; Q4 solution
- **Practical application:** Budgeting future financing.

### Break-even (units & monetary)

- **Category:** Planning & control · **Methodology:** academic
- **Formula:** Q = FC / (P − AVC); Monetary BEP = TFC / (1 − VC / Sales)
- **Required accounts:** Fixed and variable costs (Additional_Info)
- **Account classifications:** —
- **Calculation:** —
- **Interpretation:** High fixed costs = high operating leverage: small sales changes → large profit changes.
- **Benchmarks:** —
- **Assumptions:** Linear cost behaviour
- **Source:** Lecture 8 — Break-even & Operating Leverage
- **Practical application:** Profit planning and risk of operating leverage.

### Cash-flow forecast (budget)

- **Category:** Planning & control · **Methodology:** academic
- **Formula:** Receipts (cash sales + collections by credit pattern + asset sales) − payments; compare with minimum cash → surplus/deficit
- **Required accounts:** Monthly sales, collection pattern, expenditures
- **Account classifications:** —
- **Calculation:** —
- **Interpretation:** Deficit months need short-term finance.
- **Benchmarks:** Minimum cash balance
- **Assumptions:** Collection pattern (e.g. 10% cash, 90% credit: 90% after 1 month, 10% after 2)
- **Source:** Lecture 7
- **Practical application:** Short-term financial planning (not computed from annual statements).
