#!/usr/bin/env python3
"""Generate the macOS app icon (assets/icon.png + .app/Contents/Resources/app.icns).

Run with uv so Pillow doesn't need to be a project dependency:
    uv run --with pillow python assets/make_icon.py
Then rebuild the .icns with sips/iconutil (see assets/build_icns.sh).

Design: a rounded "squircle" with a blue->indigo gradient, a faint globe to
say "world/translate", and the letters A / あ with a swap arrow underneath.
"""

import os
from PIL import Image, ImageDraw, ImageFont

SIZE = 1024
MARGIN = 96                      # transparent padding around the squircle
RADIUS = 200
BOX = (MARGIN, MARGIN, SIZE - MARGIN, SIZE - MARGIN)

TOP = (91, 157, 255)             # #5b9dff
BOTTOM = (59, 70, 196)           # #3b46c4

A_FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
JP_FONT = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def vertical_gradient(size, top, bottom):
    grad = Image.new("RGB", (1, size))
    for y in range(size):
        t = y / (size - 1)
        grad.putpixel(
            (0, y),
            tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3)),
        )
    return grad.resize((size, size))


def main():
    base = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    # Squircle mask + gradient fill.
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle(BOX, radius=RADIUS, fill=255)
    grad = vertical_gradient(SIZE, TOP, BOTTOM).convert("RGBA")
    base.paste(grad, (0, 0), mask)

    # Decorative globe: faint circle + meridians/latitudes, clipped to squircle.
    deco = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(deco)
    cx, cy, r = SIZE // 2, 470, 300
    line = (255, 255, 255, 38)
    lw = 8
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=line, width=lw)
    for rx in (r, int(r * 0.55)):                      # meridians
        d.ellipse((cx - rx, cy - r, cx + rx, cy + r), outline=line, width=lw)
    for dy in (-int(r * 0.55), 0, int(r * 0.55)):      # latitudes
        half = int((r * r - dy * dy) ** 0.5)
        d.line((cx - half, cy + dy, cx + half, cy + dy), fill=line, width=lw)
    base = Image.alpha_composite(base, Image.composite(deco, Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0)), mask))

    draw = ImageDraw.Draw(base)
    white = (255, 255, 255, 255)

    # Letters: A (Latin) and あ (Japanese).
    fa = ImageFont.truetype(A_FONT, 360)
    fj = ImageFont.truetype(JP_FONT, 330)
    # soft shadow for depth
    shadow = (20, 30, 90, 90)
    for dx, dy, col in ((6, 8, shadow), (0, 0, white)):
        draw.text((362 + dx, 430 + dy), "A", font=fa, fill=col, anchor="mm")
        draw.text((668 + dx, 445 + dy), "あ", font=fj, fill=col, anchor="mm")

    # Swap arrow (drawn manually for font independence): two opposing arrows.
    ax, ay, w, gap, t = SIZE // 2, 735, 150, 34, 20
    arr = (255, 255, 255, 235)
    head = 34
    # top arrow -> right
    draw.line((ax - w, ay - gap, ax + w - head, ay - gap), fill=arr, width=t)
    draw.polygon(
        [(ax + w, ay - gap), (ax + w - head, ay - gap - head), (ax + w - head, ay - gap + head)],
        fill=arr,
    )
    # bottom arrow -> left
    draw.line((ax - w + head, ay + gap, ax + w, ay + gap), fill=arr, width=t)
    draw.polygon(
        [(ax - w, ay + gap), (ax - w + head, ay + gap - head), (ax - w + head, ay + gap + head)],
        fill=arr,
    )

    out_png = os.path.join(HERE, "icon.png")
    base.save(out_png)
    print("wrote", out_png)


if __name__ == "__main__":
    main()
