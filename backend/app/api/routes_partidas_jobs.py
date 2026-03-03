from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import auth_dep, db_dep
from app.db.models import Partida, PipelineJob, SegmentoAudio, Transcripcion
from app.schemas.api import (
    JobCreateRequest,
    JobListResponse,
    JobOut,
    PartidaDetail,
    PartidaPatch,
    PartidasListResponse,
    VideoCandidateResponse,
)
from app.services.jobs import enqueue_chain, enqueue_job, list_jobs, to_job_dict
from app.services.query_helpers import apply_partidas_filters, build_partida_badges, clamp_page_size
from app.services.video_finder import find_video_candidates

router = APIRouter(prefix="/partidas", tags=["partidas"], dependencies=[Depends(auth_dep)])


@router.get("", response_model=PartidasListResponse)
def get_partidas(
    id_partida: int | None = None,
    q: str | None = None,
    estado: str | None = Query(default=None, pattern="^(con_match_id|sin_match_id)$"),
    anio: int | None = None,
    evento: str | None = None,
    equipo: str | None = None,
    idioma: str | None = None,
    validado: bool | None = None,
    video_descargado: bool | None = None,
    has_transcription: bool | None = None,
    incompletas: bool | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=25, ge=1, le=200),
    db: Session = Depends(db_dep),
):
    size = clamp_page_size(size)
    base = select(Partida)
    base = apply_partidas_filters(
        base,
        id_partida=id_partida,
        q=q,
        estado=estado,
        anio=anio,
        evento=evento,
        equipo=equipo,
        idioma=idioma,
        validado=validado,
        video_descargado=video_descargado,
        has_transcription=has_transcription,
        incompletas=incompletas,
    )
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.scalars(
        base.order_by(Partida.id_partida.desc()).offset((page - 1) * size).limit(size)
    ).all()
    items = build_partida_badges(db, rows)
    return {"items": items, "page": page, "size": size, "total": total}


@router.get("/{id_partida}", response_model=PartidaDetail)
def get_partida(id_partida: int, db: Session = Depends(db_dep)):
    row = db.get(Partida, id_partida)
    if not row:
        raise HTTPException(status_code=404, detail="Partida not found")

    trans = db.scalar(
        select(Transcripcion.texto)
        .where(Transcripcion.id_partida == id_partida)
        .order_by(Transcripcion.id.desc())
        .limit(1)
    )

    return {
        "id_partida": row.id_partida,
        "match_id_dota": row.match_id_dota,
        "evento": row.evento,
        "fase": row.fase,
        "equipos": row.equipos,
        "resultado": row.resultado,
        "duracion": row.duracion,
        "anio": row.anio,
        "caster": row.caster,
        "canal": row.canal,
        "url_video": row.url_video,
        "video_descargado": bool(row.video_descargado),
        "ruta_video": row.ruta_video,
        "ts_inicio_video": row.ts_inicio_video,
        "ts_fin_video": row.ts_fin_video,
        "whisper_json_path": row.whisper_json_path,
        "idioma": row.idioma,
        "fuente_api": row.fuente_api,
        "video_platform": row.video_platform,
        "video_channel": row.video_channel,
        "validado": bool(row.validado),
        "motivo_invalidez": row.motivo_invalidez,
        "transcripcion_texto": trans,
    }


@router.patch("/{id_partida}", response_model=PartidaDetail)
def patch_partida(id_partida: int, payload: PartidaPatch, db: Session = Depends(db_dep)):
    row = db.get(Partida, id_partida)
    if not row:
        raise HTTPException(status_code=404, detail="Partida not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        if field == "validado" and value is not None:
            setattr(row, field, 1 if value else 0)
            continue
        setattr(row, field, value)

    db.add(row)
    db.commit()
    db.refresh(row)
    return get_partida(id_partida=id_partida, db=db)


@router.post("/{id_partida}/jobs", response_model=JobOut)
def create_job_for_partida(id_partida: int, body: JobCreateRequest, db: Session = Depends(db_dep)):
    partida = db.get(Partida, id_partida)
    if not partida:
        raise HTTPException(status_code=404, detail="Partida not found")

    job = enqueue_job(db, id_partida=id_partida, tipo=body.tipo, payload=body.payload)
    return to_job_dict(job)


@router.post("/{id_partida}/jobs/run-all", response_model=list[JobOut])
def run_all_for_partida(id_partida: int, db: Session = Depends(db_dep)):
    partida = db.get(Partida, id_partida)
    if not partida:
        raise HTTPException(status_code=404, detail="Partida not found")

    jobs = enqueue_chain(db, id_partida=id_partida, payload={})
    return [to_job_dict(x) for x in jobs]


@router.get("/{id_partida}/jobs", response_model=list[JobOut])
def list_partida_jobs(id_partida: int, db: Session = Depends(db_dep)):
    rows = db.scalars(
        select(PipelineJob).where(PipelineJob.id_partida == id_partida).order_by(PipelineJob.id_job.desc())
    ).all()
    return [to_job_dict(x) for x in rows]


@router.get("/{id_partida}/video-candidates", response_model=VideoCandidateResponse)
def video_candidates(id_partida: int, db: Session = Depends(db_dep)):
    row = db.get(Partida, id_partida)
    if not row:
        raise HTTPException(status_code=404, detail="Partida not found")
    data = find_video_candidates(equipos=row.equipos, evento=row.evento, anio=row.anio)
    return {"query": data["query"], "items": data["items"]}


jobs_router = APIRouter(prefix="/jobs", tags=["jobs"], dependencies=[Depends(auth_dep)])


@jobs_router.get("", response_model=JobListResponse)
def get_jobs(
    status: str | None = None,
    tipo: str | None = None,
    id_partida: int | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=25, ge=1, le=200),
    db: Session = Depends(db_dep),
):
    size = clamp_page_size(size)
    total, rows = list_jobs(db, status=status, tipo=tipo, id_partida=id_partida, page=page, size=size)
    return {"items": [to_job_dict(x) for x in rows], "page": page, "size": size, "total": total}


@jobs_router.get("/{id_job}", response_model=JobOut)
def get_job(id_job: int, db: Session = Depends(db_dep)):
    row = db.get(PipelineJob, id_job)
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    return to_job_dict(row)


@jobs_router.post("/{id_job}/retry", response_model=JobOut)
def retry_job(id_job: int, db: Session = Depends(db_dep)):
    row = db.get(PipelineJob, id_job)
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")

    payload = to_job_dict(row).get("payload_json") or {}
    new_job = enqueue_job(db, id_partida=row.id_partida, tipo=row.tipo, payload=payload)
    return to_job_dict(new_job)


@jobs_router.get("/{id_job}/log")
def get_job_log(id_job: int, tail: int = Query(default=400, ge=10, le=5000), db: Session = Depends(db_dep)):
    row = db.get(PipelineJob, id_job)
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    if not row.log_path:
        return {"id_job": id_job, "log": ""}
    try:
        with open(row.log_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return {"id_job": id_job, "log": ""}

    return {"id_job": id_job, "log": "".join(lines[-tail:])}
