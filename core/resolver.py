'''
from playwright.sync_api import sync_playwright
import time

def resolve(url):
    print(f"[*] Launching headless browser to resolve: {url}")
    
    with sync_playwright() as p:
        # Launch a headless Chromium browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # This variable will hold our found stream
        found_stream = None

        # 1. Listen to all network requests made by the page
        def handle_request(request):
            nonlocal found_stream
            # We look for the master playlist file (usually .m3u8)
            if ".m3u8" in request.url and "master" in request.url:
                found_stream = request.url
            # Fallback: any m3u8 if master isn't found
            elif ".m3u8" in request.url and not found_stream:
                found_stream = request.url

        page.on("request", handle_request)

        # 2. Go to the page and wait for the video to load
        try:
            page.goto(url, wait_until="networkidle")
            # Sometimes we need to wait a few extra seconds for the player to initialize
            page.wait_for_timeout(5000) 
        except Exception as e:
            print(f"[!] Browser error: {e}")

        browser.close()

        if found_stream:
            print(f"[*] Found Stream: {found_stream}")
            return found_stream
        else:
            print("[!] Failed to detect .m3u8 stream in network traffic.")
            return None
'''

from playwright.sync_api import sync_playwright

def resolve(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        found_stream = None
        found_subtitles = [] # We will store our subtitle URLs here

        def handle_request(request):
            nonlocal found_stream
            
            # 1. Look for the video stream
            if ".m3u8" in request.url and "master" in request.url:
                found_stream = request.url
            elif ".m3u8" in request.url and not found_stream:
                found_stream = request.url
                
            # 2. Look for subtitles!
            if ".vtt" in request.url or ".srt" in request.url:
                if request.url not in found_subtitles:
                    found_subtitles.append(request.url)

        page.on("request", handle_request)

        try:
            page.goto(url, wait_until="networkidle")
            page.wait_for_timeout(5000) 
        except Exception:
            pass

        browser.close()

        # Return both the stream and any subs we found
        return {
            "stream": found_stream,
            "subtitles": found_subtitles
        }
