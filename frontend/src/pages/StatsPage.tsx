import { useCallback, useEffect, useState } from "react";

import { api } from "../api/client";
import type { Stats } from "../api/types";

export function StatsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [cache, setCache] = useState("...");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const { data, cache: state } = await api.stats();
      setStats(data);
      setCache(state);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load statistics");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  if (error && !stats) return <div><p role="alert" className="alert">{error}</p><button onClick={() => void load()}>Retry statistics</button></div>;
  if (!stats) return <p role="status">Loading live statistics...</p>;
  return (
    <section>
      <div className="section-heading"><div><p className="eyebrow">Live overview</p><h1>City pulse</h1></div><span className={`cache cache-${cache.toLowerCase()}`}>Cache {cache}</span></div>
      {error && <p role="alert" className="alert">{error}</p>}
      <button className="secondary" disabled={loading} onClick={() => void load()}>{loading ? "Refreshing..." : "Refresh statistics"}</button>
      <div className="stats-hero"><strong>{stats.total}</strong><span>Total complaints</span></div>
      <div className="stats-grid">
        <div className="panel"><h2>By category</h2>{Object.entries(stats.by_category).map(([label, value]) => <div className="stat-row" key={label}><span>{label}</span><strong>{value}</strong></div>)}</div>
        <div className="panel"><h2>By priority</h2>{Object.entries(stats.by_priority).map(([label, value]) => <div className="stat-row" key={label}><span>{label}</span><strong>{value}</strong></div>)}</div>
      </div>
    </section>
  );
}
