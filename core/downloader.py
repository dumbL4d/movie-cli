import subprocess
import re

def download(stream_url, title):
    # 1. Sanitize the filename to prevent errors (remove / : * ? " < > |)
    safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
    filename = f"{safe_title}.mp4"

    print(f"[*] Initializing download for: {filename}")
    print("[*] Press Ctrl+C to cancel.")

    # 2. Build the command
    # We MUST pass the Referer header, or the download will be forbidden (403)
    cmd = [
        "yt-dlp",
        "--add-header", "Referer:https://vidking.net/",
        "-o", filename,  # Output filename
        stream_url
    ]

    # 3. Execute
    try:
        # We use call() so yt-dlp takes over the terminal to show its progress bar
        subprocess.call(cmd)
        print(f"\n[*] Download finished: {filename}")
    except KeyboardInterrupt:
        print("\n[!] Download cancelled by user.")
    except Exception as e:
        print(f"[!] Download failed: {e}")
