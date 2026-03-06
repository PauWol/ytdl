import click
import sys
import os
import yt_dlp
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich import box
import questionary
from questionary import Style as QStyle

from ytdl.downloader import download
from ytdl.utils import is_valid_youtube_url, is_playlist_url

try:
    from importlib.metadata import version as _pkg_version
    __version__ = _pkg_version("ytdl")
except Exception:
    __version__ = "1.0.0"

console = Console()

# ── Questionary theme ────────────────────────
Q_STYLE = QStyle([
    ("qmark",       "fg:#ffcc00 bold"),
    ("question",    "fg:#ffffff bold"),
    ("answer",      "fg:#ffcc00 bold"),
    ("pointer",     "fg:#ffcc00 bold"),
    ("highlighted", "fg:#ffcc00 bold"),
    ("selected",    "fg:#aaffaa"),
    ("separator",   "fg:#555555"),
    ("instruction", "fg:#555555 italic"),
    ("text",        "fg:#cccccc"),
    ("disabled",    "fg:#555555 italic"),
])

BANNER = """\
[bold yellow] ██╗   ██╗████████╗      ██████╗ ██╗[/bold yellow]
[bold yellow] ╚██╗ ██╔╝╚══██╔══╝      ██╔══██╗██║[/bold yellow]
[bold yellow]  ╚████╔╝    ██║   █████╗██║  ██║██║[/bold yellow]
[bold yellow]   ╚██╔╝     ██║   ╚════╝██║  ██║██║[/bold yellow]
[bold yellow]    ██║      ██║         ██████╔╝███████╗[/bold yellow]
[bold yellow]    ╚═╝      ╚═╝         ╚═════╝ ╚══════╝[/bold yellow]"""


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def show_banner(subtitle: str = "YouTube Downloader — songs & playlists"):
    clear()
    console.print(BANNER)
    console.print(f"  [dim]{subtitle}[/dim]   [dim]v{__version__} · yt-dlp[/dim]\n")


def show_summary(results: dict, format_type: str, output_dir: str):
    table = Table(box=box.ROUNDED, show_header=False, padding=(0, 1))
    table.add_column("Key", style="dim", width=22)
    table.add_column("Value", style="bold")
    table.add_row("✅  Downloaded", f"[green]{results['success']}[/green]")
    if results["failed"] > 0:
        table.add_row("❌  Failed", f"[red]{results['failed']}[/red]")
    table.add_row("📁  Saved to", str(output_dir))
    table.add_row("🎵  Format", format_type.upper())
    console.print()
    console.print(Panel(table, title="[bold green]Download Complete[/bold green]", border_style="green"))


def prompt_url(label: str = "Paste YouTube URL") -> str:
    url = questionary.text(
        f"{label}:",
        style=Q_STYLE,
        validate=lambda v: True if v.strip() else "URL cannot be empty",
    ).ask()
    if url is None:
        raise KeyboardInterrupt
    url = url.strip()
    if not is_valid_youtube_url(url):
        console.print("[red]  ✗ That doesn't look like a valid YouTube URL. Try again.[/red]")
        return prompt_url(label)
    return url


def prompt_output_dir(default: str = "~/Music/ytdl") -> str:
    val = questionary.text(
        "Output folder:",
        default=default,
        style=Q_STYLE,
    ).ask()
    if val is None:
        raise KeyboardInterrupt
    return str(Path(val.strip()).expanduser())


def prompt_format() -> str:
    return questionary.select(
        "Format:",
        choices=[
            questionary.Choice("🎵  MP3  — audio only (best quality)", value="mp3"),
            questionary.Choice("🎬  MP4  — video + audio",              value="mp4"),
            questionary.Choice("⚡  Best — let yt-dlp decide",          value="best"),
        ],
        style=Q_STYLE,
    ).ask() or "mp3"


def prompt_quality(fmt: str) -> str:
    if fmt == "mp4":
        return questionary.select(
            "Video quality:",
            choices=[
                questionary.Choice("4K / best available", value="2160"),
                questionary.Choice("1080p",               value="1080"),
                questionary.Choice("720p",                value="720"),
                questionary.Choice("480p",                value="480"),
            ],
            style=Q_STYLE,
        ).ask() or "1080"
    else:
        return questionary.select(
            "Audio quality:",
            choices=[
                questionary.Choice("320 kbps  — best",    value="320"),
                questionary.Choice("256 kbps  — great",   value="256"),
                questionary.Choice("192 kbps  — good",    value="192"),
                questionary.Choice("128 kbps  — compact", value="128"),
            ],
            style=Q_STYLE,
        ).ask() or "320"


def prompt_extras() -> tuple:
    extras = questionary.checkbox(
        "Embed extras (space to toggle, enter to confirm):",
        choices=[
            questionary.Choice("🖼   Thumbnail / cover art",        value="thumbnail", checked=True),
            questionary.Choice("🏷   Metadata (title, artist, album)", value="metadata",  checked=True),
        ],
        style=Q_STYLE,
    ).ask() or []
    return ("thumbnail" in extras), ("metadata" in extras)


def show_config_panel(mode, url, fmt, quality, thumbnail, metadata, output):
    console.print()
    lines = (
        f"[dim]Mode   [/dim]  {mode}\n"
        f"[dim]URL    [/dim]  {url}\n"
        f"[dim]Format [/dim]  {fmt.upper()} @ {quality}{'k' if fmt == 'mp3' else 'p'}\n"
        f"[dim]Extras [/dim]  {'🖼 thumbnail  ' if thumbnail else ''}{'🏷 metadata' if metadata else ''}\n"
        f"[dim]Output [/dim]  {output}"
    )
    console.print(Panel(lines, title="[bold cyan]Ready to Download[/bold cyan]", border_style="cyan"))
    console.print()


# ── Flow functions ───────────────────────────

def run_song_flow():
    show_banner("Download a single song or video")
    console.print(Rule("[dim]Single Track[/dim]", style="dim yellow"))
    console.print()

    url             = prompt_url("YouTube video URL")
    fmt             = prompt_format()
    qual            = prompt_quality(fmt)
    thumb, meta     = prompt_extras()
    outdir          = prompt_output_dir()

    show_config_panel("🎵 Single Track", url, fmt, qual, thumb, meta, outdir)

    go = questionary.confirm("Start download?", default=True, style=Q_STYLE).ask()
    if not go:
        console.print("[dim]  Cancelled.[/dim]")
        return

    results = download(url=url, output_dir=outdir, format_type=fmt,
                       quality=qual, embed_thumbnail=thumb, embed_metadata=meta)
    show_summary(results, fmt, outdir)


def run_playlist_flow():
    show_banner("Download a full playlist")
    console.print(Rule("[dim]Playlist[/dim]", style="dim yellow"))
    console.print()

    url             = prompt_url("YouTube playlist URL")
    fmt             = prompt_format()
    qual            = prompt_quality(fmt)
    thumb, meta     = prompt_extras()
    outdir          = prompt_output_dir()

    if not is_playlist_url(url):
        console.print("[yellow]  ⚠  This URL doesn't look like a playlist — will try anyway.[/yellow]\n")

    show_config_panel("📋 Playlist", url, fmt, qual, thumb, meta, outdir)

    go = questionary.confirm("Start download?", default=True, style=Q_STYLE).ask()
    if not go:
        console.print("[dim]  Cancelled.[/dim]")
        return

    results = download(url=url, output_dir=outdir, format_type=fmt,
                       quality=qual, embed_thumbnail=thumb, embed_metadata=meta)
    show_summary(results, fmt, outdir)


def run_info_flow(preloaded_url: str = None):
    if not preloaded_url:
        show_banner("Preview info — no download")
        console.print(Rule("[dim]Info Lookup[/dim]", style="dim yellow"))
        console.print()
        url = prompt_url("YouTube video or playlist URL")
    else:
        url = preloaded_url

    console.print("\n[dim]  Fetching metadata...[/dim]\n")
    opts = {"quiet": True, "no_warnings": True, "ignoreerrors": True}

    with yt_dlp.YoutubeDL(opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)

    if not info_dict:
        console.print("[red]  ✗ Could not retrieve info for that URL.[/red]")
        return

    is_pl = info_dict.get("_type") == "playlist"
    table = Table(box=box.ROUNDED, show_header=False, padding=(0, 1))
    table.add_column("Field", style="dim", width=18)
    table.add_column("Value", style="bold", overflow="fold")

    if is_pl:
        entries = [e for e in (info_dict.get("entries") or []) if e]
        table.add_row("Type",        "📋 Playlist")
        table.add_row("Title",       info_dict.get("title", "N/A"))
        table.add_row("Uploader",    info_dict.get("uploader", "N/A"))
        table.add_row("Track count", str(len(entries)))
        console.print(Panel(table, title="[bold]Playlist Info[/bold]", border_style="cyan"))
        if entries:
            console.print("\n  [bold]Tracks:[/bold]")
            for i, entry in enumerate(entries[:40], 1):
                dur  = entry.get("duration", 0)
                m, s = divmod(int(dur or 0), 60)
                console.print(f"  [dim]{i:02d}.[/dim] {entry.get('title','?')}  [dim]({m}:{s:02d})[/dim]")
            if len(entries) > 40:
                console.print(f"  [dim]  … and {len(entries)-40} more tracks[/dim]")
    else:
        dur  = info_dict.get("duration", 0)
        m, s = divmod(int(dur or 0), 60)
        table.add_row("Type",     "🎵 Video")
        table.add_row("Title",    info_dict.get("title", "N/A"))
        table.add_row("Uploader", info_dict.get("uploader", "N/A"))
        table.add_row("Duration", f"{m}:{s:02d}")
        table.add_row("Views",    f"{info_dict.get('view_count',0):,}" if info_dict.get("view_count") else "N/A")
        table.add_row("Date",     info_dict.get("upload_date", "N/A"))
        console.print(Panel(table, title="[bold]Video Info[/bold]", border_style="cyan"))


# ── Interactive menu ─────────────────────────

MENU_CHOICES = [
    questionary.Choice("🎵  Download a song / video",   value="song"),
    questionary.Choice("📋  Download a playlist",        value="playlist"),
    questionary.Separator(),
    questionary.Choice("ℹ   Preview info (no download)", value="info"),
    questionary.Separator(),
    questionary.Choice("❌  Quit",                        value="quit"),
]


def interactive_menu():
    while True:
        show_banner()
        console.print("  Use [bold yellow]↑ ↓[/bold yellow] to navigate  ·  [bold yellow]Enter[/bold yellow] to select  ·  [bold yellow]Ctrl+C[/bold yellow] to quit\n")

        choice = questionary.select(
            "What would you like to do?",
            choices=MENU_CHOICES,
            style=Q_STYLE,
            use_shortcuts=False,
        ).ask()

        if choice is None or choice == "quit":
            show_banner()
            console.print("  [dim]Goodbye! 👋[/dim]\n")
            sys.exit(0)

        try:
            if choice == "song":
                run_song_flow()
            elif choice == "playlist":
                run_playlist_flow()
            elif choice == "info":
                run_info_flow()
        except KeyboardInterrupt:
            console.print("\n[dim]  ↩  Back to main menu...[/dim]")
            continue

        console.print()
        again = questionary.confirm(
            "Back to main menu?", default=True, style=Q_STYLE
        ).ask()
        if not again:
            console.print("\n  [dim]Goodbye! 👋[/dim]\n")
            sys.exit(0)


# ── Click CLI group ──────────────────────────

@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name="ytdl")
@click.pass_context
def cli(ctx):
    """YT-DL — YouTube song & playlist downloader.

    Run without arguments to open the interactive menu.
    """
    if ctx.invoked_subcommand is None:
        try:
            interactive_menu()
        except KeyboardInterrupt:
            console.print("\n\n  [dim]Goodbye! 👋[/dim]\n")
            sys.exit(0)


# ── Direct CLI commands ──────────────────────

@cli.command()
@click.argument("url")
@click.option("-o", "--output",        default="~/Music/ytdl", show_default=True, help="Output directory")
@click.option("-f", "--format", "fmt", default="mp3", type=click.Choice(["mp3","mp4","best"]), show_default=True)
@click.option("-q", "--quality",       default="320", show_default=True)
@click.option("--no-thumbnail",        is_flag=True, default=False)
@click.option("--no-metadata",         is_flag=True, default=False)
def song(url, output, fmt, quality, no_thumbnail, no_metadata):
    """Download a single YouTube song/video.

    \b
    Examples:
      ytdl song https://youtu.be/dQw4w9WgXcQ
      ytdl song https://youtu.be/dQw4w9WgXcQ -o ~/Downloads -f mp3 -q 320
    """
    show_banner("Single Track Download")
    if not is_valid_youtube_url(url):
        console.print(Panel(f"[red]Invalid URL:[/red] {url}", title="❌ Error", border_style="red"))
        sys.exit(1)
    out = str(Path(output).expanduser())
    show_config_panel("🎵 Song", url, fmt, quality, not no_thumbnail, not no_metadata, out)
    results = download(url=url, output_dir=out, format_type=fmt, quality=quality,
                       embed_thumbnail=not no_thumbnail, embed_metadata=not no_metadata)
    show_summary(results, fmt, out)


@cli.command()
@click.argument("url")
@click.option("-o", "--output",        default="~/Music/ytdl", show_default=True, help="Output directory")
@click.option("-f", "--format", "fmt", default="mp3", type=click.Choice(["mp3","mp4","best"]), show_default=True)
@click.option("-q", "--quality",       default="320", show_default=True)
@click.option("--no-thumbnail",        is_flag=True, default=False)
@click.option("--no-metadata",         is_flag=True, default=False)
@click.option("-y", "--yes",           is_flag=True, default=False)
def playlist(url, output, fmt, quality, no_thumbnail, no_metadata, yes):
    """Download an entire YouTube playlist.

    \b
    Examples:
      ytdl playlist "https://www.youtube.com/playlist?list=PLxxxxxx"
    """
    show_banner("Playlist Download")
    if not is_valid_youtube_url(url):
        console.print(Panel(f"[red]Invalid URL:[/red] {url}", title="❌ Error", border_style="red"))
        sys.exit(1)
    out = str(Path(output).expanduser())
    show_config_panel("📋 Playlist", url, fmt, quality, not no_thumbnail, not no_metadata, out)
    results = download(url=url, output_dir=out, format_type=fmt, quality=quality,
                       embed_thumbnail=not no_thumbnail, embed_metadata=not no_metadata)
    show_summary(results, fmt, out)


@cli.command()
@click.argument("url")
def info(url):
    """Show metadata info about a video or playlist (no download).

    \b
    Examples:
      ytdl info https://www.youtube.com/watch?v=dQw4w9WgXcQ
    """
    show_banner("Info Lookup")
    if not is_valid_youtube_url(url):
        console.print("[red]Invalid YouTube URL.[/red]")
        sys.exit(1)
    run_info_flow(preloaded_url=url)


def main():
    cli()


if __name__ == "__main__":
    main()