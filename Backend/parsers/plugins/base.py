from abc import ABC, abstractmethod
from typing import List, Dict

"""
abc module is used for creating abstract base class without this Python will refuse to let you create an instance of it.
A list is an ordered, mutable sequence of items. You access items by index (0, 1, 2, …).
A dictionary stores key–value pairs, where each key is unique and used to access its value.
"""


class BaseParserPlugin(ABC):
    """

    Abstract base class for all log parser plugins.
    Every plugin (auth log, syslog, apache access log, etc.)
    must inherit from this class and implement parse().
    """

    # Every plugin must set this — identifies which 'source' value
    # gets stamped onto every event this plugin produces.
    source_name: str = "unknown"

    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def parse(self, filepath: str) -> List[Dict]:
        """
        Read the log file at `filepath` and return a list of
        standardized event dicts.

        Each dict MUST contain these keys:
            timestamp   (str, ISO 8601 UTC, e.g. "2005-06-18T02:08:11Z")
            source      (str, e.g. "linux_syslog")
            host        (str)
            actor       (str)
            action      (str)
            object      (str)
            result      (str)
            raw_log     (str, the original untouched line)

        If a line cannot be parsed, it should be skipped
        (not crash the whole file) — log a warning instead.
        """
        pass

    def _build_event(self, timestamp, host, actor, action, object_, result, raw_log) -> Dict:
        """
        Helper method all plugins can reuse to build a
        standardized event dict without repeating the same
        dict structure in every plugin.
        """
        return {
            "timestamp": timestamp,
            "source": self.source_name,
            "host": host,
            "actor": actor,
            "action": action,
            "object": object_,
            "result": result,
            "raw_log": raw_log,
        }

    DETECTION_PATTERNS: list = []

    @classmethod
    def detect_confidence(cls, sample_lines) -> float:
        if not sample_lines or not cls.DETECTION_PATTERNS:
            return 0.0
        matches = sum(
            1 for line in sample_lines
            if any(pattern.search(line) for pattern in cls.DETECTION_PATTERNS)
        )
        return matches / len(sample_lines)