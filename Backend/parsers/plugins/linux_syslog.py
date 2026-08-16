import re
from datetime import datetime
from typing import List, Dict
from plugins.base import BaseParserPlugin


class LinuxSyslogParser(BaseParserPlugin):
    source_name = "linux_syslog"

    def __init__(self, starting_year: int = None):
        self.starting_year = starting_year or datetime.now().year

    # Generalized prefix: process name may or may not have [PID]
    # e.g. "ftpd[31282]:" or "logrotate:" (no PID)
    PREFIX_PATTERN = re.compile(
        r"^(?P<month>\w+)\s+(?P<day>\d+)\s+(?P<time>\d+:\d+:\d+)\s+"
        r"(?P<host>\S+)\s+(?P<process>.+?)(\[\d+\])?:\s+(?P<message>.*)$"
    )

    FTP_CONNECTION = re.compile(
        r"connection from (?P<ip>\S+) \((?P<hostname>[^)]*)\) at"
    )
    SESSION_OPENED = re.compile(
        r"session opened for user (?P<user>\S+) by \(uid=(?P<uid>\d+)\)"
    )
    SESSION_CLOSED = re.compile(
        r"session closed for user (?P<user>\S+)"
    )
    ROOT_LOGIN = re.compile(
        r"ROOT LOGIN ON (?P<tty>\S+)"
    )

    DETECTION_PATTERNS = [FTP_CONNECTION, SESSION_OPENED, SESSION_CLOSED, ROOT_LOGIN]

    def parse(self, filepath: str) -> List[Dict]:
        events = []
        current_year = self.starting_year
        previous_month_num = None

        with open(filepath, "r", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                prefix_match = self.PREFIX_PATTERN.match(line)
                if not prefix_match:
                    # Doesn't even match a basic syslog line structure — skip
                    continue

                host = prefix_match.group("host")
                message = prefix_match.group("message")
                month_str = prefix_match.group("month")

                month_num = datetime.strptime(month_str, "%b").month
                if previous_month_num is not None and month_num < previous_month_num:
                    current_year += 1
                previous_month_num = month_num

                timestamp = self._build_timestamp(
                    month_str,
                    prefix_match.group("day"),
                    prefix_match.group("time"),
                    current_year,
                )

                event = self._match_single_message(message, timestamp, host, line)
                events.append(event)

        return events

    def _match_single_message(self, message, timestamp, host, raw_log):
        m = self.FTP_CONNECTION.search(message)
        if m:
            return self._build_event(
                timestamp=timestamp,
                host=host,
                actor=m.group("ip"),
                action="ftp_connection",
                object_=m.group("hostname"),
                result="unknown",
                raw_log=raw_log,
            )

        m = self.SESSION_OPENED.search(message)
        if m:
            return self._build_event(
                timestamp=timestamp,
                host=host,
                actor=f"uid={m.group('uid')}",
                action="su_session_opened",
                object_=m.group("user"),
                result="success",
                raw_log=raw_log,
            )

        m = self.SESSION_CLOSED.search(message)
        if m:
            return self._build_event(
                timestamp=timestamp,
                host=host,
                actor=m.group("user"),
                action="su_session_closed",
                object_=m.group("user"),
                result="success",
                raw_log=raw_log,
            )

        m = self.ROOT_LOGIN.search(message)
        if m:
            return self._build_event(
                timestamp=timestamp,
                host=host,
                actor="root",
                action="root_console_login",
                object_=m.group("tty"),
                result="success",
                raw_log=raw_log,
    )

        # Nothing matched — don't lose this line, tag it as unparsed
        return self._build_unparsed_event(timestamp, host, raw_log)

    def _build_unparsed_event(self, timestamp, host, raw_log):
        return self._build_event(
            timestamp=timestamp,
            host=host,
            actor="unknown",
            action="unparsed_event",
            object_="unknown",
            result="unknown",
            raw_log=raw_log,
        )

    def _build_timestamp(self, month: str, day: str, time_str: str, year: int) -> str:
        dt = datetime.strptime(
            f"{year} {month} {int(day):02d} {time_str}",
            "%Y %b %d %H:%M:%S"
        )
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")