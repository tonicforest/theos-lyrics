
import time

from outside_click import OutsideClickMonitor

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

from gi.repository import Gtk, Gdk, GLib, Pango, PangoCairo


class LyricsOverlay:

    def __init__(self):
        self.title = "Theòs Lyrics"
        self.artist = "Waiting for music..."
        self.album = ""

        self.lyrics = []
        self.position = 0.0

        # Playback interpolation
        self.anchor_position = 0.0
        self.anchor_time = time.monotonic()
        self.playing = False
        self.tick_active = False

        # Line transitions
        self.current_index = -1
        self.transition_from = -1
        self.transition_to = -1
        self.transition_started = 0.0
        self.transition_duration = 0.32
        self.transitioning = False

        self.window_width = 900
        self.window_height = 270

        screen = Gdk.Screen.get_default()

        if screen:
            self.window_width = min(
                1100,
                max(640, int(screen.get_width() * 0.78))
            )

        self.window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.window.set_title("Theòs Lyrics")
        self.window.set_decorated(False)
        self.window.set_resizable(False)
        self.window.set_keep_above(True)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_skip_pager_hint(True)
        self.window.set_accept_focus(False)
        self.window.set_focus_on_map(False)
        self.window.set_type_hint(Gdk.WindowTypeHint.NOTIFICATION)
        self.window.set_default_size(
            self.window_width,
            self.window_height
        )

        if screen:
            visual = screen.get_rgba_visual()
            if visual:
                self.window.set_visual(visual)

        self.window.set_app_paintable(True)

        self.canvas = Gtk.DrawingArea()
        self.canvas.set_size_request(
            self.window_width,
            self.window_height
        )

        self.canvas.connect("draw", self._draw)
        self.window.add(self.canvas)
        self.window.connect("delete-event", self._close)
        self.outside_monitor = OutsideClickMonitor(
            self.window,
            self.hide
        )

        self._position_window()
        self.window.show_all()

    # --------------------------------------------------
    # Window controls
    # --------------------------------------------------

    def _position_window(self):
        screen = Gdk.Screen.get_default()

        if screen:
            x = max(
                0,
                (screen.get_width() - self.window_width) // 2
            )
            self.window.move(x, 72)

    def show(self):
        self.window.show_all()
        self._position_window()
        self.outside_monitor.start()

    def hide(self):
        self.outside_monitor.stop()
        self.window.hide()

    def toggle(self):
        if self.window.get_visible():
            self.hide()
        else:
            self.show()

    def _close(self, *_):
        self.hide()
        return True

    # --------------------------------------------------
    # Player callbacks
    # --------------------------------------------------

    def set_track(self, track):
        track = track or {}

        self.title = str(track.get("title") or "Unknown track")
        self.artist = str(track.get("artist") or "Unknown artist")
        self.album = str(track.get("album") or "")

        self.lyrics = []
        self.position = 0.0
        self.anchor_position = 0.0
        self.anchor_time = time.monotonic()

        self.current_index = -1
        self.transition_from = -1
        self.transition_to = -1
        self.transitioning = False

        self.canvas.queue_draw()

    def set_lyrics(self, lines):
        self.lyrics = sorted(
            list(lines or []),
            key=lambda item: item[0]
        )

        self.current_index = self._find_current_index(
            self.position
        )

        self.transition_from = self.current_index
        self.transition_to = self.current_index
        self.transitioning = False

        self.canvas.queue_draw()

    def set_position(self, position):
        position = float(position)

        # Player sends -1 when paused.
        if position < 0:
            self.playing = False
            self.position = max(0.0, self.position)
            self.canvas.queue_draw()
            return

        self.playing = True
        self.anchor_position = position
        self.anchor_time = time.monotonic()
        self.position = position

        new_index = self._find_current_index(position)

        if new_index != self.current_index:
            self._change_active_line(new_index)

        self._start_tick()

    # --------------------------------------------------
    # Playback interpolation
    # --------------------------------------------------

    def _start_tick(self):
        if not self.tick_active:
            self.tick_active = True
            GLib.timeout_add(33, self._tick)

    def _tick(self):
        now = time.monotonic()

        if self.playing:
            # Estimate current playback position between
            # the player's 700 ms position updates.
            self.position = (
                self.anchor_position
                + now - self.anchor_time
            )

            new_index = self._find_current_index(self.position)

            if new_index != self.current_index:
                self._change_active_line(new_index)

        if self.transitioning:
            if now - self.transition_started >= self.transition_duration:
                self.transitioning = False

        self.canvas.queue_draw()

        if self.playing or self.transitioning:
            return True

        self.tick_active = False
        return False

    # --------------------------------------------------
    # Lyric synchronization
    # --------------------------------------------------

    def _find_current_index(self, position):
        if not self.lyrics:
            return -1

        index = -1

        for i, item in enumerate(self.lyrics):
            if item[0] <= position:
                index = i
            else:
                break

        return index

    def _change_active_line(self, new_index):
        old_index = self.current_index
        self.current_index = new_index

        if old_index < 0 or new_index < 0:
            self.transition_from = new_index
            self.transition_to = new_index
            self.transitioning = False
            return

        self.transition_from = old_index
        self.transition_to = new_index
        self.transition_started = time.monotonic()
        self.transitioning = True

        self._start_tick()

    # --------------------------------------------------
    # Continuous letter-level karaoke gradient
    # --------------------------------------------------

    
    def _word_progress(self, index):
        if index < 0 or index >= len(self.lyrics):
            return 0.0

        start = float(self.lyrics[index][0])

        if index + 1 < len(self.lyrics):
            end = float(self.lyrics[index + 1][0])
        else:
            end = start + 4.0

        duration = max(0.5, end - start)

        elapsed = max(0.0, self.position - start)

        # Start the sweep slightly earlier and let it finish
        # slightly before the next line.
        progress = elapsed / duration

        return max(0.0, min(1.0, progress))


    
    def _draw_karaoke_line(self, cr, text, y, progress, opacity):
        """
        Draw muted text, then reveal a white copy from
        left to right using a smoothly moving clipping boundary.
        """

        layout = PangoCairo.create_layout(cr)

        font = Pango.FontDescription()
        font.set_family("Sans")
        font.set_absolute_size(19 * Pango.SCALE)
        font.set_weight(Pango.Weight.BOLD)

        layout.set_font_description(font)
        layout.set_single_paragraph_mode(True)
        layout.set_text(text, -1)

        text_width, text_height = layout.get_pixel_size()
        x = (self.window_width - text_width) / 2

        progress = max(0.0, min(1.0, progress))

        # Draw the complete line in muted grey-blue.
        cr.move_to(x, y)
        cr.set_source_rgba(
            0.65, 0.72, 0.86, 1.0
        )
        PangoCairo.show_layout(cr, layout)

        if progress <= 0:
            return

        # Draw the white copy only up to the moving boundary.
        reveal_width = text_width * progress

        cr.save()

        cr.rectangle(
            x,
            y - 3,
            reveal_width,
            text_height + 8
        )
        cr.clip()

        cr.move_to(x, y)
        cr.set_source_rgba(
            0.96, 0.98, 1.0, 1.0
        )
        PangoCairo.show_layout(cr, layout)

        cr.restore()


    # --------------------------------------------------
    # Line transition animation
    # --------------------------------------------------

    def _animation_progress(self):
        if not self.transitioning:
            return 1.0

        elapsed = time.monotonic() - self.transition_started

        progress = min(
            1.0,
            elapsed / self.transition_duration
        )

        # Ease-out cubic.
        return 1.0 - (1.0 - progress) ** 3

    
    @staticmethod
    def _row_opacity(row):
        if row == 0:
            return 1.0

        if abs(row) == 1:
            return 0.68

        if abs(row) == 2:
            return 0.42

        return 0.0


    # --------------------------------------------------
    # Drawing helpers
    # --------------------------------------------------

    @staticmethod
    def _rounded_rectangle(cr, x, y, width, height, radius):
        cr.new_sub_path()

        cr.arc(
            x + width - radius, y + radius,
            radius, -1.5708, 0
        )
        cr.arc(
            x + width - radius, y + height - radius,
            radius, 0, 1.5708
        )
        cr.arc(
            x + radius, y + height - radius,
            radius, 1.5708, 3.14159
        )
        cr.arc(
            x + radius, y + radius,
            radius, 3.14159, 4.71239
        )

        cr.close_path()

    def _draw_text(
        self, cr, text, y, size, color, bold=False
    ):
        layout = PangoCairo.create_layout(cr)

        font = Pango.FontDescription()
        font.set_family("Sans")
        font.set_absolute_size(size * Pango.SCALE)
        font.set_weight(
            Pango.Weight.BOLD if bold else Pango.Weight.NORMAL
        )

        layout.set_font_description(font)
        layout.set_width(
            int((self.window_width - 80) * Pango.SCALE)
        )
        layout.set_alignment(Pango.Alignment.CENTER)
        layout.set_ellipsize(Pango.EllipsizeMode.END)
        layout.set_single_paragraph_mode(True)
        layout.set_text(str(text), -1)

        cr.set_source_rgba(*color)
        cr.move_to(40, y)
        PangoCairo.show_layout(cr, layout)

    # --------------------------------------------------
    # Main drawing function
    # --------------------------------------------------

    def _draw(self, widget, cr):
        width = self.window_width
        height = self.window_height

        # Clear transparent canvas.
        cr.save()
        cr.set_operator(0)
        cr.paint()
        cr.restore()

        # Uniform dark background.
        self._rounded_rectangle(
            cr, 0, 0, width, height, 22
        )

        cr.set_source_rgba(
            0.035, 0.045, 0.075, 0.88
        )
        cr.fill_preserve()

        cr.set_source_rgba(
            0.35, 0.48, 0.72, 0.18
        )
        cr.set_line_width(1)
        cr.stroke()

        # Metadata.
        metadata = self.title

        if self.artist:
            metadata += "   ·   " + self.artist

        self._draw_text(
            cr,
            metadata,
            24,
            12,
            (0.70, 0.76, 0.88, 0.80)
        )

        # Top blue accent.
        cr.set_source_rgba(
            0.30, 0.62, 1.0, 0.85
        )
        cr.rectangle(width / 2 - 18, 53, 36, 2)
        cr.fill()

        if not self.lyrics:
            self._draw_text(
                cr,
                "Waiting for synchronized lyrics...",
                120,
                17,
                (0.82, 0.85, 0.92, 0.65)
            )
            return False

        if self.current_index < 0:
            self._draw_text(
                cr,
                "♪",
                125,
                24,
                (0.45, 0.68, 1.0, 0.80)
            )
            return False

        progress = self._animation_progress()

        old_index = self.transition_from
        new_index = self.transition_to

        if not self.transitioning:
            old_index = new_index = self.current_index

        visible = set()

        for i in range(old_index - 2, old_index + 3):
            visible.add(i)

        for i in range(new_index - 2, new_index + 3):
            visible.add(i)

        center_y = 145
        spacing = 39

        for i in sorted(visible):
            if i < 0 or i >= len(self.lyrics):
                continue

            old_row = i - old_index
            new_row = i - new_index

            old_opacity = self._row_opacity(old_row)
            new_opacity = self._row_opacity(new_row)

            opacity = (
                old_opacity * (1 - progress)
                + new_opacity * progress
            )

            if opacity <= 0.01:
                continue

            old_y = center_y + old_row * spacing
            new_y = center_y + new_row * spacing

            y = old_y * (1 - progress) + new_y * progress

            lyric = str(self.lyrics[i][1] or "").strip()

            if not lyric:
                lyric = "♪"

            cr.save()
            cr.push_group()

            if i == self.current_index:
                word_progress = self._word_progress(i)

                self._draw_karaoke_line(
                    cr,
                    lyric,
                    y,
                    word_progress,
                    opacity
                )
            else:
                self._draw_text(
                    cr,
                    lyric,
                    y,
                    15,
                    (0.69, 0.75, 0.87, 1.0)
                )

            cr.pop_group_to_source()
            cr.paint_with_alpha(opacity)
            cr.restore()

        # Bottom blue accent.
        cr.set_source_rgba(
            0.30, 0.62, 1.0, 0.65
        )
        cr.rectangle(width / 2 - 10, 245, 20, 2)
        cr.fill()

        return False

