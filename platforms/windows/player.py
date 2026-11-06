"""
Windows media-session watcher for Theòs Lyrics.

Uses Windows Global System Media Transport Controls (GSMTC).
This module must run on Windows with PyWinRT installed.
"""

import asyncio
import threading


class PlayerWatcher:
    def __init__(self, client, overlay, dispatch=None):
        self.client = client
        self.overlay = overlay

        # Optional function for safely dispatching callbacks
        # onto the GUI thread (for example, Tkinter root.after).
        self.dispatch = dispatch or (lambda callback, *args: callback(*args))

        self.running = False
        self.thread = None
        self.loop = None
        self.manager = None

        self.track_id = None
        self.last_lyrics_key = None

        self.art_cb = lambda path: None
        self.overlay_track_cb = lambda track: None
        self.overlay_lyrics_cb = lambda lines: None
        self.overlay_position_cb = lambda position: None

    def set_artwork_callback(self, callback):
        self.art_cb = callback

    def set_overlay_track_callback(self, callback):
        self.overlay_track_cb = callback

    def set_overlay_lyrics_callback(self, callback):
        self.overlay_lyrics_cb = callback

    def set_overlay_position_callback(self, callback):
        self.overlay_position_cb = callback

    def _emit(self, callback, *args):
        self.dispatch(callback, *args)

    def start(self):
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(
            target=self._thread_main,
            name="TheosMediaWatcher",
            daemon=True,
        )
        self.thread.start()

    def stop(self):
        # The polling coroutine checks this flag every 700 ms.
        # Let asyncio.run() finish the coroutine normally.
        self.running = False

    def _thread_main(self):
        try:
            asyncio.run(self._run())
        except Exception as error:
            print("Theòs: Windows media watcher stopped:", error)
        finally:
            self.running = False

    async def _run(self):
        from winrt.windows.media.control import (
            GlobalSystemMediaTransportControlsSessionManager,
            GlobalSystemMediaTransportControlsSessionPlaybackStatus,
        )

        self.loop = asyncio.get_running_loop()

        print("Theòs: Connecting to Windows media sessions...")

        self.manager = await (
            GlobalSystemMediaTransportControlsSessionManager.request_async()
        )

        print("Theòs: Windows media session access ready.")

        while self.running:
            try:
                session = self.manager.get_current_session()

                if session is None:
                    self._handle_no_session()
                else:
                    await self._read_session(
                        session,
                        GlobalSystemMediaTransportControlsSessionPlaybackStatus,
                    )

            except Exception as error:
                print("Theòs: Media polling error:", error)

            await asyncio.sleep(0.7)

    async def _read_session(self, session, playback_status_type):
        properties = await session.try_get_media_properties_async()

        title = str(properties.title or "Unknown track")
        artist = str(properties.artist or "Unknown artist")
        album = str(properties.album_title or "")

        key = (title, artist, album)

        if key != self.track_id:
            self.track_id = key

            track = {
                "title": title,
                "artist": artist,
                "album": album,
                "art_url": "",
            }

            self._emit(self.overlay_track_cb, track)
            self._emit(self.art_cb, None)

            if key != self.last_lyrics_key:
                self.last_lyrics_key = key

                # LRCLIB requests are synchronous, so run them
                # in a worker thread rather than blocking asyncio.
                lines = await asyncio.to_thread(
                    self.client.fetch,
                    title,
                    artist,
                    album,
                )

                if self.running and key == self.track_id:
                    self._emit(self.overlay_lyrics_cb, lines)

        playback_info = session.get_playback_info()
        timeline = session.get_timeline_properties()

        status = playback_info.playback_status

        if status == playback_status_type.PLAYING:
            position = timeline.position.total_seconds()
            self._emit(self.overlay_position_cb, position)
        else:
            self._emit(self.overlay_position_cb, -1)

    def _handle_no_session(self):
        if self.track_id is not None:
            self.track_id = None
            self.last_lyrics_key = None

            self._emit(
                self.overlay_track_cb,
                {
                    "title": "Theòs Lyrics",
                    "artist": "Waiting for music...",
                    "album": "",
                    "art_url": "",
                },
            )
            self._emit(self.overlay_lyrics_cb, [])
            self._emit(self.overlay_position_cb, -1)
