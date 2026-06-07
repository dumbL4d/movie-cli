import subprocess
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse, unquote

def download(stream_url, title, subtitles=None, output_dir=None):
    safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
    filename = f"{safe_title}.mp4"

    if output_dir:
        output_path = Path(output_dir) / filename
    else:
        output_path = Path(filename)

    print(f"[*] Initializing download for: {filename}")
    print("[*] Press Ctrl+C to cancel.")

    cmd = [
        "yt-dlp",
        "--add-header", "Referer:https://vidking.net/",
        "-o", str(output_path),
        stream_url
    ]

    try:
        subprocess.call(cmd)
        print(f"\n[*] Download finished: {filename}")
    except KeyboardInterrupt:
        print("\n[!] Download cancelled by user.")
        return
    except Exception as e:
        print(f"[!] Download failed: {e}")
        return

    if not subtitles:
        return

    base = output_path.parent
    stem = output_path.stem
    dl_dir = base / f"{stem}_subtitles"
    dl_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] Downloading {len(subtitles)} subtitle track(s)...")
    for i, sub in enumerate(subtitles):
        sub_url = sub if isinstance(sub, str) else sub.get("url", sub.get("file", ""))
        if not sub_url:
            continue

        if sub_url.startswith("http://") or sub_url.startswith("https://"):
            parsed = urlparse(sub_url)
            ext = Path(unquote(parsed.path)).suffix or ".srt"
            out = dl_dir / f"{stem}_sub{i}{ext}"
            try:
                subprocess.run(
                    ["curl", "-sS", "-o", str(out), "--max-time", "30", sub_url],
                    check=True, timeout=35
                )
                print(f"  [+] {out.name}")
            except Exception:
                print(f"  [!] Failed: {sub_url}")
        else:
            src = Path(sub_url)
            if src.exists():
                ext = src.suffix or ".srt"
                dst = dl_dir / f"{stem}_sub{i}{ext}"
                shutil.copy2(src, dst)
                print(f"  [+] {dst.name}")
            else:
                print(f"  [!] Not found: {sub_url}")

    print(f"[*] Subtitles saved to: {dl_dir}")


def download_series(scraper, series_title, tmdb_id, seasons=None):
    from core.resolver import resolve as _resolve
    from core.subtitles import fetch as fetch_external_subtitles

    print(f"[*] Fetching details for '{series_title}'...")
    try:
        details = scraper.get_tv_details(tmdb_id)
    except ConnectionError as e:
        print(f"[!] {e}")
        return

    total_seasons = details.get('number_of_seasons', 0)
    if seasons is None:
        seasons = range(1, total_seasons + 1)

    safe_series = re.sub(r'[\\/*?:"<>|]', "", series_title)

    for season_num in seasons:
        print(f"\n{'='*60}")
        print(f"[*] Fetching Season {season_num} details...")
        try:
            season_details = scraper.get_season_details(tmdb_id, season_num)
        except ConnectionError as e:
            print(f"[!] {e}")
            continue

        episodes = season_details.get('episodes', [])
        if not episodes:
            print(f"[!] No episodes found for Season {season_num}, skipping...")
            continue

        season_dir = f"Season {season_num:02d}"
        output_dir = Path(safe_series) / season_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        for ep in episodes:
            episode_num = ep['episode_number']
            title_display = f"{series_title} S{season_num:02d}E{episode_num:02d}"

            print(f"\n[▶] Processing: {title_display}")

            stream_page = scraper.get_stream_url(
                {"tmdb_id": tmdb_id, "media_type": "tv"},
                season_num, episode_num
            )

            real_data = _resolve(stream_page)

            if not real_data or not real_data.get("stream"):
                print(f"[!] Failed to resolve stream for {title_display}, skipping...")
                continue

            real_stream = real_data["stream"]
            subtitles = real_data.get("subtitles", [])

            if not subtitles:
                external = fetch_external_subtitles(
                    tmdb_id, "tv", season_num, episode_num, title=series_title
                )
                if external:
                    subtitles = external

            download(real_stream, title_display, subtitles=subtitles, output_dir=output_dir)

    print(f"\n{'='*60}")
    print(f"[✓] Series download complete: {series_title}")
