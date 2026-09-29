import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "../api/client";
import type { Category, Complaint, Priority, Status } from "../api/types";
import { Badge } from "../components/Badge";

type Filters = { category: Category | ""; priority: Priority | ""; status: Status | "" };

export function DashboardPage() {
  const [items, setItems] = useState<Complaint[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<Filters>({ category: "", priority: "", status: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [pendingId, setPendingId] = useState<string | null>(null);
  const requestNumber = useRef(0);
  const pendingIdRef = useRef<string | null>(null);

  const load = useCallback(async () => {
    const currentRequest = ++requestNumber.current;
    const query = new URLSearchParams({ page: String(page), page_size: "10" });
    Object.entries(filters).forEach(([key, value]) => value && query.set(key, value));
    setError("");
    setLoading(true);
    setItems([]);
    setTotal(0);
    try {
      const result = await api.listComplaints(query);
      if (currentRequest !== requestNumber.current) return;
      setItems(result.items);
      setTotal(result.total);
    } catch (caught) {
      if (currentRequest !== requestNumber.current) return;
      setError(caught instanceof Error ? caught.message : "Could not load complaints");
    } finally {
      if (currentRequest === requestNumber.current) setLoading(false);
    }
  }, [filters, page]);

  useEffect(() => { void load(); }, [load]);

  const transition = async (id: string, status: Status) => {
    if (pendingIdRef.current) return;
    pendingIdRef.current = id;
    setPendingId(id);
    setError("");
    try {
      await api.updateStatus(id, status);
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Status update failed");
    } finally {
      pendingIdRef.current = null;
      setPendingId(null);
    }
  };

  const updateFilter = (name: keyof Filters, value: string) => {
    setFilters((current) => ({ ...current, [name]: value }));
    setPage(1);
  };

  return (
    <section>
      <div className="section-heading"><div><p className="eyebrow">Operations</p><h1>Complaint queue</h1></div><strong>{total} reports</strong></div>
      <div className="filters panel">
        <select aria-label="Filter by category" value={filters.category} onChange={(e) => updateFilter("category", e.target.value)}>
          <option value="">All categories</option><option value="water">Water</option><option value="electricity">Electricity</option><option value="sanitation">Sanitation</option><option value="roads">Roads</option><option value="streetlights">Streetlights</option><option value="other">Other</option>
        </select>
        <select aria-label="Filter by priority" value={filters.priority} onChange={(e) => updateFilter("priority", e.target.value)}>
          <option value="">All priorities</option><option value="high">High</option><option value="normal">Normal</option><option value="low">Low</option>
        </select>
        <select aria-label="Filter by status" value={filters.status} onChange={(e) => updateFilter("status", e.target.value)}>
          <option value="">All statuses</option><option value="open">Open</option><option value="in_progress">In progress</option><option value="resolved">Resolved</option><option value="rejected">Rejected</option>
        </select>
      </div>
      {error && <p role="alert" className="alert">{error}</p>}
      {loading && <p role="status">Loading complaints...</p>}
      {!loading && !error && items.length === 0 && <p role="status">No complaints match these filters.</p>}
      <div className="complaint-list">
        {items.map((item) => (
          <article className="complaint-card" key={item.id}>
            <div className="complaint-main">
              <div className="badges"><Badge value={item.priority} /><Badge value={item.category} /><Badge value={item.status} /></div>
              <h2>{item.ai_summary}</h2>
              <p>{item.text}</p><small>{item.location} - {new Date(item.created_at).toLocaleString()}</small>
            </div>
            <div className="actions">
              {item.allowed_transitions.map((target) => <button className="secondary" key={target} disabled={pendingId !== null} onClick={() => void transition(item.id, target)}>{pendingId === item.id ? "Updating..." : `Mark ${target.replace("_", " ")}`}</button>)}
              {!item.allowed_transitions.length && <span>Terminal</span>}
            </div>
          </article>
        ))}
      </div>
      <div className="pagination"><button className="secondary" disabled={loading || page === 1} onClick={() => setPage((value) => value - 1)}>Previous</button><span>Page {page}</span><button className="secondary" disabled={loading || page * 10 >= total} onClick={() => setPage((value) => value + 1)}>Next</button></div>
    </section>
  );
}
