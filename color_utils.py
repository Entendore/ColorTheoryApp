"""Color mathematics, conversions, and accessibility logic."""
import math


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
    if mx == mn: h = s = 0.0
    else:
        d = mx - mn
        s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
        if mx == r:   h = ((g - b) / d + (6 if g < b else 0)) * 60
        elif mx == g: h = ((b - r) / d + 2) * 60
        else:         h = ((r - g) / d + 4) * 60
    return (h, s, l)


# IMPROVE: added hsl_to_rgb — useful complement for round-trip conversions
def hsl_to_rgb(h, s, l):
    h %= 360
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2
    if h < 60:    r, g, b = c, x, 0
    elif h < 120: r, g, b = x, c, 0
    elif h < 180: r, g, b = 0, c, x
    elif h < 240: r, g, b = 0, x, c
    elif h < 300: r, g, b = x, 0, c
    else:         r, g, b = c, 0, x
    return (r + m, g + m, b + m)


def rgb_hex(r, g, b):
    return '#{:02X}{:02X}{:02X}'.format(
        max(0, min(255, int(r * 255))),
        max(0, min(255, int(g * 255))),
        max(0, min(255, int(b * 255))))


def _lum(r, g, b):
    # FIX: WCAG 2.1 erratum changes threshold from 0.03928 to 0.04045
    def lin(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def wcag_ratio(r1, g1, b1, r2, g2, b2):
    l1, l2 = _lum(r1, g1, b1), _lum(r2, g2, b2)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def _cl(v): return max(0.0, min(1.0, v))


def sim_protan(r, g, b):
    return (_cl(.56667 * r + .43333 * g), _cl(.55833 * r + .44167 * g), _cl(.24167 * g + .75833 * b))

def sim_deutan(r, g, b):
    return (_cl(.625 * r + .375 * g), _cl(.7 * r + .3 * g), _cl(.3 * g + .7 * b))

def sim_tritan(r, g, b):
    return (_cl(.95 * r + .05 * g), _cl(.43333 * g + .56667 * b), _cl(.475 * g + .525 * b))

def sim_achroma(r, g, b):
    v = .299 * r + .587 * g + .114 * b
    return (v, v, v)


CVD_SIMS = [
    ("Normal Vision",  lambda r, g, b: (r, g, b), "Trichromatic \u2013 3 cone types"),
    ("Protanopia",     sim_protan,   "Red-blind \u2013 ~1.3% of males"),
    ("Deuteranopia",   sim_deutan,   "Green-blind \u2013 ~1.2% of males"),
    ("Tritanopia",     sim_tritan,   "Blue-blind \u2013 ~0.001%"),
    ("Achromatopsia",  sim_achroma,  "Total colour blindness \u2013 ~0.003%"),
]

def fg_for(r, g, b):
    return (1, 1, 1, 1) if (r * .299 + g * .587 + b * .114) < 0.55 else (0, 0, 0, 1)