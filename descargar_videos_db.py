# descargar_videos_db.py
# -*- coding: utf-8 -*-

import os
import sys
import re
import logging
import subprocess
import mysql.connector
from datetime import datetime, timedelta, time

# =========================
# PARAMETROS CLI
# =========================
# Uso:
#   python3 descargar_videos_db.py            -> descarga todas las pendientes
#   python3 descargar_videos_db.py 127        -> descarga solo id_partida=127
if len(sys.argv) > 1:
    try:
        id_especifico = int(sys.argv[1])
    except:
        id_especifico = None
else:
    id_especifico = None

# =========================
# CONFIG
# =========================
LOG_PATH = "/mnt/100.73.64.58/MamuteroCaster/logs/descargar_videos.log"
CARPETA_VIDEOS = "/mnt/100.73.64.58/MamuteroCaster/videos"

DB_CONFIG = {
    "host": "100.71.184.34",
    "port": 3306,
    "user": "root",
    "password": "casaos",
    "database": "mamutero",
}

# Asegurar rutas
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
os.makedirs(CARPETA_VIDEOS, exist_ok=True)

# Logging
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# =========================
# UTILIDADES
# =========================
def limpiar(valor):
    if valor is None:
        return ""
    return str(valor).strip()

def limpiar_url(raw_url: str) -> str:
    """
    Normaliza URLs que vienen rotas del Excel/BD, ej:
      https:///www.twitch.tv/videos/123?...
      http:////youtube.com/...
      https:\www.twitch.tv\videos\...
    """
    url = limpiar(raw_url)

    # arreglos típicos
    url = url.replace("\\c", ":")
    url = url.replace("\\", "")

    # normalizar slashes del esquema
    url = re.sub(r"^https?:/{3,}", "https://", url)   # https:/// -> https://
    url = re.sub(r"^http:/{2,}", "https://", url)     # http:// -> https://
    url = re.sub(r"^https:/{2,}", "https://", url)    # https:// -> https:// (idempotente)

    # algunos casos llegan como "https:/www...."
    url = re.sub(r"^https:/+", "https://", url)

    return url

def limpiar_resultados(cursor):
    try:
        if cursor.with_rows:
            cursor.fetchall()
    except:
        pass
    try:
        cursor.reset()
    except:
        pass

def convertir_a_hora(valor) -> str:
    """
    Convierte a HH:MM:SS.
    Soporta datetime/time/timedelta/str/float.
    Para tu caso: datetime con fecha 1970-01-01 => se toma solo la hora.
    """
    try:
        if valor is None or (isinstance(valor, str) and valor.strip() == ""):
            return ""

        if isinstance(valor, datetime):
            return valor.strftime("%H:%M:%S")

        if isinstance(valor, time):
            return valor.strftime("%H:%M:%S")

        if isinstance(valor, timedelta):
            total_seconds = int(valor.total_seconds())
            h = total_seconds // 3600
            m = (total_seconds % 3600) // 60
            s = total_seconds % 60
            return f"{h:02}:{m:02}:{s:02}"

        if isinstance(valor, str):
            v = valor.strip()
            if re.match(r"^\d{1,2}:\d{2}:\d{2}$", v):
                h, m, s = v.split(":")
                return f"{int(h):02}:{int(m):02}:{int(s):02}"
            # intentar float (serial excel)
            valor = float(v)

        if isinstance(valor, (int, float)):
            # serial excel de día -> segundos
            total_seconds = int(float(valor) * 86400)
            h = total_seconds // 3600
            m = (total_seconds % 3600) // 60
            s = total_seconds % 60
            return f"{h:02}:{m:02}:{s:02}"

        return ""
    except Exception as e:
        logging.error(f"⚠️ Error al convertir hora '{valor}': {e}")
        return ""

def es_twitch(url: str) -> bool:
    u = (url or "").lower()
    return "twitch.tv/videos" in u

def extraer_id_twitch(url: str) -> str:
    # https://www.twitch.tv/videos/1638361523?filter=all&sort=time
    # => 1638361523
    return url.split("/")[-1].split("?")[0]

def hhmmss_a_segundos(hhmmss: str) -> int:
    h, m, s = hhmmss.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s)

def segundos_a_hhmmss(seg: int) -> str:
    seg = max(0, int(seg))
    h = seg // 3600
    m = (seg % 3600) // 60
    s = seg % 60
    return f"{h:02}:{m:02}:{s:02}"

def calcular_duracion(hora_ini: str, hora_fin: str) -> str:
    """
    Duración = fin - inicio.
    Si fin < inicio, asume que cruzó medianoche.
    """
    ini = hhmmss_a_segundos(hora_ini)
    fin = hhmmss_a_segundos(hora_fin)
    if fin < ini:
        fin += 24 * 3600
    return segundos_a_hhmmss(fin - ini)

def tiene_formato_hora(h: str) -> bool:
    return bool(h) and bool(re.match(r"^\d{2}:\d{2}:\d{2}$", h))

def asegurar_dependencia(cmd: str):
    """
    Chequeo simple (no detiene por default, solo loguea).
    """
    try:
        subprocess.run([cmd, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    except Exception:
        logging.warning(f"⚠️ No pude ejecutar '{cmd} --version'. Verifica que esté instalado y en PATH.")

# =========================
# MAIN
# =========================
def main():
    logging.info("🚀 Iniciando descarga desde BD (tabla partidas)")

    # chequeo básico de dependencias
    asegurar_dependencia("yt-dlp")
    asegurar_dependencia("ffmpeg")
    asegurar_dependencia("TwitchDownloaderCLI")

    conn = mysql.connector.connect(**DB_CONFIG, consume_results=True)
    cursor = conn.cursor(dictionary=True)

    descargadas = 0
    omitidas = 0
    fallidas = 0

    # Traer partidas pendientes
    if id_especifico:
        cursor.execute("""
            SELECT id_partida, url_video, video_descargado, ruta_video, ts_inicio_video, ts_fin_video
            FROM partidas
            WHERE id_partida = %s
            LIMIT 1
        """, (id_especifico,))
    else:
        cursor.execute("""
            SELECT id_partida, url_video, video_descargado, ruta_video, ts_inicio_video, ts_fin_video
            FROM partidas
            WHERE video_descargado = 0
              AND url_video IS NOT NULL
              AND TRIM(url_video) <> ''
              AND LOWER(TRIM(url_video)) NOT IN ('nan','none','null','n/a','na','-')
              AND (LOWER(url_video) LIKE 'http%' OR LOWER(url_video) LIKE 'www.%')
              AND ts_inicio_video IS NOT NULL
              AND ts_fin_video IS NOT NULL
              AND ts_fin_video <> ts_inicio_video
            ORDER BY id_partida ASC;

        """)

    partidas = cursor.fetchall()
    limpiar_resultados(cursor)

    if not partidas:
        logging.info("📭 No hay partidas pendientes por descargar (o no existe el ID indicado).")
        try:
            cursor.close(); conn.close()
        except:
            pass
        return

    for p in partidas:
        id_partida = p.get("id_partida")
        try:
            url = limpiar_url(p.get("url_video"))
            ya_descargado = int(p.get("video_descargado") or 0)

            if not url:
                logging.info(f"⏭️ Partida {id_partida}: sin url_video, se omite.")
                continue

            if ya_descargado == 1:
                omitidas += 1
                logging.info(f"⏭️ Partida {id_partida}: ya estaba descargada.")
                continue

            # offsets dentro del VOD (guardados como datetime con fecha 1970-01-01)
            hora_ini = convertir_a_hora(p.get("ts_inicio_video"))
            hora_fin = convertir_a_hora(p.get("ts_fin_video"))

            tiene_recorte = tiene_formato_hora(hora_ini) and tiene_formato_hora(hora_fin)

            logging.info(f"\n🎯 Descargando partida {id_partida} → {url}")
            logging.info(f"⏱️ INICIO: '{hora_ini}' | FIN: '{hora_fin}'")
            logging.info(f"⏱️ Recorte: {hora_ini} → {hora_fin}" if tiene_recorte else "📺 Video completo")

            ruta_base = os.path.join(CARPETA_VIDEOS, f"{id_partida}")
            archivo_descargado = None

            # =========================
            # TWITCH + RECORTE
            # =========================
            if es_twitch(url) and tiene_recorte:
                twitch_id = extraer_id_twitch(url)
                archivo_descargado = os.path.join(CARPETA_VIDEOS, f"{id_partida}.mp4")

                subprocess.run([
                    "TwitchDownloaderCLI", "videodownload",
                    "--id", twitch_id,
                    "--beginning", hora_ini,
                    "--ending", hora_fin,
                    "--output", archivo_descargado
                ], check=True)

            # =========================
            # NO-TWITCH + RECORTE (YouTube u otros)
            # =========================
            elif tiene_recorte:
                archivo_completo = os.path.join(CARPETA_VIDEOS, f"full_{id_partida}.mp4")
                logging.info("⬇️ Descargando video completo (yt-dlp)...")

                subprocess.run([
                    "yt-dlp",
                    "--ignore-config",
                    "-S", "res,ext:mp4:m4a,br",
                    "-f", "bv*+ba/b",
                    "--merge-output-format", "mp4",
                    "--no-part",
                    "--limit-rate", "20M",
                    "-o", archivo_completo,
                    url
                ], check=True)


                archivo_final = os.path.join(CARPETA_VIDEOS, f"{id_partida}.mp4")

                inicio = hora_ini
                fin = hora_fin
                duracion = calcular_duracion(inicio, fin)

                logging.info(f"✂️ Recortando con ffmpeg: inicio={inicio} duracion={duracion} (fin={fin})")

                # Importante: usar -t (duración) en vez de -to para evitar interpretaciones raras
                comando_ffmpeg = [
                    "ffmpeg",
                    "-ss", inicio,
                    "-i", archivo_completo,
                    "-t", duracion,
                    "-c:v", "copy",
                    "-c:a", "copy",
                    "-avoid_negative_ts", "make_zero",
                    "-y",
                    archivo_final
                ]

                logging.info(f"🔧 Comando ffmpeg: {' '.join(comando_ffmpeg)}")
                subprocess.run(comando_ffmpeg, check=True, stderr=subprocess.PIPE, text=True)

                # Verificación
                if (not os.path.exists(archivo_final)) or os.path.getsize(archivo_final) == 0:
                    size = os.path.getsize(archivo_final) if os.path.exists(archivo_final) else 0
                    raise Exception(f"El archivo recortado no se creó correctamente. Tamaño: {size} bytes")

                # limpieza
                try:
                    os.remove(archivo_completo)
                except:
                    pass

                archivo_descargado = archivo_final
                logging.info(f"✅ Recorte completado: {archivo_final} ({os.path.getsize(archivo_final)/1024/1024:.2f} MB)")

            # =========================
            # SIN RECORTE (descarga completa)
            # =========================
            else:
                comando = ["yt-dlp", "-o", ruta_base + ".%(ext)s", url]
                subprocess.run(comando, check=True)

            # Si venía de yt-dlp con plantilla, buscar extensión
            if not archivo_descargado:
                for ext in [".mp4", ".mkv", ".webm", ".mov", ".avi", ".flv"]:
                    posible = ruta_base + ext
                    if os.path.exists(posible):
                        archivo_descargado = posible
                        break

            if not archivo_descargado:
                raise Exception("No se encontró archivo final luego de la descarga/recorte.")

            logging.info(f"✅ Video guardado en: {archivo_descargado}")
            descargadas += 1

            # Revalidar conexión (por si hay timeout)
            try:
                cursor.execute("SELECT 1")
                limpiar_resultados(cursor)
            except mysql.connector.Error:
                logging.info("🔄 Reconectando a la base de datos...")
                try:
                    cursor.close(); conn.close()
                except:
                    pass
                conn = mysql.connector.connect(**DB_CONFIG, consume_results=True)
                cursor = conn.cursor(dictionary=True)

            # Actualizar BD
            cursor.execute("""
                UPDATE partidas
                SET video_descargado = 1,
                    ruta_video = %s
                WHERE id_partida = %s
            """, (archivo_descargado, id_partida))
            limpiar_resultados(cursor)
            conn.commit()

        except Exception as e:
            fallidas += 1
            logging.error(f"❌ Error en partida {id_partida}: {e}")

    # Cierre
    try:
        limpiar_resultados(cursor)
        cursor.close()
        conn.close()
    except:
        pass

    logging.info("\n🧾 RESUMEN:")
    logging.info(f"▶️ Partidas descargadas: {descargadas}")
    logging.info(f"⏭️ Partidas omitidas (ya descargadas): {omitidas}")
    logging.info(f"💥 Partidas fallidas: {fallidas}")

    if descargadas == 0 and omitidas == 0 and fallidas == 0:
        logging.info("📭 No se encontraron partidas pendientes.")
    elif descargadas == 0 and omitidas > 0 and fallidas == 0:
        logging.info("📦 Todas las partidas encontradas ya estaban descargadas. Nada nuevo que hacer.")
    elif descargadas > 0 and fallidas == 0:
        logging.info("✅ Descarga completada exitosamente para las nuevas partidas.")
    elif fallidas > 0:
        logging.info("⚠️ Hubo fallas. Revisa el log para detalles.")

if __name__ == "__main__":
    main()
