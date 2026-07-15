import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import NewCaseFile from "./pages/NewCaseFile";
import SystemSettings from "./pages/SystemSettings";
import Help from "./pages/Help";
import Plugins from "./pages/Plugins";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/cases/new" element={<NewCaseFile />} />
      <Route path="/settings" element={<SystemSettings />} />
      <Route path="/help" element={<Help />} />
      <Route path="/plugins" element={<Plugins />} />
    </Routes>
  );
}
