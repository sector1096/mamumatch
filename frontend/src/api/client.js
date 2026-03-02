export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8001";

const API_KEY = import.meta.env.VITE_API_KEY || "change-me";

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY,
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  getPartidas: (params) => request(`/partidas?${new URLSearchParams(params)}`),
  getPartida: (id) => request(`/partidas/${id}`),
  patchPartida: (id, payload) => request(`/partidas/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  createJob: (id, payload) => request(`/partidas/${id}/jobs`, { method: "POST", body: JSON.stringify(payload) }),
  runAll: (id) => request(`/partidas/${id}/jobs/run-all`, { method: "POST" }),
  getPartidaJobs: (id) => request(`/partidas/${id}/jobs`),
  getJobs: (params) => request(`/jobs?${new URLSearchParams(params)}`),
  retryJob: (id) => request(`/jobs/${id}/retry`, { method: "POST" }),
  getJobLog: (id) => request(`/jobs/${id}/log`),
  videoCandidates: (id) => request(`/partidas/${id}/video-candidates`),
};