#!/usr/bin/env python3
"""Color Theory Visualizer – Interactive Education (Kivy, single file)
   Works on Desktop (Windows/macOS/Linux) and Android."""

import math, os, sys

# ─── Colour utilities ────────────────────────────────────────

def hsv_to_rgb(h, s, v):
    h %= 360
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if h < 60:    r, g, b = c, x, 0
    elif h < 120: r, g, b = x, c, 0
    elif h < 180: r, g, b = 0, c, x
    elif h < 240: r, g, b = 0, x, c
    elif h < 300: r, g, b = x, 0, c
    else:         r, g, b = c, 0, x
    return (r + m, g + m, b + m)

def rgb_to_hsl(r, g, b):
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2
    if mx == mn:
        h = s = 0.0
    else:
        d = mx - mn
        s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
        if mx == r:   h = ((g - b) / d + (6 if g < b else 0)) * 60
        elif mx == g: h = ((b - r) / d + 2) * 60
        else:         h = ((r - g) / d + 4) * 60
    return (h, s, l)

def rgb_hex(r, g, b):
    return '#{:02X}{:02X}{:02X}'.format(
        max(0, min(255, int(r * 255))),
        max(0, min(255, int(g * 255))),
        max(0, min(255, int(b * 255))))

def _lum(r, g, b):
    def lin(c): return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)

def wcag_ratio(r1, g1, b1, r2, g2, b2):
    l1, l2 = _lum(r1, g1, b1), _lum(r2, g2, b2)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)

def _cl(v): return max(0.0, min(1.0, v))

def sim_protan(r, g, b):
    return (_cl(.56667*r+.43333*g), _cl(.55833*r+.44167*g), _cl(.24167*g+.75833*b))
def sim_deutan(r, g, b):
    return (_cl(.625*r+.375*g), _cl(.7*r+.3*g), _cl(.3*g+.7*b))
def sim_tritan(r, g, b):
    return (_cl(.95*r+.05*g), _cl(.43333*g+.56667*b), _cl(.475*g+.525*b))
def sim_achroma(r, g, b):
    v = .299*r + .587*g + .114*b
    return (v, v, v)

CVD_SIMS = [
    ("Normal Vision",  lambda r,g,b: (r,g,b), "Trichromatic – 3 cone types"),
    ("Protanopia",     sim_protan,   "Red-blind – ~1.3% of males"),
    ("Deuteranopia",   sim_deutan,   "Green-blind – ~1.2% of males"),
    ("Tritanopia",     sim_tritan,   "Blue-blind – ~0.001%"),
    ("Achromatopsia",  sim_achroma,  "Total colour blindness – ~0.003%"),
]

def _fg_for(r, g, b):
    return (1,1,1,1) if (r*.299+g*.587+b*.114) < 0.55 else (0,0,0,1)

def _draw_rr(canvas_grp, x, y, w, h, rad, rgba):
    with canvas_grp:
        Color(*rgba)
        Ellipse(pos=(x, y), size=(rad*2, rad*2))
        Ellipse(pos=(x+w-rad*2, y), size=(rad*2, rad*2))
        Ellipse(pos=(x, y+h-rad*2), size=(rad*2, rad*2))
        Ellipse(pos=(x+w-rad*2, y+h-rad*2), size=(rad*2, rad*2))
        Rectangle(pos=(x+rad, y), size=(w-2*rad, h))
        Rectangle(pos=(x, y+rad), size=(rad, h-2*rad))
        Rectangle(pos=(x+w-rad, y+rad), size=(rad, h-2*rad))
        Rectangle(pos=(x+rad, y+h-rad), size=(w-2*rad, rad))

# ─── Kivy imports ─────────────────────────────────────────────

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.popup import Popup
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Ellipse, Rectangle, Line, Mesh, StencilPush, StencilPop, StencilUse, StencilUnUse
from kivy.metrics import dp, sp as _sp
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.utils import platform as kivy_platform
from kivy.properties import NumericProperty, ListProperty, BooleanProperty, StringProperty

FS = _sp

KV = '''
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
'''


# ─── Reusable helpers ────────────────────────────────────────

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
    """Floating notification that auto-dismisses."""
    def __init__(self, text='', **kw):
        super().__init__(text=text, **kw)
        self.size_hint = (None, None)
        self.size = (dp(220), dp(40))
        self.font_size = FS(12)
        self.bold = True
        self.halign = 'center'
        self.valign = 'middle'
        with self.canvas.before:
            self._bg_c = Color(.15, .15, .28, .92)
            self._bg_r = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd, size=self._upd)
    def _upd(self, *_):
        self._bg_r.pos = self.pos; self._bg_r.size = self.size
    def show(self, root, message):
        self.text = message
        self.center_x = root.center_x
        self.y = root.height - dp(70)
        root.add_widget(self)
        Clock.schedule_once(lambda *_: root.remove_widget(self), 1.8)


class CopyHexButton(ButtonBehavior, Label):
    """Tappable hex label that copies to clipboard."""
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
            except Exception:
                pass
            app = App.get_running_app()
            if app and hasattr(app, '_toast') and app.root:
                app._toast.show(app.root, f"Copied {val}")


# ═══════════════════════════════════════════════════════════════
# 1. COLOUR WHEEL
# ═══════════════════════════════════════════════════════════════

class ColorWheelWidget(RelativeLayout):
    def __init__(self, on_change, **kw):
        super().__init__(**kw)
        self.size_hint = (None, None)
        self.size = (dp(300), dp(300))
        self._on_change = on_change
        self._hue = 180; self._sat = 255; self._val = 255
        self._dragging = False

        self._hex_lbl = Label(text='', font_size=FS(13), bold=True,
                              size_hint=(None, None), size=(dp(120), dp(24)),
                              halign='center', valign='middle')
        self.add_widget(self._hex_lbl)

        self._deg_labels = []
        for deg in range(0, 360, 30):
            lbl = Label(text=f"{deg}\u00b0", font_size=FS(7), color=(.7, .7, .82, .7),
                        size_hint=(None, None), size=(dp(28), dp(14)), halign='center')
            self.add_widget(lbl)
            self._deg_labels.append((deg, lbl))

        self.bind(size=self._redraw, pos=self._redraw)
        Clock.schedule_once(self._redraw)

    def set_hsv(self, h, s, v, propagate=False):
        self._hue = h % 360 if h >= 0 else 0
        self._sat = s; self._val = v
        self._redraw()
        if propagate:
            self._on_change(self._hue, self._sat, self._val)

    def _redraw(self, *_):
        if self.width < 10 or self.height < 10:
            return
        self.canvas.clear()
        cx, cy = self.center
        outr = min(self.width, self.height) / 2 - 18
        inr = outr * 0.62

        # Hue ring
        segs = 180
        verts, idxs = [], []
        for i in range(segs):
            a1 = math.radians(i * 360 / segs)
            a2 = math.radians((i + 1) * 360 / segs)
            r, g, b = hsv_to_rgb(i * 360 / segs, 1.0, 1.0)
            base = i * 4
            verts.extend([
                cx+outr*math.cos(a1), cy+outr*math.sin(a1), 0,0, r,g,b,1,
                cx+outr*math.cos(a2), cy+outr*math.sin(a2), 0,0, r,g,b,1,
                cx+inr *math.cos(a2), cy+inr *math.sin(a2), 0,0, r,g,b,1,
                cx+inr *math.cos(a1), cy+inr *math.sin(a1), 0,0, r,g,b,1,
            ])
            idxs.extend([base, base+1, base+2, base, base+2, base+3])
        with self.canvas:
            Mesh(vertices=verts, indices=idxs, mode='triangles')

        with self.canvas:
            Color(.09, .09, .17, 1)
            Ellipse(pos=(cx-inr, cy-inr), size=(inr*2, inr*2))

        r, g, b = hsv_to_rgb(self._hue, self._sat/255, self._val/255)
        dr = inr * 0.52
        with self.canvas:
            Color(r, g, b, 1)
            Ellipse(pos=(cx-dr, cy-dr), size=(dr*2, dr*2))
            Color(1,1,1,.3)
            Line(circle=(cx, cy, dr), width=1)

        self._hex_lbl.center = (cx, cy)
        self._hex_lbl.text = rgb_hex(r, g, b)
        self._hex_lbl.color = _fg_for(r, g, b)[:3] + (1,)

        # Hue marker
        mr = (outr + inr) / 2
        mx = cx + mr * math.cos(math.radians(self._hue))
        my = cy + mr * math.sin(math.radians(self._hue))
        with self.canvas:
            Color(1,1,1,1)
            Line(circle=(mx, my, dp(9)), width=2.5)
            Color(0,0,0,1)
            Line(circle=(mx, my, dp(9)), width=1.2)

        for deg, lbl in self._deg_labels:
            la = math.radians(deg)
            lx = cx + (outr + 14) * math.cos(la)
            ly = cy + (outr + 14) * math.sin(la)
            lbl.center = (lx, ly)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        self._dragging = True
        touch.grab(self)
        self._pick(touch)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is self and self._dragging:
            self._pick(touch)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            self._dragging = False
            touch.ungrab(self)
            return True
        return super().on_touch_up(touch)

    def _pick(self, touch):
        cx, cy = self.center
        outr = min(self.width, self.height) / 2 - 18
        inr = outr * 0.62
        dx, dy = touch.x - cx, touch.y - cy
        dist = math.hypot(dx, dy)
        if inr <= dist <= outr:
            self._hue = int(math.degrees(math.atan2(dy, dx))) % 360
            self._redraw()
            self._on_change(self._hue, self._sat, self._val)


# ═══════════════════════════════════════════════════════════════
# 2. HARMONIES
# ═══════════════════════════════════════════════════════════════

class HarmonyWidget(RelativeLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._h = 180; self._s = 255; self._v = 255
        self.bind(size=self._redraw, pos=self._redraw)
        Clock.schedule_once(self._redraw)

    def set_color(self, h, s, v):
        self._h, self._s, self._v = h, s, v
        self._redraw()

    def _redraw(self, *_):
        if self.width < 10:
            return
        self.canvas.clear()
        for c in list(self.children):
            self.remove_widget(c)
        h, s, v = self._h, self._s / 255, self._v / 255
        harms = [
            ("Complementary",
             "Opposite on the wheel – max contrast & vibrancy. Great for CTAs.",
             [(h, s, v), ((h+180)%360, s, v)]),
            ("Analogous",
             "3-5 adjacent hues – naturally harmonious. One dominant, others accent.",
             [((h-30)%360,s,v), ((h-15)%360,s,v), (h,s,v), ((h+15)%360,s,v), ((h+30)%360,s,v)]),
            ("Triadic",
             "Three equally-spaced hues (120\u00b0) – vibrant yet balanced.",
             [(h,s,v), ((h+120)%360,s,v), ((h+240)%360,s,v)]),
            ("Split-Complementary",
             "Base + two neighbours of complement – contrast with less tension.",
             [(h,s,v), ((h+150)%360,s,v), ((h+210)%360,s,v)]),
            ("Tetradic (Rectangle)",
             "Four colours in two complementary pairs – rich and versatile.",
             [(h,s,v), ((h+60)%360,s,v), ((h+180)%360,s,v), ((h+240)%360,s,v)]),
            ("Square",
             "Four evenly-spaced hues (90\u00b0) – bold and dynamic.",
             [(h,s,v), ((h+90)%360,s,v), ((h+180)%360,s,v), ((h+270)%360,s,v)]),
        ]
        sw, sh, gap = dp(44), dp(44), dp(5)
        y = dp(8)
        for name, desc, colors in harms:
            x = dp(10)
            for ch, cs, cv in colors:
                r, g, b = hsv_to_rgb(ch, cs, cv)
                with self.canvas:
                    _draw_rr(self.canvas, x, y, sw, sh, 5, (r,g,b,1))
                    Color(.3,.3,.4,1)
                    Line(rounded_rectangle=(x, y, sw, sh, 5), width=1)
                cl = CopyHexButton(hex_func=lambda rr=r,gg=r,bb=b: rgb_hex(rr,gg,bb))
                cl.x = x - gap//2; cl.y = y - dp(4)
                cl.text = rgb_hex(r, g, b)
                cl.color = _fg_for(r, g, b)[:3] + (.85,)
                self.add_widget(cl)
                x += sw + gap

            nl = Label(text=name, color=(.82,.82,.9,1), font_size=FS(11),
                       bold=True, size_hint_y=None, height=dp(16),
                       halign='left', valign='middle',
                       text_size=(self.width-dp(20), None))
            nl.x = dp(10); nl.y = y + sh + dp(4)
            self.add_widget(nl)
            dl = Label(text=desc, color=(.55,.55,.67,1), font_size=FS(9),
                       size_hint_y=None, height=dp(16), halign='left', valign='middle',
                       text_size=(self.width-dp(20), None))
            dl.x = dp(10); dl.y = y + sh + dp(20)
            self.add_widget(dl)
            y += sh + dp(60)
        self.height = y + dp(8)


# ═══════════════════════════════════════════════════════════════
# 3. COLOUR MIXING
# ═══════════════════════════════════════════════════════════════

class ColorMixingWidget(RelativeLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(size=self._redraw, pos=self._redraw)
        Clock.schedule_once(self._redraw)

    def _redraw(self, *_):
        if self.width < 10 or self.height < 10:
            return
        self.canvas.clear()
        for c in list(self.children):
            self.remove_widget(c)
        w, h = self.width, self.height
        r = min(w / 3, h / 5) * 0.55
        self._draw_mix(w/2, h*0.26, r,
                       [(1,0,0),(0,1,0),(0,0,1)],
                       ["Red","Green","Blue"],
                       "Additive Mixing (Light – RGB Model)")
        self._draw_mix(w/2, h*0.64, r,
                       [(.86,.16,.16),(.9,.82,0),(.12,.24,.82)],
                       ["Red","Yellow","Blue"],
                       "Subtractive Mixing (Paint – RYB Model)")
        note = Label(
            text="Additive = more light = brighter  |  Subtractive = more pigment = darker",
            color=(.47,.47,.59,1), font_size=FS(9),
            size_hint_y=None, height=dp(30), halign='center')
        note.x = dp(10); note.y = h - dp(36); note.width = w - dp(20)
        self.add_widget(note)

    def _draw_mix(self, cx, cy, radius, colors, labels, title):
        offsets = [(-0.45,-0.28),(0.45,-0.28),(0.0,0.32)]
        positions = [(cx+radius*ox, cy+radius*oy) for ox, oy in offsets]
        for i, (px, py) in enumerate(positions):
            r, g, b = colors[i]
            for step in range(25, 0, -1):
                alpha = (step/25.0)*0.65
                rad = radius*0.65*(step/25.0)
                with self.canvas:
                    Color(r, g, b, alpha)
                    Ellipse(pos=(px-rad, py-rad), size=(rad*2, rad*2))
        for i, (px, py) in enumerate(positions):
            lbl = Label(text=labels[i], color=(.94,.94,1,1),
                        font_size=FS(9), bold=True,
                        size_hint=(None, None), size=(dp(56), dp(16)),
                        halign='center')
            lbl.center = (px, py)
            self.add_widget(lbl)
        tl = Label(text=title, color=(.94,.94,1,1),
                   font_size=FS(12), bold=True,
                   size_hint=(None, None), size=(dp(400), dp(24)),
                   halign='center')
        tl.center = (cx, cy - radius - dp(22))
        self.add_widget(tl)


# ═══════════════════════════════════════════════════════════════
# 4. COLOUR PROPERTIES
# ═══════════════════════════════════════════════════════════════

class ColorPropertiesWidget(RelativeLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._r = 0; self._g = .78; self._b = .78; self._h = 180
        self.bind(size=self._redraw, pos=self._redraw)
        Clock.schedule_once(self._redraw)

    def set_color(self, h, s, v):
        self._h = h
        self._r, self._g, self._b = hsv_to_rgb(h, s/255, v/255)
        self._redraw()

    def _scale(self, y, title, desc, colors):
        sw, sh, gap = dp(42), dp(42), dp(5)
        tl = Label(text=title, color=(.82,.82,.9,1), font_size=FS(11),
                   bold=True, size_hint_y=None, height=dp(16), halign='left',
                   text_size=(self.width-dp(20), None))
        tl.x = dp(10); tl.y = y + sh + dp(18)
        self.add_widget(tl)
        dl = Label(text=desc, color=(.55,.55,.67,1), font_size=FS(8),
                   size_hint_y=None, height=dp(14), halign='left',
                   text_size=(self.width-dp(20), None))
        dl.x = dp(10); dl.y = y + sh + dp(4)
        self.add_widget(dl)
        x = dp(10)
        for (r, g, b) in colors:
            with self.canvas:
                _draw_rr(self.canvas, x, y, sw, sh, 4, (r,g,b,1))
                Color(.28,.28,.35,1)
                Line(rounded_rectangle=(x, y, sw, sh, 4), width=1)
            hl = CopyHexButton(hex_func=lambda rr=r,gg=g,bb=b: rgb_hex(rr,gg,bb))
            hl.x = x - gap//2; hl.y = y - dp(4)
            hl.text = rgb_hex(r, g, b)
            self.add_widget(hl)
            x += sw + gap

    def _redraw(self, *_):
        if self.width < 10:
            return
        self.canvas.clear()
        for c in list(self.children):
            self.remove_widget(c)
        r, g, b = self._r, self._g, self._b
        y = dp(42)
        tints = [(r+(1-r)*i/8, g+(1-g)*i/8, b+(1-b)*i/8) for i in range(9)]
        self._scale(y, "Tints (adding white)", "Lighter, softer – increase value, reduce contrast", tints)
        y += dp(108)
        shades = [(r*(1-i/8), g*(1-i/8), b*(1-i/8)) for i in range(9)]
        self._scale(y, "Shades (adding black)", "Darker, richer – deepen and add drama", shades)
        y += dp(108)
        gr = .5
        tones = [(r+(gr-r)*i/8, g+(gr-g)*i/8, b+(gr-b)*i/8) for i in range(9)]
        self._scale(y, "Tones (adding gray)", "Muted, subtle – reduced intensity, sophisticated", tones)
        y += dp(108)

        tl = Label(text="Color Temperature Spectrum", color=(.82,.82,.9,1),
                   font_size=FS(11), bold=True, size_hint_y=None, height=dp(16),
                   halign='left', text_size=(self.width-dp(20), None))
        tl.x = dp(10); tl.y = y + dp(74)
        self.add_widget(tl)
        dlt = Label(text="Warm (red-yellow) advance & energize – Cool (blue-green) recede & calm",
                    color=(.55,.55,.67,1), font_size=FS(8),
                    size_hint_y=None, height=dp(14), halign='left',
                    text_size=(self.width-dp(20), None))
        dlt.x = dp(10); dlt.y = y + dp(58)
        self.add_widget(dlt)
        tw = max(dp(1), (min(dp(800), self.width) - dp(20)) / 12)
        for i in range(12):
            cr, cg, cb = hsv_to_rgb(i*30, .8, .86)
            with self.canvas:
                _draw_rr(self.canvas, dp(10)+i*tw, y+dp(44), tw-dp(2), dp(28), 3, (cr,cg,cb,1))
        wl = Label(text="\u2190 Warm          Cool \u2192", color=(.62,.62,.78,1),
                   font_size=FS(9), size_hint_y=None, height=dp(14),
                   halign='left', text_size=(self.width-dp(20), None))
        wl.x = dp(10); wl.y = y + dp(28)
        self.add_widget(wl)
        y += dp(100)
        h = self._h
        sat_c = [hsv_to_rgb(h, i/8, .78) for i in range(9)]
        self._scale(y, "Saturation Scale", "Desaturated (gray) to fully saturated (vivid)", sat_c)
        self.height = y + dp(120)


# ═══════════════════════════════════════════════════════════════
# 5. HSL / HSV EXPLORER
# ═══════════════════════════════════════════════════════════════

class HSLExplorerWidget(BoxLayout):
    def __init__(self, on_change, **kw):
        super().__init__(orientation='vertical', **kw)
        self._on_change = on_change
        self._updating = False
        self.padding = [dp(20), dp(14)]
        self.spacing = dp(8)

        self.add_widget(Label(text="HSL / HSV Colour Explorer",
                              color=(.87,.87,.94,1), font_size=FS(15),
                              bold=True, size_hint_y=None, height=dp(28), halign='left'))
        self.add_widget(Label(
            text="Drag sliders to see how Hue, Saturation, and Value interact.\n"
                 "H = which colour  |  S = intensity  |  V = brightness",
            color=(.53,.53,.53,1), font_size=FS(10),
            size_hint_y=None, height=dp(34), halign='left'))

        prev_row = BoxLayout(orientation='horizontal', size_hint_y=None,
                             height=dp(90), spacing=dp(12))
        self._prev = ColorPreview(size_hint=(1, 1))
        self._prev_lbl = Label(text='', font_size=FS(10), bold=True)
        self._prev.add_widget(self._prev_lbl)
        self._comp = ColorPreview(size_hint=(1, 1))
        self._comp_lbl = Label(text='', font_size=FS(10), bold=True)
        self._comp.add_widget(self._comp_lbl)
        prev_row.add_widget(self._prev)
        prev_row.add_widget(Label(text="\u2194", color=(.4,.4,.4,1),
                                  font_size=FS(18), size_hint_x=None, width=dp(30)))
        prev_row.add_widget(self._comp)
        self.add_widget(prev_row)

        self._hex_lbl = Label(text='', color=(.67,.67,.67,1),
                              font_size=FS(14), bold=True, size_hint_y=None, height=dp(22))
        self.add_widget(self._hex_lbl)
        self._rgb_lbl = Label(text='', color=(.47,.47,.47,1),
                              font_size=FS(10), size_hint_y=None, height=dp(16))
        self.add_widget(self._rgb_lbl)
        self._hsl_lbl = Label(text='', color=(.47,.47,.47,1),
                              font_size=FS(10), size_hint_y=None, height=dp(16))
        self.add_widget(self._hsl_lbl)
        self._hsv_lbl = Label(text='', color=(.47,.47,.47,1),
                              font_size=FS(10), size_hint_y=None, height=dp(16))
        self.add_widget(self._hsv_lbl)

        self._sliders = {}
        for name, lo, hi, default in [("Hue (H)", 0, 359, 180),
                                       ("Saturation (S)", 0, 255, 255),
                                       ("Value / Brightness (V)", 0, 255, 255)]:
            row = BoxLayout(orientation='horizontal', size_hint_y=None,
                            height=dp(40), spacing=dp(8))
            row.add_widget(Label(text=name+":", color=(.8,.8,.8,1),
                                 font_size=FS(11), bold=True,
                                 size_hint_x=None, width=dp(140)))
            sl = Slider(min=lo, max=hi, value=default)
            sl.bind(value=self._on_slider)
            row.add_widget(sl)
            vl = Label(text='', color=(.67,.67,.67,1), font_size=FS(11),
                       size_hint_x=None, width=dp(50))
            row.add_widget(vl)
            self.add_widget(row)
            self._sliders[name] = (sl, vl)

        self.add_widget(Label(
            text="HSV vs HSL: In HSV, V=100% = brightest version. "
                 "In HSL, L=50% = purest hue; L=100% = always white.",
            color=(.6,.6,.6,1), font_size=FS(9), size_hint_y=None, height=dp(44)))

        # Copy button
        copy_btn = Button(text="Copy HEX to Clipboard", size_hint_y=None, height=dp(38),
                          background_color=(.18,.18,.31,1), color=(.8,.8,.8,1),
                          font_size=FS(11))
        copy_btn.bind(on_release=self._copy_hex)
        self.add_widget(copy_btn)

        self._update_display()

    def _copy_hex(self, *_):
        h = int(self._sliders["Hue (H)"][0].value)
        s = int(self._sliders["Saturation (S)"][0].value)
        v = int(self._sliders["Value / Brightness (V)"][0].value)
        r, g, b = hsv_to_rgb(h, s/255, v/255)
        hex_val = rgb_hex(r, g, b)
        try:
            from kivy.core.clipboard import Clipboard
            Clipboard.copy(hex_val)
        except Exception:
            pass
        app = App.get_running_app()
        if app and hasattr(app, '_toast') and app.root:
            app._toast.show(app.root, f"Copied {hex_val}")

    def _on_slider(self, *_):
        if self._updating: return
        self._update_display()
        h = self._sliders["Hue (H)"][0].value
        s = self._sliders["Saturation (S)"][0].value
        v = self._sliders["Value / Brightness (V)"][0].value
        self._on_change(int(h), int(s), int(v))

    def set_color(self, h, s, v):
        self._updating = True
        self._sliders["Hue (H)"][0].value = h
        self._sliders["Saturation (S)"][0].value = s
        self._sliders["Value / Brightness (V)"][0].value = v
        self._updating = False
        self._update_display()

    def _update_display(self):
        h = int(self._sliders["Hue (H)"][0].value)
        s = int(self._sliders["Saturation (S)"][0].value)
        v = int(self._sliders["Value / Brightness (V)"][0].value)
        r, g, b = hsv_to_rgb(h, s/255, v/255)
        cr, cg, cb = hsv_to_rgb((h+180)%360, s/255, v/255)

        self._prev.set_color(r, g, b)
        self._prev_lbl.color = _fg_for(r, g, b)
        self._prev_lbl.text = rgb_hex(r, g, b)
        self._comp.set_color(cr, cg, cb)
        self._comp_lbl.color = _fg_for(cr, cg, cb)
        self._comp_lbl.text = rgb_hex(cr, cg, cb)
        self._hex_lbl.text = f"{rgb_hex(r,g,b)}  |  Complement: {rgb_hex(cr,cg,cb)}"
        ri, gi, bi = int(r*255), int(g*255), int(b*255)
        self._rgb_lbl.text = f"R: {ri:3d}   G: {gi:3d}   B: {bi:3d}"
        hsl = rgb_to_hsl(r, g, b)
        self._hsl_lbl.text = f"HSL:  H: {h}   S: {int(hsl[1]*100)}%  L: {int(hsl[2]*100)}%"
        self._hsv_lbl.text = f"HSV:  H: {h}   S: {int(s/255*100)}%  V: {int(v/255*100)}%"
        self._sliders["Hue (H)"][1].text = f"{h}\u00b0"
        self._sliders["Saturation (S)"][1].text = f"{int(s/255*100)}%"
        self._sliders["Value / Brightness (V)"][1].text = f"{int(v/255*100)}%"


# ═══════════════════════════════════════════════════════════════
# 6. CONTRAST CHECKER
# ═══════════════════════════════════════════════════════════════

class ContrastCheckerWidget(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation='vertical', **kw)
        self.padding = [dp(20), dp(14)]
        self.spacing = dp(8)
        self.fg = (1, 1, 1)
        self.bg = (.118, .118, .235)
        self._sel = (0, .78, .78)

        self.add_widget(Label(text="WCAG Contrast Ratio Checker",
                              color=(.87,.87,.94,1), font_size=FS(15),
                              bold=True, size_hint_y=None, height=dp(28), halign='left'))
        self.add_widget(Label(
            text="WCAG 2.1 AA: >= 4.5:1 normal text, >= 3:1 large text.\n"
                 "WCAG 2.1 AAA: >= 7:1 normal text, >= 4.5:1 large text.",
            color=(.53,.53,.53,1), font_size=FS(10),
            size_hint_y=None, height=dp(36), halign='left'))

        # Selected colour row
        sel_row = BoxLayout(orientation='horizontal', size_hint_y=None,
                            height=dp(40), spacing=dp(8))
        sel_row.add_widget(Label(text="App colour:", color=(.7,.7,.7,1),
                                 font_size=FS(11), size_hint_x=None, width=dp(90)))
        self._sel_prev = ColorPreview(size_hint_x=None, width=dp(32), size_hint_y=None, height=dp(32))
        sel_row.add_widget(self._sel_prev)
        self._sel_hex = Label(text='', color=(.67,.67,.67,1), font_size=FS(10),
                              size_hint_x=None, width=dp(70))
        sel_row.add_widget(self._sel_hex)
        sel_row.add_widget(Widget())
        for txt, attr in [("Use as Text \u2192", 'fg'), ("Use as BG \u2192", 'bg')]:
            b = Button(text=txt, size_hint_x=None, width=dp(110),
                       background_color=(.18,.18,.31,1), color=(.8,.8,.8,1),
                       font_size=FS(10))
            b.bind(on_release=lambda *a, at=attr: self._use_sel(at))
            sel_row.add_widget(b)
        self.add_widget(sel_row)

        # FG / BG groups
        grp_row = BoxLayout(orientation='horizontal', spacing=dp(12),
                            size_hint_y=None, height=dp(200))
        for attr in ('fg', 'bg'):
            label_text = "Foreground (Text)" if attr == 'fg' else "Background"
            grp = BoxLayout(orientation='vertical', spacing=dp(6))
            grp.add_widget(Label(text=label_text, color=(.73,.73,.73,1),
                                 font_size=FS(11), bold=True,
                                 size_hint_y=None, height=dp(20)))
            prev = ColorPreview(size_hint_y=None, height=dp(70))
            setattr(self, f'_{attr}_prev', prev)
            grp.add_widget(prev)
            hx = Label(text='', color=(.67,.67,.67,1),
                       font_size=FS(10), size_hint_y=None, height=dp(16))
            setattr(self, f'_{attr}_hx', hx)
            grp.add_widget(hx)
            pb = Button(text="Pick Color...",
                        background_color=(.18,.18,.31,1), color=(.8,.8,.8,1),
                        font_size=FS(10), size_hint_y=None, height=dp(34))
            pb.bind(on_release=lambda *a, at=attr: self._pick(at))
            grp.add_widget(pb)
            preset_row = BoxLayout(spacing=dp(4), size_hint_y=None, height=dp(28))
            presets = [(1,1,1),(0,0,0),(.78,.78,.78),(.2,.2,.2)] if attr == 'fg' \
                else [(0,0,0),(1,1,1),(.118,.118,.235),(.94,.94,.94)]
            for pc in presets:
                pb2 = Button(background_normal='', background_down='',
                             background_color=pc[:3]+(1,),
                             size_hint_x=None, width=dp(28))
                pb2.bind(on_release=lambda *a, c=pc, at=attr: self._set(at, c))
                preset_row.add_widget(pb2)
            grp.add_widget(preset_row)
            grp_row.add_widget(grp)
        self.add_widget(grp_row)

        swap = Button(text="Swap Foreground / Background",
                      background_color=(.18,.18,.31,1), color=(.8,.8,.8,1),
                      font_size=FS(10), size_hint_y=None, height=dp(36))
        swap.bind(on_release=self._swap)
        self.add_widget(swap)

        # Result area
        self._result = BgCard(orientation='vertical', spacing=dp(6),
                              size_hint_y=None, height=dp(200), padding=[dp(14)])
        self.add_widget(self._result)
        self._ratio_lbl = Label(text='', font_size=FS(28), bold=True,
                                size_hint_y=None, height=dp(40))
        self._result.add_widget(self._ratio_lbl)
        self._prev_normal = Label(text="The quick brown fox jumps over the lazy dog. 0123456789",
                                  font_size=FS(13), halign='center',
                                  size_hint_y=None, height=dp(36))
        self._result.add_widget(self._prev_normal)
        self._prev_large = Label(text="Large Text Sample",
                                 font_size=FS(22), bold=True, halign='center',
                                 size_hint_y=None, height=dp(36))
        self._result.add_widget(self._prev_large)

        badge_row = BoxLayout(spacing=dp(6), size_hint_y=None, height=dp(28))
        self._badges = {}
        for key in ("AA Normal","AA Large","AAA Normal","AAA Large"):
            bl = Label(text=f"{key}: -", font_size=FS(10), bold=True,
                       size_hint_x=1, color=(.7,.7,.7,1))
            badge_row.add_widget(bl)
            self._badges[key] = bl
        self.add_widget(badge_row)
        Clock.schedule_once(lambda *_: self._refresh())

    def set_selected_color(self, r, g, b):
        self._sel = (r, g, b)
        self._refresh_sel()

    def _refresh_sel(self):
        r, g, b = self._sel
        self._sel_prev.set_color(r, g, b)
        self._sel_hex.text = rgb_hex(r, g, b)

    def _use_sel(self, which):
        if which == 'fg': self.fg = self._sel
        else: self.bg = self._sel
        self._refresh()

    def _pick(self, which):
        cp = ColorPicker(color=getattr(self, which)+(1,))
        content = BoxLayout(orientation='vertical')
        content.add_widget(cp)
        btn = Button(text="Select", size_hint_y=None, height=dp(44),
                     background_color=(.18,.18,.31,1), color=(.8,.8,.8,1))
        content.add_widget(btn)
        popup = Popup(title=f"Pick {'Foreground' if which=='fg' else 'Background'} Colour",
                      content=content, size_hint=(.85, .85))
        btn.bind(on_release=lambda *a: self._pick_done(which, cp.color, popup))
        popup.open()

    def _pick_done(self, which, col, popup):
        setattr(self, which, (col[0], col[1], col[2]))
        self._refresh(); popup.dismiss()

    def _set(self, which, c):
        setattr(self, which, c[:3]); self._refresh()

    def _swap(self, *_):
        self.fg, self.bg = self.bg, self.fg; self._refresh()

    def _refresh(self):
        for attr, prev_w, hx_w in [('fg', self._fg_prev, self._fg_hx),
                                    ('bg', self._bg_prev, self._bg_hx)]:
            r, g, b = getattr(self, attr)
            prev_w.set_color(r, g, b); hx_w.text = rgb_hex(r, g, b)
        ratio = wcag_ratio(*self.fg, *self.bg)
        self._ratio_lbl.text = f"{ratio:.2f} : 1"
        colour = (.3,.69,.31,1) if ratio >= 7 else (.55,.76,.29,1) if ratio >= 4.5 \
            else (1,.6,0,1) if ratio >= 3 else (.96,.26,.21,1)
        self._ratio_lbl.color = colour
        fr, fg_, fb = self.fg
        br, bg_, bb = self.bg
        for lbl in (self._prev_normal, self._prev_large):
            lbl.color = self.fg + (1,)
            lbl.canvas.before.clear()
            with lbl.canvas.before:
                Color(br, bg_, bb, 1)
                Rectangle(pos=lbl.pos, size=lbl.size)
        checks = {"AA Normal": ratio>=4.5, "AA Large": ratio>=3,
                   "AAA Normal": ratio>=7, "AAA Large": ratio>=4.5}
        for k, v in checks.items():
            sym = "PASS" if v else "FAIL"
            c = (.3,.69,.31,1) if v else (.96,.26,.21,1)
            bl = self._badges[k]; bl.text = f"{k}: {sym}"; bl.color = c
        self._refresh_sel()


# ═══════════════════════════════════════════════════════════════
# 7. COLOUR BLINDNESS
# ═══════════════════════════════════════════════════════════════

class ColorBlindnessWidget(RelativeLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._r = 0; self._g = .78; self._b = .78
        self.bind(size=self._redraw, pos=self._redraw)
        Clock.schedule_once(self._redraw)

    def set_color(self, h, s, v):
        self._r, self._g, self._b = hsv_to_rgb(h, s/255, v/255)
        self._redraw()

    def _redraw(self, *_):
        if self.width < 10: return
        self.canvas.clear()
        for c in list(self.children): self.remove_widget(c)
        sw, sh = dp(100), dp(64)
        y = dp(8)
        for name, simfn, desc in CVD_SIMS:
            sr, sg, sb = simfn(self._r, self._g, self._b)
            with self.canvas:
                _draw_rr(self.canvas, dp(14), y-2, sw, sh, 6, (0,0,0,.15))
                _draw_rr(self.canvas, dp(10), y, sw, sh, 6, (sr,sg,sb,1))
                Color(.35,.35,.43,1)
                Line(rounded_rectangle=(dp(10), y, sw, sh, 6), width=1)
            nl = Label(text=name, color=(.82,.82,.9,1), font_size=FS(10),
                       bold=True, size_hint_y=None, height=dp(16), halign='left')
            nl.x = dp(120); nl.y = y + sh - dp(12)
            self.add_widget(nl)
            dl = Label(text=desc, color=(.55,.55,.67,1), font_size=FS(8),
                       size_hint_y=None, height=dp(14), halign='left')
            dl.x = dp(120); dl.y = y + sh - dp(28)
            self.add_widget(dl)
            hl = Label(text=f"Simulated: {rgb_hex(sr,sg,sb)}",
                       color=(.67,.67,.78,1), font_size=FS(8),
                       size_hint_y=None, height=dp(14), halign='left')
            hl.x = dp(120); hl.y = y + sh - dp(42)
            self.add_widget(hl)
            fg = _fg_for(sr, sg, sb)
            sl = Label(text=rgb_hex(sr,sg,sb), color=fg[:3]+(1,),
                       font_size=FS(8), bold=True,
                       size_hint=(None, None), size=(sw, dp(14)), halign='center')
            sl.x = dp(10); sl.y = y + 2
            self.add_widget(sl)
            y += sh + dp(30)
        self.height = y


class PaletteBlindnessWidget(RelativeLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(size=self._redraw, pos=self._redraw)
        Clock.schedule_once(self._redraw)

    def _redraw(self, *_):
        if self.width < 10: return
        self.canvas.clear()
        for c in list(self.children): self.remove_widget(c)
        ui_colors = [("Success",.3,.69,.31), ("Warning",1,.76,.03),
                     ("Error",.96,.26,.21), ("Info",.13,.59,.95),
                     ("Link",.4,.23,.72)]
        sw, sh = dp(60), dp(24)
        row_h = sh + dp(24)
        for ri, (sname, simfn, _) in enumerate(CVD_SIMS):
            y = ri * row_h
            nl = Label(text=sname, color=(.63,.63,.7,1), font_size=FS(8),
                       bold=True, size_hint=(None, None), size=(dp(78), dp(14)),
                       halign='left')
            nl.x = 0; nl.y = y + dp(2)
            self.add_widget(nl)
            x = dp(82)
            for name, cr, cg, cb in ui_colors:
                sr, sg, sb = simfn(cr, cg, cb)
                with self.canvas:
                    _draw_rr(self.canvas, x, y, sw, sh, 4, (sr,sg,sb,1))
                cl = Label(text=name, color=(.75,.75,.82,1), font_size=FS(7),
                           size_hint=(None, None), size=(sw, dp(13)), halign='center')
                cl.x = x; cl.y = y + sh + dp(2)
                self.add_widget(cl)
                x += sw + dp(8)
        self.height = len(CVD_SIMS) * row_h + dp(8)


# ═══════════════════════════════════════════════════════════════
# 8. THEORY GUIDE
# ═══════════════════════════════════════════════════════════════

THEORY_SECTIONS = [
    ("The Colour Wheel",
     "The colour wheel arranges hues in a circle showing their relationships. "
     "Isaac Newton created the first circular diagram in 1666 by splitting sunlight "
     "through a prism. The wheel reveals harmonies based on geometric relationships.\n\n"
     "The wheel has 12 main segments: 3 primaries, 3 secondaries, and 6 tertiaries."),
    ("Primary Colours",
     "Primary colours cannot be mixed from other colours.\n\n"
     "RGB (Additive/Light): Red, Green, Blue. All three = White.\n"
     "RYB (Subtractive/Paint): Red, Yellow, Blue. All three = Dark brown.\n"
     "CMYK (Print): Cyan, Magenta, Yellow, Key (Black)."),
    ("Secondary Colours",
     "Made by mixing two primaries in equal proportion:\n\n"
     "RGB: Cyan (G+B), Magenta (R+B), Yellow (R+G)\n"
     "RYB: Orange (R+Y), Green (Y+B), Purple (R+B)\n\n"
     "Secondaries sit between their parent primaries on the wheel."),
    ("Tertiary Colours",
     "Made by mixing a primary with an adjacent secondary (e.g. Red-Orange). "
     "There are 6 tertiary colours per model, creating 12 distinct wheel segments."),
    ("Colour Temperature",
     "Warm colours (red to yellow) advance and evoke energy, passion, warmth. "
     "Cool colours (blue to green) recede and evoke calm, trust, serenity.\n\n"
     "Temperature is relative – a blue can be 'warm' if it leans toward violet."),
    ("Value, Saturation & Chroma",
     "Value: How light or dark. Tints = hue + white. Shades = hue + black.\n"
     "Saturation: Intensity or purity. Tones = hue + gray.\n"
     "Hue: The colour family name (red, blue, green, etc.)."),
    ("Simultaneous Contrast",
     "A colour appears different depending on its neighbours. Grey on yellow looks "
     "purplish; grey on blue looks orange-ish. Discovered by Chevreul in 1839."),
    ("The 60-30-10 Rule",
     "60% Dominant (background), 30% Secondary (sections), "
     "10% Accent (highlights, CTAs). Creates visual hierarchy and prevents chaos."),
    ("Accessibility & Colour",
     "~8% of men and 0.5% of women have colour-vision deficiency.\n"
     "Never rely on colour alone – add labels, patterns, icons.\n"
     "Use contrast ratios >= 4.5:1 for body text (WCAG AA)."),
    ("Colour Psychology",
     "Red: Passion, urgency. Blue: Trust, calm. Yellow: Optimism.\n"
     "Green: Nature, growth. Purple: Luxury. Orange: Energy.\n"
     "Black: Elegance. Note: associations vary by culture."),
]

class TheoryCard(BoxLayout):
    def __init__(self, title, body, **kw):
        super().__init__(orientation='vertical', **kw)
        self.padding = dp(14)
        self.spacing = dp(8)
        self.size_hint_y = None
        with self.canvas.before:
            self._bg_c = Color(.145,.145,.25,1)
            self._bg_r = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd, size=self._upd)
        t_lbl = Label(text=title, color=(.75,.75,.88,1), font_size=FS(12),
                      bold=True, size_hint_y=None, height=dp(24), halign='left',
                      valign='middle')
        t_lbl.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))
        self.add_widget(t_lbl)
        b_lbl = Label(text=body, color=(.63,.63,.75,1), font_size=FS(11),
                      size_hint_y=None, halign='left', valign='top', markup=False)
        b_lbl.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))
        b_lbl.bind(texture_size=lambda i, v: setattr(i, 'height', v[1]+dp(4)))
        self.add_widget(b_lbl)
        self.bind(minimum_height=self.setter('height'))
    def _upd(self, *_):
        self._bg_r.pos = self.pos; self._bg_r.size = self.size

class TheoryPage(ScrollView):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.bar_width = dp(10)
        self.bar_color = (.26,.26,.26,1)
        layout = BoxLayout(orientation='vertical', spacing=dp(14),
                           size_hint_y=None, padding=dp(14))
        layout.bind(minimum_height=layout.setter('height'))
        layout.add_widget(Label(text="Understanding Colour Theory",
                                color=(.88,.88,.94,1), font_size=FS(18),
                                bold=True, size_hint_y=None, height=dp(40)))
        for title, body in THEORY_SECTIONS:
            layout.add_widget(TheoryCard(title=title, body=body))
        self.add_widget(layout)


# ═══════════════════════════════════════════════════════════════
# 9. RESPONSIVE SIDEBAR / DRAWER
# ═══════════════════════════════════════════════════════════════

PAGES = [
    ("\U0001f3a8 Colour Wheel",  "wheel"),
    ("\u262f Harmonies",         "harmonies"),
    ("\U0001f5e1 Mixing",       "mixing"),
    ("\U0001f4ca Properties",   "properties"),
    ("\U0001f527 HSL Explorer", "hsl"),
    ("\u2626 Accessibility",    "access"),
    ("\U0001f441 Blindness",    "blind"),
    ("\U0001f4d6 Theory Guide", "theory"),
]

PAGE_TITLES = {
    "wheel": "Interactive Colour Wheel",
    "harmonies": "Colour Harmonies",
    "mixing": "Colour Mixing Models",
    "properties": "Colour Properties",
    "hsl": "HSL / HSV Explorer",
    "access": "WCAG Contrast Checker",
    "blind": "Colour Blindness Simulation",
    "theory": "Theory Guide",
}

class DrawerSidebar(BoxLayout):
    """Collapsible sidebar with navigation."""
    def __init__(self, on_nav, **kw):
        super().__init__(orientation='vertical', **kw)
        self.size_hint_x = None
        self.width = dp(220)
        self.spacing = dp(2)
        self.padding = [dp(10), dp(16)]
        self._on_nav = on_nav

        with self.canvas.before:
            self._bg_c = Color(.07,.07,.16,1)
            self._bg_r = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda i, v: setattr(i._bg_r, 'pos', v),
                  size=lambda i, v: setattr(i._bg_r, 'size', v))

        self.add_widget(Label(text="Color Theory", color=(.69,.69,.88,1),
                              font_size=FS(15), bold=True,
                              size_hint_y=None, height=dp(30), halign='left'))
        self.add_widget(Label(text="Interactive Visualizer", color=(.38,.38,.63,1),
                              font_size=FS(10), size_hint_y=None, height=dp(20), halign='left'))
        self.add_widget(DarkSeparator())

        self.nav_btns = []
        for text, pid in PAGES:
            b = ToggleButton(text=text, group='nav')
            b.bind(on_release=lambda btn, p=pid: self._nav(p))
            self.add_widget(b)
            self.nav_btns.append((b, pid))

        self.add_widget(Widget())
        self.add_widget(DarkSeparator())

        self.add_widget(Label(text="Selected Colour", color=(.44,.44,.63,1),
                              font_size=FS(9), size_hint_y=None, height=dp(20), halign='left'))
        self.sb_prev = ColorPreview(size_hint_y=None, height=dp(44))
        self.sb_hex = Label(text='', color=(.47,.47,.47,1),
                            font_size=FS(11), size_hint_y=None, height=dp(22), halign='center')
        self.add_widget(self.sb_prev)
        self.add_widget(self.sb_hex)

        # Version label
        self.add_widget(Label(text="v2.0 – Desktop & Android", color=(.3,.3,.45,1),
                              font_size=FS(8), size_hint_y=None, height=dp(16), halign='center'))

    def _nav(self, pid):
        self._on_nav(pid)

    def set_active(self, pid):
        for btn, bid in self.nav_btns:
            btn.state = 'down' if bid == pid else 'normal'


# ═══════════════════════════════════════════════════════════════
# 10. MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════

class ColorTheoryApp(App):
    title = "Color Theory Visualizer"

    def build(self):
        Builder.load_string(KV)

        self._hue = 180; self._sat = 255; self._val = 255
        self._toast = Toast()
        self._is_mobile = kivy_platform in ('android', 'ios')
        self._drawer_open = False

        # ── Root layout ──
        self._root = FloatLayout()

        # Main content area
        self._content = BoxLayout(orientation='horizontal')

        # ── Sidebar ──
        self._sidebar = DrawerSidebar(on_nav=self._go)
        self._sidebar.sb_prev.bind(on_touch_down=self._on_sb_prev_tap)

        # ── Screen Manager ──
        self.sm = ScreenManager(transition=SlideTransition(duration=.25))
        for _, pid in PAGES:
            self.sm.add_widget(Screen(name=pid))

        self._content.add_widget(self.sm)
        self._root.add_widget(self._content)

        # ── Top bar (mobile) ──
        self._topbar = BoxLayout(orientation='horizontal', size_hint=(1, None),
                                 height=dp(52), pos_hint={'top': 1},
                                 padding=[dp(8), dp(4)])
        with self._topbar.canvas.before:
            self._tb_bg_c = Color(.07,.07,.16,.95)
            self._tb_bg_r = Rectangle(pos=self._topbar.pos, size=self._topbar.size)
        self._topbar.bind(pos=lambda i, v: setattr(i._tb_bg_r, 'pos', v),
                          size=lambda i, v: setattr(i._tb_bg_r, 'size', v))

        self._menu_btn = Button(text='\u2630', font_size=FS(22),
                                size_hint_x=None, width=dp(48),
                                background_normal='', background_down='',
                                background_color=(.12,.12,.22,1),
                                color=(.85,.85,.85,1))
        self._menu_btn.bind(on_release=self._toggle_drawer)
        self._topbar.add_widget(self._menu_btn)
        self._page_title = Label(text='Color Theory Visualizer',
                                 color=(.88,.88,.94,1), font_size=FS(15),
                                 bold=True, halign='left', valign='middle')
        self._topbar.add_widget(self._page_title)

        # Copy hex button in topbar
        self._copy_btn = Button(text='Copy', font_size=FS(10),
                                size_hint_x=None, width=dp(60),
                                background_normal='', background_down='',
                                background_color=(.18,.18,.31,1),
                                color=(.8,.8,.8,1))
        self._copy_btn.bind(on_release=self._copy_current_hex)
        self._topbar.add_widget(self._copy_btn)

        # ── Drawer overlay ──
        self._drawer_overlay = Widget(size_hint=(1, 1))
        self._drawer_overlay.opacity = 0
        self._drawer_bg = BoxLayout(size_hint=(1, 1))
        with self._drawer_bg.canvas.before:
            Color(0, 0, 0, .5)
            Rectangle(pos=self._drawer_bg.pos, size=self._drawer_bg.size)
        self._drawer_bg.bind(pos=lambda i, v: setattr(i.canvas.before.children[-1], 'pos', v),
                             size=lambda i, v: setattr(i.canvas.before.children[-1], 'size', v))

        # ── Build pages ──
        self._build_wheel_page()
        self._build_harmony_page()
        self._build_mixing_page()
        self._build_properties_page()
        self._build_hsl_page()
        self._build_access_page()
        self._build_blindness_page()
        self._build_theory_page()

        # ── Apply layout mode ──
        self._apply_layout()

        # ── Navigate to first page ──
        self._go("wheel")
        Clock.schedule_once(lambda *_: self._propagate())

        # ── Window resize handler ──
        Window.bind(on_resize=self._on_resize)

        # ── Android back button ──
        if self._is_mobile:
            try:
                from android import mActivity
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
            except Exception:
                pass

        return self._root

    def _apply_layout(self):
        """Switch between desktop (sidebar) and mobile (drawer) layout."""
        w = Window.width
        mobile_mode = w < dp(700) or self._is_mobile
        self._mobile_mode = mobile_mode

        # Remove everything from root first
        self._root.clear_widgets()
        self._content.clear_widgets()

        if mobile_mode:
            # Mobile: top bar + content (no persistent sidebar)
            self._content.add_widget(self.sm)
            self._root.add_widget(self._content)
            self._root.add_widget(self._topbar)
            # Add padding to content so it's not behind topbar
            self._content.padding = [0, dp(52), 0, 0]
            self._sidebar.width = min(dp(280), Window.width - dp(60))
            self._drawer_open = False
        else:
            # Desktop: sidebar + content
            self._content.padding = [0, 0, 0, 0]
            self._content.add_widget(self._sidebar)
            self._content.add_widget(self.sm)
            self._root.add_widget(self._content)
            self._topbar.parent = None if self._topbar.parent else None

    def _on_resize(self, instance, width, height):
        self._apply_layout()

    def _toggle_drawer(self, *_):
        if not self._mobile_mode:
            return
        if self._drawer_open:
            self._close_drawer()
        else:
            self._open_drawer()

    def _open_drawer(self):
        self._drawer_open = True
        # Add overlay + sidebar on top
        self._root.add_widget(self._drawer_bg)
        self._drawer_bg.on_touch_down = lambda touch: self._close_drawer() or True
        self._root.add_widget(self._sidebar)
        self._sidebar.x = 0
        self._sidebar.top = self._root.height - dp(52)
        self._sidebar.height = self._root.height - dp(52)

    def _close_drawer(self, *_):
        self._drawer_open = False
        if self._drawer_bg in self._root.children:
            self._root.remove_widget(self._drawer_bg)
        if self._sidebar in self._root.children:
            self._root.remove_widget(self._sidebar)

    def _on_sb_prev_tap(self, instance, touch):
        """Copy selected colour hex on tap."""
        if instance.collide_point(*touch.pos):
            r, g, b = hsv_to_rgb(self._hue, self._sat/255, self._val/255)
            hex_val = rgb_hex(r, g, b)
            try:
                from kivy.core.clipboard import Clipboard
                Clipboard.copy(hex_val)
            except Exception:
                pass
            self._toast.show(self._root, f"Copied {hex_val}")

    def _copy_current_hex(self, *_):
        r, g, b = hsv_to_rgb(self._hue, self._sat/255, self._val/255)
        hex_val = rgb_hex(r, g, b)
        try:
            from kivy.core.clipboard import Clipboard
            Clipboard.copy(hex_val)
        except Exception:
            pass
        self._toast.show(self._root, f"Copied {hex_val}")

    def _screen(self, name):
        return self.sm.get_screen(name)

    # ─── Page Builders ───────────────────────────────────

    def _build_wheel_page(self):
        screen = self._screen("wheel")
        layout = BoxLayout(orientation='horizontal', padding=[dp(10), dp(8)], spacing=dp(10))

        # Left: wheel
        left = BoxLayout(orientation='vertical', spacing=dp(6), size_hint_x=3)
        left.add_widget(Label(text="Interactive Colour Wheel", color=(.88,.88,.94,1),
                              font_size=FS(16), bold=True, size_hint_y=None, height=dp(28),
                              halign='left'))
        left.add_widget(Label(
            text="Drag the marker around the hue ring to select a colour.\n"
                 "Adjust saturation and brightness with the sliders below.",
            color=(.55,.55,.67,1), font_size=FS(10),
            size_hint_y=None, height=dp(34), halign='left'))

        wheel_container = BoxLayout(orientation='vertical')
        self._wheel = ColorWheelWidget(on_change=self._on_wheel_change)
        wheel_container.add_widget(self._wheel)
        left.add_widget(wheel_container)

        # Sliders
        self._wheel_sliders = {}
        for name, lo, hi, default in [("Saturation", 0, 255, 255),
                                       ("Brightness", 0, 255, 255)]:
            row = BoxLayout(orientation='horizontal', size_hint_y=None,
                            height=dp(40), spacing=dp(8))
            row.add_widget(Label(text=name+":", color=(.8,.8,.8,1),
                                 font_size=FS(11), bold=True,
                                 size_hint_x=None, width=dp(100)))
            sl = Slider(min=lo, max=hi, value=default)
            sl.bind(value=self._on_wheel_slider)
            row.add_widget(sl)
            vl = Label(text='', color=(.67,.67,.67,1), font_size=FS(11),
                       size_hint_x=None, width=dp(50))
            row.add_widget(vl)
            left.add_widget(row)
            self._wheel_sliders[name] = (sl, vl)

        layout.add_widget(left)

        # Right: quick info panel
        right = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_x=2,
                          padding=[dp(8), dp(4)])
        card = BgCard(orientation='vertical', spacing=dp(6), padding=[dp(14)])
        card_label = Label(text="Selected Colour", color=(.82,.82,.9,1),
                           font_size=FS(12), bold=True, size_hint_y=None, height=dp(22))
        card.add_widget(card_label)
        self._wheel_preview = ColorPreview(size_hint_y=None, height=dp(80))
        self._wheel_preview_lbl = Label(text='', font_size=FS(14), bold=True)
        self._wheel_preview.add_widget(self._wheel_preview_lbl)
        card.add_widget(self._wheel_preview)

        self._wheel_info = Label(text='', color=(.6,.6,.75,1), font_size=FS(10),
                                 size_hint_y=None, height=dp(60), halign='left',
                                 valign='top')
        self._wheel_info.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))
        card.add_widget(self._wheel_info)

        # Quick harmonies
        self._wheel_quick = Label(text='', color=(.55,.55,.67,1), font_size=FS(9),
                                  size_hint_y=None, height=dp(80), halign='left',
                                  valign='top', markup=False)
        self._wheel_quick.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))
        card.add_widget(self._wheel_quick)

        card.bind(minimum_height=card.setter('height'))
        right.add_widget(card)
        layout.add_widget(right)

        sv = ScrollView()
        sv.add_widget(layout)
        screen.add_widget(sv)

    def _build_harmony_page(self):
        screen = self._screen("harmonies")
        layout = BoxLayout(orientation='vertical', padding=[dp(14), dp(8)], spacing=dp(8))
        layout.add_widget(Label(text="Colour Harmonies", color=(.88,.88,.94,1),
                                font_size=FS(16), bold=True, size_hint_y=None, height=dp(28),
                                halign='left'))
        layout.add_widget(Label(
            text="Tap any swatch hex to copy it. Harmonies are based on geometric positions on the colour wheel.",
            color=(.55,.55,.67,1), font_size=FS(10),
            size_hint_y=None, height=dp(28), halign='left'))
        sv = ScrollView(bar_width=dp(8))
        self._harmony = HarmonyWidget(size_hint_y=None)
        sv.add_widget(self._harmony)
        layout.add_widget(sv)
        screen.add_widget(layout)

    def _build_mixing_page(self):
        screen = self._screen("mixing")
        layout = BoxLayout(orientation='vertical', padding=[dp(14), dp(8)], spacing=dp(8))
        layout.add_widget(Label(text="Colour Mixing Models", color=(.88,.88,.94,1),
                                font_size=FS(16), bold=True, size_hint_y=None, height=dp(28),
                                halign='left'))
        layout.add_widget(Label(
            text="Additive mixing (light) combines RGB to make white. "
                 "Subtractive mixing (pigment) combines RYB to make dark.",
            color=(.55,.55,.67,1), font_size=FS(10),
            size_hint_y=None, height=dp(28), halign='left'))
        self._mixing = ColorMixingWidget(size_hint_y=None, height=dp(500))
        sv = ScrollView(bar_width=dp(8))
        sv.add_widget(self._mixing)
        layout.add_widget(sv)
        screen.add_widget(layout)

    def _build_properties_page(self):
        screen = self._screen("properties")
        layout = BoxLayout(orientation='vertical', padding=[dp(14), dp(8)], spacing=dp(8))
        layout.add_widget(Label(text="Colour Properties", color=(.88,.88,.94,1),
                                font_size=FS(16), bold=True, size_hint_y=None, height=dp(28),
                                halign='left'))
        layout.add_widget(Label(
            text="Tints, shades, tones, temperature, and saturation derived from your selected colour.",
            color=(.55,.55,.67,1), font_size=FS(10),
            size_hint_y=None, height=dp(28), halign='left'))
        sv = ScrollView(bar_width=dp(8))
        self._properties = ColorPropertiesWidget(size_hint_y=None)
        sv.add_widget(self._properties)
        layout.add_widget(sv)
        screen.add_widget(layout)

    def _build_hsl_page(self):
        screen = self._screen("hsl")
        sv = ScrollView(bar_width=dp(8))
        self._hsl_explorer = HSLExplorerWidget(on_change=self._on_hsl_change,
                                                size_hint_y=None)
        # Let it size naturally
        self._hsl_explorer.bind(minimum_height=self._hsl_explorer.setter('height'))
        sv.add_widget(self._hsl_explorer)
        screen.add_widget(sv)

    def _build_access_page(self):
        screen = self._screen("access")
        sv = ScrollView(bar_width=dp(8))
        self._contrast = ContrastCheckerWidget(size_hint_y=None)
        self._contrast.bind(minimum_height=self._contrast.setter('height'))
        sv.add_widget(self._contrast)
        screen.add_widget(sv)

    def _build_blindness_page(self):
        screen = self._screen("blind")
        layout = BoxLayout(orientation='vertical', padding=[dp(14), dp(8)], spacing=dp(8))
        layout.add_widget(Label(text="Colour Blindness Simulation", color=(.88,.88,.94,1),
                                font_size=FS(16), bold=True, size_hint_y=None, height=dp(28),
                                halign='left'))
        layout.add_widget(Label(
            text="See how your selected colour appears to people with different types of colour vision deficiency.",
            color=(.55,.55,.67,1), font_size=FS(10),
            size_hint_y=None, height=dp(28), halign='left'))
        sv = ScrollView(bar_width=dp(8))
        inner = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(14))
        inner.bind(minimum_height=inner.setter('height'))

        card1 = BgCard(orientation='vertical', spacing=dp(4), padding=[dp(10)])
        card1_lbl = Label(text="Selected Colour Under CVD", color=(.82,.82,.9,1),
                          font_size=FS(11), bold=True, size_hint_y=None, height=dp(20))
        card1.add_widget(card1_lbl)
        self._blindness = ColorBlindnessWidget(size_hint_y=None)
        card1.add_widget(self._blindness)
        card1.bind(minimum_height=card1.setter('height'))
        inner.add_widget(card1)

        card2 = BgCard(orientation='vertical', spacing=dp(4), padding=[dp(10)])
        card2_lbl = Label(text="UI Palette Under CVD", color=(.82,.82,.9,1),
                          font_size=FS(11), bold=True, size_hint_y=None, height=dp(20))
        card2.add_widget(card2_lbl)
        self._palette_blind = PaletteBlindnessWidget(size_hint_y=None)
        card2.add_widget(self._palette_blind)
        card2.bind(minimum_height=card2.setter('height'))
        inner.add_widget(card2)

        sv.add_widget(inner)
        layout.add_widget(sv)
        screen.add_widget(layout)

    def _build_theory_page(self):
        screen = self._screen("theory")
        screen.add_widget(TheoryPage())

    # ─── Navigation ──────────────────────────────────────

    def _go(self, pid):
        self.sm.current = pid
        self._sidebar.set_active(pid)
        self._page_title.text = PAGE_TITLES.get(pid, "Color Theory")
        if self._drawer_open:
            self._close_drawer()

    # ─── Colour Change Handlers ──────────────────────────

    def _on_wheel_change(self, h, s, v):
        self._hue = h; self._sat = s; self._val = v
        self._propagate()

    def _on_wheel_slider(self, *_):
        s = int(self._wheel_sliders["Saturation"][0].value)
        v = int(self._wheel_sliders["Brightness"][0].value)
        self._sat = s; self._val = v
        self._wheel_sliders["Saturation"][1].text = f"{int(s/255*100)}%"
        self._wheel_sliders["Brightness"][1].text = f"{int(v/255*100)}%"
        self._wheel.set_hsv(self._hue, s, v, propagate=False)
        self._propagate()

    def _on_hsl_change(self, h, s, v):
        self._hue = h; self._sat = s; self._val = v
        self._propagate()

    def _propagate(self):
        """Push the current colour to all widgets."""
        h, s, v = self._hue, self._sat, self._val
        r, g, b = hsv_to_rgb(h, s/255, v/255)

        # Sidebar
        self._sidebar.sb_prev.set_color(r, g, b)
        self._sidebar.sb_hex.text = rgb_hex(r, g, b)

        # Wheel page
        if hasattr(self, '_wheel_preview'):
            self._wheel_preview.set_color(r, g, b)
            self._wheel_preview_lbl.color = _fg_for(r, g, b)
            self._wheel_preview_lbl.text = rgb_hex(r, g, b)
            ri, gi, bi = int(r*255), int(g*255), int(b*255)
            hsl = rgb_to_hsl(r, g, b)
            self._wheel_info.text = (
                f"HEX: {rgb_hex(r,g,b)}\n"
                f"RGB: {ri}, {gi}, {bi}\n"
                f"HSL: {h}\u00b0, {int(hsl[1]*100)}%, {int(hsl[2]*100)}%\n"
                f"HSV: {h}\u00b0, {int(s/255*100)}%, {int(v/255*100)}%")
            cr, cg, cb = hsv_to_rgb((h+180)%360, s/255, v/255)
            tr, tg, tb = hsv_to_rgb((h+120)%360, s/255, v/255)
            self._wheel_quick.text = (
                f"Complement: {rgb_hex(cr,cg,cb)}\n"
                f"Triadic: {rgb_hex(r,g,b)}, {rgb_hex(tr,tg,tb)}, "
                f"{rgb_hex(*hsv_to_rgb((h+240)%360, s/255, v/255))}")

        # Wheel sliders
        if hasattr(self, '_wheel_sliders'):
            self._wheel_sliders["Saturation"][0].value = s
            self._wheel_sliders["Saturation"][1].text = f"{int(s/255*100)}%"
            self._wheel_sliders["Brightness"][0].value = v
            self._wheel_sliders["Brightness"][1].text = f"{int(v/255*100)}%"

        # Other pages
        if hasattr(self, '_harmony'):
            self._harmony.set_color(h, s, v)
        if hasattr(self, '_properties'):
            self._properties.set_color(h, s, v)
        if hasattr(self, '_hsl_explorer'):
            self._hsl_explorer.set_color(h, s, v)
        if hasattr(self, '_contrast'):
            self._contrast.set_selected_color(r, g, b)
        if hasattr(self, '_blindness'):
            self._blindness.set_color(h, s, v)


# ─── Run ──────────────────────────────────────────────────────

if __name__ == '__main__':
    # Set desktop window size if not on mobile
    if kivy_platform not in ('android', 'ios'):
        try:
            Window.size = (1100, 720)
            Window.minimum_width = 400
            Window.minimum_height = 500
        except Exception:
            pass

    ColorTheoryApp().run()