"""Colour Properties (Tints, Shades, Tones) page."""
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Line
from kivy.metrics import dp, sp as _sp
from kivy.clock import Clock
from color_utils import hsv_to_rgb, rgb_hex
from ui_components import draw_rr, CopyHexButton

FS = _sp


class ColorPropertiesWidget(RelativeLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._r = 0; self._g = .78; self._b = .78; self._h = 180
        self.bind(size=self._redraw, pos=self._redraw)
        Clock.schedule_once(self._redraw)

    def set_color(self, h, s, v):
        self._h = h; self._r, self._g, self._b = hsv_to_rgb(h, s / 255, v / 255)
        self._redraw()

    def _scale(self, y, title, desc, colors):
        sw, sh, gap = dp(42), dp(42), dp(5)
        tl = Label(text=title, color=(.82, .82, .9, 1), font_size=FS(11), bold=True,
                   size_hint_y=None, height=dp(16), halign='left',
                   text_size=(self.width - dp(20), None))
        tl.x = dp(10); tl.y = y + sh + dp(18); self.add_widget(tl)
        dl = Label(text=desc, color=(.55, .55, .67, 1), font_size=FS(8),
                   size_hint_y=None, height=dp(14), halign='left',
                   text_size=(self.width - dp(20), None))
        dl.x = dp(10); dl.y = y + sh + dp(4); self.add_widget(dl)
        x = dp(10)
        for (r, g, b) in colors:
            with self.canvas:
                draw_rr(self.canvas, x, y, sw, sh, 4, (r, g, b, 1))
                Color(.28, .28, .35, 1); Line(rounded_rectangle=(x, y, sw, sh, 4), width=1)
            hl = CopyHexButton(hex_func=lambda rr=r, gg=g, bb=b: rgb_hex(rr, gg, bb))
            hl.x = x - gap // 2; hl.y = y - dp(4); hl.text = rgb_hex(r, g, b)
            self.add_widget(hl); x += sw + gap

    def _redraw(self, *_):
        if self.width < 10: return
        self.canvas.clear()
        for c in list(self.children): self.remove_widget(c)
        r, g, b = self._r, self._g, self._b; y = dp(42)
        tints = [(r + (1 - r) * i / 8, g + (1 - g) * i / 8, b + (1 - b) * i / 8) for i in range(9)]
        self._scale(y, "Tints (adding white)", "Lighter, softer", tints)
        y += dp(108)
        shades = [(r * (1 - i / 8), g * (1 - i / 8), b * (1 - i / 8)) for i in range(9)]
        self._scale(y, "Shades (adding black)", "Darker, richer", shades)
        y += dp(108)
        gr = .5
        tones = [(r + (gr - r) * i / 8, g + (gr - g) * i / 8, b + (gr - b) * i / 8) for i in range(9)]
        self._scale(y, "Tones (adding gray)", "Muted, subtle", tones)
        y += dp(108)
        tl = Label(text="Color Temperature Spectrum", color=(.82, .82, .9, 1), font_size=FS(11),
                   bold=True, size_hint_y=None, height=dp(16), halign='left',
                   text_size=(self.width - dp(20), None))
        tl.x = dp(10); tl.y = y + dp(74); self.add_widget(tl)
        tw = max(dp(1), (min(dp(800), self.width) - dp(20)) / 12)
        for i in range(12):
            cr, cg, cb = hsv_to_rgb(i * 30, .8, .86)
            with self.canvas:
                draw_rr(self.canvas, dp(10) + i * tw, y + dp(44), tw - dp(2), dp(28), 3, (cr, cg, cb, 1))
        y += dp(100)
        h = self._h
        sat_c = [hsv_to_rgb(h, i / 8, .78) for i in range(9)]
        self._scale(y, "Saturation Scale", "Desaturated to vivid", sat_c)
        self.height = y + dp(120)


class PropertiesPage(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation='vertical', padding=[dp(14), dp(8)], spacing=dp(8), **kw)
        self.add_widget(Label(text="Colour Properties", color=(.88, .88, .94, 1), font_size=FS(16),
                              bold=True, size_hint_y=None, height=dp(28), halign='left'))
        self.add_widget(Label(text="Tints, shades, tones, and temperature.",
                              color=(.55, .55, .67, 1), font_size=FS(10), size_hint_y=None,
                              height=dp(28), halign='left'))
        sv = ScrollView(bar_width=dp(8))
        self._props = ColorPropertiesWidget(size_hint_y=None)
        sv.add_widget(self._props); self.add_widget(sv)

    def set_color(self, h, s, v): self._props.set_color(h, s, v)