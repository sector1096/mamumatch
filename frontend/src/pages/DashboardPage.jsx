import { useEffect, useMemo, useState } from "react";
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

  const queryParams = useMemo(() => {
    const params = {};
    Object.entries(filters).forEach(([k, v]) => {
      if (v !== "") params[k] = v;
    });
    return params;
  }, [filters]);

  const load = async () => {
    try {
      setLoading(true);
      setError("");
      const res = await api.getPartidas(queryParams);
      setData(res);
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

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
          <button onClick={() => setFilters((p) => ({ ...p, page: "1" })) || load()} disabled={loading}>
            Buscar
          </button>
          <button onClick={() => { setFilters(initialFilters); setTimeout(load, 0); }}>
            Limpiar
          </button>
        </div>
      </div>

      {error ? <p className="error">{error}</p> : null}
      {loading ? <p>Cargando...</p> : null}

      <div className="panel">
        <p>Total: {data.total}</p>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Match ID</th>
              <th>Evento / Anio</th>
              <th>Equipos</th>
              <th>Idioma</th>
              <th>Estado</th>
              <th>Acciones</th>
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
                <td className="badges-cell">
                  <Badge ok={item.video_descargado} label="Video" />
                  <Badge ok={item.has_transcription} label="Whisper" />
                  <Badge ok={item.has_segments} label="Segmentos" />
                  <Badge ok={item.validado} label="Validado" />
                </td>
                <td className="actions-row">
                  <Link to={`/partidas/${item.id_partida}`}>Abrir</Link>
                  <button onClick={() => enqueue(item.id_partida, "DOWNLOAD")}>Descargar</button>
                  <button onClick={() => enqueue(item.id_partida, "TRANSCRIBE")}>Transcribir</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}