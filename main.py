#!/usr/bin/env python3
import signal
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk, Gdk
from player import PlayerWatcher
from panel_icon import PanelIcon
from overlay import LyricsOverlay
from lyrics import LyricsClient

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    client=LyricsClient()
    overlay=LyricsOverlay()
    overlay.hide()
    watcher=PlayerWatcher(client,overlay)
    icon=PanelIcon(overlay)
    watcher.set_artwork_callback(icon.set_artwork)
    watcher.set_overlay_track_callback(overlay.set_track)
    watcher.set_overlay_lyrics_callback(overlay.set_lyrics)
    watcher.set_overlay_position_callback(overlay.set_position)
    watcher.start()
    icon.start()
    Gtk.main()

if __name__=="__main__": main()
