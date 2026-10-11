"""HSL/HSV Explorer and WCAG Accessibility Contrast Checker pages."""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget  # FIX: was missing — caused NameError on ContrastCheckerPage
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.colorpicker import ColorPicker
from kivy.metrics import dp, sp as _sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from color_utils import hsv_to_rgb, rgb_hex, fg_for, rgb_to_hsl, wcag_ratio
from ui_components import ColorPreview, BgCard

FS = _sp


class HSLExplorerPage(BoxLayout):
    def __init__(self, on_change, **kw):
        super().__init__(orientation='vertical', **kw)
        self._on_change = on_change; self._updating = False
        self.padding = [dp(20), dp(14)]; self.spacing = dp(8)

        self.add_widget(Label(text="HSL / HSV Colour Explorer", color=(.87, .87, .94, 1),
                              font_size=FS(15), bold=True, size_hint_y=None, height=dp(28), halign='left'))
        self.add_widget(Label(text="Drag sliders to see how H, S, and V interact.",
                              color=(.53, .53, .53, 1), font_size=FS(10), size_hint_y=None, height=dp(34), halign='left'))

        prev_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(90), spacing=dp(12))
        self._prev = ColorPreview(size_hint=(1, 1))
        self._prev_lbl = Label(text='', font_size=FS(10), bold=True); self._prev.add_widget(self._prev_lbl)
        self._comp = ColorPreview(size_hint=(1, 1))
        self._comp_lbl = Label(text='', font_size=FS(10), bold=True); self._comp.add_widget(self._comp_lbl)
        prev_row.add_widget(self._prev)
        prev_row.add_widget(Label(text="\u2194", color=(.4, .4, .4, 1), font_size=FS(18),
                                  size_hint_x=None, width=dp(30)))
        prev_row.add_widget(self._comp)
        self.add_widget(prev_row)

        self._hex_lbl = Label(text='', color=(.67, .67, .67, 1), font_size=FS(14),
                              bold=True, size_hint_y=None, height=dp(22)); self.add_widget(self._hex_lbl)
        self._rgb_lbl = Label(text='', color=(.47, .47, .47, 1), font_size=FS(10),
                              size_hint_y=None, height=dp(16)); self.add_widget(self._rgb_lbl)
        self._hsl_lbl = Label(text='', color=(.47, .47, .47, 1), font_size=FS(10),
                              size_hint_y=None, height=dp(16)); self.add_widget(self._hsl_lbl)
        self._hsv_lbl = Label(text='', color=(.47, .47, .47, 1), font_size=FS(10),
                              size_hint_y=None, height=dp(16)); self.add_widget(self._hsv_lbl)

        self._sliders = {}
        for name, lo, hi, default in [("Hue (H)", 0, 359, 180), ("Saturation (S)", 0, 255, 255), ("Value (V)", 0, 255, 255)]:
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(8))
            row.add_widget(Label(text=name + ":", color=(.8, .8, .8, 1), font_size=FS(11),
                                 bold=True, size_hint_x=None, width=dp(140)))
            sl = Slider(min=lo, max=hi, value=default); sl.bind(value=self._on_slider); row.add_widget(sl)
            vl = Label(text='', color=(.67, .67, .67, 1), font_size=FS(11), size_hint_x=None, width=dp(50))
            row.add_widget(vl); self.add_widget(row); self._sliders[name] = (sl, vl)

        self.add_widget(Label(text="HSV vs HSL: V=100% = brightest. L=50% = purest hue; L=100% = white.",
                              color=(.6, .6, .6, 1), font_size=FS(9), size_hint_y=None, height=dp(44)))
        copy_btn = Button(text="Copy HEX to Clipboard", size_hint_y=None, height=dp(38),
                          background_color=(.18, .18, .31, 1), color=(.8, .8, .8, 1), font_size=FS(11))
        copy_btn.bind(on_release=self._copy_hex); self.add_widget(copy_btn)
        self._update_display()

    def _copy_hex(self, *_):
        h, s, v = self._get_hsv(); r, g, b = hsv_to_rgb(h, s / 255, v / 255)
        hex_val = rgb_hex(r, g, b)
        try:
            from kivy.core.clipboard import Clipboard; Clipboard.copy(hex_val)
        except Exception: pass

    def _get_hsv(self):
        return (int(self._sliders["Hue (H)"][0].value),
                int(self._sliders["Saturation (S)"][0].value),
                int(self._sliders["Value (V)"][0].value))

    def _on_slider(self, *_):
        if self._updating: return
        self._update_display(); h, s, v = self._get_hsv(); self._on_change(h, s, v)

    def set_color(self, h, s, v):
        self._updating = True
        self._sliders["Hue (H)"][0].value = h
        self._sliders["Saturation (S)"][0].value = s
        self._sliders["Value (V)"][0].value = v
        self._updating = False; self._update_display()

    def _update_display(self):
        h, s, v = self._get_hsv(); r, g, b = hsv_to_rgb(h, s / 255, v / 255)
        cr, cg, cb = hsv_to_rgb((h + 180) % 360, s / 255, v / 255)
        self._prev.set_color(r, g, b); self._prev_lbl.color = fg_for(r, g, b)
        self._prev_lbl.text = rgb_hex(r, g, b)
        self._comp.set_color(cr, cg, cb); self._comp_lbl.color = fg_for(cr, cg, cb)
        self._comp_lbl.text = rgb_hex(cr, cg, cb)
        self._hex_lbl.text = f"{rgb_hex(r, g, b)}  |  Complement: {rgb_hex(cr, cg, cb)}"
        ri, gi, bi = int(r * 255), int(g * 255), int(b * 255)
        self._rgb_lbl.text = f"R: {ri:3d}   G: {gi:3d}   B: {bi:3d}"
        hsl = rgb_to_hsl(r, g, b)
        self._hsl_lbl.text = f"HSL:  H: {h}   S: {int(hsl[1] * 100)}%  L: {int(hsl[2] * 100)}%"
        self._hsv_lbl.text = f"HSV:  H: {h}   S: {int(s / 255 * 100)}%  V: {int(v / 255 * 100)}%"
        self._sliders["Hue (H)"][1].text = f"{h}\u00b0"
        self._sliders["Saturation (S)"][1].text = f"{int(s / 255 * 100)}%"
        self._sliders["Value (V)"][1].text = f"{int(v / 255 * 100)}%"


# FIX: custom label that tracks its background rectangle on pos/size changes
class _ContrastLabel(Label):
    """Label with a canvas.before background colour that follows pos/size."""
    def __init__(self, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            self._bg_color = Color(0, 0, 0, 1)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd_bg, size=self._upd_bg)

    def _upd_bg(self, *_):
        self._bg_rect.pos = self.pos; self._bg_rect.size = self.size

    def set_bg_color(self, r, g, b, a=1):
        self._bg_color.rgba = (r, g, b, a)


class ContrastCheckerPage(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation='vertical', **kw)
        self.padding = [dp(20), dp(14)]; self.spacing = dp(8)
        self.fg = (1, 1, 1); self.bg = (.118, .118, .235); self._sel = (0, .78, .78)

        self.add_widget(Label(text="WCAG Contrast Ratio Checker", color=(.87, .87, .94, 1),
                              font_size=FS(15), bold=True, size_hint_y=None, height=dp(28), halign='left'))
        self.add_widget(Label(text="AA: >= 4.5:1 normal, >= 3:1 large. AAA: >= 7:1 normal, >= 4.5:1 large.",
                              color=(.53, .53, .53, 1), font_size=FS(10), size_hint_y=None, height=dp(36), halign='left'))

        sel_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(8))
        sel_row.add_widget(Label(text="App colour:", color=(.7, .7, .7, 1), font_size=FS(11),
                                 size_hint_x=None, width=dp(90)))
        self._sel_prev = ColorPreview(size_hint_x=None, width=dp(32), size_hint_y=None, height=dp(32))
        sel_row.add_widget(self._sel_prev)
        self._sel_hex = Label(text='', color=(.67, .67, .67, 1), font_size=FS(10),
                              size_hint_x=None, width=dp(70)); sel_row.add_widget(self._sel_hex)
        sel_row.add_widget(Widget())
        for txt, attr in [("Use as Text \u2192", 'fg'), ("Use as BG \u2192", 'bg')]:
            b = Button(text=txt, size_hint_x=None, width=dp(110),
                       background_color=(.18, .18, .31, 1), color=(.8, .8, .8, 1), font_size=FS(10))
            b.bind(on_release=lambda *a, at=attr: self._use_sel(at)); sel_row.add_widget(b)
        self.add_widget(sel_row)

        grp_row = BoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(200))
        for attr in ('fg', 'bg'):
            grp = BoxLayout(orientation='vertical', spacing=dp(6))
            grp.add_widget(Label(text="Foreground" if attr == 'fg' else "Background", color=(.73, .73, .73, 1),
                                 font_size=FS(11), bold=True, size_hint_y=None, height=dp(20)))
            prev = ColorPreview(size_hint_y=None, height=dp(70))
            setattr(self, f'_{attr}_prev', prev); grp.add_widget(prev)
            hx = Label(text='', color=(.67, .67, .67, 1), font_size=FS(10),
                       size_hint_y=None, height=dp(16)); setattr(self, f'_{attr}_hx', hx); grp.add_widget(hx)
            pb = Button(text="Pick Color...", background_color=(.18, .18, .31, 1),
                        color=(.8, .8, .8, 1), font_size=FS(10), size_hint_y=None, height=dp(34))
            pb.bind(on_release=lambda *a, at=attr: self._pick(at)); grp.add_widget(pb)
            preset_row = BoxLayout(spacing=dp(4), size_hint_y=None, height=dp(28))
            presets = [(1, 1, 1), (0, 0, 0), (.78, .78, .78), (.2, .2, .2)] if attr == 'fg' \
                else [(0, 0, 0), (1, 1, 1), (.118, .118, .235), (.94, .94, .94)]
            for pc in presets:
                pb2 = Button(background_normal='', background_down='',
                             background_color=pc[:3] + (1,), size_hint_x=None, width=dp(28))
                pb2.bind(on_release=lambda *a, c=pc, at=attr: self._set(at, c)); preset_row.add_widget(pb2)
            grp.add_widget(preset_row); grp_row.add_widget(grp)
        self.add_widget(grp_row)

        swap = Button(text="Swap Foreground / Background", background_color=(.18, .18, .31, 1),
                      color=(.8, .8, .8, 1), font_size=FS(10), size_hint_y=None, height=dp(36))
        swap.bind(on_release=self._swap); self.add_widget(swap)

        self._result = BgCard(orientation='vertical', spacing=dp(6), size_hint_y=None,
                              height=dp(200), padding=[dp(14)])
        self.add_widget(self._result)
        self._ratio_lbl = Label(text='', font_size=FS(28), bold=True,
                                size_hint_y=None, height=dp(40)); self._result.add_widget(self._ratio_lbl)
        # FIX: use _ContrastLabel so background Rectangle follows pos/size
        self._prev_normal = _ContrastLabel(
            text="The quick brown fox jumps over the lazy dog. 0123456789",
            font_size=FS(13), halign='center', size_hint_y=None, height=dp(36))
        self._result.add_widget(self._prev_normal)
        self._prev_large = _ContrastLabel(
            text="Large Text Sample", font_size=FS(22), bold=True,
            halign='center', size_hint_y=None, height=dp(36))
        self._result.add_widget(self._prev_large)

        badge_row = BoxLayout(spacing=dp(6), size_hint_y=None, height=dp(28)); self._badges = {}
        for key in ("AA Normal", "AA Large", "AAA Normal", "AAA Large"):
            bl = Label(text=f"{key}: -", font_size=FS(10), bold=True, size_hint_x=1, color=(.7, .7, .7, 1))
            badge_row.add_widget(bl); self._badges[key] = bl
        self.add_widget(badge_row)
        Clock.schedule_once(lambda *_: self._refresh())

    # FIX: add set_color so _propagate can update this page uniformly
    def set_color(self, h, s, v):
        r, g, b = hsv_to_rgb(h, s / 255, v / 255)
        self._sel = (r, g, b); self._refresh_sel()

    def set_selected_color(self, r, g, b):
        self._sel = (r, g, b); self._refresh_sel()

    def _refresh_sel(self):
        r, g, b = self._sel
        self._sel_prev.set_color(r, g, b); self._sel_hex.text = rgb_hex(r, g, b)

    def _use_sel(self, which):
        if which == 'fg': self.fg = self._sel
        else: self.bg = self._sel
        self._refresh()

    def _pick(self, which):
        cp = ColorPicker(color=getattr(self, which) + (1,))
        content = BoxLayout(orientation='vertical'); content.add_widget(cp)
        btn = Button(text="Select", size_hint_y=None, height=dp(44),
                     background_color=(.18, .18, .31, 1), color=(.8, .8, .8, 1)); content.add_widget(btn)
        popup = Popup(title="Pick Colour", content=content, size_hint=(.85, .85))
        btn.bind(on_release=lambda *a: self._pick_done(which, cp.color, popup)); popup.open()

    def _pick_done(self, which, col, popup):
        setattr(self, which, (col[0], col[1], col[2])); self._refresh(); popup.dismiss()

    def _set(self, which, c): setattr(self, which, c[:3]); self._refresh()
    def _swap(self, *_): self.fg, self.bg = self.bg, self.fg; self._refresh()

    def _refresh(self):
        for attr, prev_w, hx_w in [('fg', self._fg_prev, self._fg_hx), ('bg', self._bg_prev, self._bg_hx)]:
            r, g, b = getattr(self, attr); prev_w.set_color(r, g, b); hx_w.text = rgb_hex(r, g, b)
        ratio = wcag_ratio(*self.fg, *self.bg); self._ratio_lbl.text = f"{ratio:.2f} : 1"
        colour = (.3, .69, .31, 1) if ratio >= 7 else (.55, .76, .29, 1) if ratio >= 4.5 \
            else (1, .6, 0, 1) if ratio >= 3 else (.96, .26, .21, 1)
        self._ratio_lbl.color = colour
        fr, fg_, fb = self.fg; br, bg_, bb = self.bg
        # FIX: use _ContrastLabel.set_bg_color instead of clearing/re-creating canvas instructions
        for lbl in (self._prev_normal, self._prev_large):
            lbl.color = self.fg + (1,)
            lbl.set_bg_color(br, bg_, bb)
        checks = {"AA Normal": ratio >= 4.5, "AA Large": ratio >= 3,
                  "AAA Normal": ratio >= 7, "AAA Large": ratio >= 4.5}
        for k, v in checks.items():
            sym = "PASS" if v else "FAIL"; c = (.3, .69, .31, 1) if v else (.96, .26, .21, 1)
            bl = self._badges[k]; bl.text = f"{k}: {sym}"; bl.color = c
        self._refresh_sel()