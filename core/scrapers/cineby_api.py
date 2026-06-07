import os
import json
import subprocess
import time
from urllib.parse import urlencode

TMDB_BASE = "https://api.themoviedb.org/3"
VIDKING_MOVIE = "https://www.vidking.net/embed/movie/{}"
VIDKING_TV = "https://www.vidking.net/embed/tv/{}/{}/{}"
USER_AGENT = "MovieCLI v1.0"


def _curl(url, params=None, timeout=15):
    key = os.getenv("TMDB_API_KEY")
    if not key:
        raise ConnectionError("TMDB_API_KEY is not set in your .env file")
    if params:
        params["api_key"] = key
    else:
        params = {"api_key": key}
    qs = urlencode(params)
    cmd = ["curl", "-sS", "--max-time", str(timeout), "-H", f"User-Agent: {USER_AGENT}", f"{url}?{qs}"]
    for i in range(3):
        result = subprocess.run(cmd, capture_output=True, timeout=timeout + 5)
        if result.returncode == 0 and result.stdout:
            return json.loads(result.stdout)
        if i < 2:
            time.sleep(1)
    return None


class CinebyAPIScraper:
    def search(self, query):
        print(f"[*] Searching TMDB for: {query}")
        data = _curl(f"{TMDB_BASE}/search/multi", {"query": query})
        if data is None:
            raise ConnectionError("Failed to connect to TMDB. The server may be down or your internet connection is interrupted.")

        results = []
        for m in data.get("results", []):
            if m.get("media_type") not in ["movie", "tv"]:
                continue
            year = m.get("release_date") or m.get("first_air_date") or ""
            title = m.get("title") or m.get("name")
            results.append({
                "title": title,
                "year": year[:4],
                "tmdb_id": m["id"],
                "media_type": m["media_type"],
            })

        return results[:10]

    def get_tv_details(self, tmdb_id):
        data = _curl(f"{TMDB_BASE}/tv/{tmdb_id}")
        if data is None:
            raise ConnectionError("Failed to connect to TMDB. The server may be down or your internet connection is interrupted.")
        return data

    def get_season_details(self, tmdb_id, season_number):
        data = _curl(f"{TMDB_BASE}/tv/{tmdb_id}/season/{season_number}")
        if data is None:
            raise ConnectionError("Failed to connect to TMDB. The server may be down or your internet connection is interrupted.")
        return data

    def get_stream_url(self, media_data, season=None, episode=None):
        if media_data["media_type"] == "movie":
            return VIDKING_MOVIE.format(media_data["tmdb_id"])
        return VIDKING_TV.format(media_data["tmdb_id"], season, episode)
