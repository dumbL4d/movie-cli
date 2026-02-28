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
