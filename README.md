# MamuMatch

Web app (UI + API + worker) para gestionar metadata de partidas de Dota y ejecutar pipeline:

1. descarga clip de video
2. transcripcion Whisper
3. extraccion de segmentos

## Stack

- Frontend: React + Vite
- API: FastAPI + SQLAlchemy
- Worker: RQ + Redis
- DB: MariaDB existente (`mamutero`)
- Deploy: Docker Compose

## Estructura

- `backend/`: API FastAPI
- `worker/`: consumidor RQ y jobs de pipeline
- `frontend/`: UI React
- `backend/migrations/001_create_pipeline_jobs.sql`: nueva tabla `pipeline_jobs`

## Configuracion

1. Copia `.env.example` a `.env` y ajusta credenciales:

```bash
cp .env.example .env
```

2. Verifica conectividad a MariaDB desde el host docker.

## Levantar todo

```bash
docker compose up -d --build
```

- UI: `http://localhost:8081`
- API: `http://localhost:8001`

## Endpoints principales

- `GET /health`
- `GET /partidas`
- `GET /partidas/{id_partida}`
- `PATCH /partidas/{id_partida}`
- `POST /partidas/{id_partida}/jobs`
- `POST /partidas/{id_partida}/jobs/run-all`
- `GET /partidas/{id_partida}/jobs`
- `GET /partidas/{id_partida}/video-candidates`
- `GET /jobs`
- `GET /jobs/{id_job}`
- `GET /jobs/{id_job}/log`
- `POST /jobs/{id_job}/retry`

Todos requieren `X-API-Key`.

## Pipeline jobs

### DOWNLOAD

- Usa `yt-dlp` para descarga (YouTube y URLs compatibles).
- Si `ts_inicio_video` y `ts_fin_video` existen, recorta con `ffmpeg`.
- Guarda en `${APP_VIDEOS_DIR}/{id_partida}.mp4`.
- Actualiza `partidas.ruta_video` y `partidas.video_descargado=1`.

### TRANSCRIBE

- Usa `openai-whisper` con modelo configurable (`APP_WHISPER_MODEL`, default `large`).
- Guarda JSON/TXT en `${APP_WHISPER_DIR}/{id_partida}.{json,txt}`.
- Upsert en `transcripciones`.
- Actualiza `partidas.whisper_json_path` y `partidas.idioma`.

### SEGMENTS

- Lee segmentos del JSON de Whisper.
- Reemplaza segmentos de `segmentos_audio` para la partida.
- Inserta `timestamp_inicio`, `timestamp_fin`, `texto` y placeholders.

### RUN ALL

- Encola `DOWNLOAD` con cadena dependiente `TRANSCRIBE -> SEGMENTS`.
- Cada paso se encola solo cuando el anterior termina en `OK`.

## Video Finder

- Boton en detalle: "Buscar videos candidatos".
- Strategy:
  1. YouTube Data API (si `APP_YOUTUBE_API_KEY` existe)
  2. Fallback `yt-dlp ytsearch10:`

## Logs de jobs

- Archivo por job: `${APP_LOGS_DIR}/{id_job}.log`
- Visible desde UI (`Jobs` y `Detalle`)

## Tests minimos

```bash
cd backend
pip install -r requirements.txt
pytest -q
```

Incluye:

- `tests/test_health.py`
- `tests/test_db.py`

## Nota sobre scripts legacy

Se dejaron en la raiz (`descargar_videos_db.py`, `transcribir_partidas_enriquecido.py`, etc.) como referencia funcional. El worker implementa la misma finalidad, integrado al sistema de jobs de la app.