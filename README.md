# 🎬 Movie CLI Pro

A blazing-fast, beautiful terminal UI for searching, streaming, and downloading movies and TV shows directly from your command line. 

> **Note:** This entire project was 100% **vibe coded**. We didn't write massive design docs or overthink the architecture; we just caught a wave of momentum, relied on intuition, and built something awesome. 🌊

## ✨ Features
* **Unified Search:** Instantly query TMDB for both Movies and TV Shows.
* **Smart Resolver:** Uses headless browser automation (Playwright) to sniff out hidden `.m3u8` streams and `.vtt` subtitles dynamically.
* **Beautiful UI:** Powered by `rich` for animated spinners, colorful tables, and interactive terminal menus.
* **Built-in Watchlist & History:** Save shows for later, and mark them as watched to build your personal streaming diary right in your terminal.
* **Data Hoarder Mode:** Pass the `-d` flag to intercept the stream and download it straight to your drive using `yt-dlp`.

## 🛠️ Prerequisites
You need a few external tools installed on your system for the player and downloader to work:
* `mpv` (The media player)
* `yt-dlp` (For resolving and downloading)
* Python 3.8+

## 🚀 Installation & Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/dumbL4d/movie-cli.git
   cd movie-cli

```

2. Install the required Python libraries:
```bash
pip install requests beautifulsoup4 rich playwright

```


3. Install the Playwright browser engine (required for bypassing stream protections):
```bash
playwright install chromium

```



## 🎮 Usage

**Search for a movie or TV show:**

```bash
python main.py the matrix

```

**Open your Watchlist:**

```bash
python main.py -w

```

**View your Watched History:**

```bash
python main.py -H

```

**Force Download Mode directly from search:**

```bash
python main.py interstellar -d
```

## 🔑 Configuration
This CLI uses TMDB to fetch movie and TV show metadata. You will need a free API key from [The Movie Database (TMDB)](https://www.themoviedb.org/).

Once you have your key, set it as an environment variable in your terminal:
```bash
export TMDB_API_KEY="your_api_key_here"
