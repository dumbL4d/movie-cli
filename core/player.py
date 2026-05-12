import os
import subprocess
import time
import platform

def play(stream_url, subtitles=None):
    cmd = [
        "mpv",
        "--force-window=immediate", 
        "--http-header-fields=Referer: https://vidking.net/"
    ]

    if subtitles:
        for sub_url in subtitles:
            if sub_url.startswith("http://") or sub_url.startswith("https://") or os.path.isfile(sub_url):
                cmd.append(f"--sub-file={sub_url}")
            
    cmd.append(stream_url)

    process = subprocess.Popen(cmd)

    if platform.system() == "Darwin":
        time.sleep(0.5) 
        try:
            subprocess.run([
                "osascript", "-e", 
                f'tell application "System Events" to set frontmost of the first process whose unix id is {process.pid} to true'
            ])
        except Exception:
            pass

    process.wait()
