import React, { useEffect, useState } from "react";
import { api } from "../api/client";

export default function JobsPage() {
  const [filters, setFilters] = useState({ status: "", tipo: "", id_partida: "", page: "1", size: "30" });
  const [data, setData] = useState({ items: [], total: 0 });
  const [log, setLog] = useState("");

  const load = async () => {
    const params = {};
    Object.entries(filters).forEach(([k, v]) => {
      if (v !== "") params[k] = v;
    });
    const res = await api.getJobs(params);
    setData(res);
  };

  useEffect(() => { load(); }, []);

  const retry = async (id) => {
    await api.retryJob(id);
    await load();
  };

  const viewLog = async (id) => {
    const res = await api.getJobLog(id);
    setLog(res.log || "");
  };

  return (
    <section>
      <h2>Jobs / Cola</h2>
      <div className="panel filters-grid">
        {Object.keys(filters).filter((x) => x !== "page" && x !== "size").map((k) => (
          <label key={k}><span>{k}</span><input value={filters[k]} onChange={(e) => setFilters((p) => ({ ...p, [k]: e.target.value }))} /></label>
        ))}
        <div className="actions-row">
          <button onClick={load}>Aplicar filtros</button>
        </div>
      </div>

      <div className="panel">
        <p>Total: {data.total}</p>
        <table>
          <thead><tr><th>id_job</th><th>id_partida</th><th>tipo</th><th>status</th><th>attempts</th><th>updated_at</th><th>acciones</th></tr></thead>
          <tbody>
            {data.items.map((j) => (
              <tr key={j.id_job}>
                <td>{j.id_job}</td>
                <td>{j.id_partida}</td>
                <td>{j.tipo}</td>
                <td>{j.status}</td>
                <td>{j.attempts}/{j.max_attempts}</td>
                <td>{j.updated_at}</td>
                <td className="actions-row">
                  <button onClick={() => viewLog(j.id_job)}>Ver log</button>
                  {j.status === "ERROR" ? <button onClick={() => retry(j.id_job)}>Retry</button> : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {log ? <pre className="log-box">{log}</pre> : null}
      </div>
    </section>
  );
}
