"""Colour Harmonies page."""
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Line
from kivy.metrics import dp, sp as _sp
from kivy.clock import Clock
from color_utils import hsv_to_rgb, rgb_hex, fg_for
from ui_components import draw_rr, CopyHexButton

FS = _sp


class HarmonyWidget(RelativeLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._h = 180; self._s = 255; self._v = 255
        self.bind(size=self._redraw, pos=self._redraw)
        Clock.schedule_once(self._redraw)

    def set_color(self, h, s, v):
        self._h, self._s, self._v = h, s, v; self._redraw()

    def _redraw(self, *_):
        if self.width < 10: return
        self.canvas.clear()
        for c in list(self.children): self.remove_widget(c)
        h, s, v = self._h, self._s / 255, self._v / 255
        harms = [
            ("Complementary", "Opposite on the wheel \u2013 max contrast.",
             [(h, s, v), ((h + 180) % 360, s, v)]),
            ("Analogous", "3-5 adjacent hues \u2013 naturally harmonious.",
             [((h - 30) % 360, s, v), ((h - 15) % 360, s, v), (h, s, v),
              ((h + 15) % 360, s, v), ((h + 30) % 360, s, v)]),
            ("Triadic", "Three equally-spaced hues (120\u00b0).",
             [(h, s, v), ((h + 120) % 360, s, v), ((h + 240) % 360, s, v)]),
            ("Split-Complementary", "Base + two neighbours of complement.",
             [(h, s, v), ((h + 150) % 360, s, v), ((h + 210) % 360, s, v)]),
            ("Tetradic (Rectangle)", "Four colours in two pairs.",
             [(h, s, v), ((h + 60) % 360, s, v), ((h + 180) % 360, s, v),
              ((h + 240) % 360, s, v)]),
            ("Square", "Four evenly-spaced hues (90\u00b0).",
             [(h, s, v), ((h + 90) % 360, s, v), ((h + 180) % 360, s, v),
              ((h + 270) % 360, s, v)]),
        ]
        sw, sh, gap = dp(44), dp(44), dp(5); y = dp(8)
        for name, desc, colors in harms:
            x = dp(10)
            for ch, cs, cv in colors:
                r, g, b = hsv_to_rgb(ch, cs, cv)
                with self.canvas:
                    draw_rr(self.canvas, x, y, sw, sh, 5, (r, g, b, 1))
                    Color(.3, .3, .4, 1); Line(rounded_rectangle=(x, y, sw, sh, 5), width=1)
                cl = CopyHexButton(hex_func=lambda rr=r, gg=g, bb=b: rgb_hex(rr, gg, bb))
                cl.x = x - gap // 2; cl.y = y - dp(4); cl.text = rgb_hex(r, g, b)
                cl.color = fg_for(r, g, b)[:3] + (.85,)
                self.add_widget(cl); x += sw + gap
            nl = Label(text=name, color=(.82, .82, .9, 1), font_size=FS(11), bold=True,
                       size_hint_y=None, height=dp(16), halign='left',
                       text_size=(self.width - dp(20), None))
            nl.x = dp(10); nl.y = y + sh + dp(4); self.add_widget(nl)
            dl = Label(text=desc, color=(.55, .55, .67, 1), font_size=FS(9),
                       size_hint_y=None, height=dp(16), halign='left',
                       text_size=(self.width - dp(20), None))
            dl.x = dp(10); dl.y = y + sh + dp(20); self.add_widget(dl)
            y += sh + dp(60)
        self.height = y + dp(8)


class HarmonyPage(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation='vertical', padding=[dp(14), dp(8)], spacing=dp(8), **kw)
        self.add_widget(Label(text="Colour Harmonies", color=(.88, .88, .94, 1), font_size=FS(16),
                              bold=True, size_hint_y=None, height=dp(28), halign='left'))
        self.add_widget(Label(text="Tap swatch hex to copy. Harmonies based on wheel geometry.",
                              color=(.55, .55, .67, 1), font_size=FS(10), size_hint_y=None,
                              height=dp(28), halign='left'))
        sv = ScrollView(bar_width=dp(8))
        self._harmony = HarmonyWidget(size_hint_y=None)
        sv.add_widget(self._harmony); self.add_widget(sv)

    def set_color(self, h, s, v): self._harmony.set_color(h, s, v)