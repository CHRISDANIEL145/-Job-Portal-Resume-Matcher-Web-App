import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

function Navbar() {
  const { role, logout } = useAuth();

  return (
    <header className="sticky top-0 z-30 border-b border-emerald-900/20 bg-white/80 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link to="/" className="text-xl font-semibold tracking-wide text-emerald-900">
          Placement Portal
        </Link>
        <div className="flex items-center gap-2">
          {!role && <Link className="btn-secondary" to="/register">Register</Link>}
          {!role && <Link className="btn-primary" to="/login">Login</Link>}
          {role && <button className="btn-primary" onClick={logout}>Logout</button>}
        </div>
      </nav>
    </header>
  );
}

export default Navbar;
