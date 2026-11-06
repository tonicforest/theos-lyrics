"""Windows entry point for Theòs Lyrics."""

import tkinter as tk
import queue

from lyrics import LyricsClient
from platforms.windows.overlay import LyricsOverlay
from platforms.windows.player import PlayerWatcher
from platforms.windows.tray import TrayIcon
from platforms.windows.outside_click import OutsideClickMonitor


def main():
    root = tk.Tk()
    root.withdraw()
    root.title("Theòs Lyrics")

    # Thread-safe queue for communication with the GUI thread.
    event_queue = queue.Queue()
    closing = False

    def dispatch(callback, *args):
        """Queue callbacks from background threads for Tkinter."""
        if not closing:
            event_queue.put((callback, args))

    def process_dispatch_queue():
        """Execute queued callbacks safely on the Tkinter thread."""
        if closing:
            return

        # Limit work per cycle so the GUI remains responsive.
        for _ in range(100):
            try:
                callback, args = event_queue.get_nowait()
            except queue.Empty:
                break

            if closing:
                break

            callback(*args)

        if not closing:
            root.after(25, process_dispatch_queue)

    overlay = LyricsOverlay(root)
    client = LyricsClient()

    watcher = PlayerWatcher(
        client,
        overlay,
        dispatch=dispatch,
    )
    # Connect Windows media events to the overlay.
    watcher.set_overlay_track_callback(overlay.set_track)
    watcher.set_overlay_lyrics_callback(overlay.set_lyrics)
    watcher.set_overlay_position_callback(overlay.set_position)
    outside_monitor = OutsideClickMonitor(
        root,
        overlay.window,
        overlay.hide,
    )

    tray = None

    def toggle_overlay():
        if overlay.visible:
            outside_monitor.stop()
            overlay.hide()
        else:
            overlay.show()
            outside_monitor.start()

    def shutdown():
        nonlocal closing

        if closing:
            return

        closing = True

        outside_monitor.stop()
        watcher.stop()

        if tray:
            tray.stop()

        overlay.close()
        root.destroy()

    tray = TrayIcon(
        toggle_callback=toggle_overlay,
        exit_callback=shutdown,
        dispatch=dispatch,
    )

    root.protocol("WM_DELETE_WINDOW", shutdown)
    overlay.window.bind("<Escape>", lambda event: shutdown())

    # Start queue processing before background services.
    root.after(25, process_dispatch_queue)

    tray.start()
    watcher.start()

    print("Theòs Lyrics is running in the system tray.")
    root.mainloop()


if __name__ == "__main__":
    main()
