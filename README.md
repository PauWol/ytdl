# 🎵 YT-DL — YouTube Song & Playlist Downloader

A fast, elegant CLI tool for downloading YouTube songs and playlists in the best available quality, with **embedded metadata** (title, artist, album) and **thumbnail art** directly in the MP3 file.

## ✨ Features

- 🎧 **Best quality audio** — 320kbps MP3 by default
- 🖼️ **Thumbnail embedding** — album art baked directly into the MP3
- 🏷️ **Metadata embedding** — title, artist, and album from YouTube
- 📋 **Playlist support** — download entire playlists in one command
- 🎬 **Video support** — also download MP4 with best video+audio quality
- ℹ️ **Info command** — preview metadata and track list before downloading
- 💅 **Beautiful terminal UX** — progress indicators, color, and clear output
- ⚡ **Fast** — concurrent fragment downloads via `yt-dlp`

## ⚙️ Requirements

- **Python 3.9+**
- **FFmpeg** — required for audio conversion and thumbnail embedding

### Install FFmpeg

**macOS (Homebrew):**
```bash
brew install ffmpeg
```

**Ubuntu / Debian:**
```bash
sudo apt update && sudo apt install ffmpeg -y
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to `PATH`, or use:
```powershell
winget install ffmpeg
```

## 🚀 Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/PauWol/ytdl.git
cd ytdl
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
```

### 3. Activate the virtual environment

**macOS / Linux:**
```bash
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Install the CLI tool

```bash
pip install -e .
```

This registers the `ytdl` command globally within your virtual environment.

---

## 🎮 Usage

### Download a single song

```bash
ytdl song https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

### Download with custom output folder

```bash
ytdl song https://youtu.be/dQw4w9WgXcQ -o ~/Music/Downloads
```

### Download as MP4 (video)

```bash
ytdl song https://www.youtube.com/watch?v=dQw4w9WgXcQ -f mp4
```

### Download a playlist (MP3, 320kbps, with art & metadata)

```bash
ytdl playlist "https://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxx"
```

### Download a playlist at lower quality

```bash
ytdl playlist "https://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxx" -q 192
```

### Download a playlist, skip confirmation prompt

```bash
ytdl playlist "https://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxx" -y
```

### Preview info without downloading

```bash
ytdl info https://www.youtube.com/watch?v=dQw4w9WgXcQ
ytdl info "https://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxx"
```

### Skip thumbnail or metadata

```bash
ytdl song https://youtu.be/dQw4w9WgXcQ --no-thumbnail
ytdl song https://youtu.be/dQw4w9WgXcQ --no-metadata
```

## ⚙️ Options Reference

### `ytdl song [URL]`

| Option | Default | Description |
|---|---|---|
| `-o, --output` | `~/Music/ytdl` | Output directory |
| `-f, --format` | `mp3` | Format: `mp3`, `mp4`, or `best` |
| `-q, --quality` | `320` | Audio quality in kbps (`320`, `256`, `192`, `128`) |
| `--no-thumbnail` | off | Skip embedding cover art |
| `--no-metadata` | off | Skip embedding title/artist metadata |

### `ytdl playlist [URL]`

Same options as `song`, plus:

| Option | Default | Description |
|---|---|---|
| `-y, --yes` | off | Skip confirmation prompt |

### `ytdl info [URL]`

No extra options — displays metadata and track list.


## 🔄 Updating yt-dlp

YouTube changes frequently. If downloads break, update `yt-dlp`:

```bash
pip install -U yt-dlp
```

---

## 📝 Notes

- Track filenames follow the pattern: `01 - Song Title.mp3`
- Playlist index is prepended for correct sorting
- All files are saved to `~/Music/ytdl` by default (customizable with `-o`)
- Errors in individual tracks are skipped automatically — the rest of the playlist continues

---

## 📄 License

MIT — free to use, modify, and distribute.
