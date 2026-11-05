import os, urllib.parse
from gi.repository import GLib
import dbus
import dbus.mainloop.glib

PREFIX="org.mpris.MediaPlayer2."
class PlayerWatcher:
    def __init__(self,client,overlay):
        self.client=client; self.overlay=overlay; self.bus=None
        self.track_id=None; self.last_lyrics_key=None
        self.art_cb=lambda path:None
        self.overlay_track_cb=lambda track:None
        self.overlay_lyrics_cb=lambda lines:None
        self.overlay_position_cb=lambda pos:None
    def set_artwork_callback(self,cb): self.art_cb=cb
    def set_overlay_track_callback(self,cb): self.overlay_track_cb=cb
    def set_overlay_lyrics_callback(self,cb): self.overlay_lyrics_cb=cb
    def set_overlay_position_callback(self,cb): self.overlay_position_cb=cb
    def start(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus=dbus.SessionBus()
        GLib.timeout_add(700,self.poll)
    def _active(self):
        names=[str(n) for n in self.bus.list_names() if str(n).startswith(PREFIX)]
        fallback=None
        for name in names:
            try:
                obj=self.bus.get_object(name,"/org/mpris/MediaPlayer2")
                p=dbus.Interface(obj,"org.freedesktop.DBus.Properties")
                state=str(p.Get("org.mpris.MediaPlayer2.Player","PlaybackStatus"))
                if state=="Playing": return name
                fallback=name
            except Exception: pass
        return fallback
    def poll(self):
        try:
            name=self._active()
            if not name: return True
            obj=self.bus.get_object(name,"/org/mpris/MediaPlayer2")
            p=dbus.Interface(obj,"org.freedesktop.DBus.Properties")
            meta=p.Get("org.mpris.MediaPlayer2.Player","Metadata")
            state=str(p.Get("org.mpris.MediaPlayer2.Player","PlaybackStatus"))
            pos=int(p.Get("org.mpris.MediaPlayer2.Player","Position"))/1e6
            title=str(meta.get("xesam:title","Unknown track"))
            artist=", ".join(map(str,meta.get("xesam:artist",[]))) or "Unknown artist"
            album=str(meta.get("xesam:album",""))
            art=str(meta.get("mpris:artUrl",""))
            key=(title,artist,album)
            if key!=self.track_id:
                self.track_id=key
                track={"title":title,"artist":artist,"album":album,"art_url":art}
                self.overlay_track_cb(track)
                self.art_cb(self._art_path(art))
                if key!=self.last_lyrics_key:
                    self.last_lyrics_key=key
                    lines=self.client.fetch(title,artist,album)
                    GLib.idle_add(self.overlay_lyrics_cb,lines)
            self.overlay_position_cb(pos if state=="Playing" else -1)
        except Exception: pass
        return True
    def _art_path(self,url):
        if not url:return None
        u=urllib.parse.urlparse(url)
        if u.scheme=="file": return urllib.parse.unquote(u.path)
        if u.scheme in ("http","https"):
            try:
                import requests
                os.makedirs(os.path.expanduser("~/.cache/theos-lyrics"),exist_ok=True)
                ext=os.path.splitext(u.path)[1] or ".jpg"
                path=os.path.expanduser("~/.cache/theos-lyrics/cover"+ext)
                r=requests.get(url,timeout=4); r.raise_for_status()
                open(path,"wb").write(r.content)
                return path
            except Exception:return None
        return None
