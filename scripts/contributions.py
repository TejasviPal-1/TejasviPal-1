#!/usr/bin/env python3
"""Fetch the profile owner's contribution calendar and render two SVGs:
contrib-heatmap.svg (red heatmap that fills in) and stats.svg (streaks + totals).

Env: GITHUB_TOKEN (the Actions token works), GH_USER (defaults to repo owner).
Run with --demo to render with fake data (for local previews).
"""
import json
import os
import random
import sys
import urllib.request
from datetime import date, timedelta

BG, BORDER, FG, DIM, ACCENT = "#0d1117", "#30363d", "#e6e6e6", "#8b949e", "#ff3b3b"
LEVELS = ["#161b22", "#4a1414", "#8c1c1c", "#d12a2a", "#ff3b3b"]
FONT = "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"

QUERY = """query($login:String!){ user(login:$login){ contributionsCollection{
  contributionCalendar{ totalContributions weeks{ contributionDays{ date contributionCount } } } } } }"""


def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    data = json.load(urllib.request.urlopen(req))
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [(d["date"], d["contributionCount"]) for w in cal["weeks"] for d in w["contributionDays"]]
    return cal["totalContributions"], days


def demo():
    start = date.today() - timedelta(days=364)
    start -= timedelta(days=(start.weekday() + 1) % 7)  # align to Sunday
    days, d = [], start
    while d <= date.today():
        days.append((d.isoformat(), max(0, int(random.gauss(3, 4)))))
        d += timedelta(days=1)
    return sum(c for _, c in days), days


def streaks(days):
    cur = best = run = 0
    for _, c in days:
        run = run + 1 if c else 0
        best = max(best, run)
    # current streak: count back from today (today allowed to be 0 so far)
    i = len(days) - 1
    if days and days[i][1] == 0:
        i -= 1
    while i >= 0 and days[i][1]:
        cur += 1
        i -= 1
    return cur, best


def level(c, mx):
    if c == 0:
        return 0
    return min(4, 1 + int(3 * c / max(1, mx)))


def heatmap(total, days):
    cell, gap = 11, 3
    weeks = (len(days) + 6) // 7
    ox, oy = 40, 46
    W = ox + weeks * (cell + gap) + 20
    H = oy + 7 * (cell + gap) + 40
    mx = sorted(c for _, c in days)[int(len(days) * 0.95)] or 1
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{total} contributions in the last year">',
        f"<style>text{{font:11px {FONT};fill:{DIM}}} .h{{fill:{FG};font-size:13px}} .c{{opacity:0;animation:in .4s ease forwards}} @keyframes in{{to{{opacity:1}}}}</style>",
        f'<rect width="100%" height="100%" rx="10" fill="{BG}" stroke="{BORDER}"/>',
        f'<text class="h" x="20" y="26"><tspan fill="{ACCENT}">➜</tspan> ./contributions.sh  <tspan fill="{DIM}">— {total:,} in the last year</tspan></text>',
    ]
    for i, lbl in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(f'<text x="8" y="{oy + i * (cell + gap) + 9}">{lbl}</text>')
    last_month, last_x = None, -99
    for idx, (ds, c) in enumerate(days):
        w, d = divmod(idx, 7)
        x, y = ox + w * (cell + gap), oy + d * (cell + gap)
        if d == 0 and ds[5:7] != last_month:
            last_month = ds[5:7]
            if x - last_x >= 3 * (cell + gap):
                last_x = x
                out.append(f'<text x="{x}" y="{oy - 6}">{date.fromisoformat(ds).strftime("%b")}</text>')
        out.append(
            f'<rect class="c" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{LEVELS[level(c, mx)]}" style="animation-delay:{w * 0.025:.3f}s"><title>{ds}: {c}</title></rect>'
        )
    lx = W - 20 - 5 * (cell + gap) - 70
    ly = H - 16
    out.append(f'<text x="{lx}" y="{ly + 9}">less</text>')
    for i, col in enumerate(LEVELS):
        out.append(f'<rect x="{lx + 32 + i * (cell + gap)}" y="{ly}" width="{cell}" height="{cell}" rx="2" fill="{col}"/>')
    out.append(f'<text x="{lx + 36 + 5 * (cell + gap)}" y="{ly + 9}">more</text>')
    out.append("</svg>")
    return "\n".join(out)


def stats(total, days):
    cur, best = streaks(days)
    active = sum(1 for _, c in days if c)
    items = [("Total (1y)", f"{total:,}"), ("Current streak", f"{cur} d"), ("Longest streak", f"{best} d"), ("Active days", f"{active}")]
    W, H = 760, 96
    colw = (W - 40) / len(items)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub stats">',
        f"<style>text{{font:12px {FONT};fill:{DIM}}} .v{{fill:{FG};font-size:24px;font-weight:700}} .a{{fill:{ACCENT}}}</style>",
        f'<rect width="100%" height="100%" rx="10" fill="{BG}" stroke="{BORDER}"/>',
    ]
    for i, (k, v) in enumerate(items):
        cx = 20 + colw * i + colw / 2
        cls = "v a" if i == 1 else "v"
        out.append(f'<text class="{cls}" x="{cx:.0f}" y="48" text-anchor="middle">{v}</text>')
        out.append(f'<text x="{cx:.0f}" y="72" text-anchor="middle">{k}</text>')
        if i:
            out.append(f'<line x1="{20 + colw * i:.0f}" y1="24" x2="{20 + colw * i:.0f}" y2="74" stroke="{BORDER}"/>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    if "--demo" in sys.argv:
        total, days = demo()
    else:
        login = os.environ.get("GH_USER") or os.environ["GITHUB_REPOSITORY_OWNER"]
        total, days = fetch(login, os.environ["GITHUB_TOKEN"])
    open("contrib-heatmap.svg", "w").write(heatmap(total, days))
    open("stats.svg", "w").write(stats(total, days))
    print(f"wrote contrib-heatmap.svg, stats.svg ({total} contributions)")
