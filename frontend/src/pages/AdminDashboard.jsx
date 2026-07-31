import { useEffect, useState } from "react";
import api from "../services/api";

function AdminDashboard() {
  const [pendingJobs, setPendingJobs] = useState([]);
  const [analytics, setAnalytics] = useState(null);

  const load = async () => {
    const [jobsRes, analyticsRes] = await Promise.all([
      api.get("/admin/jobs/pending"),
      api.get("/admin/analytics"),
    ]);
    setPendingJobs(jobsRes.data);
    setAnalytics(analyticsRes.data);
  };

  useEffect(() => {
    load();
  }, []);

  const approve = async (jobId) => {
    await api.patch(`/admin/jobs/${jobId}/approve`);
    await load();
  };

  return (
    <div className="space-y-6">
      <section className="card">
        <h2 className="title">Pending Job Approvals</h2>
        <div className="space-y-3">
          {pendingJobs.map((job) => (
            <div key={job.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-200 bg-white p-3">
              <div>
                <p className="font-semibold">{job.title}</p>
                <p className="text-sm text-slate-600">{job.company} | Min GPA: {job.min_gpa ?? "N/A"}</p>
              </div>
              <button className="btn-primary" onClick={() => approve(job.id)}>Approve</button>
            </div>
          ))}
          {pendingJobs.length === 0 && <p className="text-sm text-slate-600">No pending jobs.</p>}
        </div>
      </section>

      <section className="card">
        <h2 className="title">Placement Analytics</h2>
        {!analytics && <p className="text-sm text-slate-600">Loading analytics...</p>}
        {analytics && (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <Stat label="Students" value={analytics.total_students} />
            <Stat label="Companies" value={analytics.total_companies} />
            <Stat label="Total Jobs" value={analytics.total_jobs} />
            <Stat label="Approved Jobs" value={analytics.approved_jobs} />
            <Stat label="Applications" value={analytics.total_applications} />
            <Stat label="Shortlisted" value={analytics.shortlisted_students} />
            <Stat label="Placement Ratio" value={`${analytics.placement_ratio_percent}%`} />
          </div>
        )}
      </section>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="rounded-lg border border-emerald-100 bg-emerald-50 p-3">
      <p className="text-xs uppercase tracking-wide text-slate-600">{label}</p>
      <p className="text-2xl font-bold text-emerald-800">{value}</p>
    </div>
  );
}

export default AdminDashboard;
