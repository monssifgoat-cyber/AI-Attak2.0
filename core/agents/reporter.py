"""وكيل التقارير: يحوّل مخرجات كل المراحل إلى تقرير نهائي بتنسيق CVSS."""
from datetime import datetime, timezone

from core.agents.base import BaseAgent

CVSS_PROMPT = """
أنت محلل أمن معلومات تكتب تقرير اختبار اختراق احترافي بتنسيق CVSS v3.1.
بناءً على بيانات الاستطلاع والفحص والتحقق من الاستغلال التالية، أنتج تقريرًا
بالعربية يتضمّن:
1. ملخص تنفيذي (3-5 أسطر)
2. جدول بالثغرات المكتشفة، لكل واحدة: الاسم، درجة CVSS التقديرية (0-10)،
   متجه CVSS (Vector string) إن أمكن تقديره، الخطورة (Critical/High/Medium/Low)،
   والوصف المختصر
3. توصيات إصلاح لكل ثغرة
4. ملاحظة منهجية: هل تم التحقق الفعلي من الاستغلال أم فقط رصد أولي

بيانات المراحل:
الاستطلاع: {recon}
الفحص: {scan}
التحقق من الاستغلال: {exploit}
"""


class ReporterAgent(BaseAgent):
    def run(self, target: str, context: dict) -> dict:
        report_text = self.llm.generate(
            CVSS_PROMPT.format(
                recon=context.get("recon", {}),
                scan=context.get("scan", {}),
                exploit=context.get("exploit", {}),
            ),
            system="أنت كاتب تقارير pentest محترف، دقيق ومحايد.",
        )

        return {
            "target": target,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "format": "cvss",
            "report_markdown": report_text,
            "raw_context": context,
        }
