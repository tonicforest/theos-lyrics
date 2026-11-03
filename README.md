# Theòs Lyrics

A lightweight, cinematic lyrics overlay for Linux. Theòs Lyrics follows your music player, fetches synchronized lyrics, and displays them in an elegant floating window with a smooth karaoke-style highlight.

<p align="center">
  <strong>GTK3 · Python · MPRIS · LRCLIB</strong>
</p>

## ✨ Features

- **Synchronized lyrics** — retrieves timestamped lyrics from [LRCLIB](https://lrclib.net/).
- **Karaoke-style highlighting** — a smooth, left-to-right letter reveal follows playback.
- **Cinematic overlay** — translucent dark background, subtle blue accents, and centered typography.
- **Five-line display** — keeps the current lyric in focus while showing surrounding lines.
- **Smooth transitions** — subtle fading and vertical movement between lyric lines.
- **MPRIS integration** — follows compatible Linux media players through D-Bus.
- **Outside-click dismissal** — clicking outside the overlay hides it while allowing the underlying application to receive the click.
- **Lightweight** — built with Python and GTK3, without an Electron runtime.

> **About karaoke timing:** LRCLIB supplies line-level timestamps. Theòs interpolates between consecutive lines to estimate the highlight progression. The animation is letter-by-letter, but it is not based on individually timed words.

## 🖥️ Compatibility

The current implementation is intended for:

- Linux distributions using GTK3 and D-Bus.
- X11 desktop sessions.
- MPRIS-compatible media players.

The outside-click monitor uses X11 through Python Xlib. **Wayland is not currently supported by this implementation.**

The project has been developed and tested on Linux Mint XFCE. Other GTK3-based Linux desktops may work, but have not all been tested.

## 📦 Requirements

- Python 3
- GTK 3
- PyGObject
- D-Bus and `dbus-python`
- Python Requests
- Python Xlib
- An active D-Bus session
- Internet access to retrieve lyrics from LRCLIB

## 🚀 Installation

### Linux Mint / Ubuntu

Clone the repository:

```bash
git clone https://github.com/tonicforest/theos-lyrics.git
cd theos-lyrics
```

Run the installer:

```bash
chmod +x install.sh
./install.sh
```

The installer installs the required system packages and creates an application-menu entry.

Launch **Theòs Lyrics** from your application menu.

### Manual launch

You can also start it directly:

```bash
python3 main.py
```

## 🎵 How it works

1. Theòs monitors active media players through the MPRIS D-Bus interface.
2. When the track changes, it retrieves the title, artist, album, and artwork metadata.
3. It requests synchronized lyrics from LRCLIB.
4. The overlay tracks playback position and animates the active lyric.
5. The panel icon lets you show or hide the overlay.

A compatible media player must expose the MPRIS interface on your D-Bus session.

## ⚙️ Performance

Theòs is designed to stay lightweight:

- Player state is polled periodically.
- Lyrics are fetched when the track changes, not continuously.
- The overlay animation runs only when needed.
- The outside-click monitor runs while the overlay is visible.

Actual resource usage depends on the desktop environment and media player.

## 🛠️ Project structure

```text
theos-lyrics/
├── main.py           # Application entry point
├── player.py         # MPRIS player monitoring
├── lyrics.py         # LRCLIB lyrics retrieval
├── overlay.py        # GTK3 lyrics overlay and animations
├── outside_click.py  # X11 outside-click detection
├── panel_icon.py     # Panel/tray interaction
├── install.sh        # Linux installation script
├── requirements.txt  # Python package requirements
└── start-theos.sh    # Startup helper
```

## 🗺️ Roadmap

- [ ] Improve compatibility across Linux desktop environments.
- [ ] Add more overlay customization options.
- [ ] Improve lyric synchronization accuracy.
- [ ] Add configuration for overlay position and appearance.
- [ ] Explore Wayland-compatible outside-click handling.

## 🤝 Contributing

Contributions, suggestions, and bug reports are welcome!

If you encounter an issue, please open a GitHub issue with:
- Your Linux distribution and desktop environment.
- Whether you're using X11 or Wayland.
- Your media player.
- Relevant terminal output or error messages.

## 📄 License

Theòs Lyrics is released under the [MIT License](LICENSE).

---

<p align="center">
  Made with care for music and Linux.
</p>
