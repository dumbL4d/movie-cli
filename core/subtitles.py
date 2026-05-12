import os
import json
import subprocess
import time
from pathlib import Path
from urllib.parse import urlencode

BASE = "https://api.opensubtitles.com/api/v1"
CACHE = Path.home() / ".movie_cli_subs"
USER_AGENT = "MovieCLI v1.0"


def _curl(method, url, headers=None, data=None, timeout=15):
    cmd = ["curl", "-sSL", "--max-time", str(timeout), "-X", method]
    if headers:
        for k, v in headers.items():
            cmd.extend(["-H", f"{k}: {v}"])
    if data:
        cmd.extend(["-d", data])
    cmd.append(url)
    for i in range(5):
        result = subprocess.run(cmd, capture_output=True, timeout=timeout + 5)
        if result.returncode == 0 and result.stdout:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                pass
        if i < 4:
            time.sleep(0.5)
    return None


def _curl_raw(url, headers=None, timeout=30):
    cmd = ["curl", "-sSL", "--max-time", str(timeout)]
    if headers:
        for k, v in headers.items():
            cmd.extend(["-H", f"{k}: {v}"])
    cmd.append(url)
    for i in range(3):
        result = subprocess.run(cmd, capture_output=True, timeout=timeout + 5)
        if result.returncode == 0 and result.stdout:
            return result.stdout
        if i < 2:
            time.sleep(0.5)
    return None


def _os_fetch(tmdb_id, media_type, season, episode, lang):
    api_key = os.getenv("OPENSUBTITLES_API_KEY")
    if not api_key:
        return []

    headers = {"Api-Key": api_key, "User-Agent": USER_AGENT}
    params = {"tmdb_id": tmdb_id, "type": media_type, "languages": lang, "limit": 20}
    if media_type == "tv" and season is not None:
        params["season_number"] = season
        params["episode_number"] = episode

    qs = urlencode({k: v for k, v in params.items() if v is not None})
    data = _curl("GET", f"{BASE}/subtitles?{qs}", headers=headers)
    if not data:
        return []

    entries = data.get("data", [])
    if not entries:
        return []

    def reliability(entry):
        attrs = entry.get("attributes", {})
        dc = attrs.get("download_count", 0) or 0
        rating = attrs.get("rating", 0) or 0
        votes = attrs.get("votes", 0) or 0
        return dc * 100 + rating * votes

    entries.sort(key=reliability, reverse=True)

    downloaded = []
    for entry in entries:
        if len(downloaded) >= 5:
            break
        try:
            files = entry.get("attributes", {}).get("files", [])
            if not files:
                continue
            file_id = files[0]["file_id"]
            dl = _curl("POST", f"{BASE}/download", headers={**headers, "Content-Type": "application/json"}, data=json.dumps({"file_id": file_id}))
            if not dl:
                continue
            content = _curl_raw(dl["link"], headers=headers)
            if not content:
                continue

            CACHE.mkdir(parents=True, exist_ok=True)
            local = CACHE / f"os_{file_id}.srt"
            local.write_bytes(content)
            downloaded.append(str(local))
        except Exception:
            continue

    return downloaded


def fetch(tmdb_id, media_type="movie", season=None, episode=None, lang="en", title=None, year=None):
    return _os_fetch(tmdb_id, media_type, season, episode, lang)
