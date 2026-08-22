import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Cases from "./pages/Cases";
import UsersTeams from "./pages/UsersTeams";
import SystemSettings from "./pages/SystemSettings";
import Help from "./pages/Help";
import Plugins from "./pages/Plugins";
import HeadDashboard from "./pages/HeadDashboard";
import InvDashboard from "./pages/InvDashboard";
import CaseFilesPage from "./pages/CaseFilesPage";
import TimelinePage from "./pages/TimelinePage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      {/* <Route path="/dashboard" element={<Dashboard />} /> */}
      <Route path="/head-dashboard" element={<HeadDashboard />} />
      <Route path="/investigator-dashboard" element={<InvDashboard />} />
      <Route path="/cases" element={<Cases />} />
      <Route path="/users" element={<UsersTeams />} />
      <Route path="/settings" element={<SystemSettings />} />
      <Route path="/help" element={<Help />} />
      <Route path="/plugins" element={<Plugins />} />
      <Route path="/cases/:caseId/files" element={<CaseFilesPage />} />
      <Route path="/cases/:caseId/timeline" element={<TimelinePage />} />
    </Routes>
  );
}
