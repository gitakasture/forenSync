import json
from datetime import datetime
from typing import List, Dict
from evtx import PyEvtxParser
from plugins.base import BaseParserPlugin


class WindowsEventLogParser(BaseParserPlugin):
    source_name = "windows_event_log"

    def parse(self, filepath: str) -> List[Dict]:
        events = []
        parser = PyEvtxParser(filepath)

        for record in parser.records_json():
            try:
                data = json.loads(record["data"])
            except (json.JSONDecodeError, KeyError):
                continue  # corrupted record — skip, don't crash the whole file

            event = self._match_record(data, record["data"])
            events.append(event)

        return events

    def _match_record(self, data: dict, raw_log: str) -> Dict:
        system = data.get("Event", {}).get("System", {})
        event_data = data.get("Event", {}).get("EventData", {}) or {}

        event_id = system.get("EventID")
        host = system.get("Computer", "unknown")
        timestamp = self._build_timestamp(system)

        if event_id == 4624:
            return self._build_event(
                timestamp=timestamp, host=host,
                actor=event_data.get("IpAddress", "unknown"),
                action="windows_logon_success",
                object_=event_data.get("TargetUserName", "unknown"),
                result="success", raw_log=raw_log,
            )

        if event_id == 4648:
            return self._build_event(
                timestamp=timestamp, host=host,
                actor=event_data.get("SubjectUserName", "unknown"),
                action="windows_explicit_credential_logon",
                object_=event_data.get("TargetUserName", "unknown"),
                result="success", raw_log=raw_log,
            )

        if event_id == 4672:
            return self._build_event(
                timestamp=timestamp, host=host,
                actor=event_data.get("SubjectUserName", "unknown"),
                action="windows_privileged_logon",
                object_="elevated_privileges_assigned",
                result="success", raw_log=raw_log,
            )

        if event_id == 4616:
            return self._build_event(
                timestamp=timestamp, host=host,
                actor=event_data.get("SubjectUserName", "unknown"),
                action="windows_system_time_changed",
                object_=f"{event_data.get('PreviousTime', '?')} -> {event_data.get('NewTime', '?')}",
                result="unknown", raw_log=raw_log,
            )

        return self._build_unparsed_event(timestamp, host, raw_log)

    def _build_unparsed_event(self, timestamp, host, raw_log) -> Dict:
        return self._build_event(
            timestamp=timestamp, host=host,
            actor="unknown", action="unparsed_event",
            object_="unknown", result="unknown", raw_log=raw_log,
        )

    def _build_timestamp(self, system: dict) -> str:
        raw_ts = system.get("TimeCreated", {}).get("#attributes", {}).get("SystemTime")
        if not raw_ts:
            return "unknown"
        try:
            fmt = "%Y-%m-%dT%H:%M:%S.%fZ" if "." in raw_ts else "%Y-%m-%dT%H:%M:%SZ"
            dt = datetime.strptime(raw_ts, fmt)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            return "unknown"