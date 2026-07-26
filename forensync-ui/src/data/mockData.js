// Mock data — swap for real Axios calls once the backend endpoints are ready.

export const mockInvestigator = {
  name: "Aditi Rao",
  investigatorId: "INV-2291",
  orgId: "ORG-4410",
  orgName: "Sentinel Cyber Forensics",
};

export const mockCases = [
  {
    caseId: "CASE-1042",
    name: "Organization Info Leak",
    priority: "High Priority",
    priorityColor: "text-red-400",
    investigators: ["VK", "RS"],
    extraInvestigators: 2,
    lastUpdated: "2026-07-09\n18:22",
    status: "Active",
  },
  {
    caseId: "CASE-1041",
    name: "Unauthorized SSH Access",
    priority: "Medium Priority",
    priorityColor: "text-amber",
    investigators: ["AP", "NK"],
    extraInvestigators: 1,
    lastUpdated: "2026-07-08\n16:45",
    status: "Active",
  },
  {
    caseId: "CASE-1040",
    name: "Data Exfiltration Attempt",
    priority: "Critical",
    priorityColor: "text-red-400",
    investigators: ["SM", "RP", "VK"],
    extraInvestigators: 2,
    lastUpdated: "2026-07-08\n11:30",
    status: "Active",
  },
  {
    caseId: "CASE-1039",
    name: "Malware Infection — Endpoint",
    priority: "Medium Priority",
    priorityColor: "text-amber",
    investigators: ["AR", "PS"],
    extraInvestigators: 0,
    lastUpdated: "2026-07-07\n10:15",
    status: "Pending",
  },
  {
    caseId: "CASE-1038",
    name: "Phishing Email Investigation",
    priority: "Low Priority",
    priorityColor: "text-blue-400",
    investigators: ["JD", "VK"],
    extraInvestigators: 0,
    lastUpdated: "2026-07-06\n09:50",
    status: "Pending",
  },
];

export const recentActivity = [
  { icon: "✓", iconColor: "text-teal bg-teal/10", text: "Case CASE-1042 logs converted successfully", time: "10 mins ago" },
  { icon: "↑", iconColor: "text-amber bg-amber/10", text: "Evidence uploaded to CASE-1041", time: "25 mins ago" },
  { icon: "👤", iconColor: "text-purple-400 bg-purple-400/10", text: "New investigator Rahul Sharma added to CASE-1040", time: "1 hour ago" },
  { icon: "📄", iconColor: "text-blue-400 bg-blue-400/10", text: "Report generated for CASE-1037", time: "2 hours ago" },
];

export const currentPlugin = null;

export const supportedFormats = [
  { id: "linux-auth", label: "Linux Auth Log Parser" },
  { id: "apache-access", label: "Apache Access Log Parser" },
  { id: "custom", label: "Develop Custom Plugin" },
];
