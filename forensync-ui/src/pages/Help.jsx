import Sidebar from "../components/Sidebar";

const faqs = [
  {
    q: "How do I create a new case?",
    a: "Go to Cases on your dashboard and click \"+ New Case File\". Fill in the case name, description, upload log files, and estimate the incident timeframe.",
  },
  {
    q: "What log formats are supported?",
    a: "Linux Auth Log and Apache Access Log are supported out of the box. Additional formats can be added as a custom plugin from System Settings.",
  },
  {
    q: "Who can access System Settings?",
    a: "Only users logged in as Organization Head can view or change organization-wide settings.",
  },
];

export default function Help() {
  return (
    <div className="flex h-screen bg-ink">
      <Sidebar />

      <main className="flex-1 overflow-y-auto px-8 py-8">
        <div className="mx-auto max-w-2xl">
          <h1 className="mb-1 font-display text-xl font-medium text-paper">Help</h1>
          <p className="mb-6 text-sm text-ash">Common questions about using ForenSync.</p>

          <div className="space-y-4">
            {faqs.map((item, i) => (
              <div key={i} className="rounded-sm border border-hairline bg-panel p-5">
                <p className="mb-1.5 text-sm font-medium text-paper">{item.q}</p>
                <p className="text-sm text-ash">{item.a}</p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
