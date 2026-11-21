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

NOMS = {
    "command": "Лучшая команда по мнению командования сторон",
    "teams": "Лучшая команда по мнению других команд",
    "tech": "Лучшая техника на игре",
    "attendance": "Лучшая команда по посещаемости игр",
    "quality": "Лучшее качество игры по оценке командиров сторон",
    "impression": "Общее впечатление от игры по версии участников",
    "base": "Материальная база на игре",
    "leader": "Лучший командующий стороной",
}

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

# (nomination, place, main line, optional second line)
DIPLOMAS = [
    ("command", 1, "1 MEF", None),
    ("command", 1, "Партизаны", None),
    ("command", 1, "СК 307ОМБ", None),
    ("command", 1, "Rangers", None),
    ("command", 1, "Snow Pandas", None),
    ("teams", 1, "Rangers", None),
    ("teams", 2, "Snow Pandas", None),
    ("teams", 3, "Minotaur", None),
    ("tech", 1, "Дикарь", "ВСС Ведьмак"),
    ("tech", 2, "Бэдмобиль", "Bad's Company"),
    ("tech", 3, "Ниссан Патрол", "BLACK STORK"),
    ("attendance", 1, "Minotaur", None),
    ("attendance", 2, "Snow Pandas", None),
    ("attendance", 3, "СК 307ОМБ", None),
    ("attendance", 3, "Rangers", None),
    ("attendance", 3, "S.R.S. Jaegers", None),
    ("quality", 1, "РИСС", None),
    ("quality", 2, "Snow Pandas", None),
    ("quality", 3, "Rangers", None),
    ("impression", 1, "BADDAY Vietnam", "31.07–01.08.2026"),
    ("impression", 2, "Кровавый Алмаз 5", "16–17.05.2026"),
    ("impression", 3, "CONTROL", "15–16.08.2026"),
    ("base", 1, "BADDAY Vietnam", "31.07–01.08.2026"),
    ("base", 2, "Войны синдикатов 3", "Волчье логово (Брест) · 03–04.10.2026"),
    ("base", 3, "CONTROL", "15–16.08.2026"),
    ("leader", 1, "Лоич", None),
    ("leader", 2, "Bad", None),
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


def measure(text, size, tracking_em):
    font = ImageFont.truetype(FONT, size, layout_engine=ImageFont.Layout.RAQM)
    box = font.getbbox("H")
    xs, w = layout(font, text, tracking_em * size)
    return font, xs, w, box[3] - box[1]


def fit(text, max_w, max_cap, max_size, tracking_em):
    for size in range(max_size, 20, -2):
        font, xs, w, cap = measure(text, size, tracking_em)
        if w <= max_w and cap <= max_cap:
            return font, xs, cap, size
    raise ValueError(text)


def render_line(img, text, font, xs, cap, cx, baseline, glow):
    layer = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(layer)
    for ch, x in zip(text, xs):
        d.text((x + 100, 1000), ch, font=font, fill=255, anchor="ls", features=FEATURES)
    ink = layer.getbbox()
    dx = cx - ((ink[0] + ink[2]) / 2 - 100)

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
        v = max(150, min(255, 255 - 95 * abs(t - 0.38) * 1.5))
        gd.line([(0, y), (img.size[0], y)], fill=(int(v), int(v), int(min(255, v + 8))))
    img.paste(grad, (0, 0), mask)


def draw_block(img, plate, main, sub, glow, cap_share, max_size, tracking_em, safe_width, lift=0.02):
    """Centre one or two lines as a block on the plate (main line bigger, sub line below)."""
    left, right, top, bottom = plate
    h, max_w = bottom - top, (right - left) * safe_width
    cx, cy = (left + right) / 2, (top + bottom) / 2 - h * lift

    if sub is None:
        font, xs, cap, _ = fit(main, max_w, h * cap_share, max_size, tracking_em)
        render_line(img, main, font, xs, cap, cx, cy + cap / 2, glow)
        return

    mfont, mxs, mcap, msize = fit(main, max_w, h * cap_share * 0.78, int(max_size * 0.8), tracking_em)
    sfont, sxs, scap, _ = fit(sub, max_w, h * 0.2, int(msize * 0.7), tracking_em * 1.5)
    gap = mcap * 0.55
    total = mcap + gap + scap
    mbase = cy - total / 2 + mcap
    render_line(img, main, mfont, mxs, mcap, cx, mbase, glow)
    render_line(img, sub, sfont, sxs, scap, cx, mbase + gap + scap, glow)


def slug(s):
    return "".join(c if c.isalnum() else "_" for c in s).strip("_")[:40]


def main():
    out_dir = os.path.join(HERE, "output")
    os.makedirs(out_dir, exist_ok=True)
    for nom, place, main_text, sub in DIPLOMAS:
        t = TEMPLATES[place]
        img = Image.open(os.path.join(HERE, "templates_hires", t["file"])).convert("RGBA")
        draw_block(img, t["name"], main_text, sub, t["glow"], 0.46, 260, 0.05, 0.78)
        draw_block(img, t["nom"], NOMS[nom], None, t["glow"], 0.30, 160, 0.03, 0.88)
        out = os.path.join(out_dir, f"diploma_{nom}_place{place}_{slug(main_text)}.jpg")
        img.convert("RGB").save(out, quality=95, subsampling=0)
        print(out)


if __name__ == "__main__":
    main()
