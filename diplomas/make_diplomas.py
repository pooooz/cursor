"""Fill team names and nomination into the hi-res diploma templates.

Layout is derived from measurements of the artwork itself (neon plate borders),
not from the canvas size: each text block is centred on the real centre of its
plate, by ink bounds horizontally and by cap-height band vertically.
"""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "fonts", "CormorantSC-Bold.ttf")
FEATURES = ["lnum", "kern"]

NOM_COMMAND = "Лучшая команда по мнению командования сторон"
NOM_TEAMS = "Лучшая команда по мнению других команд"

# Plate geometry measured on the 4x templates: (left, right, top, bottom),
# coordinates of the centres of the bright neon border lines.
TEMPLATES = {
    1: dict(file="place1_red.jpg", glow=(255, 45, 45),
            name=(213, 2682, 2687, 3002), nom=(237, 2656, 3294, 3582)),
    2: dict(file="place2_blue.jpg", glow=(50, 150, 255),
            name=(213, 2683, 2689, 3006), nom=(239, 2657, 3294, 3581)),
    3: dict(file="place3_green.jpg", glow=(70, 255, 70),
            name=(212, 2683, 2777, 3089), nom=(227, 2666, 3336, 3616)),
}

DIPLOMAS = [
    (1, "1 MEF", NOM_COMMAND),
    (1, "Партизаны", NOM_COMMAND),
    (1, "СК 307ОМБ", NOM_COMMAND),
    (1, "Rangers", NOM_COMMAND),
    (1, "Snow Pandas", NOM_COMMAND),
    (1, "Rangers", NOM_TEAMS),
    (2, "Snow Pandas", NOM_TEAMS),
    (3, "Minotaur", NOM_TEAMS),
]

def glen(font, s):
    return font.getlength(s, features=FEATURES)


def layout(font, text, tracking):
    """Per-character x offsets with kerning and tracking; returns offsets, total width."""
    xs, x = [], 0.0
    for i, ch in enumerate(text):
        xs.append(x)
        adv = glen(font, ch)
        if i + 1 < len(text):
            adv += glen(font, ch + text[i + 1]) - adv - glen(font, text[i + 1])
            adv += tracking
        x += adv
    return xs, xs[-1] + glen(font, text[-1])


def fit(text, plate, max_cap_share, max_size, tracking_em, safe_width):
    left, right, top, bottom = plate
    max_w = (right - left) * safe_width
    max_cap = (bottom - top) * max_cap_share
    for size in range(max_size, 20, -2):
        font = ImageFont.truetype(FONT, size, layout_engine=ImageFont.Layout.RAQM)
        cap = -font.getbbox("H")[1] + font.getbbox("H")[3]
        xs, w = layout(font, text, tracking_em * size)
        if w <= max_w and cap <= max_cap:
            return font, xs, cap, size
    raise ValueError(text)


def draw_text(img, plate, text, glow, max_cap_share, max_size, tracking_em, safe_width, lift=0.02):
    left, right, top, bottom = plate
    font, xs, cap, size = fit(text, plate, max_cap_share, max_size, tracking_em, safe_width)
    layer = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(layer)
    for ch, x in zip(text, xs):
        d.text((x + 100, 1000), ch, font=font, fill=255, anchor="ls", features=FEATURES)
    ink = layer.getbbox()
    cx, cy = (left + right) / 2, (top + bottom) / 2 - (bottom - top) * lift
    dx = cx - ((ink[0] + ink[2]) / 2 - 100)
    baseline = cy + cap / 2

    mask = Image.new("L", img.size, 0)
    md = ImageDraw.Draw(mask)
    for ch, x in zip(text, xs):
        md.text((x + dx, baseline), ch, font=font, fill=255, anchor="ls", features=FEATURES)

    k = img.size[0] / 724
    halo = Image.new("RGBA", img.size, glow + (0,))
    halo.putalpha(mask.filter(ImageFilter.GaussianBlur(5 * k)).point(lambda v: min(255, int(v * 1.3))))
    img.alpha_composite(halo)

    outline = mask.filter(ImageFilter.MaxFilter(2 * int(k * 0.9) + 1))
    dark = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dark.putalpha(outline.point(lambda v: int(v * 0.9)))
    img.alpha_composite(dark.transform(img.size, Image.AFFINE, (1, 0, -k * 0.6, 0, 1, -k * 1.4)))

    grad = Image.new("RGB", img.size)
    gd = ImageDraw.Draw(grad)
    y0, y1 = int(baseline - cap * 1.05), int(baseline + cap * 0.25)
    for y in range(max(y0, 0), min(y1, img.size[1])):
        t = (y - y0) / (y1 - y0)
        v = 255 - 95 * abs(t - 0.38) * 1.5
        v = max(150, min(255, v))
        gd.line([(0, y), (img.size[0], y)], fill=(int(v), int(v), int(min(255, v + 8))))
    img.paste(grad, (0, 0), mask)


def slug(s):
    return s.replace(" ", "_").replace("'", "")


def main():
    out_dir = os.path.join(HERE, "output")
    os.makedirs(out_dir, exist_ok=True)
    for place, team, nom in DIPLOMAS:
        t = TEMPLATES[place]
        img = Image.open(os.path.join(HERE, "templates_hires", t["file"])).convert("RGBA")
        draw_text(img, t["name"], team, t["glow"], 0.46, 260, 0.05, 0.78)
        draw_text(img, t["nom"], nom, t["glow"], 0.30, 160, 0.03, 0.88)
        kind = "command" if nom == NOM_COMMAND else "teams"
        out = os.path.join(out_dir, f"diploma_{kind}_place{place}_{slug(team)}.jpg")
        img.convert("RGB").save(out, quality=95, subsampling=0)
        print(out)


if __name__ == "__main__":
    main()
