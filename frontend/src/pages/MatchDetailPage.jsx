import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";

const LANGS = ["es", "en", "pt", "ru", "zh", "fr"];

function toLocalInput(value) {
  if (!value) return "";
  return value.slice(0, 16);
}

export default function MatchDetailPage() {
  const { id } = useParams();
  const [item, setItem] = useState(null);
  const [form, setForm] = useState({});
  const [jobs, setJobs] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [log, setLog] = useState("");
  const [error, setError] = useState("");

  const load = async () => {
    try {
      const [p, j] = await Promise.all([api.getPartida(id), api.getPartidaJobs(id)]);
      setItem(p);
      setForm({
        match_id_dota: p.match_id_dota || "",
        evento: p.evento || "",
        anio: p.anio || "",
        fase: p.fase || "",
        equipos: p.equipos || "",
        resultado: p.resultado || "",
        duracion: p.duracion || "",
        url_video: p.url_video || "",
        idioma: p.idioma || "",
        video_platform: p.video_platform || "",
        video_channel: p.video_channel || "",
        ts_inicio_video: toLocalInput(p.ts_inicio_video),
        ts_fin_video: toLocalInput(p.ts_fin_video),
        validado: !!p.validado,
        motivo_invalidez: p.motivo_invalidez || "",
      });
      setJobs(j);
    } catch (e) {
      setError(String(e.message || e));
    }
  };

  useEffect(() => {
    load();
  }, [id]);

  const save = async () => {
    const payload = {
      ...form,
      match_id_dota: form.match_id_dota ? Number(form.match_id_dota) : null,
      anio: form.anio ? Number(form.anio) : null,
      ts_inicio_video: form.ts_inicio_video || null,
      ts_fin_video: form.ts_fin_video || null,
      validado: !!form.validado,
      motivo_invalidez: form.validado ? null : form.motivo_invalidez || "sin validar",
    };
    await api.patchPartida(id, payload);
    await load();
  };

  const enqueue = async (tipo) => {
    await api.createJob(id, { tipo, payload: {} });
    await load();
  };

  const runAll = async () => {
    await api.runAll(id);
    await load();
  };

  const fetchCandidates = async () => {
    const res = await api.videoCandidates(id);
    setCandidates(res.items || []);
  };

  const openLog = async (jobId) => {
    const res = await api.getJobLog(jobId);
    setLog(res.log || "");
  };

  if (!item) return <p>{error || "Cargando detalle..."}</p>;

  return (
    <section>
      <h2>Partida #{item.id_partida}</h2>
      {error ? <p className="error">{error}</p> : null}

      <div className="panel grid2">
        <div>
          <h3>Identidad</h3>
          {[
            "match_id_dota", "evento", "anio", "fase", "equipos", "resultado", "duracion",
          ].map((k) => (
            <label key={k}><span>{k}</span><input value={form[k] ?? ""} onChange={(e) => setForm((p) => ({ ...p, [k]: e.target.value }))} /></label>
          ))}
        </div>

        <div>
          <h3>Video</h3>
          <label><span>url_video</span><input value={form.url_video || ""} onChange={(e) => setForm((p) => ({ ...p, url_video: e.target.value }))} /></label>
          <label><span>idioma</span>
            <select value={form.idioma || ""} onChange={(e) => setForm((p) => ({ ...p, idioma: e.target.value }))}>
              <option value="">(auto)</option>
              {LANGS.map((l) => <option key={l} value={l}>{l}</option>)}
            </select>
          </label>
          <label><span>video_platform</span><input value={form.video_platform || ""} onChange={(e) => setForm((p) => ({ ...p, video_platform: e.target.value }))} /></label>
          <label><span>video_channel</span><input value={form.video_channel || ""} onChange={(e) => setForm((p) => ({ ...p, video_channel: e.target.value }))} /></label>
          <label><span>ts_inicio_video</span><input type="datetime-local" value={form.ts_inicio_video || ""} onChange={(e) => setForm((p) => ({ ...p, ts_inicio_video: e.target.value }))} /></label>
          <label><span>ts_fin_video</span><input type="datetime-local" value={form.ts_fin_video || ""} onChange={(e) => setForm((p) => ({ ...p, ts_fin_video: e.target.value }))} /></label>
          <label><span>ruta_video</span><input value={item.ruta_video || ""} readOnly /></label>
          <div className="actions-row">
            <button onClick={save}>Guardar metadata</button>
            {item.ruta_video ? <a href={`${item.ruta_video}`} target="_blank">Probar clip</a> : null}
            <button onClick={fetchCandidates}>Buscar videos candidatos</button>
          </div>
          {candidates.length ? (
            <div className="panel">
              <h4>Candidatos</h4>
              {candidates.map((c, i) => (
                <div key={i} className="candidate-row">
                  <div>
                    <strong>{c.title}</strong>
                    <div>{c.channel} | {c.duration_seconds || "?"}s | {c.language_guess || "?"}</div>
                  </div>
                  <button onClick={() => setForm((p) => ({ ...p, url_video: c.url, video_platform: "youtube", video_channel: c.channel }))}>Usar</button>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      </div>

      <div className="panel">
        <h3>Pipeline</h3>
        <div className="actions-row">
          <button onClick={() => enqueue("DOWNLOAD")}>Encolar Descarga</button>
          <button onClick={() => enqueue("TRANSCRIBE")}>Encolar Transcripcion</button>
          <button onClick={() => enqueue("SEGMENTS")}>Encolar Segmentacion</button>
          <button onClick={runAll}>Run all</button>
        </div>
        <table>
          <thead><tr><th>Job</th><th>Tipo</th><th>Status</th><th>Intentos</th><th>Fecha</th><th>Acciones</th></tr></thead>
          <tbody>
            {jobs.map((j) => (
              <tr key={j.id_job}>
                <td>{j.id_job}</td>
                <td>{j.tipo}</td>
                <td>{j.status}</td>
                <td>{j.attempts}/{j.max_attempts}</td>
                <td>{j.updated_at}</td>
                <td><button onClick={() => openLog(j.id_job)}>Ver log</button></td>
              </tr>
            ))}
          </tbody>
        </table>
        {log ? <pre className="log-box">{log}</pre> : null}
      </div>

      <div className="panel">
        <h3>Transcripcion</h3>
        <p><strong>JSON:</strong> {item.whisper_json_path || "-"}</p>
        <details>
          <summary>Ver texto</summary>
          <pre className="log-box">{item.transcripcion_texto || "(sin transcripcion)"}</pre>
        </details>
      </div>

      <div className="panel">
        <h3>Validacion final</h3>
        <label className="inline-label"><input type="checkbox" checked={!!form.validado} onChange={(e) => setForm((p) => ({ ...p, validado: e.target.checked }))} />Validado</label>
        {!form.validado ? (
          <label><span>motivo_invalidez</span><input value={form.motivo_invalidez || ""} onChange={(e) => setForm((p) => ({ ...p, motivo_invalidez: e.target.value }))} /></label>
        ) : null}
      </div>
    </section>
  );
}