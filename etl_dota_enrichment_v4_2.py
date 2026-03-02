#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SECTOR1096 - Enrichment v4.2 (DB-dedupe)
- STRATZ: objectives/teamfights/winprob + snapshots (gold/xp) + kills/buybacks

- Persiste en:
    - partidas_meta (UPSERT)
    - eventos_partida (UPSERT por event_hash)
    - snapshots_partida (UPSERT por uq_snap_point)
- --reprocesar: limpia eventos/snapshots (y reescribe todo)

Requisitos DB:
  - eventos_partida.event_hash BINARY(16) NULL
  - UNIQUE uq_evt_hash (match_id, event_hash)
  - snapshots_partida UNIQUE uq_snap_point (match_id,t_seg,metric,slot)

Uso:
  STRATZ_API_KEY=xxxx python3 etl_dota_enrichment_v4_2.py
  python3 etl_dota_enrichment_v4_2.py --id 375
  python3 etl_dota_enrichment_v4_2.py --reprocesar --delay 1.2
"""

import os
import time
import json
import argparse
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from curl_cffi import requests as crequests
import requests
import mysql.connector
from mysql.connector.errors import Error as MySQLError

# ---------------- Config ----------------
DB = dict(
    host=os.getenv("DB_HOST", "100.71.184.34"),
    port=int(os.getenv("DB_PORT", "3306")),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", "casaos"),
    database=os.getenv("DB_NAME", "mamutero"),
    autocommit=True,
    charset="utf8mb4",
    use_pure=True,
)

STRATZ_URL = "https://api.stratz.com/graphql"

ap = argparse.ArgumentParser()
ap.add_argument("--id", type=int, default=None, help="id_partida local a procesar")
ap.add_argument("--reprocesar", action="store_true", help="Limpia eventos/snapshots antes de insertar")
ap.add_argument("--delay", type=float, default=5.0, help="Sleep entre partidas")
ap.add_argument("--stratz-key", default=os.getenv("STRATZ_API_KEY", "eyJTdWJqZWN0IjoiMGFlY2MwOWMtYWExZi00MDg3LWI3ZDItY2ExYzA4NWM3ZTU0IiwiU3RlYW1JZCI6IjEwMzI5MjI3NTAiLCJBUElVc2VyIjoidHJ1ZSIsIm5iZiI6MTc1NzQzMjg5NSwiZXhwIjoxNzg4OTY4ODk1LCJpYXQiOjE3NTc0MzI4OTUsImlzcyI6Imh0dHBzOi8vYXBpLnN0cmF0ei5jb20ifQ"), help="STRATZ API KEY (env STRATZ_API_KEY)")
args = ap.parse_args()

# ---------------- Helpers ----------------
INVALID = {None, "", "nan", "null", "none", "n/a", "na", "-"}

def norm_int(x) -> Optional[int]:
    try:
        return int(x) if x is not None else None
    except Exception:
        return None

def safe_json(obj: Any) -> Optional[str]:
    if obj is None:
        return None
    return json.dumps(obj, ensure_ascii=False)

def _trim_valor(valor: Optional[str]) -> Optional[str]:
    if valor is None:
        return None
    if not isinstance(valor, str):
        valor = str(valor)
    valor = valor.strip()
    if not valor or valor.lower() in INVALID:
        return None
    return valor[:128]

def wipe_child_tables(conn, id_local: int):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM eventos_partida WHERE match_id = %s", (id_local,))
        cur.execute("DELETE FROM snapshots_partida WHERE match_id = %s", (id_local,))

def fetch_targets(conn) -> List[Dict[str, Any]]:
    with conn.cursor(dictionary=True) as cur:
        sql = "SELECT id_partida, match_id_dota FROM partidas WHERE match_id_dota IS NOT NULL"
        params = []
        if args.id:
            sql += " AND id_partida = %s"
            params.append(args.id)
        cur.execute(sql, params)
        return cur.fetchall()


# ---------------- STRATZ ----------------
def fetch_stratz_match(match_id_dota: int, api_key: str) -> Dict[str, Any]:
    q = r"""
    query($id: Long!) {
      match(id: $id) {
        id
        durationSeconds
        startDateTime
        didRadiantWin
        gameVersionId
        clusterId
        regionId
        lobbyType
        gameMode

        league { id name }
        radiantTeam { id name }
        direTeam { id name }

        pickBans {
          isPick
          heroId
          order
          isRadiant
        }

        players {
          playerSlot
          heroId
          isRadiant
          kills
          deaths
          assists
          networth
          heroDamage
          towerDamage
          level

          item0Id
          item1Id
          item2Id
          item3Id
          item4Id
          item5Id

          stats {
            networthPerMinute
            experiencePerMinute

            killEvents {
              time
              target
              byAbility
              byItem
              gold
              xp
              positionX
              positionY
              isSolo
              isGank
            }

            deathEvents {
              time
              attacker
              target
              goldFed
              xpFed
              positionX
              positionY
              isDieBack
            }

            assistEvents {
              time
              target
              gold
              xp
              positionX
              positionY
            }
          }
        }

        chatEvents {
          time
          type
          fromHeroId
          toHeroId
          value
          isRadiant
        }

        towerDeaths {
          time
          npcId
          isRadiant
          attacker
        }

        
        winRates
        predictedWinRates
        radiantNetworthLeads
        radiantExperienceLeads
        radiantKills
        direKills
      }
    }
    """


    
    # Headers mínimos y limpios
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    # Usamos curl_cffi con impersonate="chrome120"
    # Esto maneja el TLS de Cloudflare automáticamente
    r = crequests.post(
        STRATZ_URL,
        json={"query": q, "variables": {"id": int(match_id_dota)}},
        headers=headers,
        impersonate="chrome120", # <--- CLAVE PARA EL SALTO
        timeout=45,
    )

    if r.status_code != 200:
        print(f"DEBUG: Status {r.status_code} - Body: {r.text[:200]}")
        r.raise_for_status()

    j = r.json()
    if "errors" in j:
        raise RuntimeError(j["errors"])
    m = j["data"]["match"]
    if not m:
        raise RuntimeError("STRATZ returned null match")
    return m

def upsert_raw_json(cur, id_local: int, mid_dota: int, data: dict):
    cur.execute("""
        INSERT INTO match_raw_json (match_id, match_id_dota, json_data)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            json_data = VALUES(json_data),
            fetched_at = CURRENT_TIMESTAMP
    """, (
        id_local,
        mid_dota,
        json.dumps(data, ensure_ascii=False)
    ))

# ---------------- partidas_meta UPSERT ----------------
def upsert_partidas_meta_from_stratz(cur, id_local: int, s: Dict[str, Any], mid_dota: int):
    start_epoch = s.get("startDateTime")
    start_dt = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(start_epoch)) if start_epoch else None

    fields = {
        "match_id": id_local,
        "match_id_dota": mid_dota,
        "duration_s": s.get("durationSeconds"),
        "start_time_utc": start_dt,
        "radiant_win": 1 if s.get("didRadiantWin") else 0 if s.get("didRadiantWin") is not None else None,

        # si no vas a mapear a nombre, guarda el id como string o en otro campo
        "patch": str(s.get("gameVersionId")) if s.get("gameVersionId") is not None else None,

        "game_mode": s.get("gameMode"),
        "lobby_type": s.get("lobbyType"),
        "cluster": s.get("clusterId"),
        "region": s.get("regionId"),

        "avg_mmr": None,
        "avg_rank_tier": None,
        "replay_url": None,

        "league_id": (s.get("league") or {}).get("id"),
        "league_name": (s.get("league") or {}).get("name"),

        "radiant_team_id": (s.get("radiantTeam") or {}).get("id"),
        "radiant_team_name": (s.get("radiantTeam") or {}).get("name"),
        "dire_team_id": (s.get("direTeam") or {}).get("id"),
        "dire_team_name": (s.get("direTeam") or {}).get("name"),
    }


    cols = ",".join(fields.keys())
    placeholders = ",".join(["%s"] * len(fields))
    updates = ",".join([f"{k}=VALUES({k})" for k in fields.keys() if k != "match_id"])

    cur.execute(f"""
        INSERT INTO partidas_meta ({cols})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {updates}
    """, tuple(fields.values()))



# ---------------- Event hash + UPSERT ----------------
def build_event_hash(
    match_id: int,
    t_seg: Optional[int],
    tipo: str,
    actor_slot: Optional[int],
    target_slot: Optional[int],
    actor_hero: Optional[int],
    target_hero: Optional[int],
    x: Optional[int],
    y: Optional[int],
    valor: Optional[str],
) -> bytes:
    """
    Hash estable (MD5 -> 16 bytes) para dedupe.
    Importante: normaliza None como vacío.
    """
    s = "|".join([
        str(match_id),
        "" if t_seg is None else str(t_seg),
        (tipo or "")[:32],
        "" if actor_slot is None else str(actor_slot),
        "" if target_slot is None else str(target_slot),
        "" if actor_hero is None else str(actor_hero),
        "" if target_hero is None else str(target_hero),
        "" if x is None else str(x),
        "" if y is None else str(y),
        "" if valor is None else str(valor),
    ])
    return hashlib.md5(s.encode("utf-8")).digest()

def upsert_event(
    cur,
    id_local: int,
    t_sec: Optional[int],
    tipo: str,
    actor_slot: Optional[int] = None,
    target_slot: Optional[int] = None,
    actor_hero: Optional[int] = None,
    target_hero: Optional[int] = None,
    x: Optional[int] = None,
    y: Optional[int] = None,
    valor: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
):
    tipo = (tipo or "event")[:32]
    valor = _trim_valor(valor)
    ev_hash = build_event_hash(id_local, t_sec, tipo, actor_slot, target_slot, actor_hero, target_hero, x, y, valor)
    details_s = safe_json(details) if details else None

    # Si ya existe, actualiza details_json/valor y campos core por si cambian (no debería, pero ok)
    cur.execute("""
        INSERT INTO eventos_partida
          (match_id, t_seg, tipo, actor_slot, target_slot, actor_hero_id, target_hero_id, x, y, valor, details_json, event_hash)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
          details_json = VALUES(details_json),
          valor = VALUES(valor),
          actor_slot = VALUES(actor_slot),
          target_slot = VALUES(target_slot),
          actor_hero_id = VALUES(actor_hero_id),
          target_hero_id = VALUES(target_hero_id),
          x = VALUES(x),
          y = VALUES(y)
    """, (
        id_local, t_sec, tipo, actor_slot, target_slot, actor_hero, target_hero, x, y, valor, details_s, ev_hash
    ))

# ---------------- Snapshots UPSERT ----------------
def insert_snapshots_batch(cur, rows: List[Tuple[int, int, str, int, Optional[int]]]):
    if not rows:
        return
    cur.executemany("""
        INSERT INTO snapshots_partida (match_id, t_seg, metric, slot, value)
        VALUES (%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE value=VALUES(value)
    """, rows)

# ---------------- Persist blocks ----------------
def insert_objectives(cur, id_local: int, data: Dict[str, Any]):
    for obj in data.get("objectives") or []:
        upsert_event(
            cur,
            id_local=id_local,
            t_sec=norm_int(obj.get("time")),
            tipo=(obj.get("type") or "objective"),
            actor_slot=norm_int(obj.get("slot")),
            x=norm_int(obj.get("x")),
            y=norm_int(obj.get("y")),
            valor=str(obj.get("key")) if obj.get("key") not in INVALID else None,
            details=obj,
        )

def insert_teamfights(cur, id_local: int, data: Dict[str, Any]):
    tfs = ((data.get("analysis") or {}).get("teamfights")) or []
    for tf in tfs:
        start = norm_int(tf.get("start"))
        end = norm_int(tf.get("end"))
        duration = (end - start) if (start is not None and end is not None) else None
        upsert_event(
            cur,
            id_local=id_local,
            t_sec=start,
            tipo="TEAMFIGHT",
            x=norm_int(tf.get("x")),
            y=norm_int(tf.get("y")),
            valor=f"deaths:{len(tf.get('deaths') or [])};dur:{duration}" if duration is not None else f"deaths:{len(tf.get('deaths') or [])}",
            details={"start": start, "end": end, "duration": duration, "deaths": tf.get("deaths")},
        )

def _guess_time(ev: Any) -> Optional[int]:
    if not isinstance(ev, dict):
        return None
    for k in ("time", "timeSeconds", "t", "gameTime", "second"):
        if k in ev:
            return norm_int(ev.get(k))
    return None

def insert_kills_buybacks(cur, id_local: int, data: Dict[str, Any]):
    for p in data.get("players") or []:
        slot = norm_int(p.get("playerSlot"))
        hero = norm_int(p.get("heroId"))
        stats = p.get("stats") or {}

        for ev in (stats.get("killEvents") or []):
            target_hero = norm_int(ev.get("target"))
            upsert_event(
                cur, id_local,
                t_sec=_guess_time(ev),
                tipo="kill_event",
                actor_slot=slot,
                actor_hero=hero,
                target_hero=target_hero,
                details=ev,
            )

        for ev in (stats.get("deathEvents") or []):
            upsert_event(
                cur, id_local,
                t_sec=_guess_time(ev),
                tipo="death_event",
                actor_slot=slot,
                actor_hero=hero,
                valor=None,
                details=ev,
            )

        for ev in (stats.get("assistEvents") or []):
            upsert_event(
                cur, id_local,
                t_sec=_guess_time(ev),
                tipo="assist_event",
                actor_slot=slot,
                actor_hero=hero,
                valor=None,
                details=ev,
            )


def insert_winprob(cur, id_local: int, data: Dict[str, Any]):
    # winRates y predictedWinRates son arrays/objetos; no sabemos la forma exacta
    # así que guardamos cada punto como evento “winrate”
    for series_name in ("winRates", "predictedWinRates"):
        series = data.get(series_name) or []
        if not isinstance(series, list):
            # si viene como objeto, guárdalo 1 vez
            upsert_event(cur, id_local, t_sec=None, tipo=series_name, valor=None, details=series)
            continue

        for i, wp in enumerate(series):
            # intentamos sacar tiempo si existe; si no, lo dejamos None
            t = norm_int(wp.get("time")) if isinstance(wp, dict) else None
            upsert_event(
                cur, id_local,
                t_sec=t,
                tipo=series_name,
                valor=None,
                details=wp if isinstance(wp, dict) else {"idx": i, "value": wp}
            )


def insert_snapshots(cur, id_local: int, data: Dict[str, Any]):
    batch: List[Tuple[int, int, str, int, Optional[int]]] = []

    # 1) per-player
    for p in data.get("players") or []:
        slot = norm_int(p.get("playerSlot"))
        if slot is None:
            continue
        stats = p.get("stats") or {}

        for i, val in enumerate(stats.get("networthPerMinute") or []):
            batch.append((id_local, i * 60, "networth", slot, norm_int(val)))

        for i, val in enumerate(stats.get("experiencePerMinute") or []):
            batch.append((id_local, i * 60, "xp", slot, norm_int(val)))

    # 2) team leads (slot=-1)
    for i, val in enumerate(data.get("radiantNetworthLeads") or []):
        batch.append((id_local, i * 60, "networth_lead", -1, norm_int(val)))

    for i, val in enumerate(data.get("radiantExperienceLeads") or []):
        batch.append((id_local, i * 60, "xp_lead", -1, norm_int(val)))

    # 3) kills timeline (slot=-1)
    for i, val in enumerate(data.get("radiantKills") or []):
        batch.append((id_local, i * 60, "radiant_kills", -1, norm_int(val)))

    for i, val in enumerate(data.get("direKills") or []):
        batch.append((id_local, i * 60, "dire_kills", -1, norm_int(val)))

    insert_snapshots_batch(cur, batch)
    print("DEBUG snapshots batch:", len(batch))


def insert_tower_deaths(cur, id_local: int, data: Dict[str, Any]):
    for ev in data.get("towerDeaths") or []:
        upsert_event(cur, id_local, t_sec=_guess_time(ev), tipo="tower_death", details=ev)

def insert_chat_events(cur, id_local: int, data: Dict[str, Any]):
    for ev in data.get("chatEvents") or []:
        upsert_event(cur, id_local, t_sec=_guess_time(ev), tipo="chat_event", details=ev)

def upsert_match_core(cur, id_local: int, mid_dota: int, data: dict):
    start_epoch = data.get("startDateTime")
    start_dt = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(start_epoch)) if start_epoch else None

    cur.execute("""
        INSERT INTO match_core (
            match_id, match_id_dota,
            duration_seconds, start_time_utc,
            did_radiant_win, game_mode, lobby_type,
            region_id, cluster_id,
            league_id, league_name,
            radiant_team_id, radiant_team_name,
            dire_team_id, dire_team_name
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            duration_seconds = VALUES(duration_seconds),
            start_time_utc = VALUES(start_time_utc),
            did_radiant_win = VALUES(did_radiant_win)
    """, (
        id_local,
        mid_dota,
        data.get("durationSeconds"),
        start_dt,
        1 if data.get("didRadiantWin") else 0,
        data.get("gameMode"),
        data.get("lobbyType"),
        data.get("regionId"),
        data.get("clusterId"),
        (data.get("league") or {}).get("id"),
        (data.get("league") or {}).get("name"),
        (data.get("radiantTeam") or {}).get("id"),
        (data.get("radiantTeam") or {}).get("name"),
        (data.get("direTeam") or {}).get("id"),
        (data.get("direTeam") or {}).get("name"),
    ))

def insert_match_players(cur, id_local: int, data: dict):
    for p in data.get("players") or []:
        cur.execute("""
            INSERT INTO match_players (
                match_id, player_slot, hero_id, is_radiant,
                kills, deaths, assists,
                networth, hero_damage, tower_damage, level,
                item0_id, item1_id, item2_id, item3_id, item4_id, item5_id
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                kills = VALUES(kills),
                deaths = VALUES(deaths),
                assists = VALUES(assists),
                networth = VALUES(networth)
        """, (
            id_local,
            p.get("playerSlot"),
            p.get("heroId"),
            1 if p.get("isRadiant") else 0,
            p.get("kills"),
            p.get("deaths"),
            p.get("assists"),
            p.get("networth"),
            p.get("heroDamage"),
            p.get("towerDamage"),
            p.get("level"),
            p.get("item0Id"),
            p.get("item1Id"),
            p.get("item2Id"),
            p.get("item3Id"),
            p.get("item4Id"),
            p.get("item5Id"),
        ))


# ---------------- Main ----------------
def process_match(conn, id_local: int, mid_dota: int):
    print(f"--- 🎮 Procesando match_id_dota={mid_dota} (id_partida={id_local}) ---")

    data = fetch_stratz_match(mid_dota, args.stratz_key)
    p0 = (data.get("players") or [None])[0]
    if p0:
        s0 = (p0.get("stats") or {})
        print("DEBUG len networthPerMinute:", len(s0.get("networthPerMinute") or []))
        print("DEBUG len experiencePerMinute:", len(s0.get("experiencePerMinute") or []))

    print("DEBUG types:",
          "chatEvents", type(data.get("chatEvents")).__name__,
          "towerDeaths", type(data.get("towerDeaths")).__name__,
          "winRates", type(data.get("winRates")).__name__,
          "nwLeads", type(data.get("radiantNetworthLeads")).__name__)

    print("DEBUG raw_json bytes:", len(json.dumps(data, ensure_ascii=False)))
    print("DEBUG chatEvents:", data.get("chatEvents"))
    print("DEBUG towerDeaths:", data.get("towerDeaths"))
    print("DEBUG radiantNetworthLeads:", data.get("radiantNetworthLeads"))
    print("DEBUG winRates:", data.get("winRates"))
    print("DEBUG p0.stats keys:", list(((data.get("players") or [{}])[0].get("stats") or {}).keys()))

    # ================= DEBUG =================
    print("DEBUG keys match:", list(data.keys()))
    print("DEBUG winRates sample:", (data.get("winRates") or [])[:1])
    p0 = (data.get("players") or [None])[0]
    if p0:
        print("DEBUG killEvents sample:", ((p0.get("stats") or {}).get("killEvents") or [])[:1])
    # =========================================

    with conn.cursor() as cur:
        if args.reprocesar:
            wipe_child_tables(conn, id_local)

        upsert_raw_json(cur, id_local, mid_dota, data)
        upsert_match_core(cur, id_local, mid_dota, data)
        insert_match_players(cur, id_local, data)
        # 0) Meta
        upsert_partidas_meta_from_stratz(cur, id_local, data, mid_dota)

        # 1) Eventos técnicos (DB-dedupe)
        #insert_objectives(cur, id_local, data)
        #insert_teamfights(cur, id_local, data)
        insert_chat_events(cur, id_local, data)
        insert_tower_deaths(cur, id_local, data)
        insert_kills_buybacks(cur, id_local, data)
        insert_winprob(cur, id_local, data)

        # 3) Snapshots (UPSERT)
        print("DEBUG lens:",
              "chat", len(data.get("chatEvents") or []),
              "tower", len(data.get("towerDeaths") or []),
              "winRates", len(data.get("winRates") or []),
              "nwLeads", len(data.get("radiantNetworthLeads") or []),
              "rKills", len(data.get("radiantKills") or []))
        insert_snapshots(cur, id_local, data)

    print("✅ OK")

def main():
    if not args.stratz_key:
        print("⚠️ Falta STRATZ_API_KEY (env) o --stratz-key.")
        return

    conn = mysql.connector.connect(**DB)
    try:
        
        targets = fetch_targets(conn)

        if not targets:
            print("No hay partidas para enriquecer.")
            return

        print(f"Encontradas {len(targets)} partidas.")
        for i, row in enumerate(targets, 1):
            id_local = int(row["id_partida"])
            mid_dota = int(row["match_id_dota"])
            print(f"[{i}/{len(targets)}] id_partida={id_local} match_id_dota={mid_dota}")

            try:
                process_match(conn, id_local, mid_dota)
            except requests.HTTPError as e:
                code = e.response.status_code if e.response else "?"
                print(f"  ❌ HTTP {code} (id_partida={id_local} mid={mid_dota})")
            except MySQLError as e:
                print(f"  ❌ MySQL (id_partida={id_local} mid={mid_dota}): {e}")
            except Exception as e:
                print(f"  ❌ Error (id_partida={id_local} mid={mid_dota}): {e}")

            time.sleep(args.delay)
    finally:
        if conn and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    main()
