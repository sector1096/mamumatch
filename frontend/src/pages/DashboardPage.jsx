import React, { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { Badge } from "../components/Badge";

const initialFilters = {
  q: "",
  anio: "",
  evento: "",
  equipo: "",
  idioma: "",
  validado: "",
  video_descargado: "",
  has_transcription: "",
  incompletas: "",
  page: "1",
  size: "25",
};

export default function DashboardPage() {
  const [filters, setFilters] = useState(initialFilters);
  const [data, setData] = useState({ items: [], total: 0, page: 1, size: 25 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const buildParams = (source) => {
    const params = {};
    Object.entries(source).forEach(([k, v]) => {
      if (v !== "") params[k] = v;
    });
    return params;
  };

  const load = async (sourceFilters = filters) => {
    try {
      setLoading(true);
      setError("");
      const res = await api.getPartidas(buildParams(sourceFilters));
      setData(res);
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    load(initialFilters);
  }, []);

  const page = Number(data.page || filters.page || 1);
  const size = Number(data.size || filters.size || 25);
  const totalPages = Math.max(1, Math.ceil((data.total || 0) / Math.max(size, 1)));

  const goToPage = (targetPage) => {
    const nextPage = Math.max(1, Math.min(totalPages, targetPage));
    const next = { ...filters, page: String(nextPage) };
    setFilters(next);
    load(next);
  };

  const applySearch = () => {
    const next = { ...filters, page: "1" };
    setFilters(next);
    load(next);
  };

  const clearSearch = () => {
    setFilters(initialFilters);
    load(initialFilters);
  };

  const changeSize = (newSize) => {
    const next = { ...filters, size: String(newSize), page: "1" };
    setFilters(next);
    load(next);
  };

  const enqueue = async (id, tipo) => {
    await api.createJob(id, { tipo, payload: {} });
    alert(`Job ${tipo} encolado para partida ${id}`);
  };

  return (
    <section>
      <h2>Busqueda rapida</h2>
      <div className="panel filters-grid">
        {Object.keys(initialFilters)
          .filter((k) => k !== "page" && k !== "size")
          .map((key) => (
            <label key={key}>
              <span>{key}</span>
              <input
                value={filters[key]}
                onChange={(e) => setFilters((p) => ({ ...p, [key]: e.target.value }))}
                placeholder={key}
              />
            </label>
          ))}
        <div className="actions-row">
          <button onClick={applySearch} disabled={loading}>
            Buscar
          </button>
          <button onClick={clearSearch} disabled={loading}>
            Limpiar
          </button>
        </div>
      </div>

      {error ? <p className="error">{error}</p> : null}
      {loading ? <p>Cargando...</p> : null}

      <div className="panel">
        <p>Total: {data.total}</p>
        <div className="actions-row pager-row">
          <button onClick={() => goToPage(page - 1)} disabled={loading || page <= 1}>Anterior</button>
          <span>Pagina {page} de {totalPages}</span>
          <button onClick={() => goToPage(page + 1)} disabled={loading || page >= totalPages}>Siguiente</button>
          <label className="inline-label">
            <span>Por pagina</span>
            <select value={String(size)} onChange={(e) => changeSize(Number(e.target.value))} disabled={loading}>
              <option value="25">25</option>
              <option value="50">50</option>
              <option value="100">100</option>
            </select>
          </label>
        </div>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Match ID</th>
              <th>Evento / Anio</th>
              <th>Equipos</th>
              <th>Idioma</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((item) => (
              <tr key={item.id_partida}>
                <td>{item.id_partida}</td>
                <td>{item.match_id_dota || "-"}</td>
                <td>{item.evento || "-"} / {item.anio || "-"}</td>
                <td>{item.equipos || "-"}</td>
                <td>{item.idioma || "-"}</td>
                <td>
                  <div className="badges-cell">
                    <Badge ok={item.video_descargado} label="Video" />
                    <Badge ok={item.has_transcription} label="Whisper" />
                    <Badge ok={item.has_segments} label="Segmentos" />
                    <Badge ok={item.validado} label="Validado" />
                  </div>
                  <div className="actions-row actions-row-inline">
                    <Link to={`/partidas/${item.id_partida}`}>Abrir</Link>
                    <button onClick={() => enqueue(item.id_partida, "DOWNLOAD")}>Descargar</button>
                    <button onClick={() => enqueue(item.id_partida, "TRANSCRIBE")}>Transcribir</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
