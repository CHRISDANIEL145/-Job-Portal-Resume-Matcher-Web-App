import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../contexts/AuthContext";

function LoginPage() {
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { login } = useAuth();

  useEffect(() => {
    const notice = sessionStorage.getItem("auth_notice");
    if (notice) {
      setError(notice);
      sessionStorage.removeItem("auth_notice");
    }
  }, []);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const { data } = await api.post("/auth/login", form);
      login(data.access_token, data.role);
      if (data.role === "student") navigate("/student");
      if (data.role === "company") navigate("/company");
      if (data.role === "admin") navigate("/admin");
    } catch (err) {
      setError(err.normalizedMessage || "Login failed");
    }
  };

  return (
    <section className="card max-w-md">
      <h1 className="mb-1 text-3xl font-bold">Login</h1>
      <p className="mb-6 text-sm text-slate-600">Access your placement dashboard</p>
      <form onSubmit={submit} className="space-y-4">
        <input className="input" placeholder="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
        <input className="input" placeholder="Password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button className="btn-primary w-full" type="submit">Login</button>
      </form>
    </section>
  );
}

export default LoginPage;
