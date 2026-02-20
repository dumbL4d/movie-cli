import requests
import os

TMDB_KEY = os.getenv("TMDB_API_KEY", "YOUR_API_KEY_HERE")
TMDB_BASE = "https://api.themoviedb.org/3"
VIDKING_MOVIE = "https://www.vidking.net/embed/movie/{}" 
VIDKING_TV = "https://www.vidking.net/embed/tv/{}/{}/{}"

class CinebyAPIScraper:
    def search(self, query):
        print(f"[*] Searching TMDB for: {query}")
        try:
            # Switch to 'multi' to find TV shows AND movies
            r = requests.get(
                f"{TMDB_BASE}/search/multi",
                params={
                    "api_key": TMDB_KEY,
                    "query": query
                },
                timeout=10
            )
            r.raise_for_status()
            data = r.json().get("results", [])

            results = []
            for m in data:
                # Filter out people/actors, keep only content
                if m.get("media_type") not in ["movie", "tv"]:
                    continue

                year = m.get("release_date") or m.get("first_air_date") or ""
                title = m.get("title") or m.get("name")
                
                results.append({
                    "title": title,
                    "year": year[:4],
                    "tmdb_id": m["id"],
                    "media_type": m["media_type"] # 'movie' or 'tv'
                })

            return results[:10]
        except Exception as e:
            print(f"[!] Search error: {e}")
            return []

    def get_tv_details(self, tmdb_id):
        """Fetches the number of seasons and episodes for a show"""
        try:
            r = requests.get(
                f"{TMDB_BASE}/tv/{tmdb_id}",
                params={"api_key": TMDB_KEY},
                timeout=10
            )
            return r.json()
        except:
            return None

    def get_stream_url(self, media_data, season=None, episode=None):
        """Constructs the URL based on type"""
        if media_data["media_type"] == "movie":
            return VIDKING_MOVIE.format(media_data["tmdb_id"])
        
        elif media_data["media_type"] == "tv":
            # Vidking format: /embed/tv/{id}/{season}/{episode}
            return VIDKING_TV.format(media_data["tmdb_id"], season, episode)
