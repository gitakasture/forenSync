import re
from datetime import datetime
from typing import List, Dict
from plugins.base import BaseParserPlugin


class ApacheAccessParser(BaseParserPlugin):
    source_name = "apache_access"

    LOG_PATTERN = re.compile(
        r'^(?P<ip>\S+) \S+ \S+ \[(?P<datetime>[^\]]+)\] '
        r'"(?P<method>\S+) (?P<path>\S+) \S+" '
        r'(?P<status>\d+) (?P<size>\S+)'
    )

    DETECTION_PATTERNS = [LOG_PATTERN]

    def parse(self, filepath: str) -> List[Dict]:
        events = []

        with open(filepath, "r", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                event = self._match_line(line)
                events.append(event)

        return events

    def _match_line(self, line: str) -> Dict:
        m = self.LOG_PATTERN.match(line)
        if not m:
            return self._build_unparsed_event(line)

        timestamp = self._build_timestamp(m.group("datetime"))
        status = m.group("status")

        return self._build_event(
            timestamp=timestamp,
            host="apache_server",  # log itself doesn't name its own host
            actor=m.group("ip"),
            action=m.group("method"),
            object_=m.group("path"),
            result=status,
            raw_log=line,
        )

    def _build_unparsed_event(self, raw_log: str) -> Dict:
        return self._build_event(
            timestamp="unknown",
            host="unknown",
            actor="unknown",
            action="unparsed_event",
            object_="unknown",
            result="unknown",
            raw_log=raw_log,
        )

    def _build_timestamp(self, datetime_str: str) -> str:
        # e.g. "17/May/2015:10:05:03 +0000"
        from datetime import timezone
        dt = datetime.strptime(datetime_str, "%d/%b/%Y:%H:%M:%S %z")
        utc_dt = dt.astimezone(timezone.utc)
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")