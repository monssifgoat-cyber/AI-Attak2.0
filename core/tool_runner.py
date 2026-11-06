"""
مشغّل عام لأدوات الأمن الخارجية المثبّتة في صورة Docker (أو على مضيف Kali).
كل دالة هنا تستدعي أداة معروفة وموثّقة رسميًا بوضعها القياسي للفحص/الاكتشاف
(وليس بوضعها التخريبي)، وتتحقق من توفر الأداة قبل التنفيذ بدل الفشل بصمت.
"""
import json
import logging
import shutil
import subprocess

log = logging.getLogger("pentest-team")


def is_available(tool: str) -> bool:
    return shutil.which(tool) is not None


def _run(cmd: list[str], timeout: int = 300) -> str:
    log.debug("تنفيذ: %s", " ".join(cmd))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            log.warning("%s انتهى برمز %s: %s", cmd[0], result.returncode, result.stderr[:300])
        return result.stdout
    except subprocess.TimeoutExpired:
        log.warning("انتهت مهلة تنفيذ %s", cmd[0])
        return ""
    except FileNotFoundError:
        log.warning("الأداة غير مثبّتة: %s", cmd[0])
        return ""


def run_nmap(target_host: str, ports: list[int]) -> str:
    if not is_available("nmap"):
        return ""
    port_arg = ",".join(str(p) for p in ports)
    return _run(["nmap", "-sV", "-p", port_arg, "--open", target_host], timeout=180)


def run_httpx(target_url: str) -> dict:
    if not is_available("httpx"):
        return {}
    out = _run(["httpx", "-u", target_url, "-json", "-silent"], timeout=60)
    try:
        return json.loads(out.strip().splitlines()[0]) if out.strip() else {}
    except (json.JSONDecodeError, IndexError):
        return {}


def run_katana(target_url: str, max_urls: int = 200) -> list[str]:
    if not is_available("katana"):
        return []
    out = _run(["katana", "-u", target_url, "-silent", "-jc", "-depth", "2"], timeout=180)
    urls = [line.strip() for line in out.splitlines() if line.strip()]
    return urls[:max_urls]


def run_nuclei(target_url: str) -> list[dict]:
    if not is_available("nuclei"):
        return []
    out = _run(["nuclei", "-u", target_url, "-jsonl", "-silent"], timeout=600)
    findings = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            findings.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return findings


def run_sqlmap(target_url: str, level: int = 1, risk: int = 1) -> str:
    if not is_available("sqlmap"):
        return ""
    # --batch: بدون أسئلة تفاعلية | بدون --os-shell أو --dump — هذا اكتشاف فقط، ليس استغلالًا
    return _run(
        ["sqlmap", "-u", target_url, "--batch", f"--level={level}", f"--risk={risk}"],
        timeout=600,
    )
