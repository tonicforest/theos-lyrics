"""Windows system tray icon for Theòs Lyrics."""

import pystray
from PIL import Image, ImageDraw


class TrayIcon:
    def __init__(self, toggle_callback, exit_callback, dispatch):
        self.toggle_callback = toggle_callback
        self.exit_callback = exit_callback
        self.dispatch = dispatch
        self.icon = None

    @staticmethod
    def _create_image():
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Blue rounded background.
        draw.rounded_rectangle(
            (3, 3, 61, 61),
            radius=16,
            fill=(20, 32, 54, 255),
        )

        # Three stylized lyric lines.
        draw.rounded_rectangle(
            (15, 17, 49, 21),
            radius=2,
            fill=(120, 175, 255, 255),
        )
        draw.rounded_rectangle(
            (10, 29, 54, 35),
            radius=3,
            fill=(245, 248, 255, 255),
        )
        draw.rounded_rectangle(
            (17, 43, 47, 47),
            radius=2,
            fill=(120, 175, 255, 255),
        )

        return image

    def start(self):
        menu = pystray.Menu(
            pystray.MenuItem(
                "Show / Hide Lyrics",
                lambda icon, item: self.dispatch(
                    self.toggle_callback
                ),
                default=True,
            ),
            pystray.MenuItem(
                "Exit Theòs Lyrics",
                lambda icon, item: self.dispatch(
                    self.exit_callback
                ),
            ),
        )

        self.icon = pystray.Icon(
            "theos_lyrics",
            self._create_image(),
            "Theòs Lyrics",
            menu,
        )

        self.icon.run_detached()

    def stop(self):
        if self.icon:
            self.icon.stop()
            self.icon = None
