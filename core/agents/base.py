"""الفئة الأساسية (Base) التي يرث منها كل وكيل."""
import logging
import time


class BaseAgent:
    def __init__(self, name: str, llm):
        self.name = name
        self.llm = llm
        self.log = logging.getLogger("pentest-team")

    def run(self, *args, **kwargs):
        raise NotImplementedError

    def timed_run(self, *args, **kwargs):
        start = time.time()
        self.log.info("▶ بدء مرحلة: %s", self.name)
        result = self.run(*args, **kwargs)
        self.log.info("✔ انتهت مرحلة %s خلال %.1f ثانية", self.name, time.time() - start)
        return result
