"""Builds every SVG on the profile page, in a dark and a light variant.

    python scripts/build.py              # all assets (activity needs GITHUB_TOKEN)
    python scripts/build.py --activity   # only the contribution heatmap (what CI runs)

The look follows Visit Abu Dhabi, the product I build the AI concierge for: the
Seaport-to-Palm gradient, Sunset orange, Sea teal, and a stacked lowercase lockup.
Display type is Rakkas, text is Hanken Grotesk, code is Geist Mono (all SIL OFL).
SVGs shown through <img> can't load web fonts, so each file embeds a subset holding
only the glyphs it uses.
"""
import base64
import io
import json
import math
import os
import sys
import urllib.request
from datetime import date
from html import escape
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = Path(__file__).resolve().parent / "fonts"
OUT = ROOT / "assets"
USER = "bilaltaha25132"

# Visit Abu Dhabi palette: Seaport #003451, Palm #00605F, Sea #00D8CC, Sunset #FF8707, Sandstone #FCEFDE
THEMES = {
    "dark": dict(panel="#07161F", sub="#0B2230", line="#183747", line2="#102B3A", text="#FFFFFF",
                 display="#FCEFDE", muted="#A9BCC4", faint="#6F8893", accent="#FF8707", on_accent="#1A0D00",
                 sea="#00D8CC", ok="#00D8CC", ghost="#07161F", ghost_line="#2A4B5C",
                 heat=["#0D2531", "#00474A", "#00605F", "#009086", "#00D8CC"]),
    "light": dict(panel="#FFFFFF", sub="#FAF9F5", line="#E3DED4", line2="#EEEAE2", text="#111111",
                  display="#111111", muted="#565A5C", faint="#898C8D", accent="#FF8707", on_accent="#1A0D00",
                  sea="#00605F", ok="#009086", ghost="#FFFFFF", ghost_line="#D3CCBF",
                  heat=["#EFEBE4", "#CBE7E3", "#7FC8C1", "#009086", "#00605F"]),
}
FACES = {"sans": ("Hanken Grotesk", "hanken-grotesk-variable.woff2", "100 900"),
         "mono": ("Geist Mono", "geist-mono-variable.woff2", "100 900"),
         "disp": ("Rakkas", "rakkas.woff2", "400")}
ON_GRAD = dict(text="#FFFFFF", muted="#B8CDD4", faint="#7FA0AB", line="rgba(255,255,255,.22)")


# ---------------------------------------------------------------- primitives

def _subset(path, chars):
    font = TTFont(path)
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.drop_tables += ["meta"]
    opts.layout_features = ["kern", "liga", "calt", "tnum"]
    sub = subset.Subsetter(opts)
    sub.populate(text="".join(sorted(chars)))
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


_METRICS = {}


def width(s, size, font="sans"):
    """Advance width of `s` in px, read from the font's default instance."""
    file = FACES[font][1]
    if file not in _METRICS:
        f = TTFont(FONTS / file)
        _METRICS[file] = (f.getBestCmap(), f["hmtx"].metrics, f["head"].unitsPerEm)
    cmap, hmtx, upm = _METRICS[file]
    return sum(hmtx[cmap[ord(ch)]][0] for ch in s if ord(ch) in cmap) * size / upm


def svg(w, h, title, desc, body, css=""):
    chars = set(title + desc + body) | set(" 0123456789")
    used = ["sans"] + [k for k in ("mono", "disp") if f'class="{k[0]}"' in body]
    faces = "".join(f"@font-face{{font-family:'{FACES[k][0]}';font-weight:{FACES[k][2]};"
                    f"src:url(data:font/woff2;base64,{_subset(FONTS / FACES[k][1], chars)}) format('woff2')}}"
                    for k in used)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-labelledby="t d"><title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc>'
            f"<style>{faces}text{{font-family:'Hanken Grotesk',system-ui,sans-serif;font-feature-settings:'tnum'}}"
            f".m{{font-family:'Geist Mono',ui-monospace,monospace}}.d{{font-family:'Rakkas',Georgia,serif}}"
            f"{css}</style>{body}</svg>\n")


def t(x, y, s, size, fill, weight=400, anchor="start", font="sans", track=0.0, extra=""):
    cls = {"sans": "", "mono": ' class="m"', "disp": ' class="d"'}[font]
    ls = f' letter-spacing="{track}em"' if track else ""
    return (f'<text{cls} x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}"{ls} {extra}>{escape(s)}</text>')


def gradient(gid, x, y, w, h):
    """The Ask Abu Dhabi button gradient: linear-gradient(150deg, #000 -21.26%, #003451 33.47%, #00605F 115.56%)."""
    a = math.radians(150)
    dx, dy = math.sin(a), -math.cos(a)
    half = (abs(w * dx) + abs(h * dy)) / 2
    cx, cy = x + w / 2, y + h / 2
    lo, hi = -0.2126, 1.1556

    def at(p):
        return cx + dx * half * (2 * p - 1), cy + dy * half * (2 * p - 1)

    (x1, y1), (x2, y2) = at(lo), at(hi)
    off = lambda p: (p - lo) / (hi - lo)
    return (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}">'
            f'<stop offset="0" stop-color="#000"/><stop offset="{off(0.3347):.4f}" stop-color="#003451"/>'
            f'<stop offset="1" stop-color="#00605F"/></linearGradient>')


def panel(w, h, c, rx=20):
    return f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="{c["panel"]}" stroke="{c["line"]}"/>'


def check(cx, cy, c, r=9):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{c["ok"]}" stroke-width="1.6"/>'
            f'<path d="M{cx - 4} {cy} l2.8 2.8 l5 -5.4" fill="none" stroke="{c["ok"]}" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def arrow(x, y, s, color, sw=1.8):
    """A north-east arrow whose box starts at (x, y) with side s."""
    return (f'<path d="M{x} {y + s} L{x + s} {y} M{x + s * 0.3} {y} H{x + s} V{y + s * 0.7}" fill="none" '
            f'stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>')


def lockup(x, base, small, big, s_size, b_size, color):
    """Two-line stacked lowercase lockup, proportioned like the Experience Abu Dhabi logo."""
    return (t(x + 0.09 * b_size, base, small, s_size, color, font="disp")
            + t(x, base + 0.84 * b_size, big, b_size, color, font="disp"))


# ---------------------------------------------------------------- hero

def hero(c):
    W, H = 1280, 470
    b = [f"<defs>{gradient('g', 0, 0, W, H)}<clipPath id='k'><rect width='{W}' height='{H}' rx='24'/></clipPath></defs>",
         f'<g clip-path="url(#k)"><rect width="{W}" height="{H}" fill="url(#g)"/>',
         # setting sun, low on the horizon at the right edge
         f'<circle cx="{W - 110}" cy="{H + 70}" r="160" fill="none" stroke="{c["accent"]}" stroke-opacity=".28"/>'
         f'<circle cx="{W - 110}" cy="{H + 70}" r="215" fill="none" stroke="{c["accent"]}" stroke-opacity=".14"/>'
         f'<circle cx="{W - 110}" cy="{H + 70}" r="104" fill="{c["accent"]}" fill-opacity=".16"/></g>',
         f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="24" fill="none" stroke="{c["line"]}"/>']
    b.append(lockup(64, 112, "muhammad", "bilal taha", 58, 140, "#FFFFFF"))
    b.append(t(68, 298, "Full Stack AI Engineer · Karachi", 25, "#FCEFDE", 600, track=-0.01))
    b.append(t(68, 340, "I build LLM products end to end: RAG pipelines and LangGraph", 21, ON_GRAD["muted"], 400))
    b.append(t(68, 370, "agents, the APIs around them, and the interfaces people use.", 21, ON_GRAD["muted"], 400))
    label = "Building Ask Abu Dhabi on visitabudhabi.ae"
    pw = width(label, 17, "sans") * 1.04 + 64
    b.append(f'<rect x="68" y="398" width="{pw:.0f}" height="44" rx="22" fill="{c["accent"]}"/>'
             f'<circle cx="92" cy="420" r="5" fill="{c["on_accent"]}"/>'
             + t(108, 426, label, 17, c["on_accent"], 600))

    # agent graph
    nodes = {"q": ("query", 800, 196, 96), "g": ("guardrails", 918, 196, 120),
             "a": ("agent", 1046, 196, 96), "r": ("retrieval", 1168, 106, 116),
             "m": ("maps", 1168, 196, 116), "i": ("itinerary", 1168, 286, 116),
             "s": ("SSE → UI", 1046, 312, 116)}
    hh = 40

    def R(k): n = nodes[k]; return n[1] + n[3] / 2, n[2]
    def L(k): n = nodes[k]; return n[1] - n[3] / 2, n[2]
    paths = {"qg": f"M{R('q')[0]},196 H{L('g')[0]}", "ga": f"M{R('g')[0]},196 H{L('a')[0]}",
             "ar": f"M{R('a')[0]},190 C1104,190 1086,106 {L('r')[0]},106", "am": f"M{R('a')[0]},196 H{L('m')[0]}",
             "ai": f"M{R('a')[0]},202 C1104,202 1086,286 {L('i')[0]},286", "as": f"M1046,{196 + hh / 2} V{312 - hh / 2}"}
    for k, d in paths.items():
        b.append(f'<path id="p{k}" d="{d}" fill="none" stroke="#FFFFFF" stroke-opacity=".28" stroke-width="1.5"/>')
    for k, (label, cx, cy, w) in nodes.items():
        hot = k == "a"
        b.append(f'<rect x="{cx - w / 2}" y="{cy - hh / 2}" width="{w}" height="{hh}" rx="20" '
                 f'fill="{c["accent"] if hot else "#FFFFFF"}" fill-opacity="{1 if hot else 0.07}" '
                 f'stroke="{c["accent"] if hot else "#FFFFFF"}" stroke-opacity="{1 if hot else 0.3}"/>')
        b.append(t(cx, cy + 5.5, label, 15, c["on_accent"] if hot else "#E3EEF1", 600 if hot else 400, "middle", font="mono"))
    for k, begin in (("qg", 0), ("ga", 0.5), ("ar", 1.0), ("am", 1.1), ("ai", 1.2), ("as", 1.9)):
        b.append(f'<circle r="3.4" fill="#00D8CC" opacity="0"><animateMotion dur="3.4s" begin="{begin}s" '
                 f'repeatCount="indefinite" keyPoints="0;1;1" keyTimes="0;0.2;1" calcMode="linear"><mpath href="#p{k}"/>'
                 f'</animateMotion><animate attributeName="opacity" dur="3.4s" begin="{begin}s" repeatCount="indefinite" '
                 f'values="0;1;1;0;0" keyTimes="0;0.02;0.18;0.21;1"/></circle>')
    return svg(W, H, "Muhammad Bilal Taha, Full Stack AI Engineer",
               "Muhammad Bilal Taha. Full Stack AI Engineer in Karachi. I build LLM products end to end: RAG pipelines "
               "and LangGraph agents, the APIs around them, and the interfaces people use. Now building the AI "
               "concierge for Abu Dhabi tourism.", "".join(b))


# ---------------------------------------------------------------- section headings

HEADINGS = {
    "now": ("shipping on", "visitabudhabi.ae", "Shipping on visitabudhabi.ae: the AI concierge for Abu Dhabi tourism"),
    "work": ("selected", "work", "Selected work"),
    "about": ("about me,", "as code", "About me, as code"),
    "writing": ("from the", "blog", "Writing"),
    "activity": ("every day,", "shipping", "Activity"),
}


def heading(c, key):
    small, big, alt = HEADINGS[key]
    S, B = 30, 64
    w = int(max(width(small, S, "disp") + 0.09 * B, width(big, B, "disp")) + 12)
    H = 112
    body = (lockup(2, 32, small, big, S, B, c["display"])
            .replace(f'fill="{c["display"]}"', f'fill="{c["sea"]}"', 1))
    return svg(w, H, alt, alt, body)


# ---------------------------------------------------------------- link buttons

def button(c, label, primary=False):
    H = 52
    w = int(26 + width(label, 18) * 1.03 + 14 + 13 + 24)
    if primary:
        fill, fg, stroke = c["accent"], c["on_accent"], c["accent"]
    else:
        fill, fg, stroke = c["ghost"], c["text"], c["ghost_line"]
    body = (f'<rect x="0.75" y="0.75" width="{w - 1.5}" height="{H - 1.5}" rx="{(H - 1.5) / 2}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="1.5"/>' + t(26, 32.5, label, 18, fg, 600)
            + arrow(w - 24 - 11, 20, 11, fg if primary else c["accent"]))
    return svg(w, H, label, f"Link: {label}", body)


# ---------------------------------------------------------------- metrics

def metrics(c):
    W, H = 1280, 184
    tiles = [("186", "commits to visitabudhabi.ae"), ("19", "agent tools in production"),
             ("2", "live AI products, Abu Dhabi"), ("300+", "daily users on one platform")]
    b = [panel(W, H, c)]
    cw = W / 4
    for i, (num, label) in enumerate(tiles):
        x = i * cw
        if i:
            b.append(f'<line x1="{x}" y1="32" x2="{x}" y2="{H - 32}" stroke="{c["line"]}"/>')
        b.append(f'<rect x="{x + 40}" y="34" width="28" height="4" rx="2" fill="{c["accent"]}"/>')
        b.append(t(x + 38, 110, num, 64, c["display"], font="disp"))
        b.append(t(x + 40, 148, label, 18.5, c["muted"], 400))
    return svg(W, H, "Impact in numbers",
               "186 commits to the visitabudhabi.ae front end. 19 agent tools in production. 2 live AI products "
               "for DCT Abu Dhabi. 300+ daily users on one platform.", "".join(b))


# ---------------------------------------------------------------- agent trace

LOOP = 17.0


def appear(cls, at):
    p = at / LOOP * 100
    return (f".{cls}{{opacity:0;animation:{cls} {LOOP}s linear infinite}}"
            f"@keyframes {cls}{{0%,{p:.2f}%{{opacity:0;transform:translateY(5px)}}"
            f"{p + 2:.2f}%,93%{{opacity:1;transform:translateY(0)}}97%,100%{{opacity:0}}}}")


def trace(c):
    W, H, TOP = 1280, 720, 88
    css = ["g{transform-box:fill-box}", ".pulse{animation:pulse 1.6s ease-in-out infinite}"
           "@keyframes pulse{50%{opacity:.35}}"]
    b = [f"<defs>{gradient('g', 0, 0, W, TOP)}<clipPath id='k'><rect width='{W}' height='{H}' rx='20'/></clipPath></defs>",
         f'<g clip-path="url(#k)"><rect width="{W}" height="{H}" fill="{c["panel"]}"/>'
         f'<rect width="{W}" height="{TOP}" fill="url(#g)"/></g>',
         f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="20" fill="none" stroke="{c["line"]}"/>']
    b.append(t(34, 56, "ask abu dhabi", 36, "#FFFFFF", font="disp"))
    b.append(t(34 + width("ask abu dhabi", 36, "disp") + 16, 55, "Agent trace", 20, ON_GRAD["muted"], 500))
    pill = "Production"
    pw = width(pill, 16) * 1.04 + 46
    b.append(f'<rect x="{W - 34 - pw:.0f}" y="26" width="{pw:.0f}" height="36" rx="18" fill="#FFFFFF" fill-opacity=".1" '
             f'stroke="#FFFFFF" stroke-opacity=".25"/><circle class="pulse" cx="{W - 34 - pw + 20:.0f}" cy="44" r="5" fill="#00D8CC"/>'
             + t(W - 34 - pw + 34, 49.5, pill, 16, "#FFFFFF", 500))
    b.append(f'<line x1="600" y1="{TOP}" x2="600" y2="{H}" stroke="{c["line"]}"/>')

    # conversation
    b.append(t(32, 132, "Conversation", 16, c["faint"], 500))
    css.append(appear("u", 0.4))
    b.append(f'<g class="u"><rect x="186" y="154" width="382" height="80" rx="20" fill="#00605F"/>'
             + t(208, 187, "2 days in Abu Dhabi with the kids.", 19, "#FFFFFF", 450)
             + t(208, 215, "We love beaches. Can you plan it?", 19, "#FFFFFF", 450) + "</g>")
    reply = [("Here's a relaxed two-day plan:", c["text"], 600, 6.6),
             ("Day 1, Saadiyat. Louvre Abu Dhabi in the", c["muted"], 400, 7.1),
             ("morning, lunch by the water, then the", c["muted"], 400, 7.5),
             ("beach until sunset.", c["muted"], 400, 7.9),
             ("Day 2, Yas Island. Warner Bros. World,", c["muted"], 400, 8.3),
             ("then Yas Waterworld in the afternoon.", c["muted"], 400, 8.7)]
    css.append(appear("rl", 6.4))
    b.append(f'<g class="rl">' + t(32, 278, "Concierge", 16, c["faint"], 500) + "</g>")
    for i, (s, col, wt, at) in enumerate(reply):
        css.append(appear(f"r{i}", at))
        b.append(f'<g class="r{i}">' + t(32, 314 + i * 30 + (8 if i else 0), s, 19, col, wt) + "</g>")
    places = [("Louvre Abu Dhabi", "Museum · Saadiyat"), ("Saadiyat Beach", "Beach · Saadiyat"),
              ("Yas Waterworld", "Water park · Yas Island")]
    b.append(f"<defs>{gradient('tile', 0, 0, 32, 32)}</defs>")
    for i, (name, meta) in enumerate(places):
        y = 514 + i * 62
        css.append(appear(f"k{i}", 9.2 + i * 0.3))
        b.append(f'<g class="k{i}"><rect x="32" y="{y}" width="536" height="52" rx="14" fill="{c["sub"]}" stroke="{c["line"]}"/>'
                 f'<g transform="translate(42 {y + 10})"><rect width="32" height="32" rx="9" fill="url(#tile)"/></g>'
                 + t(58, y + 33, name[0].lower(), 19, "#FFFFFF", font="disp", anchor="middle")
                 + t(88, y + 32.5, name, 17, c["text"], 600) + t(552, y + 32.5, meta, 15.5, c["faint"], 400, "end") + "</g>")

    # tool calls
    b.append(t(632, 132, "Tool calls", 16, c["faint"], 500))
    calls = [("check_moderation", "message", "safe", 1.3),
             ("search_attractions", 'tags=["family", "beach"]', "14 results", 2.1),
             ("search_dining", 'near="Saadiyat Island"', "9 results", 2.9),
             ("calculate_distance_to_place", '"Louvre Abu Dhabi"', "6.2 km", 3.7),
             ("search_itineraries", "days=2, pace=relaxed", "3 results", 4.5),
             ("select_cards_to_display", "k=3", "3 cards", 5.3)]
    y = 156
    for i, (fn, args, res, at) in enumerate(calls):
        css.append(appear(f"c{i}", at))
        b.append(f'<g class="c{i}">' + check(648, y + 22, c)
                 + t(672, y + 20, fn, 17, c["text"], 450, font="mono")
                 + t(672, y + 44, args, 15, c["faint"], 400, font="mono")
                 + t(1248, y + 20, res, 15.5, c["sea"], 500, "end", font="mono")
                 + f'<line x1="632" y1="{y + 62}" x2="1248" y2="{y + 62}" stroke="{c["line2"]}"/></g>')
        y += 70
    css.append(appear("st", 6.1))
    b.append(f'<g class="st"><circle class="pulse" cx="648" cy="{y + 18}" r="5" fill="{c["accent"]}"/>'
             + t(672, y + 24, "Streaming answer to the widget over SSE", 17, c["text"], 500) + "</g>")
    css.append(appear("tr", 9.9))
    b.append(f'<g class="tr">' + check(648, y + 62, c) + t(672, y + 68, "Trace sent to Langfuse and Phoenix", 17, c["muted"], 400) + "</g>")
    b.append(t(1248, H - 28, "LangGraph ReAct agent · GPT-4o · 19 tools", 15, c["faint"], 400, "end"))
    return svg(W, H, "Ask Abu Dhabi agent trace",
               "Animated example of one request. A visitor asks for a two-day family beach trip. The agent runs "
               "check_moderation, search_attractions, search_dining, calculate_distance_to_place, search_itineraries "
               "and select_cards_to_display, streams a two-day plan with three place cards over SSE, and sends the "
               "trace to Langfuse and Phoenix.", "".join(b), "".join(css))


# ---------------------------------------------------------------- product shots

SHOTS = {
    "ask-abu-dhabi": ("ask-abu-dhabi.webp", "visitabudhabi.ae", True, "Ask Abu Dhabi",
                      "visitabudhabi.ae with the Ask Abu Dhabi panel open: a welcome message and three suggested "
                      "questions with photos, over the Find your pace home page."),
    "digital-concierge": ("digital-concierge.webp", "Digital Concierge", False, "AI trip planner",
                          "Digital Concierge: saved chat sessions on the left, an answer with Yas Island and Ferrari "
                          "World cards in the middle, and a live map of the same places on the right."),
}


def shot(c, key):
    from PIL import Image  # only the full build needs Pillow; CI runs --activity
    file, url, lock, label, desc = SHOTS[key]
    W, BAR = 1280, 64
    im = Image.open(Path(__file__).resolve().parent / "shots" / file).convert("RGB")
    ih = round(im.height * W / im.width)
    buf = io.BytesIO()
    im.resize((W, ih), Image.LANCZOS).save(buf, "JPEG", quality=84, optimize=True, progressive=True)
    data = base64.b64encode(buf.getvalue()).decode()
    H = BAR + ih
    uw = width(url, 16) * 1.03 + (64 if lock else 40)
    ux = (W - uw) / 2
    b = [f"<defs><clipPath id='k'><rect width='{W}' height='{H}' rx='20'/></clipPath>{gradient('g', 0, 0, W, BAR)}</defs>",
         f'<g clip-path="url(#k)"><rect width="{W}" height="{BAR}" fill="url(#g)"/>'
         f'<image href="data:image/jpeg;base64,{data}" x="0" y="{BAR}" width="{W}" height="{ih}"/></g>',
         f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="20" fill="none" stroke="{c["line"]}"/>',
         t(30, 42, label.lower(), 26, "#FFFFFF", font="disp"),
         f'<rect x="{ux:.0f}" y="15" width="{uw:.0f}" height="34" rx="17" fill="#000" fill-opacity=".28" '
         f'stroke="#FFFFFF" stroke-opacity=".18"/>']
    tx = ux + 20
    if lock:
        b.append(f'<g fill="none" stroke="#B8CDD4" stroke-width="1.6"><rect x="{tx:.0f}" y="29" width="11" height="9" rx="2"/>'
                 f'<path d="M{tx + 2.5:.1f} 29 v-3 a3 3 0 0 1 6 0 v3"/></g>')
        tx += 22
    b.append(t(f"{tx:.0f}", 37.5, url, 16, "#E3EEF1", 500))
    pill = "Live"
    pw = width(pill, 15) * 1.04 + 42
    b.append(f'<rect x="{W - 28 - pw:.0f}" y="17" width="{pw:.0f}" height="30" rx="15" fill="#FFFFFF" fill-opacity=".1" '
             f'stroke="#FFFFFF" stroke-opacity=".25"/><circle class="pulse" cx="{W - 28 - pw + 18:.0f}" cy="32" r="4.5" fill="#00D8CC"/>'
             + t(f"{W - 28 - pw + 30:.0f}", 37, pill, 15, "#FFFFFF", 500))
    return svg(W, H, f"{label} in production", desc, "".join(b),
               ".pulse{animation:pulse 1.6s ease-in-out infinite}@keyframes pulse{50%{opacity:.35}}")


# ---------------------------------------------------------------- commit log

COMMITS = [
    ("2026-08-12", "feat", "Shareable chat sessions with share tokens"),
    ("2026-07-26", "fix", "Keyboard and screen-reader users couldn't operate parts of the chat"),
    ("2026-07-26", "perf", "Memoize BotMessage and ChatCarousel, stabilise keys"),
    ("2026-07-26", "refactor", "Extract sendMessageToApi into a useChatStream hook"),
    ("2026-07-24", "fix", "Tear down the SSE stream and timers on unmount"),
    ("2026-07-24", "fix", "Never send an authenticated message with a null user_id"),
    ("2026-07-13", "fix", "GTM data layer for the Ask Abu Dhabi chatbot"),
    ("2026-06-18", "feat", "Create an itinerary from a chat card; map markers fixed"),
    ("2026-06-12", "fix", "Chat map not showing on deployed servers"),
    ("2026-02-16", "feat", "Add the chatbot to visitabudhabi.ae"),
]


def commits(c):
    W, TOP, ROW = 1280, 88, 50
    H = TOP + 28 + ROW * len(COMMITS) + 52
    kind = {"feat": c["sea"], "fix": c["accent"], "perf": "#FF7061", "refactor": c["muted"]}
    b = [f"<defs>{gradient('g', 0, 0, W, TOP)}<clipPath id='k'><rect width='{W}' height='{H}' rx='20'/></clipPath></defs>",
         f'<g clip-path="url(#k)"><rect width="{W}" height="{H}" fill="{c["panel"]}"/>'
         f'<rect width="{W}" height="{TOP}" fill="url(#g)"/></g>',
         f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="20" fill="none" stroke="{c["line"]}"/>',
         t(34, 56, "git log", 36, "#FFFFFF", font="disp"),
         t(34 + width("git log", 36, "disp") + 16, 55, "visitabudhabi.ae front end, my commits", 20, ON_GRAD["muted"], 500),
         t(W - 34, 55, "186 since Feb 2026", 18, "#FFFFFF", 500, "end", font="mono")]
    y = TOP + 28
    for i, (d, k, msg) in enumerate(COMMITS):
        cy = y + ROW / 2
        b.append(t(34, cy + 6, d, 16, c["faint"], 400, font="mono"))
        kw = width(k, 14.5, "mono") + 22
        b.append(f'<rect x="170" y="{cy - 14}" width="{kw:.0f}" height="28" rx="14" fill="{kind[k]}" fill-opacity=".14" '
                 f'stroke="{kind[k]}" stroke-opacity=".45"/>' + t(170 + kw / 2, cy + 5, k, 14.5, kind[k], 500, "middle", font="mono"))
        b.append(t(290, cy + 6.5, msg, 19, c["text"], 450))
        if i < len(COMMITS) - 1:
            b.append(f'<line x1="34" y1="{y + ROW}" x2="{W - 34}" y2="{y + ROW}" stroke="{c["line2"]}"/>')
        y += ROW
    b.append(t(34, H - 24, "Selected from 186 commits, Feb to Aug 2026. The full log lives in a private client repo.", 15, c["faint"], 400))
    return svg(W, H, "My commits to the visitabudhabi.ae front end",
               "Selected commits from 186 to the visitabudhabi.ae front end since February 2026: "
               + "; ".join(f"{d} {k}: {m}" for d, k, m in COMMITS) + ".", "".join(b))


# ---------------------------------------------------------------- project cards

CARDS = {
    "harbinger": ("AI market intelligence", "Harbinger",
                  ["Reads news, patents and company data around", "the clock. Agents surface the signals worth",
                   "reading in weekly briefings and a Teams bot."],
                  "LangGraph · Celery · Redis · pgvector", "Owned end to end"),
    "medianet": ("Offline-first field operations", "Medianet",
                 ["Daily driver for 300+ field officers at Pakistan's", "largest power utility. Visits, GPS and forms",
                  "keep working when the signal drops."],
                 "NestJS · Next.js · Prisma · IndexedDB", "300+ daily users"),
    "vidsense": ("Video RAG · final year project", "VidSense",
                 ["Summaries, timestamped Q&A, highlight reels and", "AI podcasts from any video, with Whisper and",
                  "DeepSeek-R1 running on a local GPU."],
                 "Whisper · Ollama · FastAPI · RAG", "Public repo"),
    "claude-nestjs": ("Claude Code skill", "claude-nestjs",
                      ["Turns a requirements doc into a production", "NestJS + Prisma backend: a phased build, living",
                       "docs, and integrations that degrade safely."],
                      "Claude Code · NestJS · Prisma", "Public repo"),
    "signal-desk": ("LLM content pipeline", "Signal Desk",
                    ["Finds post-worthy tech news, scores it with an", "LLM and drafts posts in my voice, grounded in",
                     "what I've already written."],
                    "Next.js · Supabase · pgvector", "Free tiers only"),
    "remote-hands": ("MCP server in Go", "Remote Hands",
                     ["Lets an AI agent on one machine drive another", "over the LAN: shell, files, screen, mouse and",
                      "keyboard, behind a shared secret."],
                     "Go · MCP · Claude Code", "Personal tool"),
}


def card(c, key):
    kicker, title, lines, stack, tag = CARDS[key]
    W, H = 620, 340
    b = [f"<defs>{gradient('g', 36, 36, 60, 60)}</defs>", panel(W, H, c, 20)]
    b.append(f'<rect x="36" y="36" width="60" height="60" rx="16" fill="url(#g)"/>')
    b.append(t(66, 79, title[0].lower(), 34, "#FFFFFF", font="disp", anchor="middle"))
    b.append(t(116, 58, kicker, 16.5, c["sea"], 600))
    b.append(t(114, 94, title.lower(), 36, c["display"], font="disp"))
    b.append(arrow(W - 36 - 14, 40, 14, c["accent"], 2))
    for i, ln in enumerate(lines):
        b.append(t(36, 160 + i * 30, ln, 19.5, c["muted"], 400))
    b.append(f'<line x1="0" y1="266" x2="{W}" y2="266" stroke="{c["line"]}"/>')
    b.append(t(36, 308, stack, 15.5, c["faint"], 400, font="mono"))
    b.append(f'<circle cx="{W - 36 - width(tag, 16, "sans") * 1.03 - 13:.1f}" cy="302" r="4" fill="{c["accent"]}"/>')
    b.append(t(W - 36, 308, tag, 16, c["muted"], 500, "end"))
    return svg(W, H, f"{title}: {kicker}", " ".join(lines) + f" Built with {stack.replace(' · ', ', ')}.", "".join(b))


# ---------------------------------------------------------------- activity heatmap

def fetch_calendar():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    query = ('query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{totalContributions '
             'weeks{contributionDays{date contributionCount}}}}}}')
    req = urllib.request.Request("https://api.github.com/graphql",
                                 data=json.dumps({"query": query, "variables": {"u": USER}}).encode(),
                                 headers={"Authorization": f"bearer {token}", "User-Agent": "profile-build"})
    cal = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return cal["totalContributions"], [[(d["date"], d["contributionCount"]) for d in w["contributionDays"]] for w in cal["weeks"]]


def activity(c, total, weeks):
    days = [d for w in weeks for d in w]
    counts = [n for _, n in days]
    longest = run = 0
    for n in counts:
        run = run + 1 if n else 0
        longest = max(longest, run)
    active = sum(1 for n in counts if n)
    nonzero = sorted(n for n in counts if n)
    cuts = [nonzero[int(len(nonzero) * q)] for q in (0.25, 0.5, 0.75)] if nonzero else [1, 2, 3]

    def level(n):
        if not n:
            return 0
        return 1 + sum(n > cut for cut in cuts)

    W, H = 1280, 340
    cell, gap = 17, 4.2
    x0, y0 = 72, 130
    b = [panel(W, H, c, 20)]
    num = f"{total:,}"
    b.append(t(40, 70, num, 46, c["display"], font="disp"))
    b.append(t(40 + width(num, 46, "disp") + 12, 68, "contributions in the last year", 21, c["muted"], 500))
    x = W - 40
    for label, value in (("active days", f"{active}"), ("day longest streak", f"{longest}")):
        b.append(t(x, 66, label, 18, c["faint"], 400, "end"))
        x -= width(label, 18) * 1.03 + 8
        b.append(t(x, 68, value, 30, c["display"], font="disp", anchor="end"))
        x -= width(value, 30, "disp") + 34
    last_month = None
    for wi, week in enumerate(weeks):
        for d, n in week:
            wd = date.fromisoformat(d).isoweekday() % 7
            b.append(f'<rect x="{x0 + wi * (cell + gap):.1f}" y="{y0 + wd * (cell + gap):.1f}" width="{cell}" '
                     f'height="{cell}" rx="5" fill="{c["heat"][level(n)]}"/>')
        month = date.fromisoformat(week[0][0]).strftime("%b")
        if month != last_month and wi < len(weeks) - 2:
            b.append(t(x0 + wi * (cell + gap), y0 - 14, month, 14.5, c["faint"], 400))
            last_month = month
    for wd, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        b.append(t(x0 - 12, y0 + wd * (cell + gap) + 13, name, 13.5, c["faint"], 400, "end"))
    lx = W - 40 - 5 * (cell + 4) - 44
    b.append(t(lx - 10, H - 30, "Less", 14, c["faint"], 400, "end"))
    for i in range(5):
        b.append(f'<rect x="{lx + i * (cell + 4)}" y="{H - 44}" width="{cell}" height="{cell}" rx="5" fill="{c["heat"][i]}"/>')
    b.append(t(W - 40, H - 30, "More", 14, c["faint"], 400, "end"))
    b.append(t(40, H - 30, "Private client work included", 14, c["faint"], 400))
    return svg(W, H, f"{total:,} contributions in the last year",
               f"Contribution heatmap for the last year: {total:,} contributions, {active} active days, "
               f"longest streak {longest} days. Includes private client work.", "".join(b))


# ---------------------------------------------------------------- main

def write(stem, theme, content):
    (OUT / f"{stem}-{theme}.svg").write_text(content, encoding="utf-8")


def main():
    OUT.mkdir(exist_ok=True)
    only_activity = "--activity" in sys.argv
    total, weeks = fetch_calendar()
    for name, c in THEMES.items():
        write("activity", name, activity(c, total, weeks))
        if only_activity:
            continue
        write("hero", name, hero(c))
        write("metrics", name, metrics(c))
        write("trace", name, trace(c))
        write("commits", name, commits(c))
        for key in SHOTS:
            write(f"shot-{key}", name, shot(c, key))
        for key in HEADINGS:
            write(f"h-{key}", name, heading(c, key))
        for key in CARDS:
            write(f"card-{key}", name, card(c, key))
        for stem, label, primary in (("btn-site", "mbilaltaha.com", True), ("btn-linkedin", "LinkedIn", False),
                                     ("btn-email", "Email", False), ("btn-resume", "Résumé", False)):
            write(stem, name, button(c, label, primary))
    print("built", len(list(OUT.glob("*.svg"))), "svgs")


if __name__ == "__main__":
    main()
