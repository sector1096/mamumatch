# descargar_videos.py
# -*- coding: utf-8 -*-
import os
import sys
import re
import logging
import subprocess
import mimetypes
import mysql.connector
import pandas as pd
from io import BytesIO
import requests
from datetime import timedelta

#VALIDAR SI VIENE PARTIDA ESPECIFICA
if len(sys.argv) > 1:
    id_especifico = int(sys.argv[1])
else:
    id_especifico = None

# Configurar logging a archivo
LOG_PATH = "/media/devmon/sda-ata-WDC_WD80EDBZ-11B/nasbullon/MamuteroCaster/logs/descargar_videos.log"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# CONFIGURACIÓN
CARPETA_VIDEOS = "/media/devmon/sda-ata-WDC_WD80EDBZ-11B/nasbullon/MamuteroCaster/videos"
EXCEL_URL = "http://100.71.184.34:7580/s/a5qDDGMz2DZEpdY/download"
DB_CONFIG = {
    "host": "100.71.184.34",
    "port": 3306,
    "user": "root",
    "password": "casaos",
    "database": "mamutero"
}

# FUNCIONES
def limpiar(valor):
    if pd.isna(valor): return ""
    return str(valor).strip()

def limpiar_url(raw_url):
    url = limpiar(raw_url)
    url = url.replace("\\c", ":")
    url = re.sub(r"https?\\+/", "https://", url)
    url = re.sub(r"http[s]?:/+", "https://", url)
    url = url.replace("\\", "")
    return url

def convertir_a_hora(valor):
    try:
        if valor is None or (isinstance(valor, str) and valor.strip() == ""):
            return ""
        
        if isinstance(valor, str):
            valor = valor.strip()
            if re.match(r"^\d{1,2}:\d{2}:\d{2}$", valor):
                return valor
            else:
                # Intentar parsear como float si es un número serial de Excel
                valor = float(valor)

        if isinstance(valor, (int, float)):
            total_seconds = int(float(valor) * 86400)
        elif isinstance(valor, pd.Timestamp):
            total_seconds = valor.hour * 3600 + valor.minute * 60 + valor.second
        elif hasattr(valor, "hour"):  # datetime.time o similar
            total_seconds = valor.hour * 3600 + valor.minute * 60 + valor.second
        elif isinstance(valor, timedelta):
            total_seconds = int(valor.total_seconds())
        else:
            return ""

        horas = total_seconds // 3600
        minutos = (total_seconds % 3600) // 60
        segundos = total_seconds % 60
        return f"{horas:02}:{minutos:02}:{segundos:02}"

    except Exception as e:
        logging.error(f"⚠️ Error al convertir hora '{valor}': {e}")
        return ""


def limpiar_resultados(cursor):
    try:
        if cursor.with_rows:
            cursor.fetchall()  # Solo necesitamos esto para consumir los resultados
    except:
        pass
    try:
        cursor.reset()  # Método más eficiente para limpiar
    except:
        pass

def es_twitch(url):
    return "twitch.tv/videos" in url

def extraer_id_twitch(url):
    return url.split("/")[-1].split("?")[0]

# Asegurar carpeta
os.makedirs(CARPETA_VIDEOS, exist_ok=True)

# Cargar Excel
logging.info("📥 Cargando Excel para recuperar tiempos...")
response = requests.get(EXCEL_URL)
response.raise_for_status()
df_excel = pd.read_excel(BytesIO(response.content))
logging.info("🧾 Columnas encontradas en el Excel:")
logging.info(df_excel.columns.tolist())
# Conectar a BD
conn = mysql.connector.connect(**DB_CONFIG, consume_results=True)
cursor = conn.cursor(dictionary=True)

# Preparando contador
descargadas = 0
omitidas = 0

# Procesar cada fila del Excel
for i, row in df_excel.iterrows():
    try:
        evento = limpiar(row.get("Evento"))
        fase = limpiar(row.get("Fase"))
        equipos = limpiar(row.get("Equipos"))
        resultado = limpiar(row.get("Resultado"))
        duracion = limpiar(row.get("Duración"))
        url = limpiar_url(row.get("URL del video"))
        hora_ini = convertir_a_hora(row.get("Hora_Inicio"))
        hora_fin = convertir_a_hora(row.get("Hora_Fin"))

        if not url:
            continue

        # Buscar id_partida con combinación de campos
        cursor.execute("""
            SELECT id_partida, video_descargado FROM partidas
            WHERE evento = %s AND fase = %s AND equipos = %s AND resultado = %s AND duracion = %s
        """, (evento, fase, equipos, resultado, duracion))
        resultado_bd = cursor.fetchone()
        limpiar_resultados(cursor)

        id_partida = resultado_bd['id_partida']
        ya_descargado = resultado_bd['video_descargado']
        
        # Si se especificó un ID y no coincide, se omite esta fila
        if id_especifico and id_partida != id_especifico:
            continue
            
        if ya_descargado == 1:
            omitidas += 1
            continue

        tiene_recorte = bool(hora_ini and hora_fin and re.match(r"\d{2}:\d{2}:\d{2}", hora_ini) and re.match(r"\d{2}:\d{2}:\d{2}", hora_fin))
        

        logging.info(f"\n🎯 Descargando partida {id_partida} → {url}")
        logging.info(f"⏱️ INICIO: '{hora_ini}' | FIN: '{hora_fin}'")
        logging.info(f"⏱️ Recorte: {hora_ini} → {hora_fin}" if tiene_recorte else "📺 Video completo")
        ruta_provisional = os.path.join(CARPETA_VIDEOS, f"{id_partida}")
        archivo_descargado = None
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
        
        elif tiene_recorte:
            try:
                # 1. Descarga completa
                archivo_completo = os.path.join(CARPETA_VIDEOS, f"full_{id_partida}.mp4")
                logging.info(f"⬇️ Descargando video completo desde YouTube...")
                
                subprocess.run([
                    "yt-dlp",
                    "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                    "--limit-rate", "20M",
                    "--no-part",
                    "--force-keyframes-at-cuts",  # Asegurar keyframes para recorte
                    "-o", archivo_completo,
                    url
                ], check=True)

                # 2. Recorte preciso
                logging.info(f"✂️ Recortando sección {hora_ini} a {hora_fin}...")
                archivo_final = os.path.join(CARPETA_VIDEOS, f"{id_partida}.mp4")
                
                # Convertir tiempos a formato seguro HH:MM:SS
                def formato_tiempo_seguro(tiempo_str):
                    partes = tiempo_str.split(':')
                    if len(partes) == 3:
                        return tiempo_str
                    elif len(partes) == 2:
                        return f"00:{tiempo_str}"
                    else:
                        raise ValueError(f"Formato de tiempo inválido: {tiempo_str}")

                tiempo_inicio = formato_tiempo_seguro(hora_ini)
                tiempo_fin = formato_tiempo_seguro(hora_fin)

                # Comando ffmpeg mejorado
                comando_ffmpeg = [
                    "ffmpeg",
                    "-ss", tiempo_inicio,  # Buscar punto inicial
                    "-i", archivo_completo,  # Archivo de entrada
                    "-to", tiempo_fin,  # Duración del recorte
                    "-c:v", "copy",  # Copiar video sin recompresión
                    "-c:a", "copy",  # Copiar audio sin recompresión
                    "-avoid_negative_ts", "make_zero",  # Manejo mejorado de timestamps
                    "-y",  # Sobrescribir sin preguntar
                    archivo_final
                ]
                
                logging.info(f"🔧 Comando ffmpeg: {' '.join(comando_ffmpeg)}")
                subprocess.run(comando_ffmpeg, check=True, stderr=subprocess.PIPE, text=True)

                # 3. Verificación robusta
                if not os.path.exists(archivo_final) or os.path.getsize(archivo_final) == 0:
                    raise Exception(f"El archivo recortado no se creó correctamente. Tamaño: {os.path.getsize(archivo_final)} bytes")

                # 4. Limpieza
                os.remove(archivo_completo)
                logging.info(f"✅ Recorte completado: {archivo_final} ({os.path.getsize(archivo_final)/1024/1024:.2f} MB)")

            except Exception as e:
                logging.error(f"❌ Error durante el recorte: {str(e)}")
                if 'archivo_completo' in locals() and os.path.exists(archivo_completo):
                    os.remove(archivo_completo)
                raise 
        
        else:
            # Descarga completa sin recorte
            comando = ["yt-dlp", "-o", ruta_provisional + ".%(ext)s", url]
            subprocess.run(comando, check=True)
        
        # Buscar el archivo descargado con alguna de las extensiones comunes   
        for ext in [".mp4", ".mkv", ".webm", ".mov", ".avi", ".flv"]:
            posible_archivo = ruta_provisional + ext
            if os.path.exists(posible_archivo):
                archivo_descargado = posible_archivo
                break
            
        if not archivo_descargado:
            logging.error(f"❌ No se encontró archivo final para partida {id_partida}")
            continue

        logging.info(f"✅ Video guardado en: {archivo_descargado}")
        descargadas += 1
        
        # Reabrir conexión si se ha cerrado por inactividad
        try:
            cursor.execute("SELECT 1")
        except mysql.connector.Error:
            logging.info("🔄 Reconectando a la base de datos...")
            try:
                cursor.close()
                conn.close()
            except:
                pass
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)
        
        # Actualizar BD
        cursor.execute("""
            UPDATE partidas SET video_descargado = 1, ruta_video = %s WHERE id_partida = %s
        """, (archivo_descargado, id_partida))
        limpiar_resultados(cursor) 
        conn.commit()

    except Exception as e:
        logging.error(f"❌ Error en fila {i+2}: {e}")

limpiar_resultados(cursor)
cursor.close()
conn.close()
logging.info(f"\n🧾 RESUMEN:")
logging.info(f"▶️ Partidas descargadas: {descargadas}")
logging.info(f"⏭️ Partidas omitidas (ya descargadas): {omitidas}")

if descargadas == 0 and omitidas == 0:
    logging.info("📭 No se encontraron partidas en el Excel que coincidan con la base de datos.")
elif descargadas == 0 and omitidas > 0:
    logging.info("📦 Todas las partidas encontradas ya estaban descargadas. Nada nuevo que hacer.")
elif descargadas > 0:
    logging.info("✅ Descarga completada exitosamente para las nuevas partidas.")
