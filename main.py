"""الخط الرئيسي: يمرّ بالمراحل حسب config.yaml (نفس فكرة النسخة الأصلية)."""
import argparse
import sys

from dotenv import load_dotenv
from rich.console import Console

from core.agents import ExploiterAgent, ReconAgent, ReporterAgent, ScannerAgent
from core.llm import LLM
from core.scope_guard import ScopeGuard, ScopeViolation
from core.utils import ensure_dirs, load_config, save_json, setup_logger

console = Console()


def parse_args():
    ap = argparse.ArgumentParser(description="Pentest Agent Team")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument(
        "--add-target",
        action="append",
        default=[],
        help="إضافة هدف جديد لهذه الجلسة فقط (تملك تفويضًا موثّقًا له). "
             "لا يوجد علم لتعطيل التحقق من النطاق بالكامل.",
    )
    ap.add_argument(
        "--confirm-exploit",
        action="store_true",
        help="يسمح بتنفيذ استغلال فعلي عبر Metasploit عند exploit.mode=full. "
             "بدون هذا العلم يبقى التحقق في وضع check الآمن دائمًا.",
    )
    ap.add_argument("--only-stage", choices=["recon", "scan", "exploit", "report"])
    return ap.parse_args()


def main():
    load_dotenv()
    args = parse_args()
    log = setup_logger()

    try:
        cfg = load_config(args.config)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[bold red]خطأ في الإعدادات:[/] {exc}")
        sys.exit(1)

    ensure_dirs(cfg["report"]["output_dir"], "output")

    guard = ScopeGuard(cfg["scope"]["targets"])
    for t in args.add_target:
        guard.add_target(t)
        log.info("تمت إضافة هدف لهذه الجلسة: %s", t)

    target = cfg["scope"]["targets"][0]
    try:
        guard.check(target)
    except ScopeViolation as exc:
        console.print(f"[bold red]رُفض التشغيل:[/] {exc}")
        sys.exit(1)

    llm = LLM(cfg["llm"])
    stages = cfg["stages"]
    only = args.only_stage
    context = {}

    try:
        if stages.get("recon") and (only in (None, "recon")):
            context["recon"] = ReconAgent("Recon", llm).timed_run(target, cfg)

        if stages.get("scan") and (only in (None, "scan")):
            context["scan"] = ScannerAgent("Scanner", llm).timed_run(target, cfg)

        if stages.get("exploit") and (only in (None, "exploit")):
            context["exploit"] = ExploiterAgent("Exploiter", llm).timed_run(
                target, context.get("scan", {}), cfg, confirm_exploit=args.confirm_exploit
            )

        if stages.get("report") and (only in (None, "report")):
            report = ReporterAgent("Reporter", llm).timed_run(target, context)
            out_path = f"{cfg['report']['output_dir']}/report.json"
            save_json(out_path, report)
            if cfg["report"].get("also_markdown", True):
                md_path = f"{cfg['report']['output_dir']}/report.md"
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(report["report_markdown"])
                console.print(f"[bold green]✔ التقرير جاهز:[/] {out_path} و {md_path}")
            else:
                console.print(f"[bold green]✔ التقرير جاهز:[/] {out_path}")

    except ScopeViolation as exc:
        console.print(f"[bold red]رُفض التشغيل:[/] {exc}")
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        log.exception("فشل غير متوقع أثناء التنفيذ")
        console.print(f"[bold red]خطأ:[/] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
