import { type FormEvent, useState } from "react";

import { api } from "../api/client";
import type { Complaint } from "../api/types";
import { Badge } from "../components/Badge";

export function SubmitPage() {
  const [text, setText] = useState("");
  const [location, setLocation] = useState("");
  const [contact, setContact] = useState("");
  const [result, setResult] = useState<Complaint | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setResult(null);
    const complaintText = text.trim();
    const complaintLocation = location.trim();
    if (complaintText.length < 10 || complaintText.length > 2000) {
      setError("Complaint must be between 10 and 2000 characters.");
      return;
    }
    if (complaintLocation.length < 3 || complaintLocation.length > 200) {
      setError("Location must be between 3 and 200 characters.");
      return;
    }
    if (contact.trim().length > 200) {
      setError("Contact must be 200 characters or fewer.");
      return;
    }
    setLoading(true);
    try {
      setResult(await api.createComplaint({
        text: complaintText,
        location: complaintLocation,
        reporter_contact: contact.trim() || null,
      }));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Submission failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="two-column">
      <div className="panel form-panel">
        <p className="eyebrow">Report an issue</p>
        <h1>Make your street heard.</h1>
        <p className="lede">Describe what you can see. CivicPulse will classify and prioritize it.</p>
        <form onSubmit={submit} noValidate>
          <label htmlFor="complaint-text">
            What happened?
            <textarea
              id="complaint-text"
              aria-label="What happened?"
              value={text}
              onChange={(event) => setText(event.target.value)}
              minLength={10}
              maxLength={2000}
              placeholder="A water main is flooding Street 12..."
              required
            />
            <small>{text.length}/2000</small>
          </label>
          <label htmlFor="complaint-location">
            Location
            <input id="complaint-location" aria-label="Location" value={location} onChange={(event) => setLocation(event.target.value)} required />
          </label>
          <label htmlFor="reporter-contact">
            Contact (optional)
            <input id="reporter-contact" aria-label="Contact (optional)" value={contact} onChange={(event) => setContact(event.target.value)} maxLength={200} />
          </label>
          {error && <p role="alert" className="alert">{error}</p>}
          <button type="submit" disabled={loading}>
            {loading ? "Analyzing complaint - this may take a few seconds..." : "Submit complaint"}
          </button>
        </form>
      </div>
      <aside className="panel result-panel" aria-live="polite">
        {result ? (
          <>
            <p className="eyebrow">Triage complete</p>
            <h2>{result.ai_summary}</h2>
            <div className="badges"><Badge value={result.category} /><Badge value={result.priority} /></div>
            <dl>
              <div><dt>Provider</dt><dd>{result.triaged_by}</dd></div>
              <div><dt>Latency</dt><dd>{result.triage_latency_ms} ms</dd></div>
              <div><dt>Reference</dt><dd>{result.id.slice(0, 8)}</dd></div>
            </dl>
          </>
        ) : (
          <div className="empty-state"><span>01</span><p>Your triage result will appear here.</p></div>
        )}
      </aside>
    </section>
  );
}
