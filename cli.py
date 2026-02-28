import argparse
from rich.console import Console
from rich.table import Table
from rich.prompt import IntPrompt, Prompt
from rich.panel import Panel

from core.scrapers.cineby_api import CinebyAPIScraper
from core.resolver import resolve
from core.player import play
from core.downloader import download
from core import storage

console = Console()

def run():
    parser = argparse.ArgumentParser(prog="movie")
    parser.add_argument("query", nargs="*", help="Movie or Show name")
    parser.add_argument("-d", "--download", action="store_true", help="Download content")
    parser.add_argument("-w", "--watchlist", action="store_true", help="View your watchlist")
    parser.add_argument("-H", "--history", action="store_true", help="View watched history") # <--- NEW FLAG
    args = parser.parse_args()
    
    scraper = CinebyAPIScraper()

    # --- HISTORY MODE ---
    if args.history:
        saved_items = storage.load()
        # Filter for watched items only
        watched_items = [v for v in saved_items.values() if v.get("status") == "watched"]
        
        if not watched_items:
            console.print("[bold yellow]You haven't marked anything as watched yet![/bold yellow]")
            return
            
        table = Table(title="Watched History ✅", title_style="bold green", expand=True)
        table.add_column("#", justify="right", style="cyan", no_wrap=True)
        table.add_column("Type", style="green")
        table.add_column("Title", style="magenta")
        
        for i, item in enumerate(watched_items):
            type_tag = "📺 TV" if item['media_type'] == 'tv' else "🎬 Movie"
            table.add_row(str(i + 1), type_tag, item['display_name'])
            
        console.print(table)
        return # Just display and exit

    # --- WATCHLIST MODE ---
    elif args.watchlist:
        saved_items = storage.load()
        
        # Filter to ONLY show items that are NOT watched
        active_keys = [k for k, v in saved_items.items() if v.get("status", "watchlist") == "watchlist"]
        
        if not active_keys:
            console.print("[bold yellow]Your watchlist is empty! Go find some movies.[/bold yellow]")
            return
            
        table = Table(title="Your Watchlist 🍿", title_style="bold yellow", expand=True)
        table.add_column("#", justify="right", style="cyan", no_wrap=True)
        table.add_column("Type", style="green")
        table.add_column("Title", style="magenta")
        
        for i, key in enumerate(active_keys):
            item = saved_items[key]
            type_tag = "📺 TV" if item['media_type'] == 'tv' else "🎬 Movie"
            table.add_row(str(i + 1), type_tag, item['display_name'])
            
        console.print(table)
        
        try:
            valid_choices = [str(i) for i in range(len(active_keys) + 1)]
            choice_idx = IntPrompt.ask("\nSelect a number (0 to exit)", choices=valid_choices) - 1
            if choice_idx < 0: return
            
            selected_key = active_keys[choice_idx]
            media = saved_items[selected_key]
            season = media.get('season')
            episode = media.get('episode')
            title_display = media['display_name']
            
        except (ValueError, IndexError):
            console.print("[bold red]Invalid selection.[/bold red]")
            return
            
        # The new Watchlist Action Menu!
        console.print(f"\n[bold green]Selected:[/bold green] {title_display}")
        action = Prompt.ask("Action", choices=["play", "download", "mark watched"], default="play")
        
        if action == "mark watched":
            # Flip the status and save!
            saved_items[selected_key]["status"] = "watched"
            storage.save(saved_items)
            console.print(f"[bold green]Marked '{title_display}' as Watched! ✅[/bold green]")
            return
            
        if action == "download":
            args.download = True

    # --- SEARCH MODE ---
    elif args.query:
        query_str = " ".join(args.query)
        
        with console.status(f"[bold cyan]Searching TMDB for '{query_str}'...", spinner="dots"):
            results = scraper.search(query_str)

        if not results:
            console.print("[bold red]No results found[/bold red]")
            return

        table = Table(title="Search Results", title_style="bold magenta", expand=True)
        table.add_column("#", justify="right", style="cyan", no_wrap=True)
        table.add_column("Type", style="green")
        table.add_column("Title", style="magenta")
        table.add_column("Year", style="yellow")

        for i, item in enumerate(results):
            type_tag = "📺 TV" if item['media_type'] == 'tv' else "🎬 Movie"
            table.add_row(str(i + 1), type_tag, item['title'], item['year'])

        console.print(table)

        try:
            valid_choices = [str(i) for i in range(len(results) + 1)]
            choice_idx = IntPrompt.ask("\nSelect a number (0 to exit)", choices=valid_choices) - 1
            if choice_idx < 0: return
            media = results[choice_idx]
        except (ValueError, IndexError):
            console.print("[bold red]Invalid selection.[/bold red]")
            return

        season = None
        episode = None

        if media['media_type'] == 'tv':
            with console.status(f"[bold cyan]Fetching details for '{media['title']}'...", spinner="bouncingBar"):
                details = scraper.get_tv_details(media['tmdb_id'])
                
            if details:
                console.print(Panel(f"Found [bold green]{details.get('number_of_seasons')}[/bold green] Seasons.", title="TV Details", border_style="blue"))
                
            try:
                season = IntPrompt.ask("Enter Season Number")
                episode = IntPrompt.ask("Enter Episode Number")
            except KeyboardInterrupt:
                return

        title_display = f"{media['title']}"
        if season:
            title_display += f" S{season}E{episode}"

        console.print(f"\n[bold green]Selected:[/bold green] {title_display}")
        action = Prompt.ask("Action", choices=["play", "download", "watchlist"], default="play")

        if action == "watchlist":
            watchlist_data = storage.load()
            unique_key = f"{media['tmdb_id']}_{season}_{episode}"
            
            watchlist_data[unique_key] = {
                "title": media['title'],
                "year": media['year'],
                "media_type": media['media_type'],
                "tmdb_id": media['tmdb_id'],
                "season": season,
                "episode": episode,
                "display_name": title_display,
                "status": "watchlist" # <--- Automatically labels as watchlist initially
            }
            storage.save(watchlist_data)
            console.print(f"[bold yellow]Added '{title_display}' to Watchlist![/bold yellow] 🍿")
            return
            
        if action == "download":
            args.download = True

    else:
        parser.print_help()
        return

    # --- RESOLVE AND EXECUTE ---
    stream_page = scraper.get_stream_url(media, season, episode)
    
    with console.status(f"[bold yellow]Resolving stream with Playwright...[/bold yellow]", spinner="aesthetic"):
        real_data = resolve(stream_page)

    if not real_data or not real_data.get("stream"):
        console.print("[bold red]Failed to resolve stream[/bold red]")
        return

    real_stream = real_data["stream"]
    subtitles = real_data.get("subtitles", [])

    if subtitles:
        console.print(f"[bold cyan]Found {len(subtitles)} subtitle track(s)![/bold cyan]")

    if args.download:
        console.print(f"[bold green]Starting download for:[/bold green] {title_display}")
        download(real_stream, title_display)
    else:
        console.print(f"[bold green]Starting player for:[/bold green] {title_display}")
        play(real_stream, subtitles)

if __name__ == "__main__":
    run()
