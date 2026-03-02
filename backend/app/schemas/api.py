from datetime import datetime
from pydantic import BaseModel, Field


class PartidaListItem(BaseModel):
    id_partida: int
    match_id_dota: int | None
    evento: str | None
    anio: int | None
    equipos: str | None
    idioma: str | None
    video_descargado: bool
    has_transcription: bool
    has_segments: bool
    validado: bool


class PartidasListResponse(BaseModel):
    items: list[PartidaListItem]
    page: int
    size: int
    total: int


class PartidaDetail(BaseModel):
    id_partida: int
    match_id_dota: int | None
    evento: str | None
    fase: str | None
    equipos: str | None
    resultado: str | None
    duracion: str | None
    anio: int | None
    caster: str | None
    canal: str | None
    url_video: str | None
    video_descargado: bool
    ruta_video: str | None
    ts_inicio_video: datetime | None
    ts_fin_video: datetime | None
    whisper_json_path: str | None
    idioma: str | None
    fuente_api: str | None
    video_platform: str | None
    video_channel: str | None
    validado: bool
    motivo_invalidez: str | None
    transcripcion_texto: str | None = None


class PartidaPatch(BaseModel):
    match_id_dota: int | None = None
    evento: str | None = None
    fase: str | None = None
    equipos: str | None = None
    resultado: str | None = None
    duracion: str | None = None
    anio: int | None = None
    caster: str | None = None
    canal: str | None = None
    url_video: str | None = None
    idioma: str | None = None
    video_platform: str | None = None
    video_channel: str | None = None
    ts_inicio_video: datetime | None = None
    ts_fin_video: datetime | None = None
    validado: bool | None = None
    motivo_invalidez: str | None = None


class VideoCandidate(BaseModel):
    title: str
    channel: str
    url: str
    duration_seconds: int | None
    language_guess: str | None


class VideoCandidateResponse(BaseModel):
    query: str
    items: list[VideoCandidate]


class JobCreateRequest(BaseModel):
    tipo: str = Field(..., pattern="^(DOWNLOAD|TRANSCRIBE|SEGMENTS|ENRICH)$")
    payload: dict = Field(default_factory=dict)


class JobOut(BaseModel):
    id_job: int
    id_partida: int
    tipo: str
    status: str
    payload_json: dict | None
    log_path: str | None
    error_message: str | None
    attempts: int
    max_attempts: int
    created_at: datetime
    updated_at: datetime


class JobListResponse(BaseModel):
    items: list[JobOut]
    page: int
    size: int
    total: int