from gi.repository import Gtk, GdkPixbuf
import os
class PanelIcon:
    def __init__(self,overlay):
        self.overlay=overlay
        self.icon=Gtk.StatusIcon()
        self.icon.set_title("Theòs Lyrics")
        self.icon.set_tooltip_text("Theòs Lyrics · click to toggle synced lyrics")
        self.icon.set_from_icon_name("audio-x-generic")
        self.icon.connect("activate",lambda *_:self.overlay.toggle())
    def start(self):self.icon.set_visible(True)
    def set_artwork(self,path):
        if not path or not os.path.isfile(path):return
        try:self.icon.set_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_scale(path,24,24,True))
        except Exception:pass
