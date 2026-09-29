import { useState } from "react";

import { DashboardPage } from "./pages/DashboardPage";
import { StatsPage } from "./pages/StatsPage";
import { SubmitPage } from "./pages/SubmitPage";

type View = "submit" | "dashboard" | "stats";

export function App() {
  const [view, setView] = useState<View>("submit");
  return (
    <div className="app-shell">
      <header><button className="brand" onClick={() => setView("submit")}><span>C</span>CivicPulse</button><nav aria-label="Main navigation"><button className={view === "submit" ? "active" : ""} onClick={() => setView("submit")}>Submit</button><button className={view === "dashboard" ? "active" : ""} onClick={() => setView("dashboard")}>Dashboard</button><button className={view === "stats" ? "active" : ""} onClick={() => setView("stats")}>Stats</button></nav></header>
      <main>{view === "submit" && <SubmitPage />}{view === "dashboard" && <DashboardPage />}{view === "stats" && <StatsPage />}</main>
      <footer><span>CivicPulse municipal operations</span><span>Built for accountable response</span></footer>
    </div>
  );
}
