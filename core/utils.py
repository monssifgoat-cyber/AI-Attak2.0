"""أدوات مساعدة مشتركة بين كل الوكلاء (agents)."""
import json
import logging
import os
from pathlib import Path

import yaml
from rich.logging import RichHandler


def setup_logger(name: str = "pentest-team") -> logging.Logger:
    """يهيّئ logger موحّد بمخرجات ملوّنة عبر rich."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
    )
    return logging.getLogger(name)


def load_config(path: str = "config.yaml") -> dict:
    """يحمّل config.yaml ويتحقق من وجود الحقول الأساسية."""
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    required = ["scope", "llm", "stages"]
    missing = [k for k in required if k not in cfg]
    if missing:
        raise ValueError(f"حقول ناقصة في {path}: {missing}")
    if not cfg["scope"].get("targets"):
        raise ValueError("scope.targets فارغ — أضف نطاق العميل أولًا في config.yaml")
    return cfg


def ensure_dirs(*paths: str) -> None:
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)


def save_json(path: str, data: dict) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)
