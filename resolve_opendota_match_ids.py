import re
import time
import argparse
import requests
import mysql.connector

DB = {
    "host": "100.71.184.34",
    "port": 3306,
    "user": "root",
    "password": "casaos",
    "database": "mamutero",
}

OPENDOTA = "https://api.opendota.com/api"
SLEEP_SEC = 0.5  # evita rate-limit suave

def norm_name(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^\w\s.-]", "", s)
    s = s.replace(".", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def parse_minutes(duracion_texto: str | None) -> int | None:
    if not duracion_texto:
        return None
    m = re.search(r"(\d+)\s*min", duracion_texto.lower())
    return int(m.group(1)) if m else None

def split_winner(resultado_mapa: str | None) -> str | None:
    # Ej: "1-0 (Infamous.R)" -> "Infamous.R"
    if not resultado_mapa:
        return None
    m = re.search(r"\(([^)]+)\)", resultado_mapa)
    return m.group(1).strip() if m else None

def http_get(url, params=None):
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def ensure_columns(cur):
    # intenta agregar columnas; si ya existen, ignora
    for stmt in [
        "ALTER TABLE equipos ADD COLUMN opendota_team_id INT NULL",
        "ALTER TABLE eventos ADD COLUMN opendota_league_id INT NULL",
    ]:
        try:
            cur.execute(stmt)
        except Exception:
            pass

def load_opendota_teams():
    teams = http_get(f"{OPENDOTA}/teams")
    # map por nombre normalizado
    idx = {}
    for t in teams:
        name = t.get("name") or ""
        tag = t.get("tag") or ""
        tid = t.get("team_id")
        for key in {norm_name(name), norm_name(tag)}:
            if key and tid and key not in idx:
                idx[key] = tid
    return idx, teams

def load_opendota_leagues():
    leagues = http_get(f"{OPENDOTA}/leagues")
    # index por nombre normalizado (no es perfecto; usamos heurística con año)
    idx = {}
    for l in leagues:
        name = l.get("name") or ""
        lid = l.get("leagueid")
        if lid:
            k = norm_name(name)
            if k and k not in idx:
                idx[k] = lid
    return idx, leagues

def score_event_match(evento_local: str, anio: int | None, league_name: str) -> int:
    # scoring simple para elegir league_id correcto
    a = norm_name(evento_local)
    b = norm_name(league_name)
    score = 0
    if a == b:
        score += 100
    if a and b and (a in b or b in a):
        score += 40
    if anio and str(anio) in league_name:
        score += 15
    # “DPC SA 2021/22 Tour 3” vs “DPC SA 2021/22 Tour 3: Division I”
    tokens_a = set(a.split())
    tokens_b = set(b.split())
    score += int(30 * (len(tokens_a & tokens_b) / max(1, len(tokens_a))))
    return score

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only-series", type=int, default=None, help="procesa solo un id_serie")
    args = ap.parse_args()

    cnx = mysql.connector.connect(**DB)
    cnx.autocommit = False
    cur = cnx.cursor()

    try:
        ensure_columns(cur)

        print("Cargando catálogos OpenDota...")
        team_idx, teams_raw = load_opendota_teams()
        time.sleep(SLEEP_SEC)
        league_idx, leagues_raw = load_opendota_leagues()
        time.sleep(SLEEP_SEC)

        # 1) Mapear equipos -> team_id
        cur.execute("SELECT id_equipo, nombre, opendota_team_id FROM equipos")
        equipos = cur.fetchall()
        upd_teams = 0
        for id_equipo, nombre, tid in equipos:
            if tid:
                continue
            key = norm_name(nombre)
            cand = team_idx.get(key)
            if not cand:
                # fallback: intenta contiene
                for t in teams_raw[:]:
                    if norm_name(t.get("name","")) == key:
                        cand = t.get("team_id"); break
            if cand:
                upd_teams += 1
                if not args.dry_run:
                    cur.execute("UPDATE equipos SET opendota_team_id=%s WHERE id_equipo=%s", (cand, id_equipo))
        print(f"Equipos mapeados: {upd_teams}")

        # 2) Mapear eventos -> league_id
        cur.execute("SELECT id_evento, nombre, anio, opendota_league_id FROM eventos")
        eventos = cur.fetchall()
        upd_events = 0
        for id_evento, nombre, anio, lid in eventos:
            if lid:
                continue
            # busca el league más probable por scoring
            best = (0, None)
            for l in leagues_raw:
                score = score_event_match(nombre, anio, l.get("name",""))
                if score > best[0]:
                    best = (score, l.get("leagueid"))
            if best[1] and best[0] >= 55:
                upd_events += 1
                if not args.dry_run:
                    cur.execute("UPDATE eventos SET opendota_league_id=%s WHERE id_evento=%s", (best[1], id_evento))
        print(f"Eventos mapeados: {upd_events}")

        # 3) Resolver match_id_dota por serie
        q = """
            SELECT
              s.id_serie, e.opendota_league_id,
              ea.nombre, ea.opendota_team_id,
              eb.nombre, eb.opendota_team_id
            FROM series s
            JOIN eventos e ON e.id_evento=s.id_evento
            JOIN equipos ea ON ea.id_equipo=s.id_equipo_a
            JOIN equipos eb ON eb.id_equipo=s.id_equipo_b
        """
        if args.only_series:
            q += " WHERE s.id_serie=%s"
            cur.execute(q, (args.only_series,))
        else:
            cur.execute(q)

        series_rows = cur.fetchall()
        updated_matches = 0
        skipped = 0

        for id_serie, league_id, a_name, a_tid, b_name, b_tid in series_rows:
            if not league_id or not a_tid or not b_tid:
                skipped += 1
                continue

            # matches locales pendientes
            cur.execute("""
                SELECT id_match, game_number, duracion_texto, resultado_mapa
                FROM matches
                WHERE id_serie=%s AND match_id_dota IS NULL
                ORDER BY COALESCE(game_number, 999), id_match
            """, (id_serie,))
            local = cur.fetchall()
            if not local:
                continue

            # candidates de OpenDota para esa liga
            od = http_get(f"{OPENDOTA}/leagues/{league_id}/matches")
            time.sleep(SLEEP_SEC)

            candidates = []
            for m in od:
                # pro match style: radiant_team_id / dire_team_id
                rt = m.get("radiant_team_id")
                dt = m.get("dire_team_id")
                if not rt or not dt:
                    continue
                if {rt, dt} == {a_tid, b_tid}:
                    candidates.append(m)

            # orden por start_time
            candidates.sort(key=lambda x: x.get("start_time") or 0)

            if not candidates:
                continue

            # asignación: por game_number si existe, si no, por orden
            # Creamos lista por orden de partida (1..n)
            ordered_ids = [c.get("match_id") for c in candidates if c.get("match_id")]

            # armar dict game_number -> match_id
            # si hay game_number, lo usamos; si no, rellenamos en orden.
            by_game = {}
            # primero los que tienen game_number
            for id_match, game_number, dur_text, res_map in local:
                if game_number is not None and 1 <= game_number <= len(ordered_ids):
                    by_game[id_match] = ordered_ids[game_number - 1]

            # luego los que quedan sin game_number, en orden restante
            remaining = [mid for mid in ordered_ids if mid not in set(by_game.values())]
            for id_match, game_number, dur_text, res_map in local:
                if id_match in by_game:
                    continue
                if remaining:
                    by_game[id_match] = remaining.pop(0)

            # Validación básica por duración/winner (no bloquea, solo avisa)
            for id_match, game_number, dur_text, res_map in local:
                od_match_id = by_game.get(id_match)
                if not od_match_id:
                    continue

                # intentar validar con /matches/{id} (más pesado; solo si hay señales raras)
                # aquí lo dejamos simple: update directo
                updated_matches += 1
                if not args.dry_run:
                    cur.execute("UPDATE matches SET match_id_dota=%s WHERE id_match=%s", (od_match_id, id_match))

        if args.dry_run:
            cnx.rollback()
            print(f"DRY-RUN OK. Matches que se actualizarían: {updated_matches}. Series omitidas: {skipped}")
        else:
            cnx.commit()
            print(f"OK. Matches actualizados: {updated_matches}. Series omitidas: {skipped}")

    except Exception:
        cnx.rollback()
        raise
    finally:
        cur.close()
        cnx.close()

if __name__ == "__main__":
    main()