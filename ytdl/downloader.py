import os
import time
import yt_dlp
from pathlib import Path
from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import (
    Progress, BarColumn, TextColumn, DownloadColumn,
    TransferSpeedColumn, TimeRemainingColumn, SpinnerColumn,
    TaskProgressColumn, MofNCompleteColumn,
)
from rich.table import Table
from rich.text import Text
from rich import box
from rich.rule import Rule

console = Console()


# ─────────────────────────────────────────────────────────────
# Build yt-dlp options
# ─────────────────────────────────────────────────────────────

def build_ydl_opts(output_dir: str, format_type: str, quality: str,
                   embed_thumbnail: bool, embed_metadata: bool) -> dict:
    output_dir = str(Path(output_dir).expanduser().resolve())
    os.makedirs(output_dir, exist_ok=True)

    postprocessors = []

    if format_type == "mp3":
        postprocessors.append({
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": quality,
        })
        if embed_thumbnail:
            postprocessors.append({"key": "EmbedThumbnail"})
        if embed_metadata:
            postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True})
    elif format_type == "mp4":
        if embed_metadata:
            postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True})
        if embed_thumbnail:
            postprocessors.append({"key": "EmbedThumbnail"})

    fmt_map = {"mp3": "bestaudio/best", "mp4": "bestvideo+bestaudio/best"}
    fmt = fmt_map.get(format_type, "best")

    outtmpl = os.path.join(output_dir, "%(playlist_index)s - %(title)s.%(ext)s")

    return {
        "format": fmt,
        "outtmpl": outtmpl,
        "postprocessors": postprocessors,
        "writethumbnail": embed_thumbnail,
        "addmetadata": embed_metadata,
        "noplaylist": False,
        "ignoreerrors": True,
        "quiet": True,
        "no_warnings": True,
        "retries": 5,
        "fragment_retries": 5,
        "concurrent_fragment_downloads": 4,
    }


# ─────────────────────────────────────────────────────────────
# Rich progress bar builders
# ─────────────────────────────────────────────────────────────

def make_download_progress() -> Progress:
    """Per-file download progress bar with speed + ETA."""
    return Progress(
        SpinnerColumn(spinner_name="dots", style="bold yellow"),
        TextColumn("[bold white]{task.description}", justify="left"),
        BarColumn(bar_width=36, style="yellow", complete_style="bold green", finished_style="bold green"),
        TaskProgressColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TextColumn("[dim]ETA[/dim]"),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    )


def make_overall_progress() -> Progress:
    """Playlist-level track counter."""
    return Progress(
        SpinnerColumn(spinner_name="arc", style="bold cyan"),
        TextColumn("[bold cyan]{task.description}", justify="left"),
        BarColumn(bar_width=36, style="cyan", complete_style="bold green", finished_style="bold green"),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        console=console,
        transient=False,
    )


def make_post_progress() -> Progress:
    """Post-processing spinner for convert / thumbnail / metadata."""
    return Progress(
        SpinnerColumn(spinner_name="aesthetic", style="bold magenta"),
        TextColumn("[magenta]{task.description}"),
        console=console,
        transient=True,
    )


# ─────────────────────────────────────────────────────────────
# Render helper — assembles the live panel
# ─────────────────────────────────────────────────────────────

def build_live_panel(
    dl_progress: Progress,
    post_progress: Progress,
    overall_progress: Progress | None,
    completed_lines: list[str],
    is_playlist: bool,
    playlist_title: str = "",
    format_type: str = "mp3",
    quality: str = "320",
    output_dir: str = "",
) -> Panel:

    # ── Header info row ──────────────────────
    header = Table.grid(padding=(0, 2))
    header.add_column(style="dim")
    header.add_column(style="bold")
    header.add_column(style="dim")
    header.add_column(style="bold")

    label = "📋 Playlist" if is_playlist else "🎵 Track"
    name  = playlist_title or "—"
    qual_str = f"{quality}{'k' if format_type == 'mp3' else 'p'}"
    header.add_row(f"{label}:", name, "Format:", f"{format_type.upper()} @ {qual_str}")
    header.add_row("Output:", output_dir, "", "")

    # ── Completed track log (last 6) ─────────
    log_lines = completed_lines[-6:] if completed_lines else []
    log_text = Text()
    for line in log_lines:
        log_text.append(line + "\n")

    # ── Assemble grid ────────────────────────
    grid = Table.grid(padding=(0, 0))
    grid.add_column()

    grid.add_row(header)
    grid.add_row(Text(""))

    if is_playlist and overall_progress:
        grid.add_row(overall_progress)

    grid.add_row(dl_progress)
    grid.add_row(post_progress)

    if log_lines:
        grid.add_row(Rule(style="dim"))
        grid.add_row(log_text)

    return Panel(
        grid,
        title="[bold yellow]⬇  Downloading[/bold yellow]",
        border_style="yellow",
        padding=(0, 1),
    )


# ─────────────────────────────────────────────────────────────
# Silence logger
# ─────────────────────────────────────────────────────────────

class _SilentLogger:
    def debug(self, msg):   pass
    def warning(self, msg): pass
    def error(self, msg):   pass


# ─────────────────────────────────────────────────────────────
# Main download function
# ─────────────────────────────────────────────────────────────

def download(
    url: str,
    output_dir: str,
    format_type: str = "mp3",
    quality: str = "320",
    embed_thumbnail: bool = True,
    embed_metadata: bool = True,
) -> dict:
    """Download a video or playlist with full Rich live progress UI."""

    results = {"success": 0, "failed": 0, "titles": []}
    output_dir = str(Path(output_dir).expanduser().resolve())

    # ── Pre-fetch info ────────────────────────
    with console.status("[dim]Fetching video info...[/dim]", spinner="dots"):
        probe_opts = {"quiet": True, "no_warnings": True, "ignoreerrors": True}
        with yt_dlp.YoutubeDL(probe_opts) as ydl:
            info = ydl.extract_info(url, download=False)

    if info is None:
        console.print("[red]✗ Could not retrieve video/playlist info.[/red]")
        return results

    is_playlist    = info.get("_type") == "playlist"
    playlist_title = info.get("title", "Playlist") if is_playlist else info.get("title", "Track")
    entries        = [e for e in (info.get("entries") or [info]) if e]
    total_tracks   = len(entries)

    # ── Build progress bars ───────────────────
    dl_progress      = make_download_progress()
    post_progress    = make_post_progress()
    overall_progress = make_overall_progress() if is_playlist else None

    # Task handles (created once, updated in hooks)
    state = {
        "dl_task":      None,   # active download bar task id
        "post_task":    None,   # active post-proc spinner task id
        "overall_task": None,   # playlist counter task id
        "live":         None,   # reference to Live object
        "completed":    [],     # list of "✓ title" strings
        "current_title": "",
    }

    def _refresh():
        if state["live"]:
            state["live"].update(build_live_panel(
                dl_progress, post_progress, overall_progress,
                state["completed"], is_playlist, playlist_title,
                format_type, quality, output_dir,
            ))

    # ── yt-dlp hooks ─────────────────────────

    def progress_hook(d):
        status = d.get("status")
        title  = d.get("filename", "")
        title  = Path(title).stem if title else d.get("info_dict", {}).get("title", "…")
        # Trim long titles
        title_short = (title[:52] + "…") if len(title) > 55 else title

        if status == "downloading":
            total   = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)

            if state["dl_task"] is None:
                state["current_title"] = title_short
                state["dl_task"] = dl_progress.add_task(
                    f"[white]{title_short}",
                    total=total if total else None,
                )
            else:
                dl_progress.update(
                    state["dl_task"],
                    completed=downloaded,
                    total=total if total else None,
                    description=f"[white]{title_short}",
                )
            _refresh()

        elif status == "finished":
            # Download done — move to post-processing
            if state["dl_task"] is not None:
                dl_progress.update(state["dl_task"], completed=dl_progress.tasks[state["dl_task"]].total or 1)
                dl_progress.remove_task(state["dl_task"])
                state["dl_task"] = None

            # Show post-processing spinner
            state["post_task"] = post_progress.add_task(
                f"⚙  Processing  {title_short}"
            )
            _refresh()

        elif status == "error":
            results["failed"] += 1
            if state["dl_task"] is not None:
                dl_progress.remove_task(state["dl_task"])
                state["dl_task"] = None
            _refresh()

    def postprocessor_hook(d):
        """Called at each post-processing stage."""
        status = d.get("status")
        pp     = d.get("postprocessor", "")
        title  = d.get("info_dict", {}).get("title", state["current_title"])
        title_short = (title[:52] + "…") if len(title) > 55 else title

        stage_labels = {
            "FFmpegExtractAudio": "🎵 Converting to MP3",
            "EmbedThumbnail":     "🖼  Embedding thumbnail",
            "FFmpegMetadata":     "🏷  Writing metadata",
            "MoveFiles":          "📁 Moving file",
        }
        label = stage_labels.get(pp, f"⚙  {pp}" if pp else "⚙  Processing")

        if status == "started":
            if state["post_task"] is not None:
                post_progress.update(state["post_task"], description=f"{label}  [dim]{title_short}[/dim]")
            else:
                state["post_task"] = post_progress.add_task(
                    f"{label}  [dim]{title_short}[/dim]"
                )
            _refresh()

        elif status == "finished":
            if pp in ("FFmpegMetadata", "EmbedThumbnail", "MoveFiles") or pp == "FFmpegExtractAudio":
                # Mark track fully done only when the last relevant stage finishes
                pass

            # Final stage: clean up post spinner, log success
            last_stages = {"FFmpegMetadata", "EmbedThumbnail", "MoveFiles"}
            if pp in last_stages or (pp == "FFmpegExtractAudio" and not embed_thumbnail and not embed_metadata):
                if state["post_task"] is not None:
                    post_progress.remove_task(state["post_task"])
                    state["post_task"] = None

                results["success"] += 1
                results["titles"].append(title)
                state["completed"].append(f"[green]✓[/green] [white]{title_short}[/white]")

                if overall_progress and state["overall_task"] is not None:
                    overall_progress.update(state["overall_task"], advance=1)

                _refresh()

    # ── Start live display ────────────────────
    initial_panel = build_live_panel(
        dl_progress, post_progress, overall_progress,
        [], is_playlist, playlist_title,
        format_type, quality, output_dir,
    )

    with Live(initial_panel, console=console, refresh_per_second=12, transient=False) as live:
        state["live"] = live

        if is_playlist and overall_progress:
            state["overall_task"] = overall_progress.add_task(
                f"Overall progress",
                total=total_tracks,
            )

        opts = build_ydl_opts(output_dir, format_type, quality, embed_thumbnail, embed_metadata)
        opts["logger"]              = _SilentLogger()
        opts["progress_hooks"]      = [progress_hook]
        opts["postprocessor_hooks"] = [postprocessor_hook]

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
        except yt_dlp.utils.DownloadError as e:
            console.print(f"[red]Download error:[/red] {e}")
        except Exception as e:
            console.print(f"[red]Unexpected error:[/red] {e}")

        # Finalise — complete overall bar if not already
        if overall_progress and state["overall_task"] is not None:
            overall_progress.update(state["overall_task"], completed=total_tracks)
        _refresh()
        time.sleep(0.4)   # let final frame render

    return results