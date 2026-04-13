"""
Android File Explorer - Kivy
Browses /storage/emulated/0/, navigates folders,
and shows a popup when a file is tapped.
Requests READ_EXTERNAL_STORAGE at runtime (Android 6+).
"""

import os

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.utils import platform

# ── Android permission helper ──────────────────────────────────────────────────
def request_android_permission():
    """Request READ_EXTERNAL_STORAGE on Android 6+ (API 23+)."""
    if platform != "android":
        return  # Nothing to do on desktop

    try:
        from android.permissions import request_permissions, Permission  # type: ignore
        request_permissions([Permission.READ_EXTERNAL_STORAGE])
    except Exception as exc:
        print(f"[permission] Could not request storage permission: {exc}")


# ── Constants ──────────────────────────────────────────────────────────────────
ROOT_PATH      = "/storage/emulated/0/"
BG_COLOR       = (0.10, 0.10, 0.14, 1)
HEADER_COLOR   = (0.15, 0.15, 0.20, 1)
FOLDER_COLOR   = (0.18, 0.38, 0.62, 1)   # blue-ish
FILE_COLOR     = (0.22, 0.22, 0.28, 1)   # dark grey
ACCENT_COLOR   = (0.30, 0.75, 0.55, 1)   # mint green
TEXT_COLOR     = (0.92, 0.92, 0.95, 1)
BUTTON_HEIGHT  = dp(52)
FONT_SIZE      = dp(15)


# ── Helper: styled button factory ─────────────────────────────────────────────
def make_entry_button(label_text: str, bg_color: tuple, callback) -> Button:
    btn = Button(
        text=label_text,
        size_hint_y=None,
        height=BUTTON_HEIGHT,
        background_normal="",
        background_color=bg_color,
        color=TEXT_COLOR,
        font_size=FONT_SIZE,
        halign="left",
        valign="middle",
        padding_x=dp(16),
        text_size=(Window.width - dp(32), None),
    )
    btn.bind(on_release=callback)
    return btn


# ── Main widget ────────────────────────────────────────────────────────────────
class FileExplorer(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=0, **kwargs)
        Window.clearcolor = BG_COLOR

        # ── Header bar ────────────────────────────────────────────────────────
        self.header = BoxLayout(
            size_hint_y=None,
            height=dp(56),
            padding=[dp(12), dp(8)],
            spacing=dp(8),
        )
        with self.header.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(*HEADER_COLOR)
            self.header_rect = Rectangle(pos=self.header.pos, size=self.header.size)
        self.header.bind(
            pos=lambda inst, v: setattr(self.header_rect, "pos", v),
            size=lambda inst, v: setattr(self.header_rect, "size", v),
        )

        self.back_btn = Button(
            text="◀  Back",
            size_hint=(None, 1),
            width=dp(90),
            background_normal="",
            background_color=ACCENT_COLOR,
            color=(0.05, 0.05, 0.05, 1),
            font_size=dp(14),
            bold=True,
        )
        self.back_btn.bind(on_release=self.go_back)

        self.path_label = Label(
            text=ROOT_PATH,
            color=TEXT_COLOR,
            font_size=dp(13),
            halign="left",
            valign="middle",
            shorten=True,
            shorten_from="left",
        )
        self.path_label.bind(size=lambda inst, v: setattr(inst, "text_size", v))

        self.header.add_widget(self.back_btn)
        self.header.add_widget(self.path_label)

        # ── Scrollable listing ─────────────────────────────────────────────────
        self.scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.listing = GridLayout(
            cols=1,
            size_hint_y=None,
            spacing=dp(2),
            padding=[dp(8), dp(8)],
        )
        self.listing.bind(minimum_height=self.listing.setter("height"))
        self.scroll.add_widget(self.listing)

        self.add_widget(self.header)
        self.add_widget(self.scroll)

        # History stack for "back" navigation
        self.history: list[str] = []

        self.load_path(ROOT_PATH)

    # ── Directory loader ───────────────────────────────────────────────────────
    def load_path(self, path: str):
        self.listing.clear_widgets()
        self.path_label.text = path

        try:
            entries = sorted(os.listdir(path))
        except PermissionError:
            self._show_popup("Permission Denied", f"Cannot read:\n{path}")
            return
        except FileNotFoundError:
            self._show_popup("Not Found", f"Path does not exist:\n{path}")
            return

        if not entries:
            self.listing.add_widget(
                Label(
                    text="(empty folder)",
                    color=(0.55, 0.55, 0.60, 1),
                    size_hint_y=None,
                    height=BUTTON_HEIGHT,
                    font_size=FONT_SIZE,
                )
            )
            return

        for name in entries:
            full_path = os.path.join(path, name)
            if os.path.isdir(full_path):
                icon = "📁  "
                color = FOLDER_COLOR
                cb = self._folder_callback(full_path)
            else:
                icon = "📄  "
                color = FILE_COLOR
                cb = self._file_callback(name, full_path)

            btn = make_entry_button(icon + name, color, cb)
            self.listing.add_widget(btn)

    # ── Callbacks (closures) ───────────────────────────────────────────────────
    def _folder_callback(self, path: str):
        def on_press(instance):
            self.history.append(self.path_label.text)
            self.load_path(path)
        return on_press

    def _file_callback(self, name: str, path: str):
        def on_press(instance):
            self._show_popup(
                "File Selected",
                f"[b]Name:[/b]  {name}\n\n[b]Path:[/b]  {path}",
                markup=True,
            )
        return on_press

    # ── Navigation ─────────────────────────────────────────────────────────────
    def go_back(self, *args):
        if self.history:
            prev = self.history.pop()
            self.load_path(prev)
        else:
            self.load_path(ROOT_PATH)

    # ── Popup helper ───────────────────────────────────────────────────────────
    def _show_popup(self, title: str, message: str, markup: bool = False):
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))

        msg_label = Label(
            text=message,
            markup=markup,
            color=TEXT_COLOR,
            font_size=dp(14),
            halign="left",
            valign="top",
            size_hint_y=1,
        )
        msg_label.bind(size=lambda inst, v: setattr(inst, "text_size", (v[0], None)))

        close_btn = Button(
            text="Close",
            size_hint=(1, None),
            height=dp(44),
            background_normal="",
            background_color=ACCENT_COLOR,
            color=(0.05, 0.05, 0.05, 1),
            bold=True,
            font_size=dp(15),
        )

        content.add_widget(msg_label)
        content.add_widget(close_btn)

        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.88, 0.42),
            background_color=(0.12, 0.12, 0.18, 1),
            title_color=ACCENT_COLOR,
            title_size=dp(16),
            separator_color=ACCENT_COLOR,
        )
        close_btn.bind(on_release=popup.dismiss)
        popup.open()


# ── App entry point ────────────────────────────────────────────────────────────
class FileExplorerApp(App):
    def build(self):
        request_android_permission()   # ask for storage permission early
        self.title = "File Explorer"
        return FileExplorer()


if __name__ == "__main__":
    FileExplorerApp().run()
