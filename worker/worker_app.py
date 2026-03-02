from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, time, timedelta
from pathlib import Path

from redis import Redis
from rq import Queue
from sqlalchemy import delete, select

from app.core.config import settings
from app.db.models import Partida, PipelineJob, SegmentoAudio, Transcripcion
from app.db.session import SessionLocal

_MODEL_CACHE = {}


def _now() -> datetime:
    return datetime.utcnow()


def _parse_payload(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _seconds_to_time(value: float | int | None) -> time | None:
    if value is None:
        return None
    total = max(0, int(value))
    hours = total // 3600
    minutes = (total % 3600) // 60
    seconds = total % 60
    if hours > 23:
        hours = 23
        minutes = 59
        seconds = 59
    return time(hour=hours, minute=minutes, second=seconds)


def _dt_to_hhmmss(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.strftime("%H:%M:%S")


def _ensure_dirs() -> None:
    Path(settings.videos_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.whisper_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.logs_dir).mkdir(parents=True, exist_ok=True)


def _run(cmd: list[str], log_file: Path, cwd: str | None = None) -> None:
    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"\n$ {' '.join(cmd)}\n")
        f.flush()
        proc = subprocess.run(cmd, text=True, stdout=f, stderr=f, cwd=cwd, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"Command failed with code {proc.returncode}: {' '.join(cmd)}")


def _resolve_downloaded_file(base: Path) -> Path:
    for ext in [".mp4", ".mkv", ".webm", ".mov", ".avi", ".flv", ".m4a"]:
        candidate = base.with_suffix(ext)
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"No downloaded file found for base {base}")


def _enqueue_followup(id_partida: int, tipo: str, payload: dict) -> None:
    db = SessionLocal()
    try:
        now = _now()
        item = PipelineJob(
            id_partida=id_partida,
            tipo=tipo,
            status="PENDING",
            payload_json=json.dumps(payload, ensure_ascii=False),
            attempts=0,
            max_attempts=int(payload.get("max_attempts", 3)),
            created_at=now,
            updated_at=now,
        )
        db.add(item)
        db.commit()
        db.refresh(item)

        queue = Queue(settings.rq_queue, connection=Redis.from_url(settings.redis_url))
        queue.enqueue("worker_app.execute_pipeline_job", item.id_job, job_timeout="4h")
    finally:
        db.close()


def _download_job(db, partida: Partida, payload: dict, log_file: Path) -> None:
    if not partida.url_video:
        raise ValueError("partida.url_video is required")

    output_dir = Path(settings.videos_dir)
    tmp_base = output_dir / f"tmp_full_{partida.id_partida}"
    clip_path = output_dir / f"{partida.id_partida}.mp4"

    start = _dt_to_hhmmss(partida.ts_inicio_video)
    end = _dt_to_hhmmss(partida.ts_fin_video)
    has_trim = bool(start and end and start != end)

    if has_trim:
        _run(
            [
                settings.yt_dlp_path,
                "--ignore-config",
                "-S",
                "res,ext:mp4:m4a,br",
                "-f",
                "bv*+ba/b",
                "--merge-output-format",
                "mp4",
                "--no-part",
                "-o",
                str(tmp_base.with_suffix(".%(ext)s")),
                partida.url_video,
            ],
            log_file,
        )
        downloaded = _resolve_downloaded_file(tmp_base)
        _run(
            [
                settings.ffmpeg_path,
                "-y",
                "-ss",
                start,
                "-to",
                end,
                "-i",
                str(downloaded),
                "-c:v",
                "copy",
                "-c:a",
                "copy",
                "-avoid_negative_ts",
                "make_zero",
                str(clip_path),
            ],
            log_file,
        )
        try:
            downloaded.unlink(missing_ok=True)
        except Exception:
            pass
    else:
        _run(
            [
                settings.yt_dlp_path,
                "--ignore-config",
                "-S",
                "res,ext:mp4:m4a,br",
                "-f",
                "bv*+ba/b",
                "--merge-output-format",
                "mp4",
                "--no-part",
                "-o",
                str((output_dir / str(partida.id_partida)).with_suffix(".%(ext)s")),
                partida.url_video,
            ],
            log_file,
        )
        downloaded = _resolve_downloaded_file(output_dir / str(partida.id_partida))
        if downloaded != clip_path:
            shutil.move(str(downloaded), str(clip_path))

    if not clip_path.exists() or clip_path.stat().st_size == 0:
        raise RuntimeError("Download output file not found or empty")

    partida.ruta_video = str(clip_path)
    partida.video_descargado = 1
    partida.video_platform = partida.video_platform or payload.get("video_platform") or "youtube"


def _get_whisper_model(model_name: str, device: str):
    key = f"{model_name}:{device}"
    if key in _MODEL_CACHE:
        return _MODEL_CACHE[key]
    import whisper

    model = whisper.load_model(model_name, device=device)
    _MODEL_CACHE[key] = model
    return model


def _transcribe_job(db, partida: Partida, payload: dict, log_file: Path) -> None:
    if not partida.ruta_video:
        raise ValueError("partida.ruta_video is required")
    source = Path(partida.ruta_video)
    if not source.exists():
        raise FileNotFoundError(f"Video file does not exist: {source}")

    model_name = payload.get("model") or settings.whisper_model
    device = payload.get("device") or settings.whisper_device
    lang_hint = payload.get("idioma") or partida.idioma or settings.whisper_language_default

    model = _get_whisper_model(model_name=model_name, device=device)
    result = model.transcribe(str(source), language=lang_hint, fp16=(device == "cuda"))

    whisper_dir = Path(settings.whisper_dir)
    json_path = whisper_dir / f"{partida.id_partida}.json"
    txt_path = whisper_dir / f"{partida.id_partida}.txt"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    with txt_path.open("w", encoding="utf-8") as f:
        f.write((result.get("text") or "").strip())

    texto = (result.get("text") or "").strip()
    idioma_detectado = result.get("language") or lang_hint

    row = db.scalar(
        select(Transcripcion)
        .where(Transcripcion.id_partida == partida.id_partida)
        .order_by(Transcripcion.id.desc())
        .limit(1)
    )
    if row:
        row.texto = texto
        row.calidad_audio = "alta"
        row.numero_locutores = row.numero_locutores or 1
        row.fecha_procesado = _now()
    else:
        row = Transcripcion(
            id_partida=partida.id_partida,
            texto=texto,
            calidad_audio="alta",
            numero_locutores=1,
            fecha_procesado=_now(),
        )
        db.add(row)

    partida.whisper_json_path = str(json_path)
    partida.idioma = idioma_detectado

    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"Saved JSON: {json_path}\n")
        f.write(f"Saved TXT: {txt_path}\n")


def _segments_job(db, partida: Partida, payload: dict, log_file: Path) -> None:
    json_path = payload.get("whisper_json_path") or partida.whisper_json_path
    if not json_path:
        json_path = str(Path(settings.whisper_dir) / f"{partida.id_partida}.json")

    source = Path(json_path)
    if not source.exists():
        raise FileNotFoundError(f"Whisper json not found: {source}")

    data = json.loads(source.read_text(encoding="utf-8"))
    segments = data.get("segments") or []

    db.execute(delete(SegmentoAudio).where(SegmentoAudio.id_partida == partida.id_partida))
    for seg in segments:
        db.add(
            SegmentoAudio(
                id_partida=partida.id_partida,
                timestamp_inicio=_seconds_to_time(seg.get("start")),
                timestamp_fin=_seconds_to_time(seg.get("end")),
                texto=seg.get("text"),
                emocion=None,
                tipo_evento=None,
            )
        )

    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"Inserted segments: {len(segments)}\n")


def _enrich_job(log_file: Path) -> None:
    with log_file.open("a", encoding="utf-8") as f:
        f.write("ENRICH job placeholder executed. Integrate existing OpenDota scripts here.\n")


def execute_pipeline_job(id_job: int) -> None:
    _ensure_dirs()
    db = SessionLocal()
    try:
        job = db.get(PipelineJob, id_job)
        if not job:
            return

        partida = db.get(Partida, job.id_partida)
        if not partida:
            job.status = "ERROR"
            job.error_message = "Partida not found"
            job.updated_at = _now()
            db.add(job)
            db.commit()
            return

        payload = _parse_payload(job.payload_json)
        log_file = Path(settings.logs_dir) / f"{job.id_job}.log"
        job.log_path = str(log_file)
        job.status = "RUNNING"
        job.attempts = int(job.attempts or 0) + 1
        job.updated_at = _now()
        db.add(job)
        db.commit()

        try:
            if job.tipo == "DOWNLOAD":
                _download_job(db, partida, payload, log_file)
            elif job.tipo == "TRANSCRIBE":
                _transcribe_job(db, partida, payload, log_file)
            elif job.tipo == "SEGMENTS":
                _segments_job(db, partida, payload, log_file)
            elif job.tipo == "ENRICH":
                _enrich_job(log_file)
            else:
                raise ValueError(f"Unsupported job type: {job.tipo}")

            job.status = "OK"
            job.error_message = None
            job.updated_at = _now()
            partida.actualizado_en = _now()
            db.add_all([job, partida])
            db.commit()

            chain = payload.get("chain") or []
            if isinstance(chain, list) and chain:
                next_tipo = chain[0]
                next_payload = dict(payload)
                next_payload["chain"] = chain[1:]
                _enqueue_followup(job.id_partida, next_tipo, next_payload)

        except Exception as exc:
            job.status = "ERROR"
            job.error_message = str(exc)
            job.updated_at = _now()
            db.add(job)
            db.commit()
            with log_file.open("a", encoding="utf-8") as f:
                f.write(f"ERROR: {exc}\n")
            raise
    finally:
        db.close()