import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import Records from "./pages/Records";
import NewRecord from "./pages/NewRecord";
import "./index.css";

export default function App() {
  const [page, setPage] = useState("dashboard");

  return (
    <div className="app">
      <nav className="navbar">
        <div className="navbar-brand">
          <img src="/logo.png" alt="Silge logo" style={{width:"36px", height:"36px", objectFit:"contain", flexShrink:0}}/>
          <span className="brand-name">Silge</span>
          <span className="brand-sub">Veri İmha Sistemi</span>
        </div>
        <div className="navbar-links">
          <button
            className={page === "dashboard" ? "nav-btn active" : "nav-btn"}
            onClick={() => setPage("dashboard")}
          >
            Dashboard
          </button>
          <button
            className={page === "records" ? "nav-btn active" : "nav-btn"}
            onClick={() => setPage("records")}
          >
            Kayıtlar
          </button>
          <button
            className={page === "new" ? "nav-btn active" : "nav-btn"}
            onClick={() => setPage("new")}
          >
            + Yeni Kayıt
          </button>
        </div>
      </nav>

      <main className="main-content">
        {page === "dashboard" && <Dashboard onNavigate={setPage} />}
        {page === "records" && <Records />}
        {page === "new" && <NewRecord onSuccess={() => setPage("records")} />}
      </main>
    </div>
  );
}
