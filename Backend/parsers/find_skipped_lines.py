from plugins.linux_syslog import LinuxSyslogParser

parser = LinuxSyslogParser(starting_year=2005)

total_lines = 0
blank_lines = 0
skipped_lines = []

with open("sample_logs/linux_syslog_sample.log", "r", errors="ignore") as f:
    for line_number, line in enumerate(f, start=1):
        total_lines += 1
        stripped = line.strip()
        if not stripped:
            blank_lines += 1
            continue

        match = parser.PREFIX_PATTERN.match(stripped)
        if not match:
            skipped_lines.append((line_number, stripped))

print(f"Total lines in file: {total_lines}")
print(f"Blank lines: {blank_lines}")
print(f"Lines that failed to match PREFIX_PATTERN: {len(skipped_lines)}\n")

for line_number, line in skipped_lines:
    print(f"Line {line_number}: {line}")