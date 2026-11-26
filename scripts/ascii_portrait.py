#!/usr/bin/env python3
"""Turn a photo into an animated ASCII-portrait SVG for a GitHub profile README.

Usage: python scripts/ascii_portrait.py source-photo.jpg ascii-portrait.svg

The portrait "types in" row by row, holds, then loops. Pure SVG + CSS, so it
animates inside GitHub READMEs (no JS needed).
"""
import sys
from html import escape
from PIL import Image, ImageOps, ImageFilter, ImageEnhance, ImageDraw

COLS = 76            # characters per row
CHAR_W, CHAR_H = 7.2, 12.0  # px per character cell (monospace at 12px)
RAMP = " .'`^,:;Il!i~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
ACCENT = "#ffb7ce"   # baby pink
FG = "#e6e6e6"
BG = "#0d1117"
PAD = 18
TITLE_H = 28


def background_mask(rgb, thresh=34):
    """Flood-fill from the edges to find a plain studio background (white = background)."""
    small = rgb.resize((240, int(240 * rgb.height / rgb.width)))
    work = small.copy()
    key = (255, 0, 255)
    w, h = work.size
    for x in range(0, w, 6):
        for y in (0, h - 1):
            if work.getpixel((x, y)) != key:
                ImageDraw.floodfill(work, (x, y), key, thresh=thresh)
    for y in range(0, h, 6):
        for x in (0, w - 1):
            if work.getpixel((x, y)) != key:
                ImageDraw.floodfill(work, (x, y), key, thresh=thresh)
    mask = Image.new("L", work.size, 0)
    mask.putdata([255 if p == key else 0 for p in work.get_flattened_data()])
    return mask.filter(ImageFilter.MinFilter(3)).resize(rgb.size)


def to_rows(path):
    rgb = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    # square-ish crop around the centre (portrait framing)
    w, h = rgb.size
    side = min(w, h)
    top = max(0, (h - side) // 4)
    rgb = rgb.crop(((w - side) // 2, top, (w + side) // 2, top + side))
    mask = background_mask(rgb)
    img = rgb.convert("L")
    # lift shadows so dark hair/clothes still get texture on a dark terminal
    img = img.point(lambda v: int(255 * (0.14 + 0.86 * (v / 255) ** 0.75)))
    img.paste(0, mask=mask)  # knock out the background so it renders as empty space
    img = ImageOps.autocontrast(img, cutoff=1, mask=ImageOps.invert(mask))
    img = ImageEnhance.Contrast(img).enhance(1.35)
    img = img.filter(ImageFilter.SHARPEN)
    rows = int(COLS * (CHAR_W / CHAR_H) * 1.0)
    img = img.resize((COLS, rows), Image.LANCZOS)
    px = img.load()
    out = []
    for y in range(rows):
        line = ""
        for x in range(COLS):
            v = px[x, y] / 255
            # bright pixels -> dense chars (light-on-dark rendering)
            line += RAMP[int(v * (len(RAMP) - 1))]
        out.append(line.rstrip())
    # trim fully blank rows top/bottom
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    return out


def build_svg(rows, label="tejasvi@github:~$ ./portrait.sh"):
    width = PAD * 2 + COLS * CHAR_W
    height = TITLE_H + PAD * 2 + len(rows) * CHAR_H + 20
    reveal = 3.2          # seconds to draw every row
    hold = 5.0            # seconds fully visible
    total = reveal + hold + 0.8
    step = reveal / max(1, len(rows))
    style = f"""
      .t {{ font: 12px 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; fill: {FG}; white-space: pre; }}
      .r {{ opacity: 0; animation: show {total}s linear infinite; }}
      .lbl {{ font: 11px 'SFMono-Regular', Consolas, Menlo, monospace; fill: #8b949e; }}
      .cur {{ fill: {ACCENT}; animation: blink 1s steps(1) infinite; }}
      @keyframes blink {{ 50% {{ opacity: 0; }} }}
    """
    # each row gets its own keyframes window via animation-delay; the shared
    # keyframes keep it visible until the hold ends, then fade everything out.
    vis_end = (reveal + hold) / total * 100
    style += f"""
      @keyframes show {{
        0% {{ opacity: 0; }} 1% {{ opacity: 1; }}
        {vis_end:.1f}% {{ opacity: 1; }} {min(99.9, vis_end + 6):.1f}% {{ opacity: 0; }} 100% {{ opacity: 0; }}
      }}
    """
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}" role="img" aria-label="ASCII portrait of Tejasvi Pal">',
        f"<style>{style}</style>",
        f'<rect width="100%" height="100%" rx="10" fill="{BG}" stroke="#30363d"/>',
        '<circle cx="18" cy="14" r="5" fill="#ff5f56"/><circle cx="34" cy="14" r="5" fill="#ffbd2e"/><circle cx="50" cy="14" r="5" fill="#27c93f"/>',
        f'<text class="lbl" x="{width/2:.0f}" y="18" text-anchor="middle">{escape(label)}</text>',
    ]
    y0 = TITLE_H + PAD
    for i, line in enumerate(rows):
        # each row waits for its turn, then joins the shared loop
        delay = i * step
        parts.append(
            f'<text class="t r" x="{PAD}" y="{y0 + i * CHAR_H:.1f}" style="animation-delay:{delay:.3f}s;animation-duration:{total}s" xml:space="preserve">{escape(line)}</text>'
        )
    by = y0 + len(rows) * CHAR_H + 6
    parts.append(f'<text class="lbl" x="{PAD}" y="{by:.0f}">rendering portrait… <tspan class="cur">█</tspan></text>')
    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "source-photo.jpg"
    dst = sys.argv[2] if len(sys.argv) > 2 else "ascii-portrait.svg"
    rows = to_rows(src)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(build_svg(rows))
    print(f"wrote {dst}: {len(rows)} rows x {COLS} cols")
