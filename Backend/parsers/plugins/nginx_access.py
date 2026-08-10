import re
from datetime import datetime, timezone
from typing import List, Dict
from plugins.base import BaseParserPlugin


class NginxAccessParser(BaseParserPlugin):
    source_name = "nginx_access"

    LOG_PATTERN = re.compile(
        r'^(?P<ip>\S+) \S+ \S+ \[(?P<datetime>[^\]]+)\] '
        r'"(?P<method>\S+) (?P<path>\S+) \S+" '
        r'(?P<status>\d+) (?P<size>\S+)'
    )

    def parse(self, filepath: str) -> List[Dict]:
        events = []
        with open(filepath, "r", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                events.append(self._match_line(line))
        return events

    def _match_line(self, line: str) -> Dict:
        m = self.LOG_PATTERN.match(line)
        if not m:
            return self._build_unparsed_event(line)

        timestamp = self._build_timestamp(m.group("datetime"))
        return self._build_event(
            timestamp=timestamp,
            host="nginx_server",
            actor=m.group("ip"),
            action=m.group("method"),
            object_=m.group("path"),
            result=m.group("status"),
            raw_log=line,
        )

    def _build_unparsed_event(self, raw_log: str) -> Dict:
        return self._build_event(
            timestamp="unknown", host="unknown",
            actor="unknown", action="unparsed_event",
            object_="unknown", result="unknown", raw_log=raw_log,
        )

    def _build_timestamp(self, datetime_str: str) -> str:
        dt = datetime.strptime(datetime_str, "%d/%b/%Y:%H:%M:%S %z")
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")