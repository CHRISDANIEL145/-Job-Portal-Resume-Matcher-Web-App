import { useEffect, useMemo, useState, useRef } from "react";
import api from "../services/api";

const getAvatarLogo = (companyName) => {
  const name = (companyName || "Company").trim() || "Company";
  return `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=ecfdf5&color=065f46&rounded=true&bold=true&size=64`;
};

const getFaviconLogo = (applyUrl) => {
  if (!applyUrl) return "";
  return `https://www.google.com/s2/favicons?sz=64&domain_url=${encodeURIComponent(applyUrl)}`;
};

const resolvePrimaryLogo = (companyName, logoUrl, applyUrl) => logoUrl || getFaviconLogo(applyUrl) || getAvatarLogo(companyName);

const handleLogoError = (event, companyName, applyUrl) => {
  const target = event.currentTarget;
  const faviconLogo = getFaviconLogo(applyUrl);
  const avatarLogo = getAvatarLogo(companyName);
  const currentSrc = target.getAttribute("src") || "";

  if (!target.dataset.faviconTried && faviconLogo && currentSrc !== faviconLogo) {
    target.dataset.faviconTried = "1";
    target.src = faviconLogo;
    return;
  }

  if (currentSrc !== avatarLogo) {
    target.src = avatarLogo;
    return;
  }

  target.style.display = "none";
};

const initialMentorMessages = [
  {
    role: "mentor",
    text: "Ask me about demand, resume gaps, interview practice, or how you compare with peers.",
  },
];

function SectionCard({ title, subtitle, children, className = "" }) {
  return (
    <section className={`card ${className}`}>
      <div className="mb-4">
        <h2 className="title">{title}</h2>
        {subtitle && <p className="text-sm text-slate-600">{subtitle}</p>}
      </div>
      {children}
    </section>
  );
}

function StudentDashboard() {
  const [profile, setProfile] = useState({ full_name: "", gpa: "", education: "", skills: "" });
  const [jobs, setJobs] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [recommendedCompanies, setRecommendedCompanies] = useState([]);
  const [recommendedJobs, setRecommendedJobs] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [intelligence, setIntelligence] = useState(null);
  const [mentorMessages, setMentorMessages] = useState(initialMentorMessages);
  const [mentorInput, setMentorInput] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [actionMsg, setActionMsg] = useState("");
  const [resumeInfo, setResumeInfo] = useState(null);
  const [isLoadingData, setIsLoadingData] = useState(false);
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [isUploadingResume, setIsUploadingResume] = useState(false);
  const [isSendingMentor, setIsSendingMentor] = useState(false);
  const [applyingJobId, setApplyingJobId] = useState(null);

  // New states for Tab Navigation
  const [activeTab, setActiveTab] = useState("overview");

  // New states for AI Roadmap & Trends
  const [roadmap, setRoadmap] = useState(null);
  const [skillTrends, setSkillTrends] = useState([]);
  const [isLoadingRoadmap, setIsLoadingRoadmap] = useState(false);
  const [completedRoadmapActions, setCompletedRoadmapActions] = useState({});
  const [selectedRoadmapDomain, setSelectedRoadmapDomain] = useState("");

  // New states for AI Project Reviewer
  const [projectInput, setProjectInput] = useState({ title: "", description: "", tech_stack: "", code_snippet: "" });
  const [projectReview, setProjectReview] = useState(null);
  const [isReviewingProject, setIsReviewingProject] = useState(false);

  // New states for AI Practice Interview
  const [interviewRole, setInterviewRole] = useState("Full-Stack Generalist Engineer");
  const [interviewSession, setInterviewSession] = useState(null);
  const [interviewAnswer, setInterviewAnswer] = useState("");
  const [previousFeedback, setPreviousFeedback] = useState(null);
  const [interviewReport, setInterviewReport] = useState(null);
  const [isStartingInterview, setIsStartingInterview] = useState(false);
  const [isSubmittingAnswer, setIsSubmittingAnswer] = useState(false);

  // New states for AI ATS & Probability Matcher
  const [atsData, setAtsData] = useState(null);
  const [isLoadingAts, setIsLoadingAts] = useState(false);

  // New states for AI Application Booster
  const [boosterJob, setBoosterJob] = useState(null);
  const [boosterData, setBoosterData] = useState(null);
  const [isGeneratingBooster, setIsGeneratingBooster] = useState(false);
  const [boosterModalTab, setBoosterModalTab] = useState("pitch");

  // Premium Video Interview State
  const [videoStream, setVideoStream] = useState(null);
  const [isCameraOff, setIsCameraOff] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isAiSpeaking, setIsAiSpeaking] = useState(false);
  const [interviewTime, setInterviewTime] = useState(0);
  const [isListening, setIsListening] = useState(false);
  const videoRef = useRef(null);

  const getNumericJobId = (job) => {
    if (!job) return null;
    const rawId = job.job_id || job.id;
    if (!rawId) return null;
    if (typeof rawId === "string" && rawId.startsWith("external")) return null;
    const parsed = Number(rawId);
    return !isNaN(parsed) ? parsed : null;
  };

  const parsedSkills = useMemo(() => profile.skills.split(",").map((skill) => skill.trim()).filter(Boolean), [profile.skills]);
  const parsedGpa = profile.gpa === "" ? null : Number(profile.gpa);
  const isValidGpa = profile.gpa === "" || (!Number.isNaN(parsedGpa) && parsedGpa >= 0 && parsedGpa <= 10);
  const canRunRecommendations = parsedSkills.length > 0 && isValidGpa;
  const personalizedAvailableJobs = (recommendedJobs.length > 0 ? recommendedJobs : jobs).filter((job) => job.gpa_eligible !== false);

  const demandAnalyzer = intelligence?.demand_hiring_analyzer || null;
  const resumeWeaknesses = intelligence?.resume_weakness_detector || null;
  const peerComparison = intelligence?.peer_comparison_dashboard || null;
  const interviewSimulation = intelligence?.interview_simulation || null;

  const applyRecommendationPayload = (payload) => {
    const nextCompanies = payload?.recommended_companies || [];
    const nextJobs = payload?.recommended_jobs || [];
    setRecommendedCompanies(nextCompanies);
    setRecommendedJobs(nextJobs);
    return { nextCompanies, nextJobs };
  };

  const fetchPreviewRecommendations = async (skills, gpa, limit = 10) => {
    const { data } = await api.post("/student/recommendations/preview", {
      gpa,
      skills,
      limit,
    });
    return data;
  };

  const loadRoadmapAndTrends = async (targetDomain = null) => {
    setIsLoadingRoadmap(true);
    try {
      const domainVal = targetDomain || selectedRoadmapDomain;
      const roadmapUrl = domainVal ? `/student/roadmap?domain=${encodeURIComponent(domainVal)}` : "/student/roadmap";
      
      const [roadmapRes, trendsRes] = await Promise.allSettled([
        api.get(roadmapUrl),
        api.get("/student/skill-trends")
      ]);
      if (roadmapRes.status === "fulfilled") setRoadmap(roadmapRes.value.data);
      if (trendsRes.status === "fulfilled") setSkillTrends(trendsRes.value.data);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoadingRoadmap(false);
    }
  };

  const loadAtsData = async () => {
    setIsLoadingAts(true);
    try {
      const { data } = await api.get("/student/ats-probability");
      setAtsData(data);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoadingAts(false);
    }
  };

  const loadData = async () => {
    setIsLoadingData(true);
    setErrorMsg("");
    const [jobsRes, notesRes, profileRes, companiesRes] = await Promise.allSettled([
      api.get("/jobs", { params: { page: 1, per_page: 20 } }),
      api.get("/notifications"),
      api.get("/student/profile"),
      api.get("/company"),
    ]);

    if (jobsRes.status === "fulfilled") {
      setJobs(jobsRes.value.data.items || []);
    } else {
      setJobs([]);
      setErrorMsg(jobsRes.reason?.normalizedMessage || "Unable to load jobs");
    }

    if (notesRes.status === "fulfilled") {
      setNotifications(notesRes.value.data || []);
    } else {
      setNotifications([]);
    }

    if (profileRes.status === "fulfilled") {
      const data = profileRes.value.data;
      const profileSkills = data.skills || [];
      const profileGpa = data.gpa ?? null;
      setProfile({
        full_name: data.full_name,
        gpa: profileGpa ?? "",
        education: data.education ?? "",
        resume_path: data.resume_path || null,
        skills: profileSkills.join(", "),
      });

      try {
        const { data: intelligenceData } = await api.get("/student/intelligence");
        setIntelligence(intelligenceData);
      } catch (_error) {
        setIntelligence(null);
      }

      try {
        const { data: recommendationData } = await api.get("/student/recommendations");
        const { nextCompanies } = applyRecommendationPayload(recommendationData);

        if (nextCompanies.length === 0 && profileSkills.length > 0) {
          const previewData = await fetchPreviewRecommendations(profileSkills, profileGpa, 10);
          applyRecommendationPayload(previewData);
        }
      } catch (error) {
        if (profileSkills.length > 0) {
          try {
            const previewData = await fetchPreviewRecommendations(profileSkills, profileGpa, 10);
            applyRecommendationPayload(previewData);
          } catch (previewError) {
            setRecommendedCompanies([]);
            setRecommendedJobs([]);
            setErrorMsg(previewError.normalizedMessage || "Unable to load recommendations");
          }
        } else {
          setRecommendedCompanies([]);
          setRecommendedJobs([]);
          setErrorMsg(error.normalizedMessage || "Create profile skills to load recommendations");
        }
      }

      // Load ATS data
      await loadAtsData();
    } else {
      setRecommendedCompanies([]);
      setRecommendedJobs([]);
      setIntelligence(null);
    }

    if (companiesRes.status === "fulfilled") {
      setCompanies(companiesRes.value.data || []);
    } else {
      setCompanies([]);
    }

    setIsLoadingData(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  // Timer effect for video mock call
  useEffect(() => {
    let interval = null;
    if (interviewSession) {
      interval = setInterval(() => {
        setInterviewTime(prev => prev + 1);
      }, 1000);
    } else {
      setInterviewTime(0);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [interviewSession]);

  // Webcam stream effect
  useEffect(() => {
    let activeStream = null;
    const enableWebcam = async () => {
      if (interviewSession && !isCameraOff) {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: false });
          activeStream = stream;
          setVideoStream(stream);
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
          }
        } catch (e) {
          console.warn("Webcam access denied/unavailable:", e);
        }
      } else {
        if (videoStream) {
          videoStream.getTracks().forEach(track => track.stop());
          setVideoStream(null);
        }
      }
    };
    enableWebcam();
    return () => {
      if (activeStream) {
        activeStream.getTracks().forEach(track => track.stop());
      }
    };
  }, [interviewSession, isCameraOff]);

  // TTS Voice Synthesis helper
  const speakText = (text) => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      const voices = window.speechSynthesis.getVoices();
      const preferredVoice = voices.find(v => v.lang.startsWith("en") && (v.name.includes("Google") || v.name.includes("Natural"))) || voices.find(v => v.lang.startsWith("en")) || voices[0];
      if (preferredVoice) {
        utterance.voice = preferredVoice;
      }
      utterance.onstart = () => setIsAiSpeaking(true);
      utterance.onend = () => setIsAiSpeaking(false);
      utterance.onerror = () => setIsAiSpeaking(false);
      window.speechSynthesis.speak(utterance);
    }
  };

  // STT Voice Recognition helper
  const startSpeechRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setErrorMsg("Speech recognition is not supported in this browser. Please type your answer.");
      return;
    }
    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = "en-US";
      recognition.onstart = () => {
        setIsListening(true);
        setActionMsg("Listening... speak now.");
      };
      recognition.onerror = (e) => {
        console.error(e);
        setIsListening(false);
      };
      recognition.onend = () => {
        setIsListening(false);
      };
      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInterviewAnswer(prev => prev ? prev + " " + transcript : transcript);
        setActionMsg("Speech input received!");
      };
      recognition.start();
    } catch (err) {
      console.error(err);
      setIsListening(false);
    }
  };

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, "0");
    const s = (seconds % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  };

  const saveProfile = async () => {
    if (!profile.full_name.trim()) {
      setErrorMsg("Please enter your full name before saving profile");
      return;
    }
    if (!isValidGpa) {
      setErrorMsg("CGPA must be between 0 and 10");
      return;
    }

    setErrorMsg("");
    setActionMsg("");
    setIsSavingProfile(true);
    try {
      const { data } = await api.post("/student/profile", {
        full_name: profile.full_name,
        gpa: parsedGpa,
        education: profile.education,
        skills: parsedSkills,
      });
      const currentRecommendations = data.recommendations || {};
      const { nextCompanies } = applyRecommendationPayload(currentRecommendations);
      if (nextCompanies.length === 0 && parsedSkills.length > 0) {
        const previewData = await fetchPreviewRecommendations(parsedSkills, parsedGpa, 10);
        applyRecommendationPayload(previewData);
      }
      setActionMsg("Profile saved successfully");
      await loadData();
    } catch (error) {
      setErrorMsg(error.normalizedMessage || "Unable to save profile");
    } finally {
      setIsSavingProfile(false);
    }
  };

  const previewRecommendations = async () => {
    if (!isValidGpa) {
      setErrorMsg("CGPA must be between 0 and 10");
      return;
    }
    if (parsedSkills.length === 0) {
      setErrorMsg("Enter at least one skill to get recommendations");
      return;
    }

    setErrorMsg("");
    setActionMsg("");
    setIsPreviewing(true);
    try {
      const data = await fetchPreviewRecommendations(parsedSkills, parsedGpa, 10);
      const { nextCompanies } = applyRecommendationPayload(data);
      const companyCount = (data.recommended_companies || []).length;
      const cutoff = data.meta?.score_cutoff;
      if (nextCompanies.length === 0) {
        setActionMsg("No strong matches yet. Try adding more specific skills or upload a resume.");
      } else {
        setActionMsg(`Recommendations ready: ${companyCount} companies found${cutoff ? ` (score cutoff ${cutoff})` : ""}`);
      }
    } catch (error) {
      setErrorMsg(error.normalizedMessage || "Unable to get recommendations");
    } finally {
      setIsPreviewing(false);
    }
  };

  const apply = async (jobId, companyUrl) => {
    setErrorMsg("");
    setActionMsg("");
    setApplyingJobId(jobId);

    // Open a blank window synchronously inside user click to prevent popup blocking
    let applyWindow = null;
    const targetUrl = companyUrl || "";
    if (targetUrl) {
      let formattedUrl = targetUrl;
      if (!/^https?:\/\//i.test(formattedUrl)) {
        formattedUrl = `https://${formattedUrl}`;
      }
      applyWindow = window.open(formattedUrl, "_blank");
    }

    try {
      const { data } = await api.post(`/jobs/${jobId}/apply`);
      setActionMsg(`Applied successfully. Matching score: ${data.matching_score}`);
      
      const finalUrl = data.apply_url || targetUrl;
      if (finalUrl) {
        let formattedUrl = finalUrl;
        if (!/^https?:\/\//i.test(formattedUrl)) {
          formattedUrl = `https://${formattedUrl}`;
        }
        if (applyWindow) {
          applyWindow.location.href = formattedUrl;
        } else {
          window.open(formattedUrl, "_blank");
        }
      }
      await loadData();
    } catch (error) {
      if (applyWindow) applyWindow.close();
      setErrorMsg(error.normalizedMessage || "Unable to apply for this job");
    } finally {
      setApplyingJobId(null);
    }
  };

  const uploadResume = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.append("resume", file);
    setErrorMsg("");
    setActionMsg("");
    setResumeInfo(null);
    setIsUploadingResume(true);
    try {
      const { data } = await api.post("/student/resume", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResumeInfo(data);
      if (Array.isArray(data.profile_skills)) {
        setProfile((prev) => ({ ...prev, skills: data.profile_skills.join(", ") }));
      }
      const resumeRecommendations = data.recommendations || {};
      const { nextCompanies } = applyRecommendationPayload(resumeRecommendations);
      if (nextCompanies.length === 0 && Array.isArray(data.profile_skills) && data.profile_skills.length > 0) {
        const previewData = await fetchPreviewRecommendations(data.profile_skills, data.gpa ?? parsedGpa, 10);
        applyRecommendationPayload(previewData);
      }
      const extractedCount = (data.extracted_skills || []).length;
      const companyCount = (data.recommendations?.recommended_companies || []).length;
      setActionMsg(`Resume uploaded. Extracted ${extractedCount} skills and refreshed ${companyCount} company matches.`);
      await loadData();
    } catch (error) {
      setErrorMsg(error.normalizedMessage || "Unable to upload resume");
    } finally {
      setIsUploadingResume(false);
      e.target.value = "";
    }
  };

  const sendMentorMessage = async (e) => {
    e.preventDefault();
    const message = mentorInput.trim();
    if (!message) return;

    setIsSendingMentor(true);
    setErrorMsg("");
    setMentorMessages((prev) => [...prev, { role: "you", text: message }]);
    setMentorInput("");

    try {
      const { data } = await api.post("/student/mentor", { message });
      setMentorMessages((prev) => [...prev, { role: "mentor", text: data.reply }]);
    } catch (error) {
      setMentorMessages((prev) => [...prev, { role: "mentor", text: error.normalizedMessage || "I could not answer that right now." }]);
    } finally {
      setIsSendingMentor(false);
    }
  };

  const handleStartInterview = async () => {
    setIsStartingInterview(true);
    setErrorMsg("");
    setInterviewReport(null);
    setPreviousFeedback(null);
    try {
      const { data } = await api.post("/student/interview/start", { role: interviewRole });
      setInterviewSession(data);
      setInterviewAnswer("");
      setInterviewTime(0);
      setIsCameraOff(false);
      setIsMuted(false);
      setTimeout(() => {
        speakText(data.first_question);
      }, 300);
    } catch (e) {
      setErrorMsg("Failed to start mock interview session.");
    } finally {
      setIsStartingInterview(false);
    }
  };

  const handleSubmitAnswer = async () => {
    if (!interviewAnswer.trim()) {
      setErrorMsg("Please type or speak an answer before submitting.");
      return;
    }
    setIsSubmittingAnswer(true);
    setErrorMsg("");
    try {
      const { data } = await api.post("/student/interview/submit", {
        session_id: interviewSession.session_id,
        answer: interviewAnswer
      });
      if (data.completed) {
        setInterviewReport(data);
        setInterviewSession(null);
        setPreviousFeedback(null);
        if ("speechSynthesis" in window) {
          window.speechSynthesis.cancel();
        }
        await loadAtsData();
      } else {
        setPreviousFeedback(data.feedback_on_previous);
        setInterviewSession({
          ...interviewSession,
          current_index: data.current_index,
          first_question: data.next_question
        });
        setInterviewAnswer("");
        setTimeout(() => {
          speakText(data.next_question);
        }, 300);
      }
    } catch (e) {
      setErrorMsg("Failed to submit your response.");
    } finally {
      setIsSubmittingAnswer(false);
    }
  };

  const handleReviewProject = async (e) => {
    e.preventDefault();
    if (!projectInput.title.trim() || !projectInput.description.trim()) {
      setErrorMsg("Project Title and Description are required.");
      return;
    }
    setIsReviewingProject(true);
    setErrorMsg("");
    try {
      const { data } = await api.post("/student/project/review", projectInput);
      setProjectReview(data);
    } catch (e) {
      setErrorMsg("Failed to submit project for AI review.");
    } finally {
      setIsReviewingProject(false);
    }
  };

  const handleOpenBooster = async (job) => {
    const targetJobId = job.job_id || job.id;
    setBoosterJob(job);
    setIsGeneratingBooster(true);
    setErrorMsg("");
    setBoosterModalTab("pitch");
    try {
      const companyName = job.company_name || job.company || "";
      const jobTitle = job.job_title || job.title || "";
      const requiredSkills = job.required_skills || job.skills || [];

      const { data } = await api.post("/student/placement-booster/tailor", { 
        job_id: targetJobId,
        job_title: jobTitle,
        company_name: companyName,
        required_skills: requiredSkills
      });
      setBoosterData(data);
    } catch (e) {
      setErrorMsg("Failed to generate application booster contents.");
    } finally {
      setIsGeneratingBooster(false);
    }
  };

  const handleToggleRoadmapAction = (phaseIdx, actionIdx) => {
    const key = `${phaseIdx}-${actionIdx}`;
    setCompletedRoadmapActions(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      {errorMsg && <p className="lg:col-span-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{errorMsg}</p>}
      {actionMsg && <p className="lg:col-span-3 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{actionMsg}</p>}

      {/* Header Banner */}
      <section className="lg:col-span-3 rounded-3xl border border-slate-200 bg-gradient-to-r from-slate-950 via-slate-900 to-emerald-900 p-6 text-white shadow-xl">
        <div className="grid gap-5 lg:grid-cols-[1.2fr_0.8fr] lg:items-end">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.32em] text-emerald-300">AI Student Intelligence Hub</p>
            <h1 className="mt-2 text-3xl font-black tracking-tight md:text-4xl">Maximize placement success with active AI mentoring & real-time career auditing.</h1>
            <p className="mt-3 max-w-2xl text-sm text-slate-200">
              Complete your profile and upload a resume to unlock tailored career timelines, live industry demand trends, practice interview simulations, and resume score tailoring.
            </p>
          </div>
          <div className="grid gap-3 md:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
            <div className="rounded-2xl border border-white/10 bg-white/10 p-4 backdrop-blur">
              <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-emerald-200">ATS Audit</p>
              <p className="mt-2 text-2xl font-extrabold">{atsData ? `${atsData.ats_score}%` : "Calculating"}</p>
              <p className="mt-1 text-xs text-slate-200">Resume alignment score</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/10 p-4 backdrop-blur">
              <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-emerald-200">Roadmap</p>
              <p className="mt-2 text-2xl font-extrabold">Active</p>
              <p className="mt-1 text-xs text-slate-200">16-Week learning timeline</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/10 p-4 backdrop-blur">
              <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-emerald-200">Interviews</p>
              <p className="mt-2 text-2xl font-extrabold">Practice</p>
              <p className="mt-1 text-xs text-slate-200">AI interactive mock panels</p>
            </div>
          </div>
        </div>
      </section>

      {/* Navigation Tab Bar */}
      <div className="lg:col-span-3 flex flex-wrap gap-2 border-b border-slate-200 pb-2">
        {[
          { id: "overview", label: "Dashboard Overview" },
          { id: "jobs", label: "Available Jobs" },
          { id: "roadmap", label: "AI Career Roadmap & Trends" },
          { id: "interview", label: "AI Practice Interview" },
          { id: "reviewer", label: "AI Project Reviewer" },
          { id: "ats", label: "ATS & Placement Matcher" }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => {
              setActiveTab(tab.id);
              setErrorMsg("");
              setActionMsg("");
              if (tab.id === "roadmap") {
                loadRoadmapAndTrends();
              } else if (tab.id === "ats") {
                loadAtsData();
              }
            }}
            className={`rounded-xl px-4 py-2.5 text-sm font-semibold transition-all duration-200 ${
              activeTab === tab.id
                ? "bg-emerald-950 text-white shadow-md shadow-emerald-950/20"
                : "bg-white border border-slate-200 text-slate-700 hover:bg-slate-50"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ================= TAB 1: OVERVIEW ================= */}
      {activeTab === "overview" && (
        <>
          <SectionCard title="Student Profile" subtitle="Keep your profile and skills current so the analyzer and mentor can work better." className="lg:col-span-2">
            {!isValidGpa && <p className="mb-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">CGPA should be between 0 and 10.</p>}
            <div className="space-y-3">
              <input className="input" placeholder="Full Name" value={profile.full_name} onChange={(e) => setProfile({ ...profile, full_name: e.target.value })} />
              <input className="input" placeholder="GPA" value={profile.gpa} onChange={(e) => setProfile({ ...profile, gpa: e.target.value })} />
              <input className="input" placeholder="Education" value={profile.education} onChange={(e) => setProfile({ ...profile, education: e.target.value })} />
              <textarea className="input min-h-24" placeholder="Skills (comma separated)" value={profile.skills} onChange={(e) => setProfile({ ...profile, skills: e.target.value })} />
              <button className="btn-primary w-full disabled:cursor-not-allowed disabled:opacity-60" onClick={saveProfile} disabled={isSavingProfile || !isValidGpa}>
                {isSavingProfile ? "Saving..." : "Save Profile"}
              </button>
              <button className="btn-secondary w-full disabled:cursor-not-allowed disabled:opacity-60" onClick={previewRecommendations} disabled={isPreviewing || !canRunRecommendations}>
                {isPreviewing ? "Finding companies..." : "Find Jobs by CGPA + Skills"}
              </button>
              <label className="btn-secondary block cursor-pointer text-center">
                {isUploadingResume ? "Uploading resume..." : "Upload Resume PDF"}
                <input hidden type="file" accept="application/pdf" onChange={uploadResume} disabled={isUploadingResume} />
              </label>
              {resumeInfo && (
                <div className="rounded-lg border border-emerald-100 bg-emerald-50 p-3 text-sm text-emerald-900">
                  <p className="font-semibold">Resume parsing result</p>
                  <p>Education: {resumeInfo.education || "-"}</p>
                  <p>GPA: {resumeInfo.gpa ?? "-"}</p>
                  <p>Extracted skills: {(resumeInfo.extracted_skills || []).join(", ") || "-"}</p>
                </div>
              )}
            </div>
          </SectionCard>

          <SectionCard title="Resume Snapshot" subtitle="Quick view of what the parser and profile already know.">
            <div className="space-y-3 text-sm">
              <p className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-slate-700">Status: {profile.resume_path ? "Uploaded" : "Not uploaded"}</p>
              <p className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-slate-700 break-all">File: {profile.resume_path || "Upload a PDF resume to unlock better matching"}</p>
              <p className="rounded-lg border border-emerald-100 bg-emerald-50 px-3 py-2 text-emerald-900">Education: {profile.education || "-"}</p>
              <p className="rounded-lg border border-emerald-100 bg-emerald-50 px-3 py-2 text-emerald-900">GPA: {profile.gpa || "-"}</p>
              <p className="rounded-lg border border-emerald-100 bg-emerald-50 px-3 py-2 text-emerald-900">Skills captured: {parsedSkills.length}</p>
            </div>
          </SectionCard>

          <SectionCard title="Real-time Demand Hiring Analyzer" subtitle="What companies are asking for right now, based on approved jobs." className="lg:col-span-3">
            <div className="grid gap-4 lg:grid-cols-3">
              <div className="rounded-2xl border border-emerald-100 bg-emerald-50 p-4 lg:col-span-1">
                <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-emerald-700">Insight</p>
                <p className="mt-2 text-sm text-slate-700">{demandAnalyzer?.summary || (isLoadingData ? "Analyzing hiring demand..." : "No live demand data yet.")}</p>
                <div className="mt-4 space-y-2">
                  {(demandAnalyzer?.action_plan || []).map((item) => (
                    <p key={item} className="rounded-xl bg-white px-3 py-2 text-xs text-slate-700 shadow-sm">
                      {item}
                    </p>
                  ))}
                </div>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">Top Skills</p>
                <div className="mt-3 space-y-2">
                  {(demandAnalyzer?.top_skills || []).map((item) => (
                    <div key={item.skill} className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 px-3 py-2 text-sm">
                      <span className="font-medium text-slate-900">{item.skill}</span>
                      <span className={`rounded-full px-2 py-1 text-xs font-semibold ${item.you_have_it ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`}>
                        {item.demand} jobs
                      </span>
                    </div>
                  ))}
                  {(demandAnalyzer?.top_skills || []).length === 0 && <p className="text-sm text-slate-600">No demand insight yet.</p>}
                </div>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">Top Roles</p>
                <div className="mt-3 space-y-2">
                  {(demandAnalyzer?.top_roles || []).map((item) => (
                    <div key={item.role} className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2 text-sm">
                      <p className="font-medium text-slate-900">{item.role}</p>
                      <p className="text-xs text-slate-500">{item.openings} openings</p>
                    </div>
                  ))}
                </div>
                <p className="mt-4 text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">Hot Companies</p>
                <div className="mt-2 space-y-2">
                  {(demandAnalyzer?.top_companies || []).map((item) => (
                    <div key={item.company} className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2 text-sm">
                      <p className="font-medium text-slate-900">{item.company}</p>
                      <p className="text-xs text-slate-500">{item.openings} active openings</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </SectionCard>

          <SectionCard title="AI Career Mentor Chatbot" subtitle="Ask for resume, job, interview, or skill-gap advice." className="lg:col-span-2">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
              <div className="max-h-72 space-y-3 overflow-y-auto pr-1">
                {mentorMessages.map((item, index) => (
                  <div key={`${item.role}-${index}`} className={`max-w-[90%] rounded-2xl px-3 py-2 text-sm ${item.role === "you" ? "ml-auto bg-slate-900 text-white" : "bg-white text-slate-800 shadow-sm"}`}>
                    {item.text}
                  </div>
                ))}
              </div>
            </div>
            <form className="mt-3 flex gap-2" onSubmit={sendMentorMessage}>
              <input className="input flex-1" placeholder="Ask your mentor something specific" value={mentorInput} onChange={(e) => setMentorInput(e.target.value)} />
              <button className="btn-primary disabled:cursor-not-allowed disabled:opacity-60" disabled={isSendingMentor} type="submit">
                {isSendingMentor ? "Sending..." : "Ask"}
              </button>
            </form>
            <div className="mt-3 grid gap-2 md:grid-cols-3">
              {resumeWeaknesses?.next_steps?.slice(0, 3).map((step) => (
                <div key={step} className="rounded-xl border border-emerald-100 bg-emerald-50 px-3 py-2 text-xs text-slate-700">
                  {step}
                </div>
              ))}
            </div>
          </SectionCard>

          <SectionCard title="Resume Weakness Detector" subtitle="Signals that can reduce matching or interview performance." className="lg:col-span-1">
            <div className="space-y-4 text-sm">
              <div>
                <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-emerald-700">Strengths</p>
                <div className="mt-2 space-y-2">
                  {(resumeWeaknesses?.strengths || []).map((item) => (
                    <div key={item} className="rounded-xl border border-emerald-100 bg-emerald-50 px-3 py-2 text-slate-700">
                      {item}
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-rose-700">Weaknesses</p>
                <div className="mt-2 space-y-2">
                  {(resumeWeaknesses?.weaknesses || []).map((item) => (
                    <div key={item} className="rounded-xl border border-rose-100 bg-rose-50 px-3 py-2 text-slate-700">
                      {item}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </SectionCard>

          <SectionCard title="Peer Comparison Dashboard" subtitle="How your profile compares to the student cohort." className="lg:col-span-3">
            <div className="grid gap-4 md:grid-cols-4">
              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">Your GPA</p>
                <p className="mt-2 text-2xl font-black text-slate-900">{peerComparison?.your_profile?.gpa ?? "-"}</p>
                <p className="text-xs text-slate-500">Peer percentile: {peerComparison?.percentiles?.gpa_percentile ?? 0}%</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">Your Skills</p>
                <p className="mt-2 text-2xl font-black text-slate-900">{peerComparison?.your_profile?.skill_count ?? 0}</p>
                <p className="text-xs text-slate-500">Peer percentile: {peerComparison?.percentiles?.skill_percentile ?? 0}%</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">Cohort GPA</p>
                <p className="mt-2 text-2xl font-black text-slate-900">{peerComparison?.peer_average?.gpa ?? 0}</p>
                <p className="text-xs text-slate-500">Average across saved students</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">Cohort Skills</p>
                <p className="mt-2 text-2xl font-black text-slate-900">{peerComparison?.peer_average?.skill_count ?? 0}</p>
                <p className="text-xs text-slate-500">Average skill count</p>
              </div>
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              {(peerComparison?.comparison_notes || []).map((note) => (
                <div key={note} className="rounded-xl border border-emerald-100 bg-emerald-50 px-3 py-2 text-sm text-slate-700">
                  {note}
                </div>
              ))}
            </div>
          </SectionCard>

          <SectionCard title="Notifications" subtitle="Student notifications and shortlist updates." className="lg:col-span-3">
            <div className="grid gap-3 md:grid-cols-2">
              {notifications.map((note) => (
                <div key={note.id} className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                  <p className="font-semibold">{note.title}</p>
                  <p className="text-sm text-slate-700">{note.message}</p>
                </div>
              ))}
              {notifications.length === 0 && <p className="text-sm text-slate-600">No notifications yet.</p>}
            </div>
          </SectionCard>
        </>
      )}

      {/* ================= TAB 2: JOBS ================= */}
      {activeTab === "jobs" && (
        <>
          <SectionCard title="Available Jobs" subtitle="Current campus placement positions. Use the AI booster to tailor your profile." className="lg:col-span-2">
            {isLoadingData && <p className="mb-3 text-sm text-slate-600">Loading latest jobs and recommendations...</p>}
            <div className="space-y-4">
              {personalizedAvailableJobs.map((job, index) => {
                const companyName = job.company_name || job.company || "Unknown Company";
                const jobTitle = job.job_title || job.title || "Role";
                const jobDescription = job.job_description || job.description || "";
                const requiredSkills = job.required_skills || job.skills || [];
                const localJobId = getNumericJobId(job);
                const canApplyInternally = localJobId !== null;

                return (
                  <article key={`${localJobId || job.apply_url || companyName}-${index}`} className="rounded-xl border border-emerald-100 bg-white p-4 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-start gap-3">
                      <img
                        src={resolvePrimaryLogo(companyName, job.logo_url, job.apply_url)}
                        alt={`${companyName} logo`}
                        className="h-10 w-10 rounded-md border border-emerald-100 bg-white object-contain p-1"
                        onError={(e) => handleLogoError(e, companyName, job.apply_url)}
                      />
                      <div>
                        <h3 className="text-lg font-semibold text-slate-900">{jobTitle}</h3>
                        <p className="text-sm text-slate-600">{companyName}</p>
                      </div>
                    </div>
                    {jobDescription && <p className="mt-2 text-sm text-slate-800 leading-relaxed">{jobDescription}</p>}
                    <div className="mt-3 flex flex-wrap gap-1">
                      {requiredSkills.map((sk) => (
                        <span key={sk} className="rounded-lg bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-700">
                          {sk}
                        </span>
                      ))}
                    </div>
                    
                    <div className="mt-3 grid grid-cols-2 gap-2 text-xs border-t border-slate-50 pt-2">
                      <p className="text-emerald-800 font-semibold">Matching Score: {job.matching_score ?? "N/A"}</p>
                      <p className="text-emerald-800 font-semibold">Eligibility: {job.gpa_eligible === false ? "Below Preferred CGPA" : "Eligible"}</p>
                    </div>

                    <div className="flex gap-2 mt-4">
                      {canApplyInternally ? (
                        <button 
                          className="btn-primary flex-1 disabled:cursor-not-allowed disabled:opacity-60" 
                          onClick={() => apply(localJobId, job.apply_url)} 
                          disabled={applyingJobId === localJobId}
                        >
                          {applyingJobId === localJobId ? "Applying..." : "Apply"}
                        </button>
                      ) : job.apply_url ? (
                        <a 
                          className="inline-block text-sm font-semibold text-emerald-800 border border-emerald-200 hover:bg-emerald-50 rounded-xl px-4 py-2.5 text-center flex-1 transition-colors" 
                          href={job.apply_url} 
                          target="_blank" 
                          rel="noreferrer"
                        >
                          Register / Apply externally
                        </a>
                      ) : (
                        <p className="text-xs text-slate-500 flex-1">Register as student and use Apply for internal openings.</p>
                      )}

                      <button
                        onClick={() => handleOpenBooster(job)}
                        className="rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 px-4 py-2.5 text-sm font-bold flex items-center justify-center gap-1 transition-colors"
                      >
                        ✨ Boost Application
                      </button>
                    </div>
                  </article>
                );
              })}
              {personalizedAvailableJobs.length === 0 && <p className="text-sm text-slate-600">No jobs currently match your CGPA criteria. Update profile/resume and try again.</p>}
            </div>
          </SectionCard>

          <div className="space-y-6 lg:col-span-1">
            <SectionCard title="Top Matched Jobs" subtitle="Sorted recommendations based on skills & resume.">
              <div className="grid gap-3">
                {recommendedJobs.map((job) => (
                  <div key={job.job_id} className="rounded-lg border border-emerald-100 bg-white p-3 shadow-sm">
                    <p className="font-semibold text-slate-900">{job.job_title}</p>
                    <p className="text-sm text-slate-700">{job.company_name}</p>
                    <p className="mt-1 text-xs text-emerald-700">Matching score: {job.matching_score}</p>
                    <p className="mt-1 text-xs text-slate-500">Required: {(job.required_skills || []).slice(0, 4).join(", ") || "-"}</p>
                    {job.apply_url && (
                      <a className="mt-2 inline-block text-xs font-semibold text-emerald-800 underline" href={job.apply_url} target="_blank" rel="noreferrer">
                        Apply externally
                      </a>
                    )}
                  </div>
                ))}
                {recommendedJobs.length === 0 && <p className="text-sm text-slate-600">No matched jobs found yet.</p>}
              </div>
            </SectionCard>

            <SectionCard title="Hiring Companies" subtitle="Active recruiters you can browse.">
              <div className="grid gap-3">
                {companies.map((company) => (
                  <div key={company.id} className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
                    <p className="font-semibold text-slate-900">{company.company_name}</p>
                    <p className="text-xs text-slate-600 line-clamp-2">{company.description || "No description"}</p>
                    <p className="mt-1 text-xs text-slate-500">Approved jobs: {company.approved_jobs}</p>
                  </div>
                ))}
                {companies.length === 0 && <p className="text-sm text-slate-600">No company profiles available yet.</p>}
              </div>
            </SectionCard>
          </div>
        </>
      )}

      {/* ================= TAB 3: ROADMAP & TRENDS ================= */}
      {activeTab === "roadmap" && (
        <>
          <SectionCard title="AI Career Roadmap" subtitle="Personalized 16-Week learning pathway generated from your profile stack." className="lg:col-span-2">
            {/* Domain Selection Bar */}
            <div className="mb-6 bg-slate-50 border border-slate-200 p-4 rounded-2xl space-y-2">
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider">Target Domain Pathway</label>
              <div className="flex flex-wrap gap-2">
                {[
                  { id: "frontend", label: "Frontend Specialist" },
                  { id: "backend", label: "Backend Architect" },
                  { id: "data_science", label: "Machine Learning / DS" },
                  { id: "general", label: "Full-Stack Generalist" }
                ].map((d) => (
                  <button
                    key={d.id}
                    onClick={() => {
                      setSelectedRoadmapDomain(d.id);
                      loadRoadmapAndTrends(d.id);
                    }}
                    className={`rounded-xl px-3 py-1.5 text-xs font-bold transition-all ${
                      selectedRoadmapDomain === d.id || (!selectedRoadmapDomain && roadmap?.target_domain?.toLowerCase().includes(d.id.split("_")[0]))
                        ? "bg-emerald-950 text-white shadow-sm"
                        : "bg-white border border-slate-200 text-slate-700 hover:bg-slate-50"
                    }`}
                  >
                    {d.label}
                  </button>
                ))}
              </div>
            </div>

            {isLoadingRoadmap ? (
              <div className="py-12 text-center">
                <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-emerald-700 border-t-transparent"></div>
                <p className="mt-4 text-sm text-slate-600">Generating timeline steps and resource indexing...</p>
              </div>
            ) : roadmap ? (
              <div className="space-y-6">
                <div className="rounded-2xl bg-slate-950 p-4 text-white">
                  <p className="text-xs text-emerald-400 font-bold uppercase tracking-wider">Target Domain</p>
                  <p className="text-xl font-bold">{roadmap.target_domain}</p>
                  <p className="mt-1 text-sm text-slate-300">{roadmap.description}</p>
                  {roadmap.skills_to_acquire && (
                    <div className="mt-3 border-t border-white/10 pt-3">
                      <p className="text-xs text-slate-400 font-bold uppercase">Next Skill Focus</p>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {roadmap.skills_to_acquire.map(s => (
                          <span key={s} className="rounded-md bg-emerald-900/50 border border-emerald-700/50 px-2 py-0.5 text-xs text-emerald-300 font-semibold">
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className="relative border-l-2 border-slate-200 ml-3 pl-6 space-y-6">
                  {roadmap.phases.map((phase, pIdx) => (
                    <div key={pIdx} className="relative">
                      <span className="absolute -left-[31px] top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-emerald-700 ring-4 ring-white"></span>
                      <h3 className="text-lg font-bold text-slate-900">{phase.name}</h3>
                      <p className="text-sm text-emerald-800 font-semibold mt-1">Milestone: {phase.milestone}</p>
                      
                      <div className="mt-3 space-y-2">
                        <p className="text-xs uppercase tracking-wider text-slate-500 font-bold">Actions to Complete:</p>
                        {phase.actions.map((action, aIdx) => {
                          const doneKey = `${pIdx}-${aIdx}`;
                          const isDone = !!completedRoadmapActions[doneKey];
                          return (
                            <div 
                              key={aIdx} 
                              onClick={() => handleToggleRoadmapAction(pIdx, aIdx)}
                              className={`flex gap-3 items-center p-3 rounded-xl border cursor-pointer transition-all ${
                                isDone 
                                  ? "bg-emerald-50/50 border-emerald-200 text-slate-500 line-through" 
                                  : "bg-white border-slate-200 text-slate-800 hover:border-slate-300"
                              }`}
                            >
                              <input 
                                type="checkbox" 
                                checked={isDone} 
                                readOnly
                                className="h-4 w-4 text-emerald-700 rounded border-slate-300" 
                              />
                              <span className="text-sm">{action}</span>
                            </div>
                          );
                        })}
                      </div>

                      <div className="mt-3">
                        <p className="text-xs uppercase tracking-wider text-slate-500 font-bold">Recommended Resources:</p>
                        <div className="mt-1 flex flex-wrap gap-2">
                          {phase.resources.map(res => (
                            <span key={res} className="rounded-lg bg-slate-50 border border-slate-200 text-slate-700 text-xs px-2.5 py-1 font-medium shadow-sm">
                              📖 {res}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-600">Enter skills in your Profile to generate your career roadmap.</p>
            )}
          </SectionCard>

          <SectionCard title="Live Industry Trends" subtitle="Verified technology demand growth and compensation models.">
            {isLoadingRoadmap ? (
              <p className="text-sm text-slate-600">Loading trends...</p>
            ) : skillTrends.length > 0 ? (
              <div className="space-y-4">
                {skillTrends.map(item => (
                  <div key={item.skill} className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
                    <div className="flex items-center justify-between">
                      <p className="font-bold text-slate-900">{item.skill}</p>
                      <span className={`rounded-full px-2 py-0.5 text-xs font-semibold uppercase ${
                        item.growth === "rising" ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-700"
                      }`}>
                        {item.growth === "rising" ? "▲ Rising" : "■ Stable"}
                      </span>
                    </div>

                    <div className="mt-2 space-y-1">
                      <div className="flex justify-between text-xs text-slate-500">
                        <span>Demand Match Speed</span>
                        <span>{item.demand_score}%</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-1.5">
                        <div 
                          className="bg-emerald-700 h-1.5 rounded-full" 
                          style={{ width: `${item.demand_score}%` }}
                        ></div>
                      </div>
                    </div>

                    <div className="mt-3 grid grid-cols-2 text-xs border-t border-slate-50 pt-2 text-slate-600">
                      <p>Openings: <span className="font-bold text-slate-900">{item.active_openings}</span></p>
                      <p>Avg Salary: <span className="font-bold text-slate-900">{item.average_salary}</span></p>
                    </div>

                    <div className="mt-2 text-xs border-t border-slate-50 pt-2">
                      <p className="text-slate-500 font-medium">Hiring: {item.companies.join(", ")}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-600">No industry trend charts loaded yet.</p>
            )}
          </SectionCard>
        </>
      )}

      {/* ================= TAB 4: PRACTICE INTERVIEW ================= */}
      {activeTab === "interview" && (
        <>
          <SectionCard 
            title="AI Boardroom: Interactive Panel Interview" 
            subtitle="Simulate real-time executive hiring loops. Turn on camera, mute or talk directly to the AI board." 
            className="lg:col-span-3"
          >
            {!interviewSession && !interviewReport && (
              <div className="py-12 text-center space-y-6 max-w-2xl mx-auto">
                <div className="mx-auto w-20 h-20 rounded-3xl bg-emerald-50/50 border border-emerald-100 flex items-center justify-center shadow-md">
                  <span className="text-4xl animate-bounce">🎙️</span>
                </div>
                <div className="space-y-2">
                  <h3 className="text-2xl font-black text-slate-900 tracking-tight">Technical Board Mock Simulator</h3>
                  <p className="text-sm text-slate-600 leading-relaxed">
                    Test your response times, keyword compliance, and explanations under simulated pressure. The panel will dictate questions, scan webcam feeds, and grade structural completeness.
                  </p>
                </div>

                <div className="max-w-md mx-auto space-y-3 bg-slate-50 border border-slate-200 p-6 rounded-3xl">
                  <div className="text-left">
                    <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Target Technical Role</label>
                    <select 
                      value={interviewRole} 
                      onChange={e => setInterviewRole(e.target.value)}
                      className="w-full rounded-xl border border-slate-200 p-3 text-sm focus:border-emerald-700 outline-none bg-white font-semibold text-slate-800"
                    >
                      <option value="Frontend UI React Engineer">Frontend UI React Engineer</option>
                      <option value="Backend Systems Architect">Backend Systems Architect</option>
                      <option value="Machine Learning Specialist">Machine Learning Specialist</option>
                      <option value="Full-Stack Generalist Engineer">Full-Stack Generalist Engineer</option>
                    </select>
                  </div>

                  <button 
                    onClick={handleStartInterview} 
                    disabled={isStartingInterview}
                    className="btn-primary w-full py-3.5 text-sm font-bold flex items-center justify-center gap-2 shadow-lg shadow-emerald-950/10 hover:shadow-emerald-950/20"
                  >
                    {isStartingInterview ? (
                      <>
                        <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                        Connecting Call...
                      </>
                    ) : "Enter AI Boardroom Session"}
                  </button>
                </div>
              </div>
            )}

            {interviewSession && (
              <div className="space-y-6">
                {/* Boardroom Header */}
                <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-950 p-4 text-white rounded-3xl border border-slate-800 shadow-md">
                  <div className="flex items-center gap-3">
                    <span className="relative flex h-3 w-3">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-3 w-3 bg-rose-500"></span>
                    </span>
                    <div>
                      <p className="text-[10px] text-emerald-400 font-extrabold uppercase tracking-widest">Active Hiring Loop</p>
                      <p className="text-sm font-bold text-slate-200">{interviewSession.role}</p>
                    </div>
                  </div>
                  <div className="flex gap-4 text-right">
                    <div>
                      <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Session Time</p>
                      <p className="text-sm font-mono font-bold text-emerald-400">{formatTime(interviewTime)}</p>
                    </div>
                    <div className="border-l border-slate-800 pl-4">
                      <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Progress</p>
                      <p className="text-sm font-bold">Q: {interviewSession.current_index + 1} / {interviewSession.total_questions}</p>
                    </div>
                  </div>
                </div>

                {/* Main Video Call Screen Grid */}
                <div className="grid gap-6 md:grid-cols-3">
                  {/* AI Board Panel: Feed 1 (Evelyn) & Feed 2 (Marcus) */}
                  <div className="bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden flex flex-col justify-between p-4 shadow-xl relative min-h-[290px] md:col-span-2">
                    <div className="flex justify-between items-center z-10 mb-2">
                      <span className="bg-slate-950/60 backdrop-blur px-2.5 py-1 text-[10px] font-extrabold text-slate-300 rounded-full border border-slate-800 uppercase tracking-widest flex items-center gap-1.5">
                        🤖 AI Executive Boardroom
                      </span>
                      <span className="bg-slate-950/60 backdrop-blur px-2 py-0.5 text-[9px] font-bold text-emerald-400 rounded-md">
                        {isAiSpeaking ? "Robotic Speech Transmitting" : "Awaiting Candidate Feedback"}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-4 flex-1 items-center justify-center z-0 py-2">
                      {/* Dr. Evelyn Vance (Female Robot Evaluator) */}
                      <div className="flex flex-col items-center justify-center space-y-2 bg-slate-950/70 p-3 rounded-2xl border border-fuchsia-500/20 shadow-[0_0_12px_rgba(217,70,239,0.15)] relative overflow-hidden">
                        {/* Humanoid Robot SVG Face */}
                        <div className="relative w-20 h-20 flex items-center justify-center">
                          <svg viewBox="0 0 100 100" className="w-full h-full drop-shadow-[0_0_8px_rgba(217,70,239,0.4)]">
                            {/* Metallic contoured face mask */}
                            <path d="M22,40 Q22,15 50,15 Q78,15 78,40 Q78,72 50,83 Q22,72 22,40 Z" fill="url(#metal-grad-evelyn)" stroke="#d946ef" strokeWidth="1" />
                            {/* Face Plate Inner Shield */}
                            <path d="M28,40 Q28,23 50,23 Q72,23 72,40 Q72,67 50,76 Q28,67 28,40 Z" fill="#110d29" stroke="#f5d0fe" strokeWidth="0.5" />
                            
                            {/* Left Cybernetic Eye */}
                            <circle cx="38" cy="38" r="5" fill="#1e1548" stroke="#d946ef" strokeWidth="0.5" />
                            <circle cx="38" cy="38" r="2.5" fill="#f472b6" className="animate-pulse" />
                            <circle cx="37" cy="37" r="0.8" fill="#ffffff" />
                            
                            {/* Right Cybernetic Eye */}
                            <circle cx="62" cy="38" r="5" fill="#1e1548" stroke="#d946ef" strokeWidth="0.5" />
                            <circle cx="62" cy="38" r="2.5" fill="#f472b6" className="animate-pulse" />
                            <circle cx="61" cy="37" r="0.8" fill="#ffffff" />

                            {/* Cybernetic Forehead Crest & Cheeks */}
                            <path d="M50,23 L50,30" stroke="#f5d0fe" strokeWidth="0.7" opacity="0.6" />
                            <path d="M32,48 Q40,51 44,48" stroke="#f472b6" strokeWidth="0.5" fill="none" opacity="0.5" />
                            <path d="M68,48 Q60,51 56,48" stroke="#f472b6" strokeWidth="0.5" fill="none" opacity="0.5" />

                            {/* Voice responsive mouth grid */}
                            {isAiSpeaking ? (
                              <path d="M42,60 Q50,68 58,60 Q50,56 42,60 Z" fill="#d946ef" className="animate-bounce" />
                            ) : (
                              <line x1="42" y1="60" x2="58" y2="60" stroke="#d946ef" strokeWidth="1.5" strokeLinecap="round" />
                            )}

                            <defs>
                              <linearGradient id="metal-grad-evelyn" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" stopColor="#4a044e" />
                                <stop offset="50%" stopColor="#1c0f3a" />
                                <stop offset="100%" stopColor="#2e1065" />
                              </linearGradient>
                            </defs>
                          </svg>
                          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-[1px] bg-fuchsia-500/20 pointer-events-none animate-pulse"></div>
                        </div>

                        <div className="text-center z-10">
                          <p className="text-xs font-black text-slate-200">Dr. Evelyn Vance</p>
                          <p className="text-[9px] text-fuchsia-400 font-bold uppercase tracking-wider">EV-9000 Humanoid | Online</p>
                          <p className="text-[8px] text-slate-400 italic mt-0.5 font-mono">
                            {isAiSpeaking ? "🎙️ [Synthesizing Speech...]" : "👁️ [Tracking Candidate]"}
                          </p>
                        </div>
                      </div>

                      {/* Dr. Marcus Sterling (Male Robot Evaluator) */}
                      <div className="flex flex-col items-center justify-center space-y-2 bg-slate-950/70 p-3 rounded-2xl border border-cyan-500/20 shadow-[0_0_12px_rgba(6,182,212,0.15)] relative overflow-hidden">
                        {/* Humanoid Robot SVG Face */}
                        <div className="relative w-20 h-20 flex items-center justify-center">
                          <svg viewBox="0 0 100 100" className="w-full h-full drop-shadow-[0_0_8px_rgba(6,182,212,0.4)]">
                            {/* Chiseled metallic face mask */}
                            <path d="M24,35 L32,15 L68,15 L76,35 L73,68 L50,84 L27,68 Z" fill="url(#metal-grad-marcus)" stroke="#06b6d4" strokeWidth="1" />
                            {/* Face Plate Inner Shield */}
                            <path d="M29,35 L36,22 L64,22 L71,35 L68,64 L50,78 L32,64 Z" fill="#08223d" stroke="#cffafe" strokeWidth="0.5" />
                            
                            {/* Left Cybernetic Eye */}
                            <rect x="34" y="34" width="8" height="6" rx="1.5" fill="#0a2a4a" stroke="#06b6d4" strokeWidth="0.5" />
                            <circle cx="38" cy="37" r="2.5" fill="#22d3ee" className="animate-pulse" />
                            <circle cx="37" cy="36" r="0.8" fill="#ffffff" />
                            
                            {/* Right Cybernetic Eye */}
                            <rect x="58" y="34" width="8" height="6" rx="1.5" fill="#0a2a4a" stroke="#06b6d4" strokeWidth="0.5" />
                            <circle cx="62" cy="37" r="2.5" fill="#22d3ee" className="animate-pulse" />
                            <circle cx="61" cy="36" r="0.8" fill="#ffffff" />

                            {/* Chiseled Cybernetic marks & Nose bridge */}
                            <path d="M50,15 L50,28" stroke="#06b6d4" strokeWidth="0.5" opacity="0.6" />
                            <path d="M50,42 L50,55" stroke="#22d3ee" strokeWidth="0.5" opacity="0.5" />

                            {/* Voice responsive mouth grid */}
                            {isAiSpeaking ? (
                              <path d="M40,62 L45,59 L50,62 L55,59 L60,62 L50,66 Z" fill="#22d3ee" className="animate-bounce" />
                            ) : (
                              <line x1="40" y1="62" x2="60" y2="62" stroke="#06b6d4" strokeWidth="1.5" strokeLinecap="round" />
                            )}

                            <defs>
                              <linearGradient id="metal-grad-marcus" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" stopColor="#0f172a" />
                                <stop offset="50%" stopColor="#082f49" />
                                <stop offset="100%" stopColor="#0f172a" />
                              </linearGradient>
                            </defs>
                          </svg>
                          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-[1px] bg-cyan-500/20 pointer-events-none animate-pulse"></div>
                        </div>

                        <div className="text-center z-10">
                          <p className="text-xs font-black text-slate-200">Dr. Marcus Sterling</p>
                          <p className="text-[9px] text-cyan-400 font-bold uppercase tracking-wider">MS-8000 Humanoid | Active</p>
                          <p className="text-[8px] text-slate-400 italic mt-0.5 font-mono">
                            {isAiSpeaking ? "🤖 [Auditing syntax loops...]" : "💾 [Mapping answer matrix]"}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Subtitle Caption Overlay */}
                    <div className="z-10 mt-auto bg-slate-950/80 backdrop-blur-sm border border-slate-800 text-slate-100 text-xs px-4 py-3 rounded-2xl text-center leading-relaxed max-w-[95%] mx-auto shadow-lg select-none">
                      {interviewSession.first_question}
                    </div>
                  </div>

                  {/* Student Camera Feed */}
                  <div className="bg-slate-950 border border-slate-800 rounded-3xl overflow-hidden flex flex-col justify-between p-4 shadow-xl relative min-h-[260px] md:col-span-1">
                    <div className="flex justify-between items-center z-10">
                      <span className="bg-slate-900/60 backdrop-blur px-2.5 py-1 text-[10px] font-extrabold text-slate-300 rounded-full border border-slate-800 uppercase tracking-widest flex items-center gap-1.5">
                        <span className="h-1.5 w-1.5 rounded-full bg-rose-600 animate-ping"></span>
                        REC
                      </span>
                      <span className="bg-slate-900/60 backdrop-blur px-2 py-0.5 text-[9px] font-bold text-slate-400 rounded-md">
                        {!isCameraOff && videoStream ? "1080p HD" : "Cam Offline"}
                      </span>
                    </div>

                    {/* Camera Video tag - always mounted to prevent ref binding race conditions */}
                    <video 
                      ref={videoRef} 
                      autoPlay 
                      playsInline 
                      muted 
                      style={{ display: (!isCameraOff && videoStream) ? "block" : "none" }}
                      className="absolute inset-0 w-full h-full object-cover rounded-3xl z-0"
                    />

                    {/* Fallback avatar preview */}
                    {(!videoStream || isCameraOff) && (
                      <div className="absolute inset-0 flex flex-col items-center justify-center space-y-2 bg-slate-900/60 z-0">
                        <div className="w-16 h-16 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-400">
                          <span className="text-xl font-bold">{(profile.full_name || "S").charAt(0).toUpperCase()}</span>
                        </div>
                        <p className="text-xs text-slate-500 font-bold uppercase tracking-wider">Camera Terminated</p>
                      </div>
                    )}

                    <div className="z-10 mt-auto flex justify-between items-center bg-slate-900/60 backdrop-blur px-3 py-1.5 rounded-xl border border-slate-800">
                      <p className="text-xs font-semibold text-slate-200">{profile.full_name || "Student Candidate"}</p>
                      <div className="flex items-center gap-1 text-[10px] text-slate-400">
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
                        HD connection
                      </div>
                    </div>
                  </div>
                </div>

                {/* Video Controls Bar */}
                <div className="flex flex-wrap items-center justify-center gap-3 bg-slate-50 p-4 border border-slate-200 rounded-3xl shadow-sm">
                  <button 
                    onClick={() => setIsMuted(!isMuted)}
                    className={`rounded-xl p-3 border transition-all duration-200 flex items-center justify-center ${
                      isMuted 
                        ? "bg-rose-50 border-rose-200 text-rose-600 hover:bg-rose-100" 
                        : "bg-white border-slate-200 text-slate-600 hover:bg-slate-100"
                    }`}
                    title={isMuted ? "Unmute Mic" : "Mute Mic"}
                  >
                    <span className="text-lg">{isMuted ? "🎙️ (Muted)" : "🎙️ Mute"}</span>
                  </button>

                  <button 
                    onClick={() => setIsCameraOff(!isCameraOff)}
                    className={`rounded-xl p-3 border transition-all duration-200 flex items-center justify-center ${
                      isCameraOff 
                        ? "bg-rose-50 border-rose-200 text-rose-600 hover:bg-rose-100" 
                        : "bg-white border-slate-200 text-slate-600 hover:bg-slate-100"
                    }`}
                    title={isCameraOff ? "Turn Cam On" : "Turn Cam Off"}
                  >
                    <span className="text-lg">{isCameraOff ? "📹 Video Off" : "📹 Video On"}</span>
                  </button>

                  <button 
                    onClick={startSpeechRecognition}
                    disabled={isListening}
                    className={`rounded-xl px-5 py-3 border transition-all duration-300 flex items-center gap-2 font-bold ${
                      isListening 
                        ? "bg-emerald-600 border-emerald-600 text-white animate-pulse" 
                        : "bg-white border-slate-200 text-emerald-800 hover:bg-emerald-50"
                    }`}
                  >
                    <span className="text-lg">🎤</span>
                    <span>{isListening ? "Listening..." : "Dictate Answer"}</span>
                  </button>

                  <button 
                    onClick={() => {
                      if ("speechSynthesis" in window) window.speechSynthesis.cancel();
                      setInterviewSession(null);
                    }}
                    className="rounded-xl px-4 py-3 bg-rose-700 hover:bg-rose-800 text-white font-bold transition-colors"
                  >
                    📞 End Loop
                  </button>
                </div>

                {/* Subtitle feedback and text response portal */}
                <div className="grid gap-6 md:grid-cols-[1.3fr_0.7fr] items-start border-t border-slate-100 pt-6">
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider">Candidate Explanation Transcript</label>
                      <p className="text-[11px] text-slate-500">Edit or review your dictated voice response before routing for board evaluation.</p>
                      <textarea
                        value={interviewAnswer}
                        onChange={e => setInterviewAnswer(e.target.value)}
                        placeholder="Start speaking by clicking 'Dictate Answer' above, or type your technical response here..."
                        className="input min-h-32 font-sans text-sm focus:border-emerald-700"
                      />
                      <button 
                        onClick={handleSubmitAnswer}
                        disabled={isSubmittingAnswer || !interviewAnswer.trim()}
                        className="btn-primary w-full py-3 font-bold"
                      >
                        {isSubmittingAnswer ? "Evaluating answer keyword sets..." : "Submit Answer to Board"}
                      </button>
                    </div>
                  </div>

                  {/* Previous Feedback Sidebar */}
                  <div className="bg-slate-50 border border-slate-200 rounded-3xl p-5 space-y-4">
                    <h4 className="text-xs uppercase font-extrabold text-slate-500 tracking-wider">Active Evaluator Logs</h4>
                    {previousFeedback ? (
                      <div className="space-y-3 text-sm">
                        <div className="flex justify-between items-center">
                          <span className="text-xs font-semibold text-slate-600">Question Accuracy:</span>
                          <span className="font-black text-emerald-800">{previousFeedback.score}/100</span>
                        </div>
                        <div className="space-y-1.5">
                          {previousFeedback.strengths.map((str, i) => (
                            <p key={i} className="text-xs text-slate-700 flex gap-1.5"><span className="text-emerald-700 font-bold">✓</span> {str}</p>
                          ))}
                          {previousFeedback.weaknesses.map((weak, i) => (
                            <p key={i} className="text-xs text-slate-700 flex gap-1.5"><span className="text-rose-600 font-bold">⚠</span> {weak}</p>
                          ))}
                        </div>
                        <details className="mt-2 border-t border-slate-200 pt-2">
                          <summary className="text-xs text-emerald-950 font-bold cursor-pointer outline-none">Guideline Answers</summary>
                          <p className="mt-1.5 text-xs text-slate-600 leading-relaxed font-sans bg-white p-2.5 border border-slate-100 rounded-xl max-h-40 overflow-y-auto">{previousFeedback.model_answer}</p>
                        </details>
                      </div>
                    ) : (
                      <p className="text-xs text-slate-500 leading-relaxed">No answers evaluated in this session yet. Dictate your response and submit to see logs.</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {interviewReport && (
              <div className="space-y-6 max-w-3xl mx-auto py-6">
                <div className="text-center py-8 bg-slate-50 rounded-3xl border border-slate-200 space-y-3">
                  <span className="text-5xl">🏆</span>
                  <h3 className="text-2xl font-black text-slate-900 tracking-tight">Board Evaluation Complete</h3>
                  <div className="inline-block bg-emerald-100 text-emerald-800 rounded-full px-4 py-1 text-xs font-bold uppercase tracking-wider">
                    Grade: {interviewReport.grade}
                  </div>
                  <p className="text-4xl font-black text-slate-950 mt-1">{interviewReport.average_score}%</p>
                  <p className="text-sm text-slate-600 max-w-lg mx-auto px-6 mt-1 leading-relaxed">{interviewReport.summary_feedback}</p>

                  <button 
                    onClick={() => {
                      setInterviewReport(null);
                      setInterviewSession(null);
                    }}
                    className="btn-primary px-8 py-3.5 shadow-md font-bold mt-4"
                  >
                    Initiate New Call
                  </button>
                </div>

                <div className="space-y-4">
                  <h4 className="text-sm font-bold text-slate-950 uppercase tracking-wider">Detailed Transcript Breakdown</h4>
                  {interviewReport.responses.map((res, i) => (
                    <div key={i} className="p-4 border border-slate-200 rounded-2xl bg-white space-y-3 text-sm shadow-sm">
                      <p className="font-bold text-slate-900 leading-snug">Q{i + 1}: {res.question}</p>
                      <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-slate-700 italic text-xs leading-relaxed">
                        Candidate Answer: "{res.student_answer}"
                      </div>
                      <p className="font-bold text-emerald-800 text-xs">Evaluator Score: {res.score} / 100</p>
                      
                      <div className="space-y-1.5 border-t border-slate-50 pt-2">
                        {res.feedback.strengths.map((str, j) => (
                          <p key={j} className="text-xs text-slate-700 flex gap-1.5"><span className="text-emerald-700 font-bold">✓</span> {str}</p>
                        ))}
                        {res.feedback.weaknesses.map((weak, j) => (
                          <p key={j} className="text-xs text-slate-700 flex gap-1.5"><span className="text-rose-600 font-bold">⚠</span> {weak}</p>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </SectionCard>
        </>
      )}

      {/* ================= TAB 5: PROJECT REVIEWER ================= */}
      {activeTab === "reviewer" && (
        <>
          <SectionCard title="AI Project Auditor" subtitle="Submit your application description and code snippets to generate an architectural report card." className="lg:col-span-2">
            <form onSubmit={handleReviewProject} className="space-y-3">
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Project Title</label>
                <input 
                  type="text" 
                  value={projectInput.title}
                  onChange={e => setProjectInput({ ...projectInput, title: e.target.value })}
                  placeholder="e.g. E-Commerce Server Gateway"
                  className="input"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Technologies Used (Comma Separated)</label>
                <input 
                  type="text" 
                  value={projectInput.tech_stack}
                  onChange={e => setProjectInput({ ...projectInput, tech_stack: e.target.value })}
                  placeholder="e.g. React, Flask, Redis, JWT"
                  className="input"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Detailed Description</label>
                <textarea 
                  value={projectInput.description}
                  onChange={e => setProjectInput({ ...projectInput, description: e.target.value })}
                  placeholder="Describe your project's business case, core data architectures, and features..."
                  className="input min-h-24"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Code Snippet (Optional)</label>
                <textarea 
                  value={projectInput.code_snippet}
                  onChange={e => setProjectInput({ ...projectInput, code_snippet: e.target.value })}
                  placeholder="Paste a key routing middleware or function block to check for security vulnerabilities..."
                  className="input min-h-28 font-mono text-xs"
                />
              </div>

              <button 
                type="submit" 
                disabled={isReviewingProject}
                className="btn-primary w-full"
              >
                {isReviewingProject ? "Running analysis scans..." : "Submit Project for Review"}
              </button>
            </form>
          </SectionCard>

          <div className="space-y-6 lg:col-span-1">
            <SectionCard title="Project Audit Scorecard" subtitle="Review reports are compiled based on security checks and design structures.">
              {isReviewingProject ? (
                <div className="py-8 text-center">
                  <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-emerald-700 border-t-transparent"></div>
                  <p className="mt-4 text-sm text-slate-600">Scanning tech configurations...</p>
                </div>
              ) : projectReview ? (
                <div className="space-y-4">
                  <div className="text-center py-4 bg-slate-50 rounded-2xl border border-slate-200">
                    <p className="text-xs text-slate-500 uppercase font-bold tracking-wider">Overall Rating</p>
                    <p className="text-3xl font-black text-slate-950 mt-1">{projectReview.overall_score}%</p>
                    <p className="text-sm font-semibold text-slate-800 mt-1">{projectReview.title}</p>
                  </div>

                  <div className="space-y-2 text-xs">
                    <p className="font-bold text-slate-700 uppercase tracking-wider">Metrics Breakdown</p>
                    
                    <div className="space-y-1">
                      <div className="flex justify-between">
                        <span>Code Quality</span>
                        <span>{projectReview.metrics.code_quality}/100</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-1.5">
                        <div className="bg-emerald-700 h-1.5 rounded-full" style={{ width: `${projectReview.metrics.code_quality}%` }}></div>
                      </div>
                    </div>

                    <div className="space-y-1">
                      <div className="flex justify-between">
                        <span>Architecture Design</span>
                        <span>{projectReview.metrics.architecture}/100</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-1.5">
                        <div className="bg-emerald-700 h-1.5 rounded-full" style={{ width: `${projectReview.metrics.architecture}%` }}></div>
                      </div>
                    </div>

                    <div className="space-y-1">
                      <div className="flex justify-between">
                        <span>Security Audit</span>
                        <span>{projectReview.metrics.security}/100</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-1.5">
                        <div className="bg-emerald-700 h-1.5 rounded-full" style={{ width: `${projectReview.metrics.security}%` }}></div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-slate-600 text-center py-8">Submit a project profile to generate metrics.</p>
              )}
            </SectionCard>
          </div>

          {projectReview && (
            <SectionCard title="Detailed Code Audit & Refactoring Recommendations" subtitle="Actionable items to optimize project design." className="lg:col-span-3">
              <div className="grid gap-6 lg:grid-cols-2">
                <div className="space-y-4">
                  <div>
                    <p className="text-xs font-bold text-emerald-800 uppercase tracking-wider mb-2">Project Strengths</p>
                    <ul className="space-y-1 text-sm text-slate-700">
                      {projectReview.strengths.map((str, idx) => (
                        <li key={idx} className="flex gap-2 items-start bg-emerald-50/50 p-2.5 rounded-xl border border-emerald-100/50">
                          <span className="text-emerald-800 font-bold">✓</span>
                          <span>{str}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <p className="text-xs font-bold text-rose-800 uppercase tracking-wider mb-2">Vulnerabilities / Anti-patterns</p>
                    <ul className="space-y-1 text-sm text-slate-700">
                      {projectReview.weaknesses.map((weak, idx) => (
                        <li key={idx} className="flex gap-2 items-start bg-rose-50/50 p-2.5 rounded-xl border border-rose-100/50">
                          <span className="text-rose-800 font-bold">⚠</span>
                          <span>{weak}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Actionable Suggestions</p>
                    <ul className="space-y-1 text-sm text-slate-700">
                      {projectReview.suggestions.map((sug, idx) => (
                        <li key={idx} className="flex gap-2 items-start bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                          <span className="text-slate-500 font-bold">✦</span>
                          <span>{sug}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {projectReview.code_recommendation?.before && (
                  <div className="space-y-3">
                    <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Refactoring Comparison</p>
                    <div className="space-y-2 font-mono text-xs">
                      <div className="rounded-xl border border-rose-200 bg-rose-50/50 p-3">
                        <p className="text-[10px] text-rose-800 uppercase tracking-widest font-bold mb-1">Vulnerable / Inefficient Code</p>
                        <pre className="overflow-x-auto whitespace-pre-wrap">{projectReview.code_recommendation.before}</pre>
                      </div>

                      <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-3">
                        <p className="text-[10px] text-emerald-800 uppercase tracking-widest font-bold mb-1">AI Optimized Code</p>
                        <pre className="overflow-x-auto whitespace-pre-wrap">{projectReview.code_recommendation.after}</pre>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </SectionCard>
          )}
        </>
      )}

      {/* ================= TAB 6: ATS & PLACEMENT MATCHER ================= */}
      {activeTab === "ats" && (
        <>
          <SectionCard title="ATS Compliance Dashboard" subtitle="Evaluates keyword density and layout structures to predict resume parsing success." className="lg:col-span-2">
            {isLoadingAts ? (
              <div className="py-12 text-center">
                <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-emerald-700 border-t-transparent"></div>
                <p className="mt-4 text-sm text-slate-600">Analyzing keyword compliance structures...</p>
              </div>
            ) : atsData ? (
              <div className="grid gap-6 md:grid-cols-[1fr_2fr] items-start">
                <div className="text-center p-6 bg-slate-50 rounded-3xl border border-slate-200 space-y-2">
                  <p className="text-xs text-slate-500 uppercase font-bold tracking-wider">ATS Score</p>
                  <p className="text-5xl font-black text-slate-950">{atsData.ats_score}%</p>
                  <p className="text-xs text-slate-600 mt-2">Score of 75% or higher is recommended for auto-shortlisting.</p>
                  <div className="w-full bg-slate-200 rounded-full h-2 mt-4">
                    <div 
                      className={`h-2 rounded-full ${atsData.ats_score >= 75 ? "bg-emerald-700" : atsData.ats_score >= 50 ? "bg-amber-600" : "bg-rose-600"}`} 
                      style={{ width: `${atsData.ats_score}%` }}
                    ></div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-2">ATS Audit Report Logs</h3>
                    <ul className="space-y-1 text-sm text-slate-700">
                      {atsData.ats_feedback.map((f, i) => (
                        <li key={i} className="flex gap-2 items-center bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                          {f.includes("+") ? (
                            <span className="text-emerald-700 font-bold">✓</span>
                          ) : (
                            <span className="text-rose-600 font-bold">⚠</span>
                          )}
                          <span>{f}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-2">Critical Optimization Actions</h3>
                    <ul className="space-y-1.5 text-sm text-slate-700">
                      {atsData.ats_suggestions.map((s, i) => (
                        <li key={i} className="flex gap-2 items-start bg-emerald-50/50 p-3 rounded-xl border border-emerald-100/50">
                          <span className="text-emerald-800 font-bold">✦</span>
                          <span>{s}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-600">Update profile details to calculate ATS audit compliance.</p>
            )}
          </SectionCard>

          <SectionCard title="Placement Success Matcher" subtitle="Evaluates match probability and key actions for active companies.">
            {isLoadingAts ? (
              <p className="text-sm text-slate-600">Calculating success metrics...</p>
            ) : atsData && atsData.placement_matrix?.length > 0 ? (
              <div className="space-y-4">
                {atsData.placement_matrix.map(c => (
                  <div key={c.company_name} className="rounded-2xl border border-slate-200 bg-white p-3.5 shadow-sm space-y-2">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-bold text-slate-900">{c.company_name}</h4>
                        <p className="text-xs text-slate-500">Target Role: {c.target_role}</p>
                      </div>
                      
                      <div className="text-right">
                        <span className={`inline-block rounded-full px-2.5 py-1 text-xs font-bold ${
                          c.tier === "High" 
                            ? "bg-emerald-100 text-emerald-800" 
                            : c.tier === "Medium"
                              ? "bg-amber-100 text-amber-800"
                              : "bg-rose-100 text-rose-800"
                        }`}>
                          {c.tier} Match ({c.probability}%)
                        </span>
                      </div>
                    </div>

                    <div className="border-t border-slate-50 pt-2 text-xs">
                      <p className="text-slate-500 font-bold uppercase tracking-wider mb-1">Critical Actions:</p>
                      <ul className="space-y-1 text-slate-700">
                        {c.critical_actions.map((act, i) => (
                          <li key={i} className="flex gap-2 items-center">
                            <span className="text-emerald-700 font-bold">»</span>
                            <span>{act}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-600 text-center py-6">No matching company profiles are active. Add profile skills and try again.</p>
            )}
          </SectionCard>
        </>
      )}

      {/* ================= APPLICATION BOOSTER MODAL ================= */}
      {boosterJob && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
          <div className="relative w-full max-w-3xl rounded-3xl border border-slate-200 bg-white p-6 shadow-2xl overflow-y-auto max-h-[90vh]">
            <button
              onClick={() => {
                setBoosterJob(null);
                setBoosterData(null);
              }}
              className="absolute right-4 top-4 rounded-full border border-slate-200 bg-slate-50 p-2 text-slate-600 hover:bg-slate-100"
            >
              ✕
            </button>
            
            <div className="mb-4">
              <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
                AI Application Booster
              </span>
              <h2 className="mt-2 text-2xl font-bold text-slate-950">
                Tailor for {boosterJob.title || boosterJob.job_title} at {boosterJob.company || boosterJob.company_name}
              </h2>
              <p className="text-sm text-slate-600 font-medium">
                Generate tailored pitches, cover letters, and outreach templates for this opening.
              </p>
            </div>

            {isGeneratingBooster ? (
              <div className="py-8 text-center">
                <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-emerald-700 border-t-transparent"></div>
                <p className="mt-4 text-sm text-slate-600">Analyzing job requirements and formatting templates...</p>
              </div>
            ) : boosterData ? (
              <div className="space-y-4">
                {/* Modal Tab Controls */}
                <div className="flex gap-2 border-b border-slate-100 pb-2">
                  {[
                    { id: "pitch", label: "Elevator Pitch" },
                    { id: "cover", label: "Cover Letter" },
                    { id: "outreach", label: "Cold Outreach Draft" },
                    { id: "adjustments", label: "CV Tweaks" }
                  ].map(tab => (
                    <button
                      key={tab.id}
                      onClick={() => setBoosterModalTab(tab.id)}
                      className={`border-b-2 px-3 py-2 text-xs font-bold transition-all ${
                        boosterModalTab === tab.id
                          ? "border-emerald-700 text-emerald-800"
                          : "border-transparent text-slate-500 hover:text-slate-900"
                      }`}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>

                {/* Modal Tab Contents */}
                {boosterModalTab === "pitch" && (
                  <div className="space-y-3">
                    <p className="text-xs text-slate-500 uppercase tracking-wider font-bold">Elevator Pitch (30-60 Seconds)</p>
                    <div className="rounded-2xl bg-slate-50 p-4 border border-slate-100 text-slate-800 text-sm leading-relaxed whitespace-pre-wrap select-all">
                      {boosterData.elevator_pitch}
                    </div>
                    <button 
                      onClick={() => {
                        navigator.clipboard.writeText(boosterData.elevator_pitch);
                        setActionMsg("Elevator pitch copied to clipboard!");
                      }} 
                      className="btn-secondary w-full"
                    >
                      Copy Pitch
                    </button>
                  </div>
                )}

                {boosterModalTab === "cover" && (
                  <div className="space-y-3">
                    <p className="text-xs text-slate-500 uppercase tracking-wider font-bold">Tailored Cover Letter</p>
                    <div className="rounded-2xl bg-slate-50 p-4 border border-slate-100 text-slate-800 text-sm leading-relaxed whitespace-pre-wrap font-mono max-h-72 overflow-y-auto select-all">
                      {boosterData.cover_letter}
                    </div>
                    <button 
                      onClick={() => {
                        navigator.clipboard.writeText(boosterData.cover_letter);
                        setActionMsg("Cover letter copied to clipboard!");
                      }} 
                      className="btn-secondary w-full"
                    >
                      Copy Cover Letter
                    </button>
                  </div>
                )}

                {boosterModalTab === "outreach" && (
                  <div className="space-y-3">
                    <p className="text-xs text-slate-500 uppercase tracking-wider font-bold">LinkedIn Outreach Message Template</p>
                    <div className="rounded-2xl bg-slate-50 p-4 border border-slate-100 text-slate-800 text-sm leading-relaxed whitespace-pre-wrap select-all">
                      {boosterData.cold_outreach}
                    </div>
                    <button 
                      onClick={() => {
                        navigator.clipboard.writeText(boosterData.cold_outreach);
                        setActionMsg("Outreach message copied to clipboard!");
                      }} 
                      className="btn-secondary w-full"
                    >
                      Copy Outreach Message
                    </button>
                  </div>
                )}

                {boosterModalTab === "adjustments" && (
                  <div className="space-y-3">
                    <p className="text-xs text-slate-500 uppercase tracking-wider font-bold">Resume Customization Tweaks</p>
                    <ul className="space-y-2">
                      {boosterData.cv_adjustments.map((adj, i) => (
                        <li key={i} className="flex gap-2 items-start text-sm text-slate-700 bg-emerald-50/50 p-3 rounded-xl border border-emerald-100/50">
                          <span className="text-emerald-800 font-bold">✓</span>
                          <span>{adj}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-rose-600">Failed to generate booster details.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default StudentDashboard;
