import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { setRole as persistRole } from "../utils/auth";

export default function Login() {
  const navigate = useNavigate();
  const [role, setRole] = useState("investigator"); // "head" | "investigator"
  const [form, setForm] = useState({ orgId: "", userId: "" });

  const handleSubmit = (e) => {
    e.preventDefault();
    // Mock auth — replace with real Axios call to auth endpoint later.
    persistRole(role);
    navigate("/dashboard");
  };

  const idLabel = role === "head" ? "Organization Head ID" : "Investigator ID";
  const idPlaceholder = role === "head" ? "HEAD-XXXX" : "INV-XXXX";

  return (
    <div className="flex min-h-screen items-center justify-center bg-ink px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <p className="font-display text-2xl font-semibold text-paper">ForenSync</p>
          <p className="mt-1 font-mono text-xs tracking-wide text-ash">CASE MANAGEMENT — SIGN IN</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-sm border border-hairline bg-panel p-7"
        >
          <div className="mb-5 flex rounded-sm border border-hairline bg-ink p-1">
            <button
              type="button"
              onClick={() => setRole("investigator")}
              className={`flex-1 rounded-sm py-2 text-xs font-medium uppercase tracking-wide transition-colors ${
                role === "investigator" ? "bg-amber text-ink" : "text-ash hover:text-paper"
              }`}
            >
              Investigator
            </button>
            <button
              type="button"
              onClick={() => setRole("head")}
              className={`flex-1 rounded-sm py-2 text-xs font-medium uppercase tracking-wide transition-colors ${
                role === "head" ? "bg-amber text-ink" : "text-ash hover:text-paper"
              }`}
            >
              Organization Head
            </button>
          </div>

          <div className="mb-5">
            <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">Org ID</label>
            <input
              type="text"
              required
              value={form.orgId}
              onChange={(e) => setForm({ ...form, orgId: e.target.value })}
              placeholder="ORG-XXXX"
              className="w-full rounded-sm border border-hairline bg-ink px-3 py-2.5 font-mono text-sm text-paper placeholder:text-ash/60 focus:border-amber outline-none"
            />
          </div>

          <div className="mb-6">
            <label className="mb-1.5 block text-xs uppercase tracking-wide text-ash">{idLabel}</label>
            <input
              type="text"
              required
              value={form.userId}
              onChange={(e) => setForm({ ...form, userId: e.target.value })}
              placeholder={idPlaceholder}
              className="w-full rounded-sm border border-hairline bg-ink px-3 py-2.5 font-mono text-sm text-paper placeholder:text-ash/60 focus:border-amber outline-none"
            />
          </div>

          <button
            type="submit"
            className="w-full rounded-sm bg-amber py-2.5 text-sm font-medium text-ink transition-colors hover:bg-amber-hover"
          >
            Login
          </button>

          <p className="mt-5 text-center text-sm text-ash">
            New organization?{" "}
            <Link to="/register" className="text-amber hover:text-amber-hover hover:underline">
              Register
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
