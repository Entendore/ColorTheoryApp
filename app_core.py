"""Main Application Core, Screen Manager, and Responsive Navigation."""
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.utils import platform as kivy_platform
from kivy.animation import Animation  # IMPROVE: drawer animation

from color_utils import hsv_to_rgb, rgb_hex
from ui_components import ColorPreview, DarkSeparator, Toast, FS

from wheel_page import WheelPage
from harmony_page import HarmonyPage
from properties_page import PropertiesPage
from mixing_page import MixingPage
from explorer_access_page import HSLExplorerPage, ContrastCheckerPage
from blindness_theory_page import BlindnessPage, TheoryPage

PAGES = [
    ("\U0001f3a8 Colour Wheel",  "wheel"),
    ("\u262f Harmonies",         "harmonies"),
    ("\U0001f4ca Properties",   "properties"),
    ("\U0001f5e1 Mixing",       "mixing"),
    ("\U0001f527 HSL Explorer", "hsl"),
    ("\u2626 Accessibility",    "access"),
    ("\U0001f441 Blindness",    "blind"),
    ("\U0001f4d6 Theory Guide", "theory"),
]

PAGE_TITLES = {
    "wheel": "Interactive Colour Wheel", "harmonies": "Colour Harmonies",
    "properties": "Colour Properties", "mixing": "Colour Mixing Models",
    "hsl": "HSL / HSV Explorer", "access": "WCAG Contrast Checker",
    "blind": "Colour Blindness Simulation", "theory": "Theory Guide",
}


class DrawerSidebar(BoxLayout):
    def __init__(self, on_nav, **kw):
        super().__init__(orientation='vertical', **kw)
        self.size_hint_x = None; self.width = dp(220); self.spacing = dp(2); self.padding = [dp(10), dp(16)]
        self._on_nav = on_nav
        with self.canvas.before:
            self._bg_c = Color(.07, .07, .16, 1)
            self._bg_r = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda i, v: setattr(i._bg_r, 'pos', v), size=lambda i, v: setattr(i._bg_r, 'size', v))

        # FIX: bind width so halign='left' actually works
        title = Label(text="Color Theory", color=(.69, .69, .88, 1), font_size=FS(15),
                      bold=True, size_hint_y=None, height=dp(30), halign='left')
        title.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))
        self.add_widget(title)

        subtitle = Label(text="Interactive Visualizer", color=(.38, .38, .63, 1),
                         font_size=FS(10), size_hint_y=None, height=dp(20), halign='left')
        subtitle.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))
        self.add_widget(subtitle)

        self.add_widget(DarkSeparator())

        self.nav_btns = []
        for text, pid in PAGES:
            b = ToggleButton(text=text, group='nav')
            b.bind(on_release=lambda btn, p=pid: self._nav(p))
            self.add_widget(b); self.nav_btns.append((b, pid))
        self.add_widget(Widget()); self.add_widget(DarkSeparator())

        sel_lbl = Label(text="Selected Colour", color=(.44, .44, .63, 1),
                        font_size=FS(9), size_hint_y=None, height=dp(20), halign='left')
        sel_lbl.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))
        self.add_widget(sel_lbl)
        self.sb_prev = ColorPreview(size_hint_y=None, height=dp(44))
        self.sb_prev.bind(on_touch_down=self._on_sb_prev_tap)
        self.sb_hex = Label(text='', color=(.47, .47, .47, 1), font_size=FS(11),
                            size_hint_y=None, height=dp(22), halign='center')
        self.add_widget(self.sb_prev); self.add_widget(self.sb_hex)
        ver = Label(text="v2.0 – Modular", color=(.3, .3, .45, 1),
                    font_size=FS(8), size_hint_y=None, height=dp(16), halign='center')
        ver.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))
        self.add_widget(ver)

    def _nav(self, pid): self._on_nav(pid)
    def set_active(self, pid):
        for btn, bid in self.nav_btns: btn.state = 'down' if bid == pid else 'normal'

    def _on_sb_prev_tap(self, instance, touch):
        if instance.collide_point(*touch.pos):
            app = App.get_running_app()
            if app:
                r, g, b = hsv_to_rgb(app._hue, app._sat / 255, app._val / 255)
                hex_val = rgb_hex(r, g, b)
                try:
                    from kivy.core.clipboard import Clipboard; Clipboard.copy(hex_val)
                except Exception: pass
                app._toast.show(app.root, f"Copied {hex_val}")


class ColorTheoryApp(App):
    title = "Color Theory Visualizer"

    def build(self):
        self._hue = 180; self._sat = 255; self._val = 255
        self._toast = Toast()
        self._is_mobile = kivy_platform in ('android', 'ios')
        self._drawer_open = False; self._mobile_mode = False

        self._root = FloatLayout()
        self._content = BoxLayout(orientation='horizontal')
        self._sidebar = DrawerSidebar(on_nav=self._go)
        self.sm = ScreenManager(transition=SlideTransition(duration=.25))
        for _, pid in PAGES: self.sm.add_widget(Screen(name=pid))
        self._content.add_widget(self.sm); self._root.add_widget(self._content)

        # Top bar
        self._topbar = BoxLayout(orientation='horizontal', size_hint=(1, None),
                                 height=dp(52), pos_hint={'top': 1}, padding=[dp(8), dp(4)])
        with self._topbar.canvas.before:
            self._tb_bg_c = Color(.07, .07, .16, .95)
            self._tb_bg_r = Rectangle(pos=self._topbar.pos, size=self._topbar.size)
        # FIX: was i._tb_bg_r but i is topbar widget, not app — _tb_bg_r lives on self (app)
        self._topbar.bind(
            pos=lambda i, v: setattr(self._tb_bg_r, 'pos', v),
            size=lambda i, v: setattr(self._tb_bg_r, 'size', v))
        self._menu_btn = Button(text='\u2630', font_size=FS(22), size_hint_x=None, width=dp(48),
                                background_normal='', background_down='',
                                background_color=(.12, .12, .22, 1), color=(.85, .85, .85, 1))
        self._menu_btn.bind(on_release=self._toggle_drawer); self._topbar.add_widget(self._menu_btn)
        self._page_title = Label(text='Color Theory Visualizer', color=(.88, .88, .94, 1),
                                 font_size=FS(15), bold=True, halign='left', valign='middle')
        self._page_title.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))
        self._topbar.add_widget(self._page_title)
        self._copy_btn = Button(text='Copy', font_size=FS(10), size_hint_x=None, width=dp(60),
                                background_normal='', background_down='',
                                background_color=(.18, .18, .31, 1), color=(.8, .8, .8, 1))
        self._copy_btn.bind(on_release=self._copy_current_hex); self._topbar.add_widget(self._copy_btn)

        # Drawer scrim
        self._drawer_bg = BoxLayout(size_hint=(1, 1))
        with self._drawer_bg.canvas.before:
            _sc = Color(0, 0, 0, .5)
            self._scrim_rect = Rectangle(pos=self._drawer_bg.pos, size=self._drawer_bg.size)
        # FIX: store rect reference instead of fragile children[-1] index access
        self._drawer_bg.bind(
            pos=lambda i, v: setattr(self._scrim_rect, 'pos', v),
            size=lambda i, v: setattr(self._scrim_rect, 'size', v))

        self._build_pages(); self._apply_layout(); self._go("wheel")
        Window.bind(on_resize=self._on_resize)
        return self._root

    def _build_pages(self):
        s = self.sm.get_screen("wheel");     s.add_widget(WheelPage(on_change=self._on_color_change))
        s = self.sm.get_screen("harmonies");  s.add_widget(HarmonyPage())
        s = self.sm.get_screen("properties"); s.add_widget(PropertiesPage())
        s = self.sm.get_screen("mixing");     s.add_widget(MixingPage())
        s = self.sm.get_screen("hsl");        s.add_widget(HSLExplorerPage(on_change=self._on_color_change))
        s = self.sm.get_screen("access");     s.add_widget(ContrastCheckerPage())
        s = self.sm.get_screen("blind");      s.add_widget(BlindnessPage())
        s = self.sm.get_screen("theory");     s.add_widget(TheoryPage())

    def _apply_layout(self):
        w = Window.width; mobile_mode = w < dp(700) or self._is_mobile; self._mobile_mode = mobile_mode
        self._root.clear_widgets(); self._content.clear_widgets()
        if mobile_mode:
            self._content.add_widget(self.sm); self._root.add_widget(self._content)
            self._root.add_widget(self._topbar)
            self._content.padding = [0, dp(52), 0, 0]
            self._sidebar.width = min(dp(280), Window.width - dp(60))
            # FIX: ensure drawer closed on layout change
            if self._drawer_open: self._close_drawer()
        else:
            self._content.padding = [0, 0, 0, 0]
            self._content.add_widget(self._sidebar); self._content.add_widget(self.sm)
            self._root.add_widget(self._content)

    def _on_resize(self, instance, width, height): self._apply_layout()

    def _toggle_drawer(self, *_):
        if not self._mobile_mode: return
        self._close_drawer() if self._drawer_open else self._open_drawer()

    def _open_drawer(self):
        self._drawer_open = True
        self._root.add_widget(self._drawer_bg)
        # FIX: cleaner scrim dismiss
        self._drawer_bg.on_touch_down = lambda touch: (self._close_drawer(), True)[1]
        # IMPROVE: slide-in animation
        self._sidebar.x = -self._sidebar.width
        self._sidebar.top = self._root.height - dp(52)
        self._sidebar.height = self._root.height - dp(52)
        self._root.add_widget(self._sidebar)
        Animation(x=0, duration=0.2, t='out_cubic').start(self._sidebar)

    def _close_drawer(self, *_):
        if not self._drawer_open: return  # FIX: guard against double-close
        self._drawer_open = False
        # IMPROVE: slide-out animation, remove widgets after animation completes
        anim = Animation(x=-self._sidebar.width, duration=0.15, t='in_cubic')
        anim.bind(on_complete=lambda *_: self._remove_drawer_widgets())
        anim.start(self._sidebar)

    def _remove_drawer_widgets(self):
        if self._drawer_bg in self._root.children: self._root.remove_widget(self._drawer_bg)
        if self._sidebar in self._root.children: self._root.remove_widget(self._sidebar)

    def _copy_current_hex(self, *_):
        r, g, b = hsv_to_rgb(self._hue, self._sat / 255, self._val / 255); hex_val = rgb_hex(r, g, b)
        try:
            from kivy.core.clipboard import Clipboard; Clipboard.copy(hex_val)
        except Exception: pass
        self._toast.show(self._root, f"Copied {hex_val}")

    def _go(self, pid):
        self.sm.current = pid; self._sidebar.set_active(pid)
        self._page_title.text = PAGE_TITLES.get(pid, "Color Theory")
        if self._drawer_open: self._close_drawer()
        self._propagate()

    def _on_color_change(self, h, s, v):
        self._hue = h; self._sat = s; self._val = v; self._propagate()

    def _propagate(self):
        h, s, v = self._hue, self._sat, self._val
        r, g, b = hsv_to_rgb(h, s / 255, v / 255)
        self._sidebar.sb_prev.set_color(r, g, b); self._sidebar.sb_hex.text = rgb_hex(r, g, b)
        screen = self.sm.current_screen
        child = screen.children[0] if screen.children else None
        if child and hasattr(child, 'set_color'): child.set_color(h, s, v)