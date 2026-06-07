import argparse
from rich.console import Console
from rich.table import Table
from rich.prompt import IntPrompt, Prompt
from rich.panel import Panel

from core.scrapers.cineby_api import CinebyAPIScraper
from core.resolver import resolve
from core.player import play
from core.downloader import download, download_series
from core import storage
from core.subtitles import fetch as fetch_external_subtitles

console = Console()


def show_action_menu(title_display):
    console.print(f"\n[bold green]Selected:[/bold green] {title_display}")
    console.print("  1) Play")
    console.print("  2) Download")
    console.print("  3) Add to Watchlist")
    return IntPrompt.ask("Choose", choices=["1", "2", "3"], default="1")


def parse_seasons(raw):
    if raw.lower() == "all":
        return None
    seasons = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            try:
                start, end = part.split("-", 1)
                seasons.extend(range(int(start.strip()), int(end.strip()) + 1))
            except ValueError:
                console.print(f"[bold red]Invalid range: '{part}'[/bold red]")
                return []
        else:
            try:
                seasons.append(int(part))
            except ValueError:
                console.print(f"[bold red]Invalid season: '{part}'[/bold red]")
                return []
    return seasons


def resolve_and_execute(media, season, episode, title_display, force_download):
    stream_page = media['_scraper'].get_stream_url(media, season, episode)

    with console.status(f"[bold yellow]Resolving stream with Playwright...[/bold yellow]", spinner="aesthetic"):
        real_data = resolve(stream_page)

    if not real_data or not real_data.get("stream"):
        console.print("[bold red]Failed to resolve stream[/bold red]")
        return

    real_stream = real_data["stream"]
    subtitles = real_data.get("subtitles", [])

    if not subtitles:
        with console.status("[bold cyan]Searching for subtitles...", spinner="dots"):
            external = fetch_external_subtitles(
                media['tmdb_id'], media['media_type'], season, episode,
                title=media.get('title'), year=media.get('year')
            )
            if external:
                subtitles = external

    if subtitles:
        console.print(f"[bold cyan]Found {len(subtitles)} subtitle track(s)![/bold cyan]")

    if force_download:
        console.print(f"[bold green]Starting download for:[/bold green] {title_display}")
        download(real_stream, title_display, subtitles=subtitles)
    else:
        console.print(f"[bold green]Starting player for:[/bold green] {title_display}")
        play(real_stream, subtitles)


def handle_history():
    saved_items = storage.load()
    watched_items = [v for v in saved_items.values() if v.get("status") == "watched"]

    if not watched_items:
        console.print("[bold yellow]You haven't marked anything as watched yet![/bold yellow]")
        return

    table = Table(title="Watched History \u2705", title_style="bold green", expand=True)
    table.add_column("#", justify="right", style="cyan", no_wrap=True)
    table.add_column("Type", style="green")
    table.add_column("Title", style="magenta")

    for i, item in enumerate(watched_items):
        type_tag = "\U0001f4fa TV" if item['media_type'] == 'tv' else "\U0001f3ac Movie"
        table.add_row(str(i + 1), type_tag, item['display_name'])

    console.print(table)


def handle_watchlist(scraper):
    saved_items = storage.load()
    active_keys = [k for k, v in saved_items.items() if v.get("status", "watchlist") == "watchlist"]

    if not active_keys:
        console.print("[bold yellow]Your watchlist is empty! Go find some movies.[/bold yellow]")
        return

    table = Table(title="Your Watchlist \U0001f37f", title_style="bold yellow", expand=True)
    table.add_column("#", justify="right", style="cyan", no_wrap=True)
    table.add_column("Type", style="green")
    table.add_column("Title", style="magenta")

    for i, key in enumerate(active_keys):
        item = saved_items[key]
        type_tag = "\U0001f4fa TV" if item['media_type'] == 'tv' else "\U0001f3ac Movie"
        table.add_row(str(i + 1), type_tag, item['display_name'])

    console.print(table)

    try:
        valid_choices = [str(i) for i in range(len(active_keys) + 1)]
        choice_idx = IntPrompt.ask("\nSelect a number (0 to go back)", choices=valid_choices) - 1
        if choice_idx < 0: return

        selected_key = active_keys[choice_idx]
        media = saved_items[selected_key]
        season = media.get('season')
        episode = media.get('episode')
        title_display = media['display_name']

    except (ValueError, IndexError):
        console.print("[bold red]Invalid selection.[/bold red]")
        return

    media['_scraper'] = scraper

    console.print(f"\n[bold green]Selected:[/bold green] {title_display}")
    console.print("  1) Play")
    console.print("  2) Download")
    console.print("  3) Mark as Watched")
    console.print("  4) Remove from Watchlist")
    action = IntPrompt.ask("Choose", choices=["1", "2", "3", "4"], default="1")

    if action == 4:
        del saved_items[selected_key]
        storage.save(saved_items)
        console.print(f"[bold yellow]Removed '{title_display}' from Watchlist.[/bold yellow]")
        return

    if action == 3:
        saved_items[selected_key]["status"] = "watched"
        storage.save(saved_items)
        console.print(f"[bold green]Marked '{title_display}' as Watched! \u2705[/bold green]")
        return

    resolve_and_execute(media, season, episode, title_display, force_download=(action == 2))


def search_and_select(scraper, query_str):
    try:
        with console.status(f"[bold cyan]Searching for '{query_str}'...", spinner="dots"):
            results = scraper.search(query_str)
    except ConnectionError as e:
        console.print(f"[bold red]{e}[/bold red]")
        return None

    if not results:
        console.print("[bold yellow]No results found for your query[/bold yellow]")
        return None

    table = Table(title="Search Results", title_style="bold magenta", expand=True)
    table.add_column("#", justify="right", style="cyan", no_wrap=True)
    table.add_column("Type", style="green")
    table.add_column("Title", style="magenta")
    table.add_column("Year", style="yellow")

    for i, item in enumerate(results):
        type_tag = "\U0001f4fa TV" if item['media_type'] == 'tv' else "\U0001f3ac Movie"
        table.add_row(str(i + 1), type_tag, item['title'], item['year'])

    console.print(table)

    try:
        valid_choices = [str(i) for i in range(len(results) + 1)]
        choice_idx = IntPrompt.ask("\nSelect a number (0 to go back)", choices=valid_choices) - 1
        if choice_idx < 0: return None
        return results[choice_idx]
    except (ValueError, IndexError):
        return None


def get_tv_episode(scraper, media):
    with console.status(f"[bold cyan]Fetching details for '{media['title']}'...", spinner="bouncingBar"):
        try:
            details = scraper.get_tv_details(media['tmdb_id'])
        except ConnectionError as e:
            console.print(f"[bold red]{e}[/bold red]")
            return None, None

    if not details:
        console.print("[bold red]Failed to fetch TV details from TMDB.[/bold red]")
        return None, None

    season_count = details.get('number_of_seasons', 0)
    console.print(Panel(f"Found [bold green]{season_count}[/bold green] Seasons.", title="TV Details", border_style="blue"))

    season_raw = Prompt.ask("Season(s) (e.g. '1', '1-3', '1,2,3')", default="all")
    seasons_list = parse_seasons(season_raw)

    if seasons_list is None:
        seasons_list = list(range(1, season_count + 1))
    elif not seasons_list:
        console.print("[bold red]No valid seasons specified.[/bold red]")
        return None, None

    if len(seasons_list) == 1:
        ep_raw = Prompt.ask(f"Episode in Season {seasons_list[0]} (or press Enter for all)", default="")
        if ep_raw == "":
            download_series(scraper, media['title'], media['tmdb_id'], seasons=seasons_list)
            return None, None
        try:
            episode = int(ep_raw)
        except ValueError:
            console.print("[bold red]Invalid episode number.[/bold red]")
            return None, None
        return seasons_list[0], episode

    download_series(scraper, media['title'], media['tmdb_id'], seasons=seasons_list)
    return None, None


def handle_search(scraper, query_str, force_download=False):
    media = search_and_select(scraper, query_str)
    if media is None:
        return

    media['_scraper'] = scraper
    season = None
    episode = None

    if media['media_type'] == 'tv':
        season, episode = get_tv_episode(scraper, media)
        if season is None and episode is None:
            return

    title_display = f"{media['title']}"
    if season is not None:
        title_display += f" S{season}E{episode}"

    if not force_download:
        action = show_action_menu(title_display)
        if action == 3:
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
                "status": "watchlist"
            }
            storage.save(watchlist_data)
            console.print(f"[bold yellow]Added '{title_display}' to Watchlist! \U0001f37f[/bold yellow]")
            return
        force_download = (action == 2)

    resolve_and_execute(media, season, episode, title_display, force_download)


def interactive_loop(scraper):
    while True:
        console.print()
        console.print(Panel("[bold cyan]Movie CLI[/bold cyan]", border_style="cyan"))
        console.print("  1) Search & Watch")
        console.print("  2) Search & Download")
        console.print("  3) View Watchlist")
        console.print("  4) View History")
        console.print("  5) Exit")

        choice = IntPrompt.ask("Choose", choices=["1", "2", "3", "4", "5"], default="1")

        if choice == 5:
            console.print("[bold green]Goodbye![/bold green]")
            break
        elif choice == 4:
            handle_history()
        elif choice == 3:
            handle_watchlist(scraper)
        else:
            query = Prompt.ask("Search for")
            if not query:
                continue
            handle_search(scraper, query, force_download=(choice == 2))


def run():
    parser = argparse.ArgumentParser(prog="movie")
    parser.add_argument("query", nargs="*", help="Movie or Show name")
    parser.add_argument("-d", "--download", action="store_true", help="Download content")
    parser.add_argument("-w", "--watchlist", action="store_true", help="View your watchlist")
    parser.add_argument("-H", "--history", action="store_true", help="View watched history")
    args = parser.parse_args()

    scraper = CinebyAPIScraper()

    if args.history:
        handle_history()
    elif args.watchlist:
        handle_watchlist(scraper)
    elif args.query:
        handle_search(scraper, " ".join(args.query), force_download=args.download)
    else:
        interactive_loop(scraper)


if __name__ == "__main__":
    run()
