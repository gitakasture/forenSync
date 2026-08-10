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