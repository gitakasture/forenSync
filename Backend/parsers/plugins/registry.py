from plugins.auth_log import AuthLogParser
from plugins.linux_syslog import LinuxSyslogParser
from plugins.apache_access import ApacheAccessParser
from plugins.nginx_access import NginxAccessParser
from plugins.windows_event_log import WindowsEventLogParser

PLUGIN_REGISTRY = {
    "auth_log": AuthLogParser,
    "linux_syslog": LinuxSyslogParser,
    "apache_access": ApacheAccessParser,
    "nginx_access": NginxAccessParser,
    "windows_event_log": WindowsEventLogParser,
}


def get_plugin(source_name: str, **kwargs):
    """
    Look up and instantiate a plugin by its registered name.
    kwargs are passed through to the plugin's constructor
    (e.g. starting_year for auth_log/linux_syslog).
    """
    plugin_class = PLUGIN_REGISTRY.get(source_name)
    if plugin_class is None:
        raise ValueError(f"No plugin registered for source: '{source_name}'")
    return plugin_class(**kwargs)


def list_available_plugins():
    """Returns the names of all registered plugins — powers the Plugin Store UI."""
    return list(PLUGIN_REGISTRY.keys())

PLUGIN_CATALOG = {
    "auth_log": {"label": "Linux Auth Log (SSH)", "description": "Parses SSH login attempts and authentication events."},
    "linux_syslog": {"label": "Linux Syslog", "description": "Parses general Linux system logs (FTP, su sessions, root logins)."},
    "apache_access": {"label": "Apache Access Log", "description": "Parses Apache web server access logs (Combined Log Format)."},
    "nginx_access": {"label": "Nginx Access Log", "description": "Parses Nginx web server access logs (Combined Log Format)."},
    "windows_event_log": {"label": "Windows Event Log", "description": "Parses Windows Security event logs (.evtx)."},
}


def detect_format(file_bytes: bytes) -> list:
    """Returns a ranked list of (plugin_name, confidence 0.0-1.0)."""
    if file_bytes[:8] == b"ElfFile\x00":
        return [("windows_event_log", 1.0)]

    text = file_bytes.decode("utf-8", errors="ignore")
    sample_lines = [l for l in text.splitlines() if l.strip()][:50]

    scores = []
    for name, plugin_class in PLUGIN_REGISTRY.items():
        if name == "windows_event_log":
            continue
        confidence = plugin_class.detect_confidence(sample_lines)
        scores.append((name, round(confidence, 2)))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores