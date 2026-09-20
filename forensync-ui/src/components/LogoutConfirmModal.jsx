import { useNavigate } from "react-router-dom";
import { logout } from "../utils/auth";

export default function LogoutConfirmModal({ onClose }) {
  const navigate = useNavigate();

  const handleConfirm = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4" onClick={onClose}>
      <div className="relative w-full max-w-sm rounded-sm border border-hairline bg-panel p-6 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <p className="mb-2 text-sm font-medium text-paper">Log out?</p>
        <p className="mb-5 text-sm text-ash">You'll need to sign in again to access your dashboard.</p>
        <div className="flex gap-3">
          <button onClick={onClose} className="flex-1 rounded-sm border border-hairline py-2 text-sm text-ash transition-colors hover:border-amber hover:text-amber">
            Cancel
          </button>
          <button onClick={handleConfirm} className="flex-1 rounded-sm bg-danger py-2 text-sm font-medium text-paper transition-colors hover:opacity-90">
            Logout
          </button>
        </div>
      </div>
    </div>
  );
}