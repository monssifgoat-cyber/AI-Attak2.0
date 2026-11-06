"""
غلاف بسيط حول REST API الرسمي لـ OWASP ZAP.
ZAP نفسه هو من يقوم بإرسال اختبارات الفحص الفعلية (active scan) —
هذا الملف يكتفي بتشغيل العملية ومتابعتها وسحب النتائج عبر الـ API الموثّق.
"""
import logging
import time

import requests

log = logging.getLogger("pentest-team")


class ZAPClient:
    def __init__(self, base_url: str, api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _get(self, path: str, **params):
        params["apikey"] = self.api_key
        resp = requests.get(f"{self.base_url}{path}", params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def spider(self, target: str, timeout_sec: int = 120) -> None:
        log.info("ZAP: بدء الزحف (spider) على %s", target)
        scan_id = self._get("/JSON/spider/action/scan/", url=target)["scan"]
        start = time.time()
        while time.time() - start < timeout_sec:
            status = int(self._get("/JSON/spider/view/status/", scanId=scan_id)["status"])
            if status >= 100:
                return
            time.sleep(3)
        log.warning("ZAP spider: انتهت المهلة قبل اكتمال 100%%")

    def active_scan(self, target: str, timeout_sec: int = 900) -> None:
        log.info("ZAP: بدء الفحص النشط (active scan) على %s", target)
        scan_id = self._get("/JSON/ascan/action/scan/", url=target)["scan"]
        start = time.time()
        while time.time() - start < timeout_sec:
            status = int(self._get("/JSON/ascan/view/status/", scanId=scan_id)["status"])
            if status >= 100:
                return
            time.sleep(5)
        log.warning("ZAP active scan: انتهت المهلة قبل اكتمال 100%%")

    def get_alerts(self, target: str) -> list[dict]:
        data = self._get("/JSON/core/view/alerts/", baseurl=target)
        return data.get("alerts", [])
