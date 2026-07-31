import { Navigate, Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import StudentDashboard from "./pages/StudentDashboard";
import CompanyDashboard from "./pages/CompanyDashboard";
import AdminDashboard from "./pages/AdminDashboard";
import { useAuth } from "./contexts/AuthContext";

function RoleRoute({ allow, children }) {
  const { role } = useAuth();
  if (!role) return <Navigate to="/login" />;
  if (!allow.includes(role)) return <Navigate to="/" />;
  return children;
}

function HomeRedirect() {
  const { role } = useAuth();
  if (role === "student") return <Navigate to="/student" />;
  if (role === "company") return <Navigate to="/company" />;
  if (role === "admin") return <Navigate to="/admin" />;
  return <Navigate to="/login" />;
}

function App() {
  return (
    <div className="min-h-screen bg-pattern text-slate-900">
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-8">
        <Routes>
          <Route path="/" element={<HomeRedirect />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            path="/student"
            element={
              <RoleRoute allow={["student"]}>
                <StudentDashboard />
              </RoleRoute>
            }
          />
          <Route
            path="/company"
            element={
              <RoleRoute allow={["company"]}>
                <CompanyDashboard />
              </RoleRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <RoleRoute allow={["admin"]}>
                <AdminDashboard />
              </RoleRoute>
            }
          />
        </Routes>
      </main>
    </div>
  );
}

export default App;
