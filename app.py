#!/usr/bin/env python3
"""Color Theory Visualizer - Entry Point"""
from kivy.utils import platform as kivy_platform
from kivy.core.window import Window

# Set desktop window size before app loads
if kivy_platform not in ('android', 'ios'):
    try:
        Window.size = (1100, 720)
        Window.minimum_width = 400
        Window.minimum_height = 500
    except Exception:
        pass

from app_core import ColorTheoryApp

if __name__ == '__main__':
    ColorTheoryApp().run()