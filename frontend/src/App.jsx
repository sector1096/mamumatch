import { Link, Route, Routes } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import MatchDetailPage from "./pages/MatchDetailPage";
import JobsPage from "./pages/JobsPage";

export default function App() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <h1>MamuMatch</h1>
        <nav>
          <Link to="/">Dashboard</Link>
          <Link to="/jobs">Jobs</Link>
        </nav>
      </header>
      <main className="content">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/partidas/:id" element={<MatchDetailPage />} />
          <Route path="/jobs" element={<JobsPage />} />
        </Routes>
      </main>
    </div>
  );
}