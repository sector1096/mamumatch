from __future__ import annotations

from sqlalchemy import String, exists, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Partida, PipelineJob, SegmentoAudio, Transcripcion


def apply_partidas_filters(
    query,
    id_partida: int | None,
    q: str | None,
    estado: str | None,
    anio: int | None,
    evento: str | None,
    equipo: str | None,
    idioma: str | None,
    validado: bool | None,
    video_descargado: bool | None,
    has_transcription: bool | None,
    incompletas: bool | None,
):
    if id_partida is not None:
        query = query.where(Partida.id_partida == id_partida)
    if q:
        like = f"%{q.strip()}%"
        query = query.where(
            or_(
                Partida.equipos.ilike(like),
                Partida.evento.ilike(like),
                Partida.fase.ilike(like),
                Partida.caster.ilike(like),
                Partida.canal.ilike(like),
                func.cast(Partida.id_partida, String).ilike(like),
                func.cast(Partida.match_id_dota, String).ilike(like),
            )
        )
    if estado == "con_match_id":
        query = query.where(Partida.match_id_dota.is_not(None))
    elif estado == "sin_match_id":
        query = query.where(Partida.match_id_dota.is_(None))
    if anio is not None:
        query = query.where(Partida.anio == anio)
    if evento:
        query = query.where(Partida.evento.ilike(f"%{evento.strip()}%"))
    if equipo:
        query = query.where(Partida.equipos.ilike(f"%{equipo.strip()}%"))
    if idioma:
        query = query.where(Partida.idioma == idioma)
    if validado is not None:
        query = query.where(Partida.validado == (1 if validado else 0))
    if video_descargado is not None:
        query = query.where(Partida.video_descargado == (1 if video_descargado else 0))
    if has_transcription is not None:
        subq = select(Transcripcion.id).where(Transcripcion.id_partida == Partida.id_partida)
        query = query.where(exists(subq) if has_transcription else ~exists(subq))
    if incompletas:
        query = query.where(
            or_(
                Partida.match_id_dota.is_(None),
                Partida.url_video.is_(None),
                Partida.url_video == "",
                Partida.ts_inicio_video.is_(None),
                Partida.ts_fin_video.is_(None),
            )
        )
    return query


def build_partida_badges(db: Session, rows: list[Partida]) -> list[dict]:
    ids = [r.id_partida for r in rows]
    if not ids:
        return []

    trans_ids = {
        x[0]
        for x in db.execute(
            select(Transcripcion.id_partida).where(Transcripcion.id_partida.in_(ids)).distinct()
        ).all()
    }
    seg_ids = {
        x[0]
        for x in db.execute(
            select(SegmentoAudio.id_partida).where(SegmentoAudio.id_partida.in_(ids)).distinct()
        ).all()
    }

    items = []
    for row in rows:
        items.append(
            {
                "id_partida": row.id_partida,
                "match_id_dota": row.match_id_dota,
                "evento": row.evento,
                "anio": row.anio,
                "equipos": row.equipos,
                "idioma": row.idioma,
                "video_descargado": bool(row.video_descargado),
                "has_transcription": row.id_partida in trans_ids,
                "has_segments": row.id_partida in seg_ids,
                "validado": bool(row.validado),
            }
        )
    return items


def parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    value = value.strip().lower()
    if value in {"1", "true", "yes", "si"}:
        return True
    if value in {"0", "false", "no"}:
        return False
    return None


def clamp_page_size(size: int) -> int:
    return max(1, min(size, settings.page_size_max))
