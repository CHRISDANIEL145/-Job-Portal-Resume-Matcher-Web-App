import { useEffect, useState } from "react";
import api from "../services/api";

function CompanyDashboard() {
  const [profile, setProfile] = useState({ company_name: "", description: "", website_url: "" });

  const [job, setJob] = useState({ title: "", description: "", min_gpa: "", skills: "" });
  const [myJobs, setMyJobs] = useState([]);
  const [jobMeta, setJobMeta] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [pendingMsg, setPendingMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  const load = async () => {
    setErrorMsg("");
    const [profileRes, jobsRes, notesRes] = await Promise.allSettled([
      api.get("/company/profile"),
      api.get("/company/jobs", { params: { page: 1, per_page: 10 } }),
      api.get("/notifications"),
    ]);

      if (profileRes.status === "fulfilled") {
        setProfile({
          company_name: profileRes.value.data.company_name || "",
          description: profileRes.value.data.description || "",
          website_url: profileRes.value.data.website_url || "",
        });

    } else {
      setProfile({ company_name: "", description: "", website_url: "" });
      if (profileRes.reason?.response?.status !== 404) {
        setErrorMsg(profileRes.reason?.normalizedMessage || "Unable to load company profile");
      }
    }


    if (jobsRes.status === "fulfilled") {
      setMyJobs(jobsRes.value.data.items || []);
      setJobMeta(jobsRes.value.data.pagination || null);
    } else {
      setMyJobs([]);
      setJobMeta(null);
      setErrorMsg((current) => current || jobsRes.reason?.normalizedMessage || "Unable to load company jobs");
    }

    if (notesRes.status === "fulfilled") {
      setNotifications(notesRes.value.data || []);
    } else {
      setNotifications([]);
    }
  };

  const saveProfile = async () => {
    setErrorMsg("");
    try {
      await api.post("/company/profile", profile);
      setPendingMsg("Company profile saved");
      await load();
    } catch (error) {
      setErrorMsg(error.normalizedMessage || "Unable to save profile");
    }
  };

  const postJob = async () => {
    setErrorMsg("");
    try {
      const payload = {
        ...job,
        min_gpa: job.min_gpa ? Number(job.min_gpa) : null,
        skills: job.skills.split(",").map((s) => s.trim()).filter(Boolean),
      };
      await api.post("/company/jobs", payload);
      setPendingMsg("Job submitted for admin approval");
      setJob({ title: "", description: "", min_gpa: "", skills: "" });
      await load();
    } catch (error) {
      setErrorMsg(error.normalizedMessage || "Unable to create job");
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <section className="card">
        <h2 className="title">Company Profile</h2>
        <div className="space-y-3">
          <input className="input" placeholder="Company Name" value={profile.company_name} onChange={(e) => setProfile({ ...profile, company_name: e.target.value })} />
          <textarea className="input min-h-28" placeholder="Company Description" value={profile.description} onChange={(e) => setProfile({ ...profile, description: e.target.value })} />
          <input
            className="input"
            placeholder="Company Website URL (e.g., https://company.com)"
            value={profile.website_url}
            onChange={(e) => setProfile({ ...profile, website_url: e.target.value })}
          />
          <button className="btn-primary" onClick={saveProfile}>Save Company Profile</button>

        </div>
      </section>

      <section className="card">
        <h2 className="title">Post Job Opening</h2>
        <div className="space-y-3">
          <input className="input" placeholder="Job Title" value={job.title} onChange={(e) => setJob({ ...job, title: e.target.value })} />
          <textarea className="input min-h-28" placeholder="Job Description" value={job.description} onChange={(e) => setJob({ ...job, description: e.target.value })} />
          <input className="input" placeholder="Minimum GPA" value={job.min_gpa} onChange={(e) => setJob({ ...job, min_gpa: e.target.value })} />
          <input className="input" placeholder="Required skills (comma separated)" value={job.skills} onChange={(e) => setJob({ ...job, skills: e.target.value })} />
          <button className="btn-primary" onClick={postJob}>Post Job</button>
        </div>
        {pendingMsg && <p className="mt-3 text-sm text-emerald-700">{pendingMsg}</p>}
        {errorMsg && <p className="mt-3 text-sm text-rose-700">{errorMsg}</p>}
      </section>

      <section className="card lg:col-span-2">
        <h2 className="title">My Jobs</h2>
        <div className="space-y-3">
          {myJobs.map((item) => (
            <article key={item.id} className="rounded-xl border border-slate-200 bg-white p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="font-semibold">{item.title}</h3>
                <span className={`rounded-full px-2 py-1 text-xs ${item.approved ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`}>
                  {item.approved ? "Approved" : "Pending"}
                </span>
              </div>
              <p className="mt-2 text-sm text-slate-700">{item.description}</p>
              <p className="mt-2 text-xs text-slate-500">Skills: {(item.skills || []).join(", ") || "-"}</p>
              <p className="mt-1 text-xs text-slate-500">Applications: {item.applications}</p>
            </article>
          ))}
          {myJobs.length === 0 && <p className="text-sm text-slate-600">No jobs posted yet.</p>}
        </div>
        {jobMeta && (
          <p className="mt-3 text-xs text-slate-500">
            Page {jobMeta.page} of {jobMeta.pages || 1} | Total jobs: {jobMeta.total}
          </p>
        )}
      </section>

      <section className="card lg:col-span-2">
        <h2 className="title">Company Notifications</h2>
        <p className="mb-3 text-sm text-slate-600">Applications, shortlist updates, and job approval alerts appear here.</p>
        <div className="space-y-3">
          {notifications.map((note) => (
            <article key={note.id} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="font-semibold">{note.title}</h3>
                <span className={`rounded-full px-2 py-1 text-xs ${note.read ? "bg-slate-200 text-slate-700" : "bg-emerald-100 text-emerald-800"}`}>
                  {note.read ? "Read" : "New"}
                </span>
              </div>
              <p className="mt-2 text-sm text-slate-700">{note.message}</p>
            </article>
          ))}
          {notifications.length === 0 && <p className="text-sm text-slate-600">No company notifications yet.</p>}
        </div>
      </section>
    </div>
  );
}

export default CompanyDashboard;
