"""Detect mouse clicks outside the Windows lyrics overlay."""

import ctypes
import tkinter as tk


class POINT(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_long),
        ("y", ctypes.c_long),
    ]


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class OutsideClickMonitor:
    VK_LBUTTON = 0x01
    GA_ROOT = 2
    POLL_INTERVAL = 50

    def __init__(self, root, window, hide_callback):
        self.root = root
        self.window = window
        self.hide_callback = hide_callback

        self.user32 = ctypes.WinDLL("user32", use_last_error=True)

        self.user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
        self.user32.GetAsyncKeyState.restype = ctypes.c_short

        self.user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
        self.user32.GetCursorPos.restype = ctypes.c_bool

        self.user32.GetWindowRect.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(RECT),
        ]
        self.user32.GetWindowRect.restype = ctypes.c_bool

        self.user32.GetAncestor.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint,
        ]
        self.user32.GetAncestor.restype = ctypes.c_void_p

        self.running = False
        self.after_id = None
        self.was_pressed = False

    def start(self):
        if self.running:
            return

        self.running = True
        self.was_pressed = bool(
            self.user32.GetAsyncKeyState(self.VK_LBUTTON) & 0x8000
        )
        self._schedule()

    def stop(self):
        self.running = False

        if self.after_id is not None:
            try:
                self.root.after_cancel(self.after_id)
            except tk.TclError:
                pass

            self.after_id = None

    def _schedule(self):
        if self.running:
            self.after_id = self.root.after(
                self.POLL_INTERVAL,
                self._check,
            )

    def _check(self):
        self.after_id = None

        if not self.running:
            return

        pressed = bool(
            self.user32.GetAsyncKeyState(self.VK_LBUTTON) & 0x8000
        )

        # Detect a new click rather than repeatedly reacting while held.
        if pressed and not self.was_pressed:
            self._handle_click()

        self.was_pressed = pressed
        self._schedule()

    def _handle_click(self):
        try:
            self.window.update_idletasks()

            hwnd = self.user32.GetAncestor(
                self.window.winfo_id(),
                self.GA_ROOT,
            )

            if not hwnd:
                return

            rect = RECT()
            point = POINT()

            if not self.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                return

            if not self.user32.GetCursorPos(ctypes.byref(point)):
                return

            inside = (
                rect.left <= point.x < rect.right
                and rect.top <= point.y < rect.bottom
            )

            if not inside:
                self.stop()
                self.hide_callback()

        except (tk.TclError, OSError):
            self.stop()
