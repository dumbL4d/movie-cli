class DemoScraper:
    def search(self, query):
        return [
            {
                "title": query.title(),
                "url": "https://example.com/fake_movie_page"
            }
        ]

    def get_streams(self, movie_url):
        return [
            {
                "server": "DemoServer",
                "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"
            }
        ]
