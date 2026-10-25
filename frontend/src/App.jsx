import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowDownRight,
  ArrowLeft,
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronRight,
  CircleHelp,
  Clock3,
  FileText,
  Headphones,
  History,
  LoaderCircle,
  MessageSquareText,
  Mic2,
  Phone,
  PhoneCall,
  Plus,
  Save,
  Sparkles,
  Target,
  UserRound,
  X,
} from "lucide-react";

const API_BASE = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000/api"
).replace(/\/+$/, "");

const FALLBACK_STAGES = [
  {
    id: 1,
    name: "Opening",
    purpose: "Start with clarity and establish who you are speaking with.",
    prompt: "Hi, this is [Your Name] from [Company]. Am I speaking with [Prospect Name]?",
    guidance: "Keep the introduction brief, natural, and professional.",
  },
  {
    id: 2,
    name: "Purpose",
    purpose: "Give the prospect a concise reason for the call.",
    prompt: "I'm calling because we help teams improve [specific business outcome].",
    guidance: "Connect the call to a relevant business outcome. Avoid a long pitch.",
  },
  {
    id: 3,
    name: "Permission",
    purpose: "Respect the prospect's time before continuing.",
    prompt: "Is now a bad time for a quick question?",
    guidance: "Pause and listen. If they are busy, ask about a more suitable time.",
  },
  {
    id: 4,
    name: "Their business",
    purpose: "Learn how their team works today.",
    prompt: "Could you tell me a little about how your team handles this today?",
    guidance: "Use open questions and listen before describing a solution.",
  },
  {
    id: 5,
    name: "Their need",
    purpose: "Understand the problem in the prospect's own words.",
    prompt: "What is the biggest challenge you face with your current process?",
    guidance: "Capture the prospect's exact wording. Separate their words from your interpretation.",
  },
  {
    id: 6,
    name: "Objection",
    purpose: "Understand concerns without becoming defensive.",
    prompt: "I understand. Could you tell me a little more about that concern?",
    guidance: "Acknowledge, clarify, and respond honestly. Never pressure the prospect.",
  },
  {
    id: 7,
    name: "Next step",
    purpose: "Agree on a useful and specific follow-up.",
    prompt: "Would a short follow-up conversation or a relevant resource be useful?",
    guidance: "Record the action and timing that the prospect actually agreed to.",
  },
  {
    id: 8,
    name: "Close",
    purpose: "End professionally and confirm the outcome.",
    prompt: "Thank you for your time. I appreciate the conversation.",
    guidance: "Summarize the agreed next step, if any, and thank the prospect.",
  },
];

const FALLBACK_OUTCOMES = [
  "Interested",
  "Agreed to receive report",
  "Follow-up required",
  "Next step agreed",
  "Not interested",
  "Do not call",
  "Wrong person",
  "Call again",
  "Moved company",
  "No outcome logged",
];

const QUICK_OUTCOMES = [
  { label: "Interested", icon: Sparkles },
  { label: "Follow-up required", icon: Clock3 },
  { label: "Not interested", icon: X },
  { label: "Next step agreed", icon: CheckCircle2 },
];

async function requestApi(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.error || `Request failed (${response.status})`);
  }

  return data;
}

function getInitials(name = "") {
  return name
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("") || "PC";
}

function formatDate(value) {
  if (!value) return "Just now";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Date unavailable";

  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export default function App() {
  const [stages, setStages] = useState(FALLBACK_STAGES);
  const [outcomes, setOutcomes] = useState(FALLBACK_OUTCOMES);
  const [calls, setCalls] = useState([]);
  const [activeCall, setActiveCall] = useState(null);

  const [prospectName, setProspectName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [filter, setFilter] = useState("All calls");

  const [apiState, setApiState] = useState("checking");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const stageNumber = activeCall?.current_stage || 1;
  const currentStage = useMemo(
    () => stages.find((stage) => stage.id === stageNumber) || stages[0],
    [stages, stageNumber]
  );
  const isCallOpen = activeCall?.status === "in_progress";
  const isReadOnly = Boolean(activeCall && !isCallOpen);

  async function refreshCalls() {
    const data = await requestApi("/calls");
    setCalls(data.calls || []);
  }

  useEffect(() => {
    let cancelled = false;

    async function loadData() {
      try {
        const data = await requestApi("/stages");
        if (!cancelled && data.stages?.length) setStages(data.stages);
      } catch {
        // Keep the built-in stage guide available if the server is offline.
      }

      try {
        const data = await requestApi("/outcomes");
        if (!cancelled && data.outcomes?.length) setOutcomes(data.outcomes);
      } catch {
        // Use the built-in outcome options until the API is available.
      }

      try {
        const data = await requestApi("/calls");
        if (!cancelled) {
          setCalls(data.calls || []);
          setApiState("connected");
          setError("");
        }
      } catch {
        if (!cancelled) {
          setApiState("offline");
          setError("Could not reach the backend. Start Flask to save and load calls.");
        }
      }
    }

    loadData();
    return () => {
      cancelled = true;
    };
  }, []);

  async function startCall(event) {
    event.preventDefault();
    setError("");
    setNotice("");
    setLoading(true);

    try {
      const data = await requestApi("/calls", {
        method: "POST",
        body: JSON.stringify({
          prospect_name: prospectName.trim() || "Unknown",
          company_name: companyName.trim(),
        }),
      });

      setActiveCall(data.call);
      setProspectName("");
      setCompanyName("");
      setNotice("New call started. You're ready to go.");
      setApiState("connected");
      await refreshCalls();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function updateCall(patch, successMessage = "Changes saved.") {
    if (!activeCall?.id || !isCallOpen) return false;

    setError("");
    setNotice("");
    setSaving(true);

    try {
      const data = await requestApi(`/calls/${activeCall.id}`, {
        method: "PATCH",
        body: JSON.stringify(patch),
      });

      setActiveCall(data.call);
      await refreshCalls();
      setNotice(successMessage);
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    } finally {
      setSaving(false);
    }
  }

  async function changeStage(nextStage) {
    if (!isCallOpen || nextStage < 1 || nextStage > stages.length) return;
    if (nextStage === stageNumber) return;
    await updateCall({ current_stage: nextStage }, `Stage ${nextStage} selected.`);
  }

  async function saveNotes() {
    if (!activeCall) return;
    await updateCall({
      prospect_words: activeCall.prospect_words || "",
      notes: activeCall.notes || "",
      next_step: activeCall.next_step || "",
      outcome: activeCall.outcome || "No outcome logged",
    });
  }

  async function endCall() {
    if (!isCallOpen) return;

    const confirmed = window.confirm(
      "End this call and save the current stage, notes, and outcome?"
    );
    if (!confirmed) return;

    setError("");
    setNotice("");
    setSaving(true);

    try {
      const data = await requestApi(`/calls/${activeCall.id}/end`, {
        method: "POST",
        body: JSON.stringify({
          prospect_words: activeCall.prospect_words || "",
          notes: activeCall.notes || "",
          next_step: activeCall.next_step || "",
          outcome: activeCall.outcome || "No outcome logged",
        }),
      });

      setActiveCall(data.call);
      await refreshCalls();
      setNotice("Call ended and saved to history.");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function openCall(call) {
    setError("");
    setNotice("");

    try {
      const data = await requestApi(`/calls/${call.id}`);
      setActiveCall(data.call);
    } catch (err) {
      setError(err.message);
    }
  }

  function updateDraft(field, value) {
    setActiveCall((previous) => ({
      ...previous,
      [field]: value,
    }));
  }

  function startAnotherCall() {
    setActiveCall(null);
    setError("");
    setNotice("");
  }

  const visibleCalls = calls.filter((call) => {
    if (filter === "In progress") return call.status === "in_progress";
    if (filter === "Completed") return call.status !== "in_progress";
    return true;
  });

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#top" aria-label="Callflow home">
          <span className="brand-mark"><PhoneCall size={21} strokeWidth={2.5} /></span>
          <span className="brand-copy">
            <strong>callflow<span>.</span></strong>
            <small>CONVERSATION DESK</small>
          </span>
        </a>

        <div className="workspace-label">WORKSPACE</div>
        <button
          className={`side-link ${!activeCall ? "side-link-active" : ""}`}
          onClick={startAnotherCall}
        >
          <Headphones size={18} />
          <span>Live call guide</span>
          <span className="side-link-dot" />
        </button>

        <div className="workspace-label history-label">
          YOUR ACTIVITY <span>{calls.length.toString().padStart(2, "0")}</span>
        </div>
        <button
          className="side-link"
          onClick={() => document.getElementById("call-history")?.scrollIntoView({ behavior: "smooth" })}
        >
          <History size={18} />
          <span>Call history</span>
        </button>

        <div className="sidebar-spacer" />

        <div className="sidebar-tip">
          <div className="tip-icon"><Sparkles size={17} /></div>
          <strong>Listen first.</strong>
          <p>The best calls feel like a conversation, not a script.</p>
        </div>

        <div className="sidebar-user">
          <div className="avatar avatar-user">Y</div>
          <div className="user-copy">
            <strong>Your workspace</strong>
            <small>Sales companion</small>
          </div>
          <CircleHelp size={17} className="muted-icon" />
        </div>
      </aside>

      <main className="main-area" id="top">
        <header className="topbar">
          <div className="breadcrumb">
            <span>Workspace</span><ChevronRight size={14} /><strong>Call companion</strong>
          </div>
          <div className="topbar-right">
            <span className={`connection-pill ${apiState === "connected" ? "connection-live" : ""}`}>
              <span className="connection-dot" />
              {apiState === "connected" ? "Backend connected" : apiState === "checking" ? "Connecting…" : "Backend offline"}
            </span>
            <div className="top-avatar">C</div>
          </div>
        </header>

        <div className="page-content">
          <section className="page-heading">
            <div>
              <div className="eyebrow"><span className="eyebrow-line" /> CONVERSATION DESK</div>
              <h1>Make every call <em>count.</em></h1>
              <p className="page-subtitle">
                A little structure. A lot more listening. Your guide to better conversations.
              </p>
            </div>
            <div className="heading-mark"><Activity size={24} /><span>CALL<br />WITH INTENT</span></div>
          </section>

          {(error || notice) && (
            <div className={`feedback-banner ${error ? "feedback-error" : "feedback-success"}`} role="status">
              {error ? <CircleHelp size={17} /> : <CheckCircle2 size={17} />}
              <span>{error || notice}</span>
              <button onClick={() => { setError(""); setNotice(""); }} aria-label="Dismiss message">
                <X size={16} />
              </button>
            </div>
          )}

          <section className="workspace-grid">
            <div className="primary-column">
              {!activeCall ? (
                <section className="panel start-panel">
                  <div className="panel-overline"><span className="live-indicator" /> READY WHEN YOU ARE</div>
                  <div className="start-icon"><PhoneCall size={26} /></div>
                  <h2>Start a new conversation</h2>
                  <p className="panel-description">
                    Add the prospect details to begin. You can end the call at any stage and keep the notes.
                  </p>
                  <form className="start-form" onSubmit={startCall}>
                    <label>
                      Prospect name <span className="label-optional">OPTIONAL</span>
                      <div className="input-wrap">
                        <UserRound size={17} />
                        <input
                          value={prospectName}
                          onChange={(event) => setProspectName(event.target.value)}
                          placeholder="e.g. Alex Morgan"
                          maxLength={120}
                        />
                      </div>
                    </label>
                    <label>
                      Company <span className="label-optional">OPTIONAL</span>
                      <div className="input-wrap">
                        <Target size={17} />
                        <input
                          value={companyName}
                          onChange={(event) => setCompanyName(event.target.value)}
                          placeholder="e.g. Northstar Labs"
                          maxLength={160}
                        />
                      </div>
                    </label>
                    <button className="button button-primary button-full" type="submit" disabled={loading}>
                      {loading ? <LoaderCircle size={18} className="spin" /> : <PhoneCall size={18} />}
                      Start call
                      {!loading && <ArrowRight size={17} className="button-arrow" />}
                    </button>
                  </form>
                  <div className="start-footnote"><Check size={14} /> Your notes are saved to your call history.</div>
                </section>
              ) : (
                <section className="panel live-panel">
                  <div className="live-panel-top">
                    <div className="contact-ident">
                      <div className="avatar avatar-contact">{getInitials(activeCall.prospect_name)}</div>
                      <div>
                        <div className="panel-overline">{isCallOpen ? "CALL IN PROGRESS" : "CALL SUMMARY"}</div>
                        <h2>{activeCall.prospect_name || "Unknown prospect"}</h2>
                        <p>{activeCall.company_name || "Company not specified"}</p>
                      </div>
                    </div>
                    <span className={`status-tag ${isCallOpen ? "status-progress" : "status-complete"}`}>
                      <span />{isCallOpen ? "In progress" : "Completed"}
                    </span>
                  </div>

                  <div className="stage-progress-head">
                    <span>CALL PROGRESS</span>
                    <strong>{stageNumber}<small> / {stages.length}</small></strong>
                  </div>
                  <div className="progress-track">
                    <div className="progress-fill" style={{ width: `${(stageNumber / stages.length) * 100}%` }} />
                  </div>

                  <div className="stage-stepper" aria-label="Call stages">
                    {stages.map((stage) => {
                      const isCurrent = stage.id === stageNumber;
                      const isDone = stage.id < stageNumber;
                      return (
                        <button
                          key={stage.id}
                          className={`stage-step ${isCurrent ? "stage-current" : ""} ${isDone ? "stage-done" : ""}`}
                          onClick={() => changeStage(stage.id)}
                          disabled={!isCallOpen || saving}
                          title={stage.name}
                          aria-label={`Go to stage ${stage.id}: ${stage.name}`}
                        >
                          <span className="step-number">{isDone ? <Check size={14} /> : stage.id}</span>
                          <span className="step-label">{stage.name}</span>
                        </button>
                      );
                    })}
                  </div>

                  <div className="stage-card">
                    <div className="stage-card-top">
                      <span className="stage-chip">STAGE {String(stageNumber).padStart(2, "0")}</span>
                      <span className="stage-small-note"><Mic2 size={14} /> Stay present</span>
                    </div>
                    <h2>{currentStage?.name}</h2>
                    <p className="stage-purpose">{currentStage?.purpose}</p>

                    <div className="prompt-box">
                      <div className="prompt-label"><MessageSquareText size={15} /> SUGGESTED TALK TRACK</div>
                      <p>“{currentStage?.prompt}”</p>
                      <span className="prompt-hint">Use your own words. This is a guide, not a script.</span>
                    </div>

                    <div className="guidance-row">
                      <div className="guidance-icon"><Sparkles size={17} /></div>
                      <div><strong>Keep in mind</strong><p>{currentStage?.guidance}</p></div>
                    </div>

                    <div className="stage-actions">
                      <button
                        className="button button-secondary"
                        onClick={() => changeStage(stageNumber - 1)}
                        disabled={!isCallOpen || stageNumber <= 1 || saving}
                      >
                        <ArrowLeft size={16} /> Previous
                      </button>
                      <button
                        className="button button-primary"
                        onClick={() => changeStage(stageNumber + 1)}
                        disabled={!isCallOpen || stageNumber >= stages.length || saving}
                      >
                        {saving ? <LoaderCircle size={17} className="spin" /> : null}
                        {stageNumber >= stages.length ? "Last stage" : "Next stage"}
                        {stageNumber < stages.length && <ArrowRight size={17} />}
                      </button>
                    </div>
                  </div>
                </section>
              )}

              <section className="panel notes-panel">
                <div className="section-heading">
                  <div className="section-heading-icon"><FileText size={18} /></div>
                  <div><h3>Conversation notes</h3><p>Capture what matters while it's fresh.</p></div>
                  {activeCall && <span className="section-side-label">CALL NOTES</span>}
                </div>

                <label className="field-label" htmlFor="prospect-words">
                  <span>Their need, in their words</span>
                  <span className="field-emphasis">CAPTURE VERBATIM</span>
                </label>
                <textarea
                  id="prospect-words"
                  value={activeCall?.prospect_words || ""}
                  onChange={(event) => updateDraft("prospect_words", event.target.value)}
                  placeholder={'“We spend too much time manually preparing weekly reports…”'}
                  rows={3}
                  disabled={!isCallOpen}
                />
                <p className="field-helper">Keep the prospect's original phrasing. Avoid rewriting it as a sales summary.</p>

                <label className="field-label" htmlFor="call-notes">Additional notes</label>
                <textarea
                  id="call-notes"
                  value={activeCall?.notes || ""}
                  onChange={(event) => updateDraft("notes", event.target.value)}
                  placeholder="Business context, concerns, current process, or details to remember…"
                  rows={3}
                  disabled={!isCallOpen}
                />

                <div className="notes-bottom">
                  <span><LockIcon /> {isReadOnly ? "Saved call · read only" : "Notes stay attached to this call"}</span>
                  <button
                    className="button button-secondary button-save"
                    onClick={saveNotes}
                    disabled={!isCallOpen || saving}
                  >
                    {saving ? <LoaderCircle size={16} className="spin" /> : <Save size={16} />}
                    Save notes
                  </button>
                </div>
              </section>

              {activeCall && (
                <section className="panel outcome-panel">
                  <div className="section-heading">
                    <div className="section-heading-icon outcome-heading-icon"><Target size={18} /></div>
                    <div><h3>Outcome & next step</h3><p>Record what was actually agreed.</p></div>
                  </div>
                  <div className="outcome-options">
                    {QUICK_OUTCOMES.map(({ label, icon: Icon }) => (
                      <button
                        key={label}
                        className={`outcome-option ${activeCall.outcome === label ? "outcome-selected" : ""}`}
                        onClick={() => updateDraft("outcome", label)}
                        disabled={!isCallOpen}
                      >
                        <Icon size={16} /><span>{label}</span>
                        {activeCall.outcome === label && <Check size={14} className="outcome-check" />}
                      </button>
                    ))}
                  </div>
                  <label className="field-label" htmlFor="other-outcome">Other outcome</label>
                  <select
                    id="other-outcome"
                    value={activeCall.outcome || "No outcome logged"}
                    onChange={(event) => updateDraft("outcome", event.target.value)}
                    disabled={!isCallOpen}
                  >
                    {outcomes.map((outcome) => <option key={outcome} value={outcome}>{outcome}</option>)}
                  </select>

                  <label className="field-label" htmlFor="next-step">Agreed next step</label>
                  <textarea
                    id="next-step"
                    value={activeCall.next_step || ""}
                    onChange={(event) => updateDraft("next_step", event.target.value)}
                    placeholder="e.g. Send the overview by Tuesday; follow up on Friday."
                    rows={2}
                    disabled={!isCallOpen}
                  />

                  {isCallOpen ? (
                    <button className="button button-danger button-full end-call-button" onClick={endCall} disabled={saving}>
                      {saving ? <LoaderCircle size={17} className="spin" /> : <Phone size={17} />}
                      End call & save summary
                    </button>
                  ) : (
                    <button className="button button-primary button-full" onClick={startAnotherCall}>
                      <Plus size={17} /> Start another call
                    </button>
                  )}
                  {isCallOpen && <p className="end-call-note"><ArrowDownRight size={14} /> Calls can end at any stage. Your current stage will be recorded.</p>}
                </section>
              )}
            </div>

            <aside className="right-column">
              <section className="panel focus-panel">
                <div className="focus-top">
                  <div className="focus-icon"><Target size={19} /></div>
                  <span className="focus-tag">TODAY'S FOCUS</span>
                </div>
                <h3>Curiosity over pitching.</h3>
                <p>Your goal isn't to say everything. It's to learn enough to make the next step useful.</p>
                <div className="focus-rule" />
                <div className="focus-detail"><CheckCircle2 size={16} /><span>Ask, then listen</span></div>
                <div className="focus-detail"><CheckCircle2 size={16} /><span>Use their own words</span></div>
                <div className="focus-detail"><CheckCircle2 size={16} /><span>Agree on one clear next step</span></div>
              </section>

              <section className="panel history-panel" id="call-history">
                <div className="history-heading">
                  <div>
                    <div className="section-heading-icon history-heading-icon"><History size={17} /></div>
                    <h3>Recent calls</h3>
                    <p>Your conversations, all in one place.</p>
                  </div>
                  <span className="history-count">{calls.length}</span>
                </div>
                <div className="history-filter" role="group" aria-label="Filter calls">
                  {["All calls", "In progress", "Completed"].map((option) => (
                    <button
                      key={option}
                      className={filter === option ? "filter-active" : ""}
                      onClick={() => setFilter(option)}
                    >
                      {option}
                    </button>
                  ))}
                </div>

                <div className="call-list">
                  {visibleCalls.length === 0 ? (
                    <div className="history-empty">
                      <div className="empty-icon"><History size={21} /></div>
                      <strong>No calls yet</strong>
                      <p>Start a conversation and it'll appear here.</p>
                    </div>
                  ) : (
                    visibleCalls.map((call) => (
                      <button
                        key={call.id}
                        className={`call-history-item ${activeCall?.id === call.id ? "call-history-active" : ""}`}
                        onClick={() => openCall(call)}
                      >
                        <div className="avatar history-avatar">{getInitials(call.prospect_name)}</div>
                        <div className="history-item-content">
                          <strong>{call.prospect_name || "Unknown prospect"}</strong>
                          <span>{call.company_name || "No company"} · Stage {call.current_stage}</span>
                          <small>{formatDate(call.ended_at || call.started_at)}</small>
                        </div>
                        <ChevronRight size={16} className="history-chevron" />
                      </button>
                    ))
                  )}
                </div>
                <div className="history-foot"><span className="history-foot-dot" /> History is stored by your backend</div>
              </section>

              <div className="privacy-note">
                <div><CheckCircle2 size={16} /></div>
                <p><strong>Be thoughtful with data.</strong> Record only relevant business notes and respect a prospect's request not to be contacted.</p>
              </div>
            </aside>
          </section>

          <footer className="page-footer">
            <span>CALLFLOW <i>·</i> BUILT FOR BETTER CONVERSATIONS</span>
            <span>Eight stages. One human conversation.</span>
          </footer>
        </div>
      </main>
    </div>
  );
}

function LockIcon() {
  return <CheckCircle2 size={14} />;
}
