"""Colour Blindness Simulation and Theory Guide pages."""
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp, sp as _sp
from kivy.clock import Clock
from color_utils import hsv_to_rgb, rgb_hex, fg_for, CVD_SIMS
from ui_components import draw_rr, BgCard

FS = _sp


class ColorBlindnessWidget(RelativeLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._r = 0; self._g = .78; self._b = .78
        self.bind(size=self._redraw, pos=self._redraw); Clock.schedule_once(self._redraw)

    def set_color(self, h, s, v):
        self._r, self._g, self._b = hsv_to_rgb(h, s / 255, v / 255); self._redraw()

    def _redraw(self, *_):
        if self.width < 10: return
        self.canvas.clear()
        for c in list(self.children): self.remove_widget(c)
        sw, sh = dp(100), dp(64); y = dp(8)
        for name, simfn, desc in CVD_SIMS:
            sr, sg, sb = simfn(self._r, self._g, self._b)
            with self.canvas:
                draw_rr(self.canvas, dp(14), y - 2, sw, sh, 6, (0, 0, 0, .15))
                draw_rr(self.canvas, dp(10), y, sw, sh, 6, (sr, sg, sb, 1))
                Color(.35, .35, .43, 1); Line(rounded_rectangle=(dp(10), y, sw, sh, 6), width=1)
            nl = Label(text=name, color=(.82, .82, .9, 1), font_size=FS(10), bold=True,
                       size_hint_y=None, height=dp(16), halign='left')
            nl.x = dp(120); nl.y = y + sh - dp(12); self.add_widget(nl)
            dl = Label(text=desc, color=(.55, .55, .67, 1), font_size=FS(8),
                       size_hint_y=None, height=dp(14), halign='left')
            dl.x = dp(120); dl.y = y + sh - dp(28); self.add_widget(dl)
            hl = Label(text=f"Simulated: {rgb_hex(sr, sg, sb)}", color=(.67, .67, .78, 1),
                       font_size=FS(8), size_hint_y=None, height=dp(14), halign='left')
            hl.x = dp(120); hl.y = y + sh - dp(42); self.add_widget(hl)
            fg = fg_for(sr, sg, sb)
            sl = Label(text=rgb_hex(sr, sg, sb), color=fg[:3] + (1,), font_size=FS(8), bold=True,
                       size_hint=(None, None), size=(sw, dp(14)), halign='center')
            sl.x = dp(10); sl.y = y + 2; self.add_widget(sl)
            y += sh + dp(30)
        self.height = y


class PaletteBlindnessWidget(RelativeLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(size=self._redraw, pos=self._redraw); Clock.schedule_once(self._redraw)

    def _redraw(self, *_):
        if self.width < 10: return
        self.canvas.clear()
        for c in list(self.children): self.remove_widget(c)
        ui_colors = [("Success", .3, .69, .31), ("Warning", 1, .76, .03),
                     ("Error", .96, .26, .21), ("Info", .13, .59, .95), ("Link", .4, .23, .72)]
        sw, sh = dp(60), dp(24); row_h = sh + dp(24)
        for ri, (sname, simfn, _) in enumerate(CVD_SIMS):
            y = ri * row_h
            nl = Label(text=sname, color=(.63, .63, .7, 1), font_size=FS(8), bold=True,
                       size_hint=(None, None), size=(dp(78), dp(14)), halign='left')
            nl.x = 0; nl.y = y + dp(2); self.add_widget(nl)
            x = dp(82)
            for name, cr, cg, cb in ui_colors:
                sr, sg, sb = simfn(cr, cg, cb)
                with self.canvas:
                    draw_rr(self.canvas, x, y, sw, sh, 4, (sr, sg, sb, 1))
                cl = Label(text=name, color=(.75, .75, .82, 1), font_size=FS(7),
                           size_hint=(None, None), size=(sw, dp(13)), halign='center')
                cl.x = x; cl.y = y + sh + dp(2); self.add_widget(cl); x += sw + dp(8)
        self.height = len(CVD_SIMS) * row_h + dp(8)


class BlindnessPage(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation='vertical', padding=[dp(14), dp(8)], spacing=dp(8), **kw)
        self.add_widget(Label(text="Colour Blindness Simulation", color=(.88, .88, .94, 1),
                              font_size=FS(16), bold=True, size_hint_y=None, height=dp(28), halign='left'))
        self.add_widget(Label(text="How your selected colour appears with CVD.",
                              color=(.55, .55, .67, 1), font_size=FS(10), size_hint_y=None,
                              height=dp(28), halign='left'))
        sv = ScrollView(bar_width=dp(8))
        inner = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(14))
        inner.bind(minimum_height=inner.setter('height'))
        card1 = BgCard(orientation='vertical', spacing=dp(4), padding=[dp(10)])
        card1.add_widget(Label(text="Selected Colour Under CVD", color=(.82, .82, .9, 1),
                               font_size=FS(11), bold=True, size_hint_y=None, height=dp(20)))
        self._blindness = ColorBlindnessWidget(size_hint_y=None)
        card1.add_widget(self._blindness)
        card1.bind(minimum_height=card1.setter('height')); inner.add_widget(card1)
        card2 = BgCard(orientation='vertical', spacing=dp(4), padding=[dp(10)])
        card2.add_widget(Label(text="UI Palette Under CVD", color=(.82, .82, .9, 1),
                               font_size=FS(11), bold=True, size_hint_y=None, height=dp(20)))
        self._palette_blind = PaletteBlindnessWidget(size_hint_y=None)
        card2.add_widget(self._palette_blind)
        card2.bind(minimum_height=card2.setter('height')); inner.add_widget(card2)
        sv.add_widget(inner); self.add_widget(sv)

    def set_color(self, h, s, v): self._blindness.set_color(h, s, v)


# --- THEORY ---
THEORY_SECTIONS = [
    ("The Colour Wheel",
     "The colour wheel arranges hues in a circle. Newton created the first diagram in 1666. "
     "The wheel reveals harmonies based on geometric positions.\n\n"
     "It has 12 segments: 3 primaries, 3 secondaries, 6 tertiaries."),
    ("Primary Colours",
     "Cannot be mixed from others.\n\n"
     "RGB (Light): Red, Green, Blue = White.\n"
     "RYB (Paint): Red, Yellow, Blue = Dark brown.\n"
     "CMYK (Print): Cyan, Magenta, Yellow, Black."),
    ("Secondary Colours",
     "Mixing two primaries equally.\n\n"
     "RGB: Cyan, Magenta, Yellow.\n"
     "RYB: Orange, Green, Purple."),
    ("Tertiary Colours",
     "Mixing a primary with an adjacent secondary (e.g., Red-Orange). "
     "Creates 12 distinct wheel segments."),
    ("Colour Temperature",
     "Warm (red-yellow) advance and energize. Cool (blue-green) recede and calm. "
     "Temperature is relative."),
    ("Value, Saturation & Chroma",
     "Value: Light/dark. Tints = hue + white. Shades = hue + black.\n"
     "Saturation: Intensity. Tones = hue + gray."),
    ("Simultaneous Contrast",
     "Colours appear different beside their neighbours. Discovered by Chevreul, 1839."),
    ("The 60-30-10 Rule",
     "60% Dominant, 30% Secondary, 10% Accent. Creates visual hierarchy."),
    ("Accessibility",
     "~8% of men have CVD. Never rely on colour alone. "
     "WCAG AA requires >= 4.5:1 contrast for text."),
    ("Colour Psychology",
     "Red: Passion. Blue: Trust. Yellow: Optimism. Green: Nature. "
     "Purple: Luxury. Orange: Energy. Black: Elegance."),
]


class TheoryCard(BoxLayout):
    def __init__(self, title, body, **kw):
        super().__init__(orientation='vertical', **kw)
        self.padding = dp(14); self.spacing = dp(8); self.size_hint_y = None
        with self.canvas.before:
            self._bg_c = Color(.145, .145, .25, 1)
            self._bg_r = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd, size=self._upd)
        t_lbl = Label(text=title, color=(.75, .75, .88, 1), font_size=FS(12), bold=True,
                      size_hint_y=None, height=dp(24), halign='left', valign='middle')
        t_lbl.bind(width=lambda i, v: setattr(i, 'text_size', (v, None))); self.add_widget(t_lbl)
        b_lbl = Label(text=body, color=(.63, .63, .75, 1), font_size=FS(11), size_hint_y=None,
                      halign='left', valign='top')
        b_lbl.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))
        b_lbl.bind(texture_size=lambda i, v: setattr(i, 'height', v[1] + dp(4)))
        self.add_widget(b_lbl)
        self.bind(minimum_height=self.setter('height'))

    def _upd(self, *_): self._bg_r.pos = self.pos; self._bg_r.size = self.size


class TheoryPage(ScrollView):
    def __init__(self, **kw):
        super().__init__(**kw); self.bar_width = dp(10); self.bar_color = (.26, .26, .26, 1)
        layout = BoxLayout(orientation='vertical', spacing=dp(14), size_hint_y=None, padding=dp(14))
        layout.bind(minimum_height=layout.setter('height'))
        layout.add_widget(Label(text="Understanding Colour Theory", color=(.88, .88, .94, 1),
                                font_size=FS(18), bold=True, size_hint_y=None, height=dp(40)))
        for title, body in THEORY_SECTIONS:
            layout.add_widget(TheoryCard(title=title, body=body))
        self.add_widget(layout)