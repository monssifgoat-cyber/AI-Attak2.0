"""
وكيل الفحص: يشغّل أدوات فحص الثغرات القياسية (ZAP, nuclei, sqlmap) على
الهدف ويجمع تنبيهاتها في بنية موحّدة. كل أداة هنا تنفّذ اختباراتها
الخاصة وفق سلوكها الافتراضي الموثّق رسميًا — هذا الوكيل ينظّم تشغيلها
فقط ولا يضيف أي منطق هجومي من عنده.
"""
from core.agents.base import BaseAgent
from core.tool_runner import run_nuclei, run_sqlmap
from core.zap_client import ZAPClient


class ScannerAgent(BaseAgent):
    def run(self, target: str, cfg: dict) -> dict:
        scan_cfg = cfg.get("scan", {})
        tools = scan_cfg.get("tools", [])
        result = {"target": target, "alerts": []}

        if "zap" in tools:
            zap_cfg = scan_cfg.get("zap", {})
            zap = ZAPClient(zap_cfg.get("base_url", "http://zap:8080"))
            zap.spider(target, timeout_sec=zap_cfg.get("spider_timeout_sec", 120))
            zap.active_scan(target, timeout_sec=zap_cfg.get("ascan_timeout_sec", 900))
            for alert in zap.get_alerts(target):
                result["alerts"].append({
                    "source": "zap",
                    "name": alert.get("name"),
                    "risk": alert.get("risk"),
                    "confidence": alert.get("confidence"),
                    "url": alert.get("url"),
                    "param": alert.get("param"),
                    "description": alert.get("description"),
                    "solution": alert.get("solution"),
                })

        if "nuclei" in tools:
            for finding in run_nuclei(target):
                info = finding.get("info", {})
                result["alerts"].append({
                    "source": "nuclei",
                    "name": info.get("name"),
                    "risk": info.get("severity"),
                    "url": finding.get("matched-at"),
                    "description": info.get("description"),
                    "cve": info.get("classification", {}).get("cve-id"),
                })

        if "sqlmap" in tools:
            sqlmap_cfg = scan_cfg.get("sqlmap", {})
            raw = run_sqlmap(target, level=sqlmap_cfg.get("level", 1), risk=sqlmap_cfg.get("risk", 1))
            if "is vulnerable" in raw.lower() or "injection point" in raw.lower():
                result["alerts"].append({
                    "source": "sqlmap",
                    "name": "SQL Injection (مرشّح)",
                    "risk": "High",
                    "url": target,
                    "description": "sqlmap وجد مؤشرات على ثغرة حقن SQL — راجع الإخراج الكامل في السجلّ",
                })

        self.log.info("مرحلة الفحص: %d تنبيه إجمالًا", len(result["alerts"]))
        return result
