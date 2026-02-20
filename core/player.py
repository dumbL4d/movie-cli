'''import subprocess

def play(stream_url):
    # We pass the Referer header to mpv so the server accepts the connection
    subprocess.call([
        "mpv",
        "--http-header-fields=Referer: https://vidking.net/",
        stream_url
    ])
    '''
'''
import subprocess
import time
import platform

def play(stream_url):
    # 1. Prepare the command
    cmd = [
        "mpv",
        "--force-window=immediate",  # Create the window immediately
        "--http-header-fields=Referer: https://vidking.net/",
        stream_url
    ]

    # 2. Launch mpv without blocking the script (Popen instead of call)
    process = subprocess.Popen(cmd)

    # 3. macOS Specific: Force Focus
    if platform.system() == "Darwin":
        # Give mpv a split second to spawn its window
        time.sleep(0.5) 
        try:
            # We use AppleScript to tell System Events: 
            # "Find the process with this specific PID and pull it to the front"
            # This bypasses the OS restriction on focus stealing.
            subprocess.run([
                "osascript", "-e", 
                f'tell application "System Events" to set frontmost of the first process whose unix id is {process.pid} to true'
            ])
        except Exception as e:
            print(f"[!] Could not force focus: {e}")

    # 4. Wait for the movie to finish before exiting Python
    process.wait()
'''

import subprocess
import time
import platform

def play(stream_url, subtitles=None):
    cmd = [
        "mpv",
        "--force-window=immediate", 
        "--http-header-fields=Referer: https://vidking.net/"
    ]

    # Inject all scraped subtitles into mpv
    if subtitles:
        for sub_url in subtitles:
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
