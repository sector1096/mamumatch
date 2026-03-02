#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transcribe partidas con Whisper y enriquece la BD:
- Guarda TXT + JSON completos de Whisper por partida.
- Inserta segmentos en `whisper_segments`.
- Inserta/actualiza fila en `transcripciones`.
- Actualiza `partidas.idioma` y `partidas.whisper_json_path`.

Uso:
  python3 transcribir_partidas_enriquecido.py
  python3 transcribir_partidas_enriquecido.py --id 127 --reprocesar
  python3 transcribir_partidas_enriquecido.py --modelo turbo --idioma es
"""

import os
import sys
import json
import argparse
from datetime import datetime
import mysql.connector
from mysql.connector.errors import OperationalError, InterfaceError, DatabaseError
import whisper

# --- Config ---
RUTA_VIDEOS = "/media/devmon/sda-ata-WDC_WD80EDBZ-11B/nasbullon/MamuteroCaster/videos"
RUTA_SALIDA = "/media/devmon/sda-ata-WDC_WD80EDBZ-11B/nasbullon/MamuteroCaster/transcript"

DB_CFG = dict(
    host="100.71.184.34",
    port=3306,
    user="root",
    password="casaos",
    database="mamutero",
    autocommit=True,          # commit automático por operación
    connection_timeout=10,
    charset="utf8mb4",
    use_pure=True,
)

# --- CLI ---
ap = argparse.ArgumentParser()
ap.add_argument("--id", type=int, default=None, help="id_partida local a reprocesar")
ap.add_argument("--modelo", default="turbo", help="modelo whisper (turbo/base/small/medium/large)")
ap.add_argument("--idioma", default="es", help="idioma a forzar (ej. es)")
ap.add_argument("--reprocesar", action="store_true", help="borra transcripcion y segmentos previos de la(s) partida(s)")
args = ap.parse_args()

# --- Utilidades de conexión robusta ---
_conn = None

def get_conn():
    global _conn
    if _conn is None or not _conn.is_connected():
        _conn = mysql.connector.connect(**DB_CFG)
    else:
        try:
            # revalida y reconecta si hace falta
            _conn.ping(reconnect=True, attempts=3, delay=2)
        except Exception:
            _conn = mysql.connector.connect(**DB_CFG)
    return _conn

def with_retry(fn, *a, **kw):
    """
    Ejecuta una función que usa DB; si la conexión cayó, reconecta y reintenta 1 vez.
    """
    try:
        return fn(*a, **kw)
    except (OperationalError, InterfaceError, DatabaseError) as e:
        # reconectar y reintentar una vez
        try:
            get_conn()  # fuerza ping/reconnect
            return fn(*a, **kw)
        except Exception as e2:
            raise e2

# --- Operaciones BD ---
def cargar_pendientes():
    conn = get_conn()
    with conn.cursor(dictionary=True) as cur:
        if args.id:
            cur.execute("""
                SELECT p.id_partida, p.ruta_video
                FROM partidas p
                WHERE p.video_descargado = 1
                  AND p.ruta_video IS NOT NULL
                  AND p.id_partida = %s
            """, (args.id,))
        else:
            cur.execute("""
                SELECT p.id_partida, p.ruta_video
                FROM partidas p
                LEFT JOIN transcripciones t ON p.id_partida = t.id_partida
                WHERE p.video_descargado = 1
                  AND p.ruta_video IS NOT NULL
                  AND (t.id_partida IS NULL OR %s=1)
            """, (1 if args.reprocesar else 0,))
        return cur.fetchall()

def borrar_previos(id_partida):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM whisper_segments WHERE match_id = %s", (id_partida,))
        cur.execute("DELETE FROM transcripciones WHERE id_partida = %s", (id_partida,))

def insertar_transcripcion(id_partida, texto):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO transcripciones (id_partida, texto, calidad_audio, numero_locutores, fecha_procesado)
            VALUES (%s, %s, %s, %s, %s)
        """, (id_partida, texto, "alta", 1, datetime.now()))

def batch_insert_segmentos(id_partida, segmentos):
    if not segmentos:
        return
    conn = get_conn()
    sql = """
        INSERT INTO whisper_segments
            (match_id, segment_id, t_inicio, t_fin, texto, avg_logprob, compression_ratio, no_speech_prob, words_json)
        VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    data = []
    for seg in segmentos:
        data.append((
            id_partida,
            seg.get("id"),
            seg.get("start"),
            seg.get("end"),
            seg.get("text"),
            seg.get("avg_logprob"),
            seg.get("compression_ratio"),
            seg.get("no_speech_prob"),
            json.dumps(seg.get("words"), ensure_ascii=False) if seg.get("words") is not None else None
        ))
    conn = get_conn()
    with conn.cursor() as cur:
        cur.executemany(sql, data)

def actualizar_partidas_con_json(id_partida, idioma, ruta_json):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE partidas
            SET idioma = %s,
                whisper_json_path = %s,
                actualizado_en = CURRENT_TIMESTAMP
            WHERE id_partida = %s
        """, (idioma, ruta_json, id_partida))

# --- Main ---
def main():
    os.makedirs(RUTA_SALIDA, exist_ok=True)

    print(f"🧠 Cargando Whisper '{args.modelo}' ...")
    model = whisper.load_model(args.modelo)

    # obtenemos pendientes con conexión válida
    pendientes = with_retry(cargar_pendientes)
    if not pendientes:
        print("No hay partidas pendientes.")
        return

    for row in pendientes:
        id_partida = row["id_partida"]
        ruta_video = row["ruta_video"]

        if not ruta_video or not os.path.exists(ruta_video):
            print(f"❌ {id_partida}: archivo no encontrado -> {ruta_video}")
            continue

        print(f"🎙️ {id_partida}: transcribiendo -> {ruta_video}")

        try:
            # transcribe (esto puede tardar: no usamos DB aquí)
            result = model.transcribe(ruta_video, language=args.idioma, fp16=False)
            texto = (result.get("text") or "").strip()
            idioma_detectado = result.get("language") or args.idioma
            segmentos = result.get("segments", [])

            # guarda archivos
            ruta_txt = os.path.join(RUTA_SALIDA, f"{id_partida}.txt")
            ruta_json = os.path.join(RUTA_SALIDA, f"{id_partida}.json")
            with open(ruta_txt, "w", encoding="utf-8") as f:
                f.write(texto)
            with open(ruta_json, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"📄 TXT:  {ruta_txt}")
            print(f"🧾 JSON: {ruta_json}")

            # si se pidió reprocesar, borra previos ahora (con reconexión y retry)
            if args.reprocesar:
                with_retry(borrar_previos, id_partida)

            # inserta en DB (cada operación hace ping/reconnect y retry)
            with_retry(insertar_transcripcion, id_partida, texto)
            with_retry(batch_insert_segmentos, id_partida, segmentos)
            with_retry(actualizar_partidas_con_json, id_partida, idioma_detectado, ruta_json)

            print(f"✅ {id_partida}: transcripción y {len(segmentos)} segmentos almacenados.")

        except Exception as e:
            print(f"⚠️ {id_partida}: error -> {e}")

    # cierra si seguía abierta
    try:
        if _conn and _conn.is_connected():
            _conn.close()
    except Exception:
        pass

    print("🏁 Listo.")

if __name__ == "__main__":
    main()
