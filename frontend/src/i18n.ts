import { createContext, useContext } from "react";

const AR: Record<string, string> = {
  "Financial Analysis Platform": "منصة التحليل المالي", "AI-assisted, analyst-controlled": "بمساعدة الذكاء الاصطناعي وتحت سيطرة المحلل",
  Companies: "الشركات", "New company": "شركة جديدة", Benchmarks: "المعايير المرجعية", "Multi-company comparison": "مقارنة الشركات",
  Methodology: "المنهجية", Overview: "نظرة عامة", "Upload & Data Review": "الرفع ومراجعة البيانات", Classification: "تصنيف الحسابات",
  Assumptions: "الافتراضات", Statements: "القوائم المالية", Ratios: "النسب المالية", "Year comparison": "مقارنة السنوات",
  "Sources & Uses": "المصادر والاستخدامات", "AI Analyst": "المحلل الذكي", "Forecasting & Planning": "التنبؤ والتخطيط المالي", "Evaluation & Reports": "التقييم والتقارير", "Audit trail": "سجل التدقيق",
  User: "المستخدم", Language: "اللغة", Create: "إنشاء", Name: "الاسم", Industry: "القطاع", Currency: "العملة", Country: "الدولة",
  "Download template": "تحميل القالب", "Download 5-year sample": "تحميل نموذج لخمس سنوات", "Upload Excel": "رفع ملف Excel",
  Approve: "اعتماد", Modify: "تعديل", Reject: "رفض", "Request info": "طلب معلومات", Reopen: "إعادة فتح", Accept: "قبول",
  "Apply to similar": "تطبيق على المشابه", Status: "الحالة", Year: "السنة", Value: "القيمة", Account: "الحساب", Formula: "المعادلة",
  Interpretation: "التفسير", Risk: "المخاطر", Benchmark: "المعيار", "Suggested action": "الإجراء المقترح", Source: "المصدر",
  "Approve analysis": "اعتماد التحليل", "Export Excel": "تصدير Excel", "Export PDF": "تصدير PDF", Strengths: "نقاط القوة", Weaknesses: "نقاط الضعف",
  Risks: "المخاطر", Recommendations: "التوصيات", Limitations: "القيود", "Ask": "اسأل", "Data versions": "نسخ البيانات",
  "Validation issues": "مشكلات التحقق", "Pending": "قيد الانتظار", "Why": "السبب", Question: "سؤال", Confidence: "الثقة",
  "Balance Sheet": "الميزانية", "Income Statement": "قائمة الدخل", "Cash Flow": "التدفقات النقدية", Methodology_academic: "أكاديمية",
};
export type Lang = "en" | "ar";
export const LangCtx = createContext<Lang>("en");
export function useT() {
  const lang = useContext(LangCtx);
  return (s: string) => (lang === "ar" ? AR[s] || s : s);
}
export function useLang() { return useContext(LangCtx); }
