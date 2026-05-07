import subprocess
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse, unquote

def download(stream_url, title, subtitles=None):
    safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
    filename = f"{safe_title}.mp4"

    print(f"[*] Initializing download for: {filename}")
    print("[*] Press Ctrl+C to cancel.")

    cmd = [
        "yt-dlp",
        "--add-header", "Referer:https://vidking.net/",
        "-o", filename,
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

    base = Path(filename).parent
    stem = Path(filename).stem
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
