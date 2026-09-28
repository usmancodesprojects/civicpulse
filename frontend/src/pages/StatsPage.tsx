import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { Stats } from "../api/types";

export function StatsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [cache, setCache] = useState("...");
  const [error, setError] = useState("");

  useEffect(() => {
    api.stats().then(({ data, cache: state }) => { setStats(data); setCache(state); }).catch((caught: unknown) => setError(caught instanceof Error ? caught.message : "Could not load statistics"));
  }, []);

  if (error) return <p role="alert" className="alert">{error}</p>;
  if (!stats) return <p>Loading live statistics...</p>;
  return (
    <section>
      <div className="section-heading"><div><p className="eyebrow">Live overview</p><h1>City pulse</h1></div><span className={`cache cache-${cache.toLowerCase()}`}>Cache {cache}</span></div>
      <div className="stats-hero"><strong>{stats.total}</strong><span>Total complaints</span></div>
      <div className="stats-grid">
        <div className="panel"><h2>By category</h2>{Object.entries(stats.by_category).map(([label, value]) => <div className="stat-row" key={label}><span>{label}</span><strong>{value}</strong></div>)}</div>
        <div className="panel"><h2>By priority</h2>{Object.entries(stats.by_priority).map(([label, value]) => <div className="stat-row" key={label}><span>{label}</span><strong>{value}</strong></div>)}</div>
      </div>
    </section>
  );
}
