# Theòs Lyrics prototype 0.1
GTK3 tray companion for MPRIS players; fetches synced lyrics from LRCLIB and displays a translucent top-quarter overlay.

## Install on Linux Mint
```bash
chmod +x install.sh
./install.sh
```
Launch Theòs Lyrics from the application menu. The player must expose MPRIS on the DBus session.

Prototype caveats: tray icon is GTK3 `StatusIcon`; initial cover icon is square-sized (round masking and panel positioning refinements are planned). Lyrics retrieval needs internet.
