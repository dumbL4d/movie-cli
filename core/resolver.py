from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
import re

SUB_EXTENSIONS = [".vtt", ".srt", ".ass", ".ssa"]


def resolve(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        found_stream = None
        found_subtitles = []
        seen_urls = set()

        def handle_request(request):
            nonlocal found_stream
            req_url = request.url
            if ".m3u8" in req_url:
                if "master" in req_url:
                    found_stream = req_url
                elif not found_stream:
                    found_stream = req_url
            if any(ext in req_url for ext in SUB_EXTENSIONS):
                if req_url not in seen_urls:
                    seen_urls.add(req_url)
                    found_subtitles.append(req_url)

        def handle_response(response):
            url = response.url
            ct = response.headers.get("content-type", "")
            if any(st in ct for st in ["text/vtt", "application/x-subrip", "text/srt"]):
                if url not in seen_urls:
                    seen_urls.add(url)
                    found_subtitles.append(url)
            if ".m3u8" in url:
                try:
                    body = response.body().decode("utf-8", errors="replace")
                    for match in re.finditer(
                        r'#EXT-X-MEDIA:TYPE=SUBTITLES[^#]*URI="([^"]+)"',
                        body, re.DOTALL
                    ):
                        sub_url = urljoin(url, match.group(1))
                        if sub_url not in seen_urls:
                            seen_urls.add(sub_url)
                            found_subtitles.append(sub_url)
                except Exception:
                    pass

        page.on("request", handle_request)
        page.on("response", handle_response)

        try:
            page.goto(url, wait_until="networkidle")
            page.wait_for_timeout(5000)
        except Exception:
            pass

        browser.close()

        return {"stream": found_stream, "subtitles": found_subtitles}
