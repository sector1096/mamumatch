from datetime import datetime
import json

from redis import Redis
from rq import Queue
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import PipelineJob

TERMINAL_STATES = {"OK", "ERROR", "CANCELLED"}


def get_queue() -> Queue:
    redis_conn = Redis.from_url(settings.redis_url)
    return Queue(settings.rq_queue, connection=redis_conn)


def enqueue_job(db: Session, id_partida: int, tipo: str, payload: dict | None = None) -> PipelineJob:
    payload = payload or {}
    now = datetime.utcnow()
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

    queue = get_queue()
    queue.enqueue("worker_app.execute_pipeline_job", item.id_job, job_timeout="4h")
    return item


def enqueue_chain(db: Session, id_partida: int, payload: dict | None = None) -> list[PipelineJob]:
    payload = payload or {}
    chain = ["TRANSCRIBE", "SEGMENTS"]
    body = dict(payload)
    body["chain"] = chain
    first = enqueue_job(db, id_partida=id_partida, tipo="DOWNLOAD", payload=body)
    return [first]


def parse_payload(raw: str | None) -> dict | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}


def to_job_dict(item: PipelineJob) -> dict:
    return {
        "id_job": item.id_job,
        "id_partida": item.id_partida,
        "tipo": item.tipo,
        "status": item.status,
        "payload_json": parse_payload(item.payload_json),
        "log_path": item.log_path,
        "error_message": item.error_message,
        "attempts": item.attempts,
        "max_attempts": item.max_attempts,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def list_jobs(
    db: Session,
    status: str | None,
    tipo: str | None,
    id_partida: int | None,
    page: int,
    size: int,
):
    query = select(PipelineJob)
    if status:
        query = query.where(PipelineJob.status == status)
    if tipo:
        query = query.where(PipelineJob.tipo == tipo)
    if id_partida:
        query = query.where(PipelineJob.id_partida == id_partida)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.order_by(PipelineJob.id_job.desc()).offset((page - 1) * size).limit(size)
    ).all()
    return total, rows
