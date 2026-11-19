"""Builds every SVG on the profile page, in a dark and a light variant.

    python scripts/build.py              # all assets (activity needs GITHUB_TOKEN)
    python scripts/build.py --activity   # only the contribution heatmap (what CI runs)

SVGs shown through <img> can't load web fonts, so each file embeds a Geist subset
holding only the glyphs it uses.
"""
import base64
import io
import json
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

THEMES = {
    "dark": dict(panel="#0F1012", sub="#16171A", line="#25272C", line2="#1C1D21", text="#F2F3F5",
                 muted="#9A9EA7", faint="#62666F", accent="#7C83F5", ok="#4CB782",
                 heat=["#18191D", "#272A4A", "#3A4180", "#555DC4", "#8189F6"]),
    "light": dict(panel="#FFFFFF", sub="#F6F6F7", line="#E4E4E8", line2="#EEEEF1", text="#16171A",
                  muted="#5F636C", faint="#9A9DA5", accent="#5E6AD2", ok="#2F9E6A",
                  heat=["#EFEFF2", "#D9DBF7", "#B2B7EF", "#7F87E2", "#5E6AD2"]),
}
SANS, MONO = "Geist", "Geist Mono"


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


def width(s, size, mono=False):
    """Advance width of `s` in px, read from the font's default instance."""
    key = "geist-mono-variable.woff2" if mono else "geist-variable.woff2"
    if key not in _METRICS:
        f = TTFont(FONTS / key)
        _METRICS[key] = (f.getBestCmap(), f["hmtx"].metrics, f["head"].unitsPerEm)
    cmap, hmtx, upm = _METRICS[key]
    return sum(hmtx[cmap[ord(ch)]][0] for ch in s if ord(ch) in cmap) * size / upm


def svg(w, h, title, desc, body, css=""):
    chars = set(title + desc + body) | set(" 0123456789")
    faces = "".join(
        f"@font-face{{font-family:'{fam}';font-weight:100 900;"
        f"src:url(data:font/woff2;base64,{_subset(FONTS / file, chars)}) format('woff2')}}"
        for fam, file in ((SANS, "geist-variable.woff2"), (MONO, "geist-mono-variable.woff2")))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-labelledby="t d"><title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc>'
            f"<style>{faces}text{{font-family:'{SANS}',system-ui,sans-serif;font-feature-settings:'tnum'}}"
            f".m{{font-family:'{MONO}',ui-monospace,monospace}}{css}</style>{body}</svg>\n")


def t(x, y, s, size, fill, weight=400, anchor="start", mono=False, track=0.0, extra=""):
    cls = ' class="m"' if mono else ""
    ls = f' letter-spacing="{track}em"' if track else ""
    return (f'<text{cls} x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}"{ls} {extra}>{escape(s)}</text>')


def panel(w, h, c, rx=16):
    return f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="{c["panel"]}" stroke="{c["line"]}"/>'


def check(cx, cy, c, r=9):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{c["ok"]}" stroke-width="1.6"/>'
            f'<path d="M{cx - 4} {cy} l2.8 2.8 l5 -5.4" fill="none" stroke="{c["ok"]}" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


# ---------------------------------------------------------------- hero

def hero(c):
    W, H = 1280, 400
    b = [panel(W, H, c, 20)]
    b.append(t(72, 98, "Full Stack AI Engineer · Karachi", 21, c["muted"], 450))
    b.append(t(68, 178, "Bilal Taha", 84, c["text"], 600, track=-0.045))
    for i, line in enumerate(["I build LLM products end to end: RAG pipelines",
                              "and LangGraph agents, the APIs around them,",
                              "and the interfaces people actually use."]):
        b.append(t(72, 236 + i * 34, line, 24, c["text"] if i == 2 else c["muted"], 400, track=-0.01))
    b.append(f'<circle cx="78" cy="344" r="5" fill="{c["ok"]}"/>')
    b.append(t(94, 350, "Now building the AI concierge for Abu Dhabi tourism", 18, c["faint"], 450))

    # agent graph
    nodes = {"q": ("query", 760, 200, 100), "g": ("guardrails", 884, 200, 124),
             "a": ("agent", 1018, 200, 104), "r": ("retrieval", 1166, 110, 124),
             "m": ("maps", 1166, 200, 124), "i": ("itinerary", 1166, 290, 124),
             "s": ("SSE → UI", 1018, 316, 124)}
    hh = 40

    def R(k): n = nodes[k]; return n[1] + n[3] / 2, n[2]
    def L(k): n = nodes[k]; return n[1] - n[3] / 2, n[2]
    paths = {"qg": f"M{R('q')[0]},200 H{L('g')[0]}", "ga": f"M{R('g')[0]},200 H{L('a')[0]}",
             "ar": f"M{R('a')[0]},194 C1090,194 1070,110 {L('r')[0]},110", "am": f"M{R('a')[0]},200 H{L('m')[0]}",
             "ai": f"M{R('a')[0]},206 C1090,206 1070,290 {L('i')[0]},290", "as": f"M1018,{200 + hh / 2} V{316 - hh / 2}"}
    for k, d in paths.items():
        b.append(f'<path id="p{k}" d="{d}" fill="none" stroke="{c["line"]}" stroke-width="1.5"/>')
    for k, (label, cx, cy, w) in nodes.items():
        hot = k == "a"
        b.append(f'<rect x="{cx - w / 2}" y="{cy - hh / 2}" width="{w}" height="{hh}" rx="9" fill="{c["sub"]}" '
                 f'stroke="{c["accent"] if hot else c["line"]}" stroke-width="{1.5 if hot else 1}"/>')
        b.append(t(cx, cy + 5.5, label, 15, c["text"] if hot else c["muted"], 500 if hot else 400, "middle", mono=True))
    for k, begin in (("qg", 0), ("ga", 0.5), ("ar", 1.0), ("am", 1.1), ("ai", 1.2), ("as", 1.9)):
        b.append(f'<circle r="3.2" fill="{c["accent"]}" opacity="0"><animateMotion dur="3.4s" begin="{begin}s" '
                 f'repeatCount="indefinite" keyPoints="0;1;1" keyTimes="0;0.2;1" calcMode="linear"><mpath href="#p{k}"/>'
                 f'</animateMotion><animate attributeName="opacity" dur="3.4s" begin="{begin}s" repeatCount="indefinite" '
                 f'values="0;1;1;0;0" keyTimes="0;0.02;0.18;0.21;1"/></circle>')
    return svg(W, H, "Bilal Taha, Full Stack AI Engineer",
               "Full Stack AI Engineer in Karachi. I build LLM products end to end: RAG pipelines and LangGraph agents, "
               "the APIs around them, and the interfaces people use. Now building the AI concierge for Abu Dhabi tourism.",
               "".join(b))


# ---------------------------------------------------------------- link buttons

def button(c, label, primary=False):
    w = int(20 + width(label, 17) + 14 + width("↗", 15) + 18)
    H = 48
    fill, fg, stroke = (c["text"], c["panel"], c["text"]) if primary else (c["panel"], c["text"], c["line"])
    body = (f'<rect x="0.5" y="0.5" width="{w - 1}" height="{H - 1}" rx="11" fill="{fill}" stroke="{stroke}"/>'
            + t(20, 30.5, label, 17, fg, 500, track=-0.01)
            + t(w - 18, 30.5, "↗", 15, c["faint"] if not primary else fg, 400, "end"))
    return svg(w, H, label, f"Link: {label}", body)


# ---------------------------------------------------------------- metrics

def metrics(c):
    W, H = 1280, 168
    tiles = [("19", "agent tools in production"), ("300+", "daily users on one platform"),
             ("2", "live AI products, Abu Dhabi"), ("4.6k", "contributions since 2024")]
    b = [panel(W, H, c)]
    cw = W / 4
    for i, (num, label) in enumerate(tiles):
        x = i * cw
        if i:
            b.append(f'<line x1="{x}" y1="28" x2="{x}" y2="{H - 28}" stroke="{c["line"]}"/>')
        b.append(t(x + 40, 92, num, 56, c["text"], 500, track=-0.04))
        b.append(t(x + 40, 130, label, 18.5, c["muted"], 400))
    return svg(W, H, "Impact in numbers",
               "19 agent tools in production. 300+ daily users on one platform. 2 public AI products for DCT Abu Dhabi. "
               "4.6k contributions since 2024.", "".join(b))


# ---------------------------------------------------------------- agent trace

LOOP = 17.0


def appear(cls, at):
    p = at / LOOP * 100
    return (f".{cls}{{opacity:0;animation:{cls} {LOOP}s linear infinite}}"
            f"@keyframes {cls}{{0%,{p:.2f}%{{opacity:0;transform:translateY(5px)}}"
            f"{p + 2:.2f}%,93%{{opacity:1;transform:translateY(0)}}97%,100%{{opacity:0}}}}")


def trace(c):
    W, H = 1280, 700
    css = ["g{transform-box:fill-box}", ".pulse{animation:pulse 1.6s ease-in-out infinite}"
           "@keyframes pulse{50%{opacity:.35}}"]
    b = [panel(W, H, c, 18)]
    b.append(f'<line x1="0" y1="72" x2="{W}" y2="72" stroke="{c["line"]}"/>')
    b.append(t(32, 44, "Ask Abu Dhabi", 21, c["text"], 600, track=-0.02))
    b.append(t(32 + width("Ask Abu Dhabi", 21) * 0.98 + 10, 44, "Agent trace", 21, c["faint"], 400, track=-0.01))
    b.append(f'<circle class="pulse" cx="{W - 150}" cy="37" r="5" fill="{c["ok"]}"/>')
    b.append(t(W - 136, 43, "Production", 17, c["muted"], 450))
    b.append(f'<line x1="600" y1="72" x2="600" y2="{H}" stroke="{c["line"]}"/>')

    # conversation
    b.append(t(32, 116, "Conversation", 16, c["faint"], 450))
    css.append(appear("u", 0.4))
    b.append(f'<g class="u"><rect x="196" y="140" width="372" height="78" rx="14" fill="{c["sub"]}" stroke="{c["line2"]}"/>'
             + t(216, 172, "2 days in Abu Dhabi with the kids.", 19, c["text"], 400)
             + t(216, 200, "We love beaches. Can you plan it?", 19, c["text"], 400) + "</g>")
    reply = [("Here's a relaxed two-day plan:", c["text"], 500, 6.6),
             ("Day 1, Saadiyat. Louvre Abu Dhabi in the", c["muted"], 400, 7.1),
             ("morning, lunch by the water, then the", c["muted"], 400, 7.5),
             ("beach until sunset.", c["muted"], 400, 7.9),
             ("Day 2, Yas Island. Warner Bros. World,", c["muted"], 400, 8.3),
             ("then Yas Waterworld in the afternoon.", c["muted"], 400, 8.7)]
    css.append(appear("rl", 6.4))
    b.append(f'<g class="rl">' + t(32, 262, "Concierge", 16, c["faint"], 450) + "</g>")
    for i, (s, col, wt, at) in enumerate(reply):
        css.append(appear(f"r{i}", at))
        b.append(f'<g class="r{i}">' + t(32, 298 + i * 30 + (8 if i else 0), s, 19, col, wt) + "</g>")
    places = [("Louvre Abu Dhabi", "Museum · Saadiyat"), ("Saadiyat Beach", "Beach · Saadiyat"),
              ("Yas Waterworld", "Water park · Yas Island")]
    for i, (name, meta) in enumerate(places):
        y = 498 + i * 58
        css.append(appear(f"k{i}", 9.2 + i * 0.3))
        b.append(f'<g class="k{i}"><rect x="32" y="{y}" width="536" height="48" rx="10" fill="{c["panel"]}" stroke="{c["line"]}"/>'
                 f'<rect x="44" y="{y + 12}" width="24" height="24" rx="6" fill="{c["sub"]}" stroke="{c["line"]}"/>'
                 + t(56, y + 29, name[0], 13, c["muted"], 600, "middle")
                 + t(82, y + 30, name, 17, c["text"], 500) + t(552, y + 30, meta, 15.5, c["faint"], 400, "end") + "</g>")

    # tool calls
    b.append(t(632, 116, "Tool calls", 16, c["faint"], 450))
    calls = [("check_moderation", "message", "safe", 1.3),
             ("search_attractions", 'tags=["family", "beach"]', "14 results", 2.1),
             ("search_dining", 'near="Saadiyat Island"', "9 results", 2.9),
             ("calculate_distance_to_place", '"Louvre Abu Dhabi"', "6.2 km", 3.7),
             ("search_itineraries", "days=2, pace=relaxed", "3 results", 4.5),
             ("select_cards_to_display", "k=3", "3 cards", 5.3)]
    y = 140
    for i, (fn, args, res, at) in enumerate(calls):
        css.append(appear(f"c{i}", at))
        b.append(f'<g class="c{i}">' + check(648, y + 22, c)
                 + t(672, y + 20, fn, 17, c["text"], 450, mono=True)
                 + t(672, y + 44, args, 15, c["faint"], 400, mono=True)
                 + t(1248, y + 20, res, 15.5, c["muted"], 400, "end", mono=True)
                 + f'<line x1="632" y1="{y + 62}" x2="1248" y2="{y + 62}" stroke="{c["line2"]}"/></g>')
        y += 70
    css.append(appear("st", 6.1))
    b.append(f'<g class="st"><circle class="pulse" cx="648" cy="{y + 18}" r="5" fill="{c["accent"]}"/>'
             + t(672, y + 24, "Streaming answer to the widget over SSE", 17, c["text"], 450) + "</g>")
    css.append(appear("tr", 9.9))
    b.append(f'<g class="tr">' + check(648, y + 62, c) + t(672, y + 68, "Trace sent to Langfuse and Phoenix", 17, c["muted"], 400) + "</g>")
    b.append(t(1248, H - 28, "LangGraph ReAct agent · GPT-4o · 19 tools", 15, c["faint"], 400, "end"))
    return svg(W, H, "Ask Abu Dhabi agent trace",
               "Animated example of one request. A visitor asks for a two-day family beach trip. The agent runs "
               "check_moderation, search_attractions, search_dining, calculate_distance_to_place, search_itineraries "
               "and select_cards_to_display, streams a two-day plan with three place cards over SSE, and sends the "
               "trace to Langfuse and Phoenix.", "".join(b), "".join(css))


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
    W, H = 620, 330
    b = [panel(W, H, c, 16)]
    b.append(t(36, 56, kicker, 18, c["muted"], 450))
    b.append(t(W - 36, 56, "↗", 20, c["faint"], 400, "end"))
    b.append(t(34, 106, title, 36, c["text"], 600, track=-0.035))
    for i, ln in enumerate(lines):
        b.append(t(36, 152 + i * 30, ln, 19.5, c["muted"], 400))
    b.append(f'<line x1="0" y1="258" x2="{W}" y2="258" stroke="{c["line"]}"/>')
    b.append(t(36, 299, stack, 16, c["faint"], 400, mono=True))
    b.append(f'<circle cx="{W - 36 - width(tag, 16) - 13:.1f}" cy="293" r="4" fill="{c["ok"]}"/>')
    b.append(t(W - 36, 299, tag, 16, c["muted"], 450, "end"))
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

    W, H = 1280, 330
    cell, gap = 17, 4.2
    x0, y0 = 72, 120
    b = [panel(W, H, c, 18)]
    b.append(t(40, 58, f"{total:,} contributions in the last year", 26, c["text"], 500, track=-0.02))
    x = W - 40
    for label, value in (("active days", f"{active}"), ("day longest streak", f"{longest}")):
        b.append(t(x, 58, label, 19, c["faint"], 400, "end"))
        x -= width(label, 19) + 7
        b.append(t(x, 58, value, 22, c["text"], 500, "end"))
        x -= width(value, 22) + 32
    last_month = None
    for wi, week in enumerate(weeks):
        for d, n in week:
            wd = date.fromisoformat(d).isoweekday() % 7
            b.append(f'<rect x="{x0 + wi * (cell + gap):.1f}" y="{y0 + wd * (cell + gap):.1f}" width="{cell}" '
                     f'height="{cell}" rx="4" fill="{c["heat"][level(n)]}"/>')
        month = date.fromisoformat(week[0][0]).strftime("%b")
        if month != last_month and wi < len(weeks) - 2:
            b.append(t(x0 + wi * (cell + gap), y0 - 14, month, 14.5, c["faint"], 400))
            last_month = month
    for wd, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        b.append(t(x0 - 12, y0 + wd * (cell + gap) + 13, name, 13.5, c["faint"], 400, "end"))
    lx = W - 40 - 5 * (cell + 4) - 44
    b.append(t(lx - 10, H - 30, "Less", 14, c["faint"], 400, "end"))
    for i in range(5):
        b.append(f'<rect x="{lx + i * (cell + 4)}" y="{H - 44}" width="{cell}" height="{cell}" rx="4" fill="{c["heat"][i]}"/>')
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
        for key in CARDS:
            write(f"card-{key}", name, card(c, key))
        for stem, label, primary in (("btn-site", "mbilaltaha.com", True), ("btn-linkedin", "LinkedIn", False),
                                     ("btn-email", "Email", False), ("btn-resume", "Résumé", False)):
            write(stem, name, button(c, label, primary))
    print("built", len(list(OUT.glob("*.svg"))), "svgs")


if __name__ == "__main__":
    main()
