"""Additive and Subtractive Colour Mixing page."""
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Ellipse
from kivy.metrics import dp, sp as _sp
from kivy.clock import Clock

FS = _sp


class ColorMixingWidget(RelativeLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(size=self._redraw, pos=self._redraw)
        Clock.schedule_once(self._redraw)

    def _redraw(self, *_):
        if self.width < 10 or self.height < 10: return
        self.canvas.clear()
        for c in list(self.children): self.remove_widget(c)
        w, h = self.width, self.height
        r = min(w / 3, h / 5) * 0.55
        self._draw_mix(w / 2, h * 0.26, r, [(1, 0, 0), (0, 1, 0), (0, 0, 1)],
                       ["Red", "Green", "Blue"], "Additive Mixing (Light \u2013 RGB Model)")
        self._draw_mix(w / 2, h * 0.64, r, [(.86, .16, .16), (.9, .82, 0), (.12, .24, .82)],
                       ["Red", "Yellow", "Blue"], "Subtractive Mixing (Paint \u2013 RYB Model)")
        note = Label(text="Additive = more light = brighter  |  Subtractive = more pigment = darker",
                     color=(.47, .47, .59, 1), font_size=FS(9), size_hint_y=None,
                     height=dp(30), halign='center')
        note.x = dp(10); note.y = h - dp(36); note.width = w - dp(20); self.add_widget(note)

    def _draw_mix(self, cx, cy, radius, colors, labels, title):
        offsets = [(-0.45, -0.28), (0.45, -0.28), (0.0, 0.32)]
        positions = [(cx + radius * ox, cy + radius * oy) for ox, oy in offsets]
        for i, (px, py) in enumerate(positions):
            r, g, b = colors[i]
            for step in range(25, 0, -1):
                alpha = (step / 25.0) * 0.65; rad = radius * 0.65 * (step / 25.0)
                with self.canvas:
                    Color(r, g, b, alpha); Ellipse(pos=(px - rad, py - rad), size=(rad * 2, rad * 2))
        for i, (px, py) in enumerate(positions):
            lbl = Label(text=labels[i], color=(.94, .94, 1, 1), font_size=FS(9), bold=True,
                        size_hint=(None, None), size=(dp(56), dp(16)), halign='center')
            lbl.center = (px, py); self.add_widget(lbl)
        tl = Label(text=title, color=(.94, .94, 1, 1), font_size=FS(12), bold=True,
                   size_hint=(None, None), size=(dp(400), dp(24)), halign='center')
        tl.center = (cx, cy - radius - dp(22)); self.add_widget(tl)


class MixingPage(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation='vertical', padding=[dp(14), dp(8)], spacing=dp(8), **kw)
        self.add_widget(Label(text="Colour Mixing Models", color=(.88, .88, .94, 1),
                              font_size=FS(16), bold=True, size_hint_y=None, height=dp(28), halign='left'))
        self.add_widget(Label(text="How primary colours combine in light vs. paint.",
                              color=(.55, .55, .67, 1), font_size=FS(10), size_hint_y=None,
                              height=dp(28), halign='left'))
        sv = ScrollView(bar_width=dp(8))
        sv.add_widget(ColorMixingWidget(size_hint_y=None, height=dp(500)))
        self.add_widget(sv)