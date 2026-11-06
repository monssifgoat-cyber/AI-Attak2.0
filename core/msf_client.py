"""
تكامل مع Metasploit عبر RPC API (msfrpcd) باستخدام مكتبة pymetasploit3.

المتطلبات: تشغيل msfrpcd على المضيف (متوفر افتراضيًا على Kali Linux):
    msfrpcd -P $MSF_RPC_PASSWORD -S -a 127.0.0.1 -p 55553

التصميم الآمن المتعمّد:
- check() فقط هو ما يُستدعى تلقائيًا ضمن خط الأنابيب (pipeline). وهو إجراء
  غير مدمّر يسأل الـ module نفسه "هل الهدف عرضة لهذه الثغرة؟" دون إرسال
  أي payload فعلي.
- exploit() ينفّذ استغلالًا حقيقيًا وقد يفتح shell على الهدف. هذه الدالة
  موجودة للتكامل، لكن main.py لا يستدعيها إلا إذا مرّر المستخدم صراحة
  --confirm-exploit في سطر الأوامر — ولا تُفعَّل أبدًا من config.yaml وحده
  أو تلقائيًا بقرار من الـ LLM.
"""
import logging

log = logging.getLogger("pentest-team")


class MSFClient:
    def __init__(self, password: str, server: str = "127.0.0.1",
                 port: int = 55553, ssl: bool = True):
        from pymetasploit3.msfrpc import MsfRpcClient  # استيراد مؤجَّل: اختياري التثبيت

        self.client = MsfRpcClient(password, server=server, port=port, ssl=ssl)

    def find_modules(self, query: str) -> list[str]:
        """يبحث في قاعدة بيانات Metasploit عن modules مطابقة (مثلاً اسم/نسخة خدمة)."""
        try:
            results = self.client.modules.search(query)
            return [r.get("fullname") for r in results if r.get("fullname")]
        except Exception as exc:  # noqa: BLE001
            log.warning("فشل البحث في Metasploit عن '%s': %s", query, exc)
            return []

    def check(self, module_type: str, module_name: str, target: str,
              port: int, extra_opts: dict | None = None) -> str:
        """تحقق آمن فقط — لا يغيّر شيئًا في الهدف. يعيد 'vulnerable'/'safe'/'unknown'."""
        mod = self.client.modules.use(module_type, module_name)
        mod["RHOSTS"] = target
        mod["RPORT"] = port
        for k, v in (extra_opts or {}).items():
            mod[k] = v
        try:
            result = mod.check()
            return result.get("code", "unknown") if isinstance(result, dict) else str(result)
        except Exception as exc:  # noqa: BLE001
            log.warning("فشل check() على %s: %s", module_name, exc)
            return "unknown"

    def exploit(self, module_type: str, module_name: str, target: str, port: int,
                payload: str | None = None, extra_opts: dict | None = None) -> dict:
        """
        ⚠️ استغلال فعلي — يُستدعى فقط بعد --confirm-exploit من سطر الأوامر
        ومراجعة بشرية لنتيجة check(). راجع ملاحظة التصميم أعلى الملف.
        """
        mod = self.client.modules.use(module_type, module_name)
        mod["RHOSTS"] = target
        mod["RPORT"] = port
        for k, v in (extra_opts or {}).items():
            mod[k] = v
        if payload:
            pay = self.client.modules.use("payload", payload)
            return mod.execute(payload=pay)
        return mod.execute()
