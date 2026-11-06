"""
غلاف موحّد للـ LLM: يدعم Ollama (محلي) و Gemini (سحابي) بنفس الواجهة،
بحيث لا يهتم أي وكيل بأي مزوّد يُستخدم فعليًا.
"""
import json
import logging
import time

import requests

from core.utils import env

log = logging.getLogger("pentest-team")


class LLM:
    def __init__(self, cfg: dict):
        self.provider = cfg.get("provider", "ollama")
        self.temperature = cfg.get("temperature", 0.2)

        if self.provider == "ollama":
            self.base_url = cfg.get("ollama_url", "http://localhost:11434")
            self.model = cfg.get("model", "qwen2.5:14b")
        elif self.provider == "gemini":
            self.model = cfg.get("gemini_model", "gemini-2.0-flash")
            self.api_key = env("GEMINI_API_KEY")
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY غير موجود في .env")
        else:
            raise ValueError(f"مزوّد LLM غير مدعوم: {self.provider}")

    def generate(self, prompt: str, system: str | None = None,
                 json_mode: bool = False, retries: int = 2) -> str:
        """يستدعي النموذج ويعيد النص (أو نص JSON إن json_mode=True)."""
        for attempt in range(retries + 1):
            try:
                if self.provider == "ollama":
                    return self._call_ollama(prompt, system, json_mode)
                return self._call_gemini(prompt, system, json_mode)
            except Exception as exc:  # noqa: BLE001
                log.warning("فشل استدعاء LLM (محاولة %s/%s): %s", attempt + 1, retries + 1, exc)
                if attempt == retries:
                    raise
                time.sleep(2 * (attempt + 1))

    def generate_json(self, prompt: str, system: str | None = None) -> dict:
        raw = self.generate(prompt, system=system, json_mode=True)
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            log.warning("تعذّر تحليل JSON من رد النموذج، سيُعاد كنص خام")
            return {"raw": raw}

    def _call_ollama(self, prompt, system, json_mode) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system or "",
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        if json_mode:
            payload["format"] = "json"
        resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=180)
        resp.raise_for_status()
        return resp.json()["response"]

    def _call_gemini(self, prompt, system, json_mode) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"temperature": self.temperature},
        }
        if json_mode:
            payload["generationConfig"]["response_mime_type"] = "application/json"
        resp = requests.post(url, json=payload, timeout=180)
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
