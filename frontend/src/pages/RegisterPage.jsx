import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../services/api";

function RegisterPage() {
  const [form, setForm] = useState({ email: "", password: "", role: "student" });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setMessage("");
    setError("");
    try {
      await api.post("/auth/register", form);
      setMessage("Account created. Please login.");
      setTimeout(() => navigate("/login"), 700);
    } catch (err) {
      setError(err.normalizedMessage || "Registration failed");
    }
  };

  return (
    <section className="card max-w-md">
      <h1 className="mb-1 text-3xl font-bold">Create Account</h1>
      <p className="mb-6 text-sm text-slate-600">Student, company, or admin</p>
      <form onSubmit={submit} className="space-y-4">
        <input className="input" placeholder="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
        <input className="input" placeholder="Password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
        <select className="input" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
          <option value="student">Student</option>
          <option value="company">Company</option>
          <option value="admin">Admin</option>
        </select>
        {error && <p className="text-sm text-red-600">{error}</p>}
        {message && <p className="text-sm text-emerald-700">{message}</p>}
        <button className="btn-primary w-full" type="submit">Register</button>
      </form>
      <p className="mt-5 text-sm text-slate-600">
        Already registered? <Link className="font-semibold text-emerald-700" to="/login">Login</Link>
      </p>
    </section>
  );
}

export default RegisterPage;
