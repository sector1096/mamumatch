import json
import re
import subprocess
from datetime import datetime

import requests

from app.core.config import settings


def normalize_duration_iso8601(raw: str | None) -> int | None:
    if not raw:
        return None
    pattern = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")
    m = pattern.fullmatch(raw)
    if not m:
        return None
    h = int(m.group(1) or 0)
    m_ = int(m.group(2) or 0)
    s = int(m.group(3) or 0)
    return h * 3600 + m_ * 60 + s


def guess_language(text: str) -> str | None:
    lower = text.lower()
    if any(k in lower for k in ["espanol", "latam", "spanish", "cast"]):
        return "es"
    if any(k in lower for k in ["english", "eng", "na dota"]):
        return "en"
    if any(k in lower for k in ["pt", "portuguese", "br"]):
        return "pt"
    if any(k in lower for k in ["ru", "russian"]):
        return "ru"
    return None


def build_query(equipos: str | None, evento: str | None, anio: int | None) -> str:
    chunks = [equipos or "", evento or "", str(anio) if anio else "", "dota 2"]
    query = " ".join(part.strip() for part in chunks if part and part.strip())
    return query.strip() or "dota 2 full match"


def search_youtube_api(query: str, limit: int = 10) -> list[dict]:
    key = settings.youtube_api_key.strip()
    if not key:
        return []

    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "maxResults": min(limit, 25),
        "type": "video",
        "key": key,
        "order": "relevance",
    }
    resp = requests.get(search_url, params=params, timeout=20)
    resp.raise_for_status()
    items = resp.json().get("items", [])
    video_ids = [item.get("id", {}).get("videoId") for item in items if item.get("id", {}).get("videoId")]
    if not video_ids:
        return []

    details_url = "https://www.googleapis.com/youtube/v3/videos"
    detail_params = {
        "part": "contentDetails",
        "id": ",".join(video_ids),
        "key": key,
    }
    details_resp = requests.get(details_url, params=detail_params, timeout=20)
    details_resp.raise_for_status()
    duration_map = {
        item["id"]: normalize_duration_iso8601(item.get("contentDetails", {}).get("duration"))
        for item in details_resp.json().get("items", [])
    }

    out = []
    for item in items:
        snippet = item.get("snippet", {})
        video_id = item.get("id", {}).get("videoId")
        if not video_id:
            continue
        title = snippet.get("title") or ""
        channel = snippet.get("channelTitle") or ""
        out.append(
            {
                "title": title,
                "channel": channel,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "duration_seconds": duration_map.get(video_id),
                "language_guess": guess_language(f"{title} {channel}"),
            }
        )
    return out


def search_ytdlp(query: str, limit: int = 10) -> list[dict]:
    cmd = [
        settings.yt_dlp_path,
        f"ytsearch{limit}:{query}",
        "--dump-json",
        "--skip-download",
        "--flat-playlist",
        "--no-warnings",
        "--ignore-config",
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        return []

    items = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        title = obj.get("title") or ""
        channel = obj.get("uploader") or obj.get("channel") or ""
        url = obj.get("url")
        if url and not url.startswith("http"):
            url = f"https://www.youtube.com/watch?v={url}"
        items.append(
            {
                "title": title,
                "channel": channel,
                "url": url,
                "duration_seconds": obj.get("duration"),
                "language_guess": guess_language(f"{title} {channel}"),
            }
        )
    return items


def find_video_candidates(equipos: str | None, evento: str | None, anio: int | None, limit: int = 10) -> dict:
    query = build_query(equipos, evento, anio)
    items = search_youtube_api(query, limit=limit)
    if not items:
        items = search_ytdlp(query, limit=limit)
    return {"query": query, "items": items[:limit], "generated_at": datetime.utcnow().isoformat()}