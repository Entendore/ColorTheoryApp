"""Colour Wheel interactive page – Professional 2D Picker."""
import math
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.graphics import (
    Color, Ellipse, Line, Mesh,
    StencilPush, StencilUse, StencilUnUse, StencilPop,
)
from kivy.metrics import dp, sp as _sp
from kivy.clock import Clock
from color_utils import hsv_to_rgb, rgb_hex, fg_for, rgb_to_hsl
from ui_components import ColorPreview, BgCard, CopyHexButton

FS = _sp


class ColorWheelWidget(RelativeLayout):
    """Professional colour wheel with hue ring and circular-masked SV picker.

    The SV picker uses a 32×32 subdivided mesh because the HSV→RGB mapping
    is non-linear: a naive 4-vertex (2-triangle) quad produces incorrect
    colours since GPU barycentric interpolation ≠ true bilinear interpolation.
    """

    _SV_RES = 32          # mesh subdivision for the gradient square
    _RING_PAD = dp(8)     # extra touch padding around the hue ring
    _SV_PAD = dp(4)       # extra touch padding around the SV circle

    def __init__(self, on_change, **kw):
        super().__init__(**kw)
        self.size_hint = (None, None)
        self.size = (dp(290), dp(290))
        self._on_change = on_change

        # Internal state – S and V stored as 0.0-1.0 for simpler maths
        self._hue = 180.0
        self._sat = 1.0
        self._val = 1.0
        self._drag = None          # 'hue' | 'sv' | None

        # Geometry cache (set in _redraw, read in touch handlers)
        self._cx = self._cy = 0.0
        self._outr = self._inr = self._svr = 0.0
        self._sv_side = 0.0
        self._sv_x0 = self._sv_y0 = 0.0

        # Degree labels around the wheel
        self._deg_labels = []
        for deg in range(0, 360, 30):
            lbl = Label(
                text=f"{deg}\u00b0",
                font_size=FS(7),
                color=(.62, .62, .76, .65),
                size_hint=(None, None),
                size=(dp(30), dp(14)),
                halign='center',
            )
            self.add_widget(lbl)
            self._deg_labels.append((deg, lbl))

        self.bind(size=self._redraw, pos=self._redraw)
        Clock.schedule_once(self._redraw)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_hsv(self, h, s_255, v_255, propagate=False):
        self._hue = h % 360 if h >= 0 else 0
        self._sat = max(0.0, min(1.0, s_255 / 255.0))
        self._val = max(0.0, min(1.0, v_255 / 255.0))
        self._redraw()
        if propagate:
            self._on_change(self._hue, int(self._sat * 255), int(self._val * 255))

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def _redraw(self, *_):
        w, h = self.width, self.height
        if w < 10 or h < 10:
            return

        self.canvas.clear()
        cx, cy = self.center

        # --- geometry ---
        outr = min(w, h) / 2 - 22       # outer edge of hue ring
        ring_w = dp(20)                   # ring thickness
        inr = outr - ring_w               # inner edge of hue ring
        gap = dp(3)                       # visual gap between ring & SV circle
        svr = inr - gap                   # radius of the SV circle

        # cache for touch handlers
        self._cx, self._cy = cx, cy
        self._outr, self._inr, self._svr = outr, inr, svr

        # inscribed square inside the SV circle
        sv_side = svr * math.sqrt(2)
        sv_half = sv_side / 2
        sv_x0, sv_y0 = cx - sv_half, cy - sv_half
        self._sv_side = sv_side
        self._sv_x0, self._sv_y0 = sv_x0, sv_y0

        # ---- 1. Hue ring (360-segment Mesh) ----
        segs = 360
        verts, idxs = [], []
        for i in range(segs):
            a1 = math.radians(i)
            a2 = math.radians(i + 1)
            r, g, b = hsv_to_rgb(i, 1.0, 1.0)
            base = i * 4
            verts += [
                cx + outr * math.cos(a1), cy + outr * math.sin(a1), 0, 0, r, g, b, 1,
                cx + outr * math.cos(a2), cy + outr * math.sin(a2), 0, 0, r, g, b, 1,
                cx + inr  * math.cos(a2), cy + inr  * math.sin(a2), 0, 0, r, g, b, 1,
                cx + inr  * math.cos(a1), cy + inr  * math.sin(a1), 0, 0, r, g, b, 1,
            ]
            idxs += [base, base+1, base+2, base, base+2, base+3]

        with self.canvas:
            Mesh(vertices=verts, indices=idxs, mode='triangles')
            # subtle ring borders
            Color(.18, .18, .30, .55)
            Line(circle=(cx, cy, outr), width=1)
            Line(circle=(cx, cy, inr),  width=1)

        # ---- 2. Background circle for SV area ----
        with self.canvas:
            Color(.09, .09, .17, 1)
            Ellipse(pos=(cx - svr, cy - svr), size=(svr * 2, svr * 2))

        # ---- 3. SV picker (subdivided Mesh, stencil-clipped to circle) ----
        N = self._SV_RES
        sv_verts, sv_idxs = [], []
        for j in range(N + 1):
            v = j / N
            py = sv_y0 + v * sv_side
            for i in range(N + 1):
                s = i / N
                px = sv_x0 + s * sv_side
                r, g, b = hsv_to_rgb(self._hue, s, v)
                sv_verts += [px, py, 0, 0, r, g, b, 1]

        for j in range(N):
            for i in range(N):
                idx = j * (N + 1) + i
                sv_idxs += [
                    idx,     idx + 1,     idx + N + 1,
                    idx + 1, idx + N + 2, idx + N + 1,
                ]

        with self.canvas:
            StencilPush()
            Ellipse(pos=(cx - svr, cy - svr), size=(svr * 2, svr * 2))
            StencilUse()
            Mesh(vertices=sv_verts, indices=sv_idxs, mode='triangles')
            StencilUnUse()
            StencilPop()

        # thin border around SV circle
        with self.canvas:
            Color(.22, .22, .34, .7)
            Line(circle=(cx, cy, svr), width=dp(1))

        # ---- 4. Hue marker ----
        mid_r = (outr + inr) / 2
        mx = cx + mid_r * math.cos(math.radians(self._hue))
        my = cy + mid_r * math.sin(math.radians(self._hue))
        mr = dp(11)
        hue_r, hue_g, hue_b = hsv_to_rgb(self._hue, 1.0, 1.0)
        with self.canvas:
            Color(0, 0, 0, .35)
            Ellipse(pos=(mx - mr - 1, my - mr - 1), size=((mr + 1) * 2, (mr + 1) * 2))
            Color(1, 1, 1, 1)
            Ellipse(pos=(mx - mr, my - mr), size=(mr * 2, mr * 2))
            Color(hue_r, hue_g, hue_b, 1)
            Ellipse(pos=(mx - mr + 2.5, my - mr + 2.5), size=((mr - 2.5) * 2, (mr - 2.5) * 2))
            Color(0, 0, 0, 1)
            Line(circle=(mx, my, mr - 1.5), width=1)

        # ---- 5. SV marker ----
        svx = sv_x0 + self._sat * sv_side
        svy = sv_y0 + self._val * sv_side
        sr = dp(9)
        sel_r, sel_g, sel_b = hsv_to_rgb(self._hue, self._sat, self._val)
        with self.canvas:
            Color(0, 0, 0, .45)
            Ellipse(pos=(svx - sr - 1, svy - sr - 1), size=((sr + 1) * 2, (sr + 1) * 2))
            Color(1, 1, 1, 1)
            Ellipse(pos=(svx - sr, svy - sr), size=(sr * 2, sr * 2))
            Color(sel_r, sel_g, sel_b, 1)
            Ellipse(pos=(svx - sr + 2.5, svy - sr + 2.5), size=((sr - 2.5) * 2, (sr - 2.5) * 2))
            Color(0, 0, 0, 1)
            Line(circle=(svx, svy, sr - 1.5), width=1)

        # ---- 6. Degree labels ----
        for deg, lbl in self._deg_labels:
            la = math.radians(deg)
            lbl.center = (cx + (outr + 16) * math.cos(la),
                          cy + (outr + 16) * math.sin(la))

    # ------------------------------------------------------------------
    # Touch handling
    # ------------------------------------------------------------------
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False

        dx = touch.x - self._cx
        dy = touch.y - self._cy
        dist = math.hypot(dx, dy)

        # Hue ring (checked first – it visually surrounds the SV area)
        if (self._inr - self._RING_PAD) <= dist <= (self._outr + self._RING_PAD):
            self._drag = 'hue'
            touch.grab(self)
            self._update_hue(touch)
            return True

        # SV circle
        if dist <= self._svr + self._SV_PAD:
            self._drag = 'sv'
            touch.grab(self)
            self._update_sv(touch)
            return True

        return False

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return super().on_touch_move(touch)
        if self._drag == 'hue':
            self._update_hue(touch)
        elif self._drag == 'sv':
            self._update_sv(touch)
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            self._drag = None
            touch.ungrab(self)
            return True
        return super().on_touch_up(touch)

    def _update_hue(self, touch):
        dx = touch.x - self._cx
        dy = touch.y - self._cy
        self._hue = int(math.degrees(math.atan2(dy, dx))) % 360
        self._redraw()
        self._on_change(self._hue, int(self._sat * 255), int(self._val * 255))

    def _update_sv(self, touch):
        side = self._sv_side
        if side > 0:
            self._sat = max(0.0, min(1.0, (touch.x - self._sv_x0) / side))
            self._val = max(0.0, min(1.0, (touch.y - self._sv_y0) / side))
        self._redraw()
        self._on_change(self._hue, int(self._sat * 255), int(self._val * 255))


# ======================================================================
# Page layout
# ======================================================================

class WheelPage(BoxLayout):
    def __init__(self, on_change, **kw):
        super().__init__(orientation='horizontal', padding=[dp(10), dp(8)], spacing=dp(10), **kw)
        self._on_change = on_change
        self._updating = False

        # ---- Left: wheel + sliders ----
        left = BoxLayout(orientation='vertical', spacing=dp(6), size_hint_x=3)
        left.add_widget(Label(
            text="Interactive Colour Wheel",
            color=(.88, .88, .94, 1), font_size=FS(16), bold=True,
            size_hint_y=None, height=dp(28), halign='left'))
        left.add_widget(Label(
            text="Drag the ring for Hue. Drag the centre for Saturation & Value.",
            color=(.55, .55, .67, 1), font_size=FS(10),
            size_hint_y=None, height=dp(34), halign='left'))

        self._wheel = ColorWheelWidget(on_change=self._internal_change)
        left.add_widget(self._wheel)

        self._sliders = {}
        for name, lo, hi, default in [("Saturation", 0, 255, 255),
                                       ("Brightness", 0, 255, 255)]:
            row = BoxLayout(orientation='horizontal', size_hint_y=None,
                            height=dp(40), spacing=dp(8))
            row.add_widget(Label(
                text=name + ":", color=(.8, .8, .8, 1), font_size=FS(11),
                bold=True, size_hint_x=None, width=dp(110)))
            sl = Slider(min=lo, max=hi, value=default)
            sl.bind(value=self._on_slider)
            row.add_widget(sl)
            vl = Label(text='', color=(.67, .67, .67, 1), font_size=FS(11),
                       size_hint_x=None, width=dp(50))
            row.add_widget(vl)
            left.add_widget(row)
            self._sliders[name] = (sl, vl)

        self.add_widget(left)

        # ---- Right: info panel ----
        right = BoxLayout(orientation='vertical', spacing=dp(8),
                          size_hint_x=2, padding=[dp(8), dp(4)])
        card = BgCard(orientation='vertical', spacing=dp(6), padding=[dp(14)])
        card.add_widget(Label(
            text="Selected Colour", color=(.82, .82, .9, 1), font_size=FS(12),
            bold=True, size_hint_y=None, height=dp(22)))

        self._preview = ColorPreview(size_hint_y=None, height=dp(90))
        self._preview_lbl = Label(text='', font_size=FS(16), bold=True)
        self._preview.add_widget(self._preview_lbl)
        card.add_widget(self._preview)

        self._copy_btn = CopyHexButton(font_size=FS(12), size_hint_y=None, height=dp(30))
        card.add_widget(self._copy_btn)

        self._info = Label(
            text='', color=(.6, .6, .75, 1), font_size=FS(11),
            size_hint_y=None, height=dp(80), halign='left', valign='top')
        self._info.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))
        card.add_widget(self._info)

        self._quick = Label(
            text='', color=(.55, .55, .67, 1), font_size=FS(10),
            size_hint_y=None, height=dp(80), halign='left', valign='top')
        self._quick.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))
        card.add_widget(self._quick)

        right.add_widget(card)
        self.add_widget(right)
        self._update_ui()

    # ------------------------------------------------------------------
    # Internal sync
    # ------------------------------------------------------------------
    def _internal_change(self, h, s, v):
        """Callback from the 2-D wheel widget."""
        if self._updating:
            return
        self._updating = True
        self._sliders["Saturation"][0].value = s
        self._sliders["Brightness"][0].value = v
        self._updating = False
        self._update_ui()
        self._on_change(h, s, v)

    def _on_slider(self, *_):
        if self._updating:
            return
        s = int(self._sliders["Saturation"][0].value)
        v = int(self._sliders["Brightness"][0].value)
        h = self._wheel._hue
        self._wheel.set_hsv(h, s, v, propagate=False)
        self._update_ui()
        self._on_change(h, s, v)

    def _update_ui(self):
        h = self._wheel._hue
        s = int(self._sliders["Saturation"][0].value)
        v = int(self._sliders["Brightness"][0].value)

        self._sliders["Saturation"][1].text = f"{int(s / 255 * 100)}%"
        self._sliders["Brightness"][1].text = f"{int(v / 255 * 100)}%"

        r, g, b = hsv_to_rgb(h, s / 255, v / 255)
        hex_val = rgb_hex(r, g, b)
        ri, gi, bi = int(r * 255), int(g * 255), int(b * 255)
        hsl = rgb_to_hsl(r, g, b)

        self._preview.set_color(r, g, b)
        self._preview_lbl.color = fg_for(r, g, b)
        self._preview_lbl.text = hex_val

        self._copy_btn.text = f"  Copy {hex_val}"
        self._copy_btn.hex_func = lambda hv=hex_val: hv

        self._info.text = (
            f"HEX: {hex_val}\n"
            f"RGB: {ri}, {gi}, {bi}\n"
            f"HSL: {h}\u00b0, {int(hsl[1]*100)}%, {int(hsl[2]*100)}%\n"
            f"HSV: {h}\u00b0, {int(s/255*100)}%, {int(v/255*100)}%"
        )

        cr, cg, cb = hsv_to_rgb((h + 180) % 360, s / 255, v / 255)
        tr, tg, tb = hsv_to_rgb((h + 120) % 360, s / 255, v / 255)
        qr, qg, qb = hsv_to_rgb((h + 240) % 360, s / 255, v / 255)
        self._quick.text = (
            f"Complement: {rgb_hex(cr, cg, cb)}\n"
            f"Triadic: {rgb_hex(tr, tg, tb)}, {rgb_hex(qr, qg, qb)}"
        )

    def set_color(self, h, s, v):
        self._updating = True
        self._wheel.set_hsv(h, s, v, propagate=False)
        self._sliders["Saturation"][0].value = s
        self._sliders["Brightness"][0].value = v
        self._updating = False
        self._update_ui()