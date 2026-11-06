
import gi
gi.require_version("Gtk", "3.0")

from gi.repository import GLib
from Xlib import X, display


class OutsideClickMonitor:

    def __init__(self, window, on_outside_click):
        self.window = window
        self.callback = on_outside_click

        self.display = None
        self.root = None
        self.source_id = None
        self.active = False

    def start(self):
        if self.active:
            return

        try:
            self.display = display.Display()
            self.root = self.display.screen().root

            self.root.grab_button(
                X.AnyButton,
                X.AnyModifier,
                False,
                X.ButtonPressMask,
                X.GrabModeSync,
                X.GrabModeAsync,
                X.NONE,
                X.NONE
            )

            self.display.sync()

            self.active = True
            self.source_id = GLib.timeout_add(
                15,
                self._poll
            )

        except Exception as error:
            print("Theòs: Outside-click monitor unavailable:", error)
            self.stop()

    def stop(self):
        self.active = False

        if self.source_id:
            GLib.source_remove(self.source_id)
            self.source_id = None

        if self.display:
            try:
                self.root.ungrab_button(
                    X.AnyButton,
                    X.AnyModifier
                )
                self.display.sync()
                self.display.close()
            except Exception:
                pass

        self.display = None
        self.root = None

    def _poll(self):
        if not self.active or not self.display:
            return False

        try:
            while self.display.pending_events():
                event = self.display.next_event()

                if event.type != X.ButtonPress:
                    continue

                x = event.root_x
                y = event.root_y

                wx, wy = self.window.get_position()
                ww, wh = self.window.get_size()

                inside = (
                    wx <= x <= wx + ww
                    and wy <= y <= wy + wh
                )

                # Replay the click so the application
                # underneath still receives it.
                self.display.allow_events(
                    X.ReplayPointer,
                    event.time
                )
                self.display.flush()

                if not inside:
                    # Allow the original click to reach
                    # its application before hiding.
                    GLib.timeout_add(
                        50,
                        self._hide_overlay
                    )

        except Exception as error:
            print("Theòs: Outside-click monitor stopped:", error)
            self.stop()
            return False

        return True

    def _hide_overlay(self):
        if self.active:
            self.callback()
        return False
