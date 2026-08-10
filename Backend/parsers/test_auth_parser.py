#run this to test auth logs parser
# from plugins.auth_log import AuthLogParser
# from collections import Counter

# parser = AuthLogParser(starting_year=2005)
# events = parser.parse("sample_logs/auth_log_sample.log")

# print(f"Parsed {len(events)} events total\n")

# print("First 10 events:")
# for e in events[:10]:
#     print(e)

# print("\nLast 5 events:")
# for e in events[-5:]:
#     print(e)

# action_counts = Counter(e['action'] for e in events)
# print("\nEvent breakdown by action type:")
# for action, count in action_counts.items():
#     print(f"  {action}: {count}")













#run this to test sys logs parser
# from plugins.linux_syslog import LinuxSyslogParser
# from collections import Counter

# parser = LinuxSyslogParser(starting_year=2005)
# events = parser.parse("sample_logs/linux_syslog_sample.log")

# print(f"Parsed {len(events)} events total\n")

# print("First 10 events:")
# for e in events[:10]:
#     print(e)

# print("\nLast 5 events:")
# for e in events[-5:]:
#     print(e)

# action_counts = Counter(e['action'] for e in events)
# print("\nEvent breakdown by action type:")
# for action, count in action_counts.items():
#     print(f"  {action}: {count}")
















#run this to test apache logs parser
# from plugins.apache_access import ApacheAccessParser
# from collections import Counter

# parser = ApacheAccessParser()
# events = parser.parse("sample_logs/apache_access_sample.log")

# print(f"Parsed {len(events)} events total\n")

# for e in events:
#     print(e)

# action_counts = Counter(e['action'] for e in events)
# print("\nEvent breakdown by action type:")
# for action, count in action_counts.items():
#     print(f"  {action}: {count}")







#run this to test windows logs parser
# from plugins.windows_event_log import WindowsEventLogParser
# from collections import Counter

# parser = WindowsEventLogParser()
# events = parser.parse("sample_logs/security.evtx")

# print(f"Parsed {len(events)} events total\n")

# print("First 5 events:")
# for e in events[:5]:
#     print(e)

# action_counts = Counter(e['action'] for e in events)
# print("\nEvent breakdown by action type:")
# for action, count in action_counts.items():
#     print(f"  {action}: {count}")







#run this to test nginx logs parser
# from plugins.nginx_access import NginxAccessParser
# from collections import Counter

# parser = NginxAccessParser()
# events = parser.parse("sample_logs/nginx_access_sample.log")

# print(f"Parsed {len(events)} events total\n")
# print("First 5 events:")
# for e in events[:5]:
#     print(e)

# action_counts = Counter(e['action'] for e in events)
# print("\nEvent breakdown by action type:")
# for action, count in list(action_counts.items())[:10]:
#     print(f"  {action}: {count}")

# unparsed = sum(1 for e in events if e['action'] == 'unparsed_event')
# print(f"\nUnparsed: {unparsed} / {len(events)}")





#run this to get list of available plugins
from plugins.registry import get_plugin, list_available_plugins

print("Available plugins:", list_available_plugins())

parser = get_plugin("nginx_access")
events = parser.parse("sample_logs/nginx_access_sample.log")
print(f"Parsed {len(events)} events via registry")