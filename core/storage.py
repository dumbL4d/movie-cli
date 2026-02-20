import json
from pathlib import Path

CACHE = Path.home() / ".movie_cli_cache.json"

def save(data):
    CACHE.write_text(json.dumps(data))

def load():
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    return {}
