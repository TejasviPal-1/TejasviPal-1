#!/usr/bin/env python3
"""Render data/profile.json as a neofetch-style terminal card SVG (types itself in)."""
import json
import sys
from html import escape

ACCENT = "#ffb7ce"
KEY = "#ffd3e1"
FG = "#e6e6e6"
DIM = "#8b949e"
BG = "#0d1117"
LH = 20          # line height
PAD = 22
W = 520


def main(src="data/profile.json", dst="terminal-card.svg"):
    p = json.load(open(src, encoding="utf-8"))
    lines = []  # (kind, payload)
    lines.append(("prompt", f"{p['handle']}:~$ neofetch"))
    lines.append(("title", p["handle"]))
    lines.append(("rule", ""))
    for k, v in p["about"]:
        lines.append(("kv", (k, v)))
    lines.append(("gap", ""))
    lines.append(("head", "Stack"))
    for k, v in p["stack"]:
        lines.append(("kv", (k, v)))
    lines.append(("gap", ""))
    lines.append(("head", "Highlights"))
    for h in p["highlights"]:
        lines.append(("bullet", h))
    lines.append(("gap", ""))
    lines.append(("cursor", f"{p['handle']}:~$ "))

    H = 40 + PAD + len(lines) * LH
    step = 0.12
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(p["name"])}: {escape(p["tagline"])}">',
        f"""<style>
  text {{ font: 13px 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; fill: {FG}; white-space: pre; }}
  .k {{ fill: {KEY}; font-weight: 600; }} .d {{ fill: {DIM}; }} .a {{ fill: {ACCENT}; font-weight: 700; }}
  .l {{ opacity: 0; animation: in .25s ease forwards; }}
  .cur {{ fill: {ACCENT}; animation: blink 1s steps(1) infinite; }}
  @keyframes in {{ to {{ opacity: 1; }} }}
  @keyframes blink {{ 50% {{ opacity: 0; }} }}
</style>""",
        f'<rect width="100%" height="100%" rx="10" fill="{BG}" stroke="#30363d"/>',
        '<circle cx="18" cy="16" r="5" fill="#ff5f56"/><circle cx="34" cy="16" r="5" fill="#ffbd2e"/><circle cx="50" cy="16" r="5" fill="#27c93f"/>',
        f'<text class="d" x="{W/2}" y="20" text-anchor="middle" style="font-size:11px">{escape(p["handle"])} — zsh</text>',
    ]
    y = 40 + PAD
    for i, (kind, val) in enumerate(lines):
        st = f'style="animation-delay:{i*step:.2f}s"'
        if kind == "prompt":
            out.append(f'<text class="l" x="{PAD}" y="{y}" {st}><tspan class="a">➜</tspan> <tspan class="d">{escape(val)}</tspan></text>')
        elif kind == "title":
            out.append(f'<text class="l a" x="{PAD}" y="{y}" {st}>{escape(val)}</text>')
        elif kind == "rule":
            out.append(f'<text class="l d" x="{PAD}" y="{y - 6}" {st}>{"─" * 44}</text>')
        elif kind == "head":
            out.append(f'<text class="l" x="{PAD}" y="{y}" {st}><tspan class="d">─ </tspan><tspan class="a">{escape(val)}</tspan><tspan class="d"> {"─" * (40 - len(val))}</tspan></text>')
        elif kind == "kv":
            k, v = val
            out.append(f'<text class="l" x="{PAD}" y="{y}" {st}><tspan class="k">{escape(k)}</tspan><tspan x="{PAD + 92}">{escape(v)}</tspan></text>')
        elif kind == "bullet":
            out.append(f'<text class="l" x="{PAD}" y="{y}" {st}><tspan class="a">▸</tspan> {escape(val)}</text>')
        elif kind == "cursor":
            out.append(f'<text class="l" x="{PAD}" y="{y}" {st}><tspan class="a">➜</tspan> <tspan class="d">{escape(val)}</tspan><tspan class="cur">█</tspan></text>')
        y += LH
    out.append("</svg>")
    open(dst, "w", encoding="utf-8").write("\n".join(out))
    print(f"wrote {dst}")


if __name__ == "__main__":
    main(*sys.argv[1:])
