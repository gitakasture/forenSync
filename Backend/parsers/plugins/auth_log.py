import re
from datetime import datetime
from typing import List, Dict
from plugins.base import BaseParserPlugin


class AuthLogParser(BaseParserPlugin):
    source_name = "auth_log"

    def __init__(self, starting_year: int = None):
        # If the investigator doesn't specify a year, default to current year
        self.starting_year = starting_year or datetime.now().year

    # Prefix shared by every line: "Dec 10 08:24:40 LabSZ sshd[24363]: "
    PREFIX_PATTERN = re.compile(
        r"^(?P<month>\w+)\s+(?P<day>\d+)\s+(?P<time>\d+:\d+:\d+)\s+"
        r"(?P<host>\S+)\s+sshd\[\d+\]:\s+(?P<message>.*)$"
    )

    FAILED_PASSWORD = re.compile(
        r"Failed password for (invalid user )?(?P<user>\S+) from (?P<ip>\S+) port (?P<port>\d+) ssh2"
    )
    ACCEPTED_PASSWORD = re.compile(
        r"Accepted password for (?P<user>\S+) from (?P<ip>\S+) port (?P<port>\d+) ssh2"
    )
    INVALID_USER = re.compile(
        r"^Invalid user (?P<user>\S+) from (?P<ip>\S+)$"
    )
    REPEATED_MESSAGE = re.compile(
        r"^message repeated (?P<count>\d+) times: \[ (?P<inner_message>.*)\s*\]$"
    )
    SESSION_OPENED = re.compile(
        r"session opened for user (?P<user>\S+) by \(uid=(?P<uid>\d+)\)"
    )

    # This dataset doesn't include the year, so we assume one.
    # In a real system this would come from file metadata or user input.
    # ASSUMED_YEAR = 2005

    def parse(self, filepath: str) -> List[Dict]:
        events = []
        current_year = self.starting_year
        previous_month_num = None

        with open(filepath, "r", errors="ignore") as f:
            for line_number, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue

                prefix_match = self.PREFIX_PATTERN.match(line)
                if not prefix_match:
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

                event_list = self._match_message(message, timestamp, host, line)
                events.extend(event_list)

        return events

    def _match_message(self, message, timestamp, host, raw_log):
        # Check for syslog's "message repeated N times" compression first
        repeated_match = self.REPEATED_MESSAGE.match(message)
        if repeated_match:
            count = int(repeated_match.group("count"))
            inner_message = repeated_match.group("inner_message")
            single_event = self._match_single_message(inner_message, timestamp, host, raw_log)
            return [single_event.copy() for _ in range(count)]

        # Normal case: try to match a single event
        single_event = self._match_single_message(message, timestamp, host, raw_log)
        return [single_event]

    def _match_single_message(self, message, timestamp, host, raw_log):
        m = self.FAILED_PASSWORD.search(message)
        if m:
            return self._build_event(
                timestamp=timestamp,
                host=host,
                actor=m.group("ip"),
                action="ssh_login_failed",
                object_=m.group("user"),
                result="failure",
                raw_log=raw_log,
            )

        m = self.ACCEPTED_PASSWORD.search(message)
        if m:
            return self._build_event(
                timestamp=timestamp,
                host=host,
                actor=m.group("ip"),
                action="ssh_login_success",
                object_=m.group("user"),
                result="success",
                raw_log=raw_log,
            )

        m = self.INVALID_USER.search(message)
        if m:
            return self._build_event(
                timestamp=timestamp,
                host=host,
                actor=m.group("ip"),
                action="ssh_invalid_user_attempt",
                object_=m.group("user"),
                result="failure",
                raw_log=raw_log,
            )

        m = self.SESSION_OPENED.search(message)
        if m:
            return self._build_event(
                timestamp=timestamp,
                host=host,
                actor=f"uid={m.group('uid')}",
                action="ssh_session_opened",
                object_=m.group("user"),
                result="success",
                raw_log=raw_log,
            )

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

    