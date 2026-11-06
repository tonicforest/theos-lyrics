"""
Theòs Lyrics — Windows Tkinter overlay.

Rendering: Pillow
Window: Tkinter
Animation: Tkinter after()
"""

import time
import tkinter as tk
from PIL import Image, ImageDraw, ImageFont, ImageTk


class LyricsOverlay:
    WIDTH = 900
    HEIGHT = 270
    TICK_MS = 33
    TRANSITION_DURATION = 0.32
    TRANSPARENT_COLOR = "#010203"

    def __init__(self, root=None):
        self.window = tk.Toplevel(root) if root else tk.Tk()
        self.window.title("Theòs Lyrics")
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)

        # Windows color-key transparency makes the rounded corners
        # transparent. The actual window behavior must be tested on Windows.
        try:
            self.window.configure(bg=self.TRANSPARENT_COLOR)
            self.window.attributes(
                "-transparentcolor", self.TRANSPARENT_COLOR
            )
        except tk.TclError:
            pass

        try:
            self.window.attributes("-alpha", 0.88)
        except tk.TclError:
            pass

        screen_width = self.window.winfo_screenwidth()
        self.width = min(1100, max(640, int(screen_width * 0.78)))
        self.height = self.HEIGHT

        self._position_window()

        self.canvas = tk.Label(
            self.window,
            bg=self.TRANSPARENT_COLOR,
            bd=0,
            highlightthickness=0,
        )
        self.canvas.pack()

        self.title = "Theòs Lyrics"
        self.artist = "Waiting for music..."
        self.album = ""

        self.lyrics = []
        self.position = 0.0

        # Playback interpolation
        self.anchor_position = 0.0
        self.anchor_time = time.monotonic()
        self.playing = False
        self.tick_id = None

        # Line transitions
        self.current_index = -1
        self.transition_from = -1
        self.transition_to = -1
        self.transition_started = 0.0
        self.transitioning = False

        self.visible = False
        self._photo = None

        self.window.protocol("WM_DELETE_WINDOW", self.hide)
        self.window.withdraw()
        self._render()

    # --------------------------------------------------
    # Window controls
    # --------------------------------------------------

    def _position_window(self):
        self.window.update_idletasks()
        screen_width = self.window.winfo_screenwidth()
        x = max(0, (screen_width - self.width) // 2)
        self.window.geometry(f"{self.width}x{self.height}+{x}+72")

    def show(self):
        self.visible = True
        self._position_window()
        self.window.deiconify()
        self.window.lift()
        self.window.attributes("-topmost", True)
        self._render()
        self._start_tick()

    def hide(self):
        self.visible = False
        self.window.withdraw()

    def toggle(self):
        if self.visible:
            self.hide()
        else:
            self.show()

    def close(self):
        if self.tick_id is not None:
            self.window.after_cancel(self.tick_id)
            self.tick_id = None
        self.window.destroy()

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

        self._render()

    def set_lyrics(self, lines):
        self.lyrics = sorted(
            list(lines or []),
            key=lambda item: item[0],
        )

        self.current_index = self._find_current_index(self.position)
        self.transition_from = self.current_index
        self.transition_to = self.current_index
        self.transitioning = False

        self._render()

    def set_position(self, position):
        position = float(position)

        # The player sends -1 when paused.
        if position < 0:
            self.playing = False
            self.position = max(0.0, self.position)
            self._render()
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
        if self.tick_id is None and self.visible:
            self.tick_id = self.window.after(self.TICK_MS, self._tick)

    def _tick(self):
        self.tick_id = None
        now = time.monotonic()

        if self.playing:
            self.position = (
                self.anchor_position + now - self.anchor_time
            )

            new_index = self._find_current_index(self.position)
            if new_index != self.current_index:
                self._change_active_line(new_index)

        if self.transitioning:
            if now - self.transition_started >= self.TRANSITION_DURATION:
                self.transitioning = False

        self._render()

        if self.visible and (self.playing or self.transitioning):
            self._start_tick()

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

        return max(0.0, min(1.0, elapsed / duration))

    def _animation_progress(self):
        if not self.transitioning:
            return 1.0

        elapsed = time.monotonic() - self.transition_started
        progress = min(1.0, elapsed / self.TRANSITION_DURATION)

        # Ease-out cubic.
        return 1.0 - (1.0 - progress) ** 3

    # --------------------------------------------------
    # Pillow rendering helpers
    # --------------------------------------------------

    @staticmethod
    def _font(size, bold=False):
        candidates = (
            ["segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"]
            if bold else
            ["segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"]
        )

        for name in candidates:
            try:
                return ImageFont.truetype(name, size)
            except OSError:
                continue

        return ImageFont.load_default()

    @staticmethod
    def _row_opacity(row):
        if row == 0:
            return 1.0
        if abs(row) == 1:
            return 0.68
        if abs(row) == 2:
            return 0.42
        return 0.0

    def _draw_centered(self, draw, text, y, font, fill):
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) / 2
        draw.text((x, y), text, font=font, fill=fill)
        return x, text_width, bbox[3] - bbox[1]

    def _draw_centered_faded(self, image, text, y, font, color, opacity):
        if opacity <= 0:
            return

        layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        alpha = int(255 * max(0.0, min(1.0, opacity)))

        self._draw_centered(
            draw,
            text,
            int(y),
            font,
            (*color, alpha),
        )
        image.alpha_composite(layer)

    # --------------------------------------------------
    # Main renderer
    # --------------------------------------------------

    def _render(self):
        image = Image.new(
            "RGBA",
            (self.width, self.height),
            (0, 0, 0, 0),
        )
        draw = ImageDraw.Draw(image)

        # Rounded dark background and subtle border.
        draw.rounded_rectangle(
            (0, 0, self.width - 1, self.height - 1),
            radius=22,
            fill=(9, 12, 20, 224),
            outline=(89, 122, 184, 46),
            width=1,
        )

        # Metadata.
        metadata = self.title
        if self.artist:
            metadata += "   ·   " + self.artist

        metadata_font = self._font(12)
        self._draw_centered(
            draw,
            metadata,
            24,
            metadata_font,
            (179, 194, 224, 204),
        )

        # Top blue accent.
        draw.rectangle(
            (self.width // 2 - 18, 53, self.width // 2 + 18, 55),
            fill=(77, 158, 255, 217),
        )

        if not self.lyrics:
            self._draw_centered(
                draw,
                "Waiting for synchronized lyrics...",
                120,
                self._font(17),
                (209, 217, 235, 166),
            )
            self._finish_render(image)
            return

        if self.current_index < 0:
            self._draw_centered(
                draw,
                "♪",
                125,
                self._font(24),
                (115, 173, 255, 204),
            )
            self._finish_render(image)
            return

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

            lyric = str(self.lyrics[i][1] or "").strip() or "♪"

            if i == self.current_index:
                self._draw_karaoke(
                    image,
                    lyric,
                    int(y),
                    self._word_progress(i),
                    opacity,
                )
            else:
                self._draw_centered_faded(
                    image,
                    lyric,
                    int(y),
                    self._font(15, bold=True),
                    (176, 191, 221),
                    opacity,
                )

        # Bottom blue accent.
        draw = ImageDraw.Draw(image)
        draw.rectangle(
            (self.width // 2 - 10, 245, self.width // 2 + 10, 247),
            fill=(77, 158, 255, 166),
        )

        self._finish_render(image)

    def _draw_karaoke(self, image, text, y, progress, opacity):
        font = self._font(19, bold=True)

        bbox = ImageDraw.Draw(image).textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (self.width - text_width) / 2

        alpha = int(255 * max(0.0, min(1.0, opacity)))

        # Muted full line.
        layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        layer_draw = ImageDraw.Draw(layer)
        layer_draw.text(
            (x, y),
            text,
            font=font,
            fill=(166, 184, 220, alpha),
        )
        image.alpha_composite(layer)

        # White reveal clipped from left to right.
        reveal_width = int(text_width * max(0.0, min(1.0, progress)))
        if reveal_width <= 0:
            return

        white_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        white_draw = ImageDraw.Draw(white_layer)
        white_draw.text(
            (x, y),
            text,
            font=font,
            fill=(245, 250, 255, alpha),
        )

        mask = Image.new("L", image.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rectangle(
            (int(x), y - 3, int(x + reveal_width), y + text_height + 8),
            fill=255,
        )

        image.alpha_composite(
            Image.composite(
                white_layer,
                Image.new("RGBA", image.size, (0, 0, 0, 0)),
                mask,
            )
        )

    def _finish_render(self, image):
        self._photo = ImageTk.PhotoImage(image)
        self.canvas.configure(image=self._photo)


