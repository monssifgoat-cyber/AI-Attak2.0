"""
حارس النطاق (Scope Guard)
==========================
يمنع أي وكيل (recon/scan/exploit) من العمل على هدف لم يُدرج صراحة في
scope.targets داخل config.yaml، أو يُضَف عبر --add-target في نفس الجلسة.

ملاحظة مهمة: هذه الأداة لا توفّر — وبشكل مقصود — أي خيار سطر أوامر أو
إعداد لتعطيل هذا التحقق بالكامل. السبب أن تعطيله يُفقد الفريق الغطاء
القانوني لعمله (العميل وقّع على نطاق محدد، وليس "كل شيء"). الطريقة
الصحيحة لإضافة هدف جديد هي --add-target، وتُستخدم فقط بعد الحصول على
تفويض موثّق من العميل لذلك النطاق.
"""
from urllib.parse import urlparse


class ScopeViolation(Exception):
    """يُرفع عند محاولة استهداف نطاق غير مصرّح به."""


class ScopeGuard:
    def __init__(self, allowed_targets: list[str]):
        if not allowed_targets:
            raise ValueError("قائمة الأهداف المصرّح بها فارغة")
        self.allowed = set(allowed_targets)

    def add_target(self, target: str) -> None:
        """
        إضافة صريحة لهدف جديد ضمن هذه الجلسة فقط (لا يُكتب في config.yaml
        تلقائيًا). استخدمها فقط بعد التأكد من وجود تفويض موثّق من العميل.
        """
        self.allowed.add(target)

    @staticmethod
    def _host(value: str) -> str:
        parsed = urlparse(value if "://" in value else f"https://{value}")
        return (parsed.hostname or value).lower()

    def check(self, target: str) -> None:
        """يرفع ScopeViolation إن كان الهدف خارج النطاق المصرّح به."""
        host = self._host(target)
        for allowed in self.allowed:
            allowed_host = self._host(allowed)
            if host == allowed_host or host.endswith("." + allowed_host):
                return
        raise ScopeViolation(
            f"الهدف '{target}' خارج النطاق المصرّح به في config.yaml.\n"
            f"إن كان هذا نطاقًا جديدًا تملك تفويضًا موثّقًا لاختباره، "
            f"أضفه عبر: --add-target \"{target}\""
        )
