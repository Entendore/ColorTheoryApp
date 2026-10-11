"""Shared custom Kivy widgets and UI primitives."""
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Rectangle, Ellipse, Line
from kivy.metrics import dp, sp as _sp
from kivy.lang import Builder
from kivy.app import App
from color_utils import rgb_hex, fg_for

FS = _sp

# Load KV styles for standard buttons
Builder.load_string('''
<NavButton@ToggleButton>:
    background_normal: ''
    background_down: ''
    background_color: (.16, .16, .29, 1) if self.state == 'normal' else (.29, .29, .48, 1)
    color: (.88, .88, .88, 1) if self.state == 'normal' else (1, 1, 1, 1)
    halign: 'left'
    padding_x: dp(14)
    font_size: sp(13)
    size_hint_y: None
    height: dp(44)
''')

def draw_rr(canvas_grp, x, y, w, h, rad, rgba):
    with canvas_grp:
        Color(*rgba)
        Ellipse(pos=(x, y), size=(rad * 2, rad * 2))
        Ellipse(pos=(x + w - rad * 2, y), size=(rad * 2, rad * 2))
        Ellipse(pos=(x, y + h - rad * 2), size=(rad * 2, rad * 2))
        Ellipse(pos=(x + w - rad * 2, y + h - rad * 2), size=(rad * 2, rad * 2))
        Rectangle(pos=(x + rad, y), size=(w - 2 * rad, h))
        Rectangle(pos=(x, y + rad), size=(rad, h - 2 * rad))
        Rectangle(pos=(x + w - rad, y + rad), size=(rad, h - 2 * rad))
        Rectangle(pos=(x + rad, y + h - rad), size=(w - 2 * rad, rad))


class ColorPreview(BoxLayout):
    def __init__(self, r=0, g=0, b=0, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            self._bg_c = Color(r, g, b, 1)
            self._bg_r = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *_):
        self._bg_r.pos = self.pos; self._bg_r.size = self.size

    def set_color(self, r, g, b):
        self._bg_c.rgba = (r, g, b, 1)


class BgCard(BoxLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            self._bg_c = Color(.145, .145, .25, 1)
            self._bg_r = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *_):
        self._bg_r.pos = self.pos; self._bg_r.size = self.size


class DarkSeparator(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.size_hint_y = None; self.height = dp(1)
        with self.canvas.before:
            self._c = Color(.16, .16, .29, 1)
            self._r = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *_):
        self._r.pos = self.pos; self._r.size = self.size


class Toast(Label):
    def __init__(self, text='', **kw):
        super().__init__(text=text, **kw)
        self.size_hint = (None, None); self.size = (dp(220), dp(40))
        self.font_size = FS(12); self.bold = True; self.halign = 'center'; self.valign = 'middle'
        with self.canvas.before:
            self._bg_c = Color(.15, .15, .28, .92)
            self._bg_r = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd, size=self._upd)
        self._dismiss_event = None  # FIX: track scheduled dismiss

    def _upd(self, *_):
        self._bg_r.pos = self.pos; self._bg_r.size = self.size

    def show(self, root, message):
        # FIX: cancel previous dismiss schedule and remove from old parent to prevent crashes/overlaps
        if self._dismiss_event:
            self._dismiss_event.cancel()
            self._dismiss_event = None
        if self.parent:
            self.parent.remove_widget(self)

        self.text = message
        self.center_x = root.center_x
        self.y = root.height - dp(70)
        root.add_widget(self)

        from kivy.clock import Clock
        self._dismiss_event = Clock.schedule_once(
            lambda dt: self._safe_remove(root), 1.8)

    def _safe_remove(self, root):
        # FIX: guard against widget already removed or parent changed
        if self.parent == root:
            root.remove_widget(self)
        self._dismiss_event = None


class CopyHexButton(ButtonBehavior, Label):
    def __init__(self, hex_func=None, **kw):
        super().__init__(**kw)
        self.hex_func = hex_func or (lambda: '')
        self.font_size = FS(9)
        self.color = (.6, .6, .75, 1)
        self.halign = 'center'
        self.size_hint = (None, None)
        self.size = (dp(56), dp(16))

    def on_release(self):
        val = self.hex_func()
        if val:
            try:
                from kivy.core.clipboard import Clipboard
                Clipboard.copy(val)
            except Exception: pass
            app = App.get_running_app()
            if app and hasattr(app, '_toast') and app.root:
                app._toast.show(app.root, f"Copied {val}")