from datetime import datetime, time
from sqlalchemy import BigInteger, DateTime, Integer, SmallInteger, String, Text, Time
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Partida(Base):
    __tablename__ = "partidas"

    id_partida: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id_dota: Mapped[int | None] = mapped_column(BigInteger)
    evento: Mapped[str | None] = mapped_column(String(255))
    fase: Mapped[str | None] = mapped_column(String(100))
    equipos: Mapped[str | None] = mapped_column(String(255))
    resultado: Mapped[str | None] = mapped_column(String(100))
    duracion: Mapped[str | None] = mapped_column(String(50))
    anio: Mapped[int | None] = mapped_column(SmallInteger)
    caster: Mapped[str | None] = mapped_column(String(255))
    canal: Mapped[str | None] = mapped_column(String(255))
    url_video: Mapped[str | None] = mapped_column(Text)
    video_descargado: Mapped[int] = mapped_column(SmallInteger, default=0)
    ruta_video: Mapped[str | None] = mapped_column(Text)
    ts_inicio_video: Mapped[datetime | None] = mapped_column(DateTime)
    ts_fin_video: Mapped[datetime | None] = mapped_column(DateTime)
    whisper_json_path: Mapped[str | None] = mapped_column(Text)
    idioma: Mapped[str | None] = mapped_column(String(16))
    fuente_api: Mapped[str] = mapped_column(String(32), default="OpenDota")
    video_platform: Mapped[str | None] = mapped_column(String(32))
    video_channel: Mapped[str | None] = mapped_column(String(128))
    validado: Mapped[int] = mapped_column(SmallInteger, default=1)
    motivo_invalidez: Mapped[str | None] = mapped_column(String(255))
    creado_en: Mapped[datetime] = mapped_column(DateTime)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime)


class PartidaMeta(Base):
    __tablename__ = "partidas_meta"

    match_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id_dota: Mapped[int | None] = mapped_column(BigInteger)
    duration_s: Mapped[int | None] = mapped_column(Integer)
    start_time_utc: Mapped[datetime | None] = mapped_column(DateTime)
    patch: Mapped[str | None] = mapped_column(String(16))
    game_mode: Mapped[str | None] = mapped_column(String(32))
    league_name: Mapped[str | None] = mapped_column(String(128))
    radiant_team_name: Mapped[str | None] = mapped_column(String(128))
    dire_team_name: Mapped[str | None] = mapped_column(String(128))


class Video(Base):
    __tablename__ = "videos"

    id_video: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_match: Mapped[int] = mapped_column(Integer)
    plataforma: Mapped[str | None] = mapped_column(String(32))
    canal_video: Mapped[str | None] = mapped_column(String(128))
    url_video: Mapped[str | None] = mapped_column(Text)
    ruta_video: Mapped[str | None] = mapped_column(Text)
    ts_inicio_video: Mapped[datetime | None] = mapped_column(DateTime)
    ts_fin_video: Mapped[datetime | None] = mapped_column(DateTime)
    video_descargado: Mapped[int] = mapped_column(SmallInteger)
    whisper_json_path: Mapped[str | None] = mapped_column(Text)


class Transcripcion(Base):
    __tablename__ = "transcripciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_partida: Mapped[int] = mapped_column(Integer)
    texto: Mapped[str | None] = mapped_column(Text)
    calidad_audio: Mapped[str | None] = mapped_column(String(50))
    numero_locutores: Mapped[int | None] = mapped_column(Integer)
    fecha_procesado: Mapped[datetime | None] = mapped_column(DateTime)


class SegmentoAudio(Base):
    __tablename__ = "segmentos_audio"

    id_segmento: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_partida: Mapped[int | None] = mapped_column(Integer)
    timestamp_inicio: Mapped[time | None] = mapped_column(Time)
    timestamp_fin: Mapped[time | None] = mapped_column(Time)
    texto: Mapped[str | None] = mapped_column(Text)
    emocion: Mapped[str | None] = mapped_column(String(50))
    tipo_evento: Mapped[str | None] = mapped_column(String(100))


class PipelineJob(Base):
    __tablename__ = "pipeline_jobs"

    id_job: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_partida: Mapped[int] = mapped_column(Integer, nullable=False)
    tipo: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    payload_json: Mapped[str | None] = mapped_column(Text)
    log_path: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
