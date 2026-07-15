// Mock data — swap for real Axios calls once the backend endpoints are ready.
// Keep this shape in sync with the API response schema when it lands.

export const mockInvestigator = {
  name: "Aditi Rao",
  investigatorId: "INV-2291",
  orgId: "ORG-4410",
  orgName: "Sentinel Cyber Forensics",
};

export const mockCases = [
  {
    caseId: "CASE-1042",
    name: "Unauthorized SSH Access — prod-web-03",
    timeframe: "02 Jul – 05 Jul 2026",
    lastModified: "2026-07-09 18:22",
    status: "Active",
    action: "Open",
  },
  {
    caseId: "CASE-1041",
    name: "Suspicious Apache Traffic Spike",
    timeframe: "28 Jun – 30 Jun 2026",
    lastModified: "2026-07-08 11:05",
    status: "Under Review",
    action: "Open",
  },
  {
    caseId: "CASE-1038",
    name: "Failed Login Brute Force — auth-gateway",
    timeframe: "18 Jun – 20 Jun 2026",
    lastModified: "2026-07-02 09:40",
    status: "Active",
    action: "Open",
  },
  {
    caseId: "CASE-1031",
    name: "Data Exfiltration Attempt — file-srv-01",
    timeframe: "01 Jun – 04 Jun 2026",
    lastModified: "2026-06-25 16:12",
    status: "Closed",
    action: "View",
  },
  {
    caseId: "CASE-1027",
    name: "Privilege Escalation — internal CI runner",
    timeframe: "14 May – 16 May 2026",
    lastModified: "2026-06-10 08:55",
    status: "Closed",
    action: "View",
  },
];

export const currentPlugin = null; // null = "Not added"; otherwise { name, addedOn }

export const supportedFormats = [
  { id: "linux-auth", label: "Linux Auth Log Parser" },
  { id: "apache-access", label: "Apache Access Log Parser" },
  { id: "custom", label: "Develop Custom Plugin" },
];
