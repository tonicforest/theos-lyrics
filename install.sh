#!/usr/bin/env bash
set -e

echo "Installing Theòs Lyrics dependencies..."

sudo apt update
sudo apt install -y \
    python3 \
    python3-gi \
    python3-dbus \
    python3-requests \
    python3-xlib \
    gir1.2-gtk-3.0

PROJECT="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$HOME/.local/bin"
mkdir -p "$HOME/.local/share/applications"

cat > "$HOME/.local/bin/theos-lyrics" <<EOF
#!/usr/bin/env bash
exec /usr/bin/python3 "$PROJECT/main.py"
EOF

chmod +x "$HOME/.local/bin/theos-lyrics"

cat > "$HOME/.local/share/applications/theos-lyrics.desktop" <<EOF
[Desktop Entry]
Name=Theòs Lyrics
Comment=Synced lyrics overlay for MPRIS players
Exec=$HOME/.local/bin/theos-lyrics
Icon=audio-x-generic
Terminal=false
Type=Application
Categories=AudioVideo;Audio;
EOF

echo
echo "Theòs Lyrics has been installed!"
echo "You can launch it from your application menu."
