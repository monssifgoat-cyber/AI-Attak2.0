"""
وكيل الاستطلاع: جمع معلومات حول الهدف (منافذ مفتوحة، تقنيات مستخدمة،
نطاقات فرعية محتملة، روابط) دون إرسال أي حمولة هجومية — هذه مرحلة
معلوماتية بحتة تسبق مرحلة الفحص.
"""
from urllib.parse import urlparse

import dns.resolver
import whois

from core.agents.base import BaseAgent
from core.tool_runner import run_httpx, run_katana, run_nmap


class ReconAgent(BaseAgent):
    def run(self, target: str, cfg: dict) -> dict:
        host = urlparse(target).hostname or target
        recon_cfg = cfg.get("recon", {})
        tools = recon_cfg.get("tools", [])
        result = {"target": target, "host": host}

        if recon_cfg.get("dns", True):
            result["dns"] = self._dns_lookup(host)

        if recon_cfg.get("whois", True):
            result["whois"] = self._whois_lookup(host)

        if "nmap" in tools:
            result["nmap_raw"] = run_nmap(host, cfg["scope"]["allowed_ports"])

        if "httpx" in tools:
            result["httpx"] = run_httpx(target)

        if "katana" in tools:
            result["discovered_urls"] = run_katana(target)

        summary = self.llm.generate(
            f"لخّص نتائج الاستطلاع التالية لهدف اختبار اختراق مصرّح به في 3-4 أسطر "
            f"بالعربية، مع التركيز على أي معلومة تقنية مفيدة لمرحلة الفحص التالية:\n"
            f"{result}",
            system="أنت محلل أمن معلومات تساعد فريق pentest على تلخيص نتائج الاستطلاع.",
        )
        result["llm_summary"] = summary
        return result

    @staticmethod
    def _dns_lookup(host: str) -> dict:
        records = {}
        for rtype in ("A", "AAAA", "MX", "NS", "TXT"):
            try:
                answers = dns.resolver.resolve(host, rtype, lifetime=5)
                records[rtype] = [str(r) for r in answers]
            except Exception:  # noqa: BLE001
                continue
        return records

    @staticmethod
    def _whois_lookup(host: str) -> dict:
        try:
            w = whois.whois(host)
            return {
                "registrar": w.get("registrar"),
                "creation_date": str(w.get("creation_date")),
                "expiration_date": str(w.get("expiration_date")),
            }
        except Exception:  # noqa: BLE001
            return {}
