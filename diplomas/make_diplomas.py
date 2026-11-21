"""Fill team names and nomination into diploma templates."""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

NOM_COMMAND = "Лучшая команда по мнению командования сторон"
NOM_TEAMS = "Лучшая команда по мнению других команд"

TEMPLATES = {
    1: dict(file="place1_red.jpg", glow=(255, 40, 40),
            name_box=(52, 672, 672, 750), nom_box=(58, 823, 638, 896)),
    2: dict(file="place2_blue.jpg", glow=(40, 140, 255),
            name_box=(52, 672, 672, 750), nom_box=(58, 823, 665, 896)),
    3: dict(file="place3_green.jpg", glow=(60, 255, 60),
            name_box=(52, 695, 672, 773), nom_box=(58, 833, 665, 905)),
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


def wrap(draw, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    if len(lines) == 2:
        best = min(range(1, len(words)),
                   key=lambda i: max(draw.textlength(" ".join(words[:i]), font=font),
                                     draw.textlength(" ".join(words[i:]), font=font)))
        lines = [" ".join(words[:best]), " ".join(words[best:])]
    return lines


def draw_block(img, box, text, max_size, min_size, glow, max_lines, pad=36, single_line_min=0):
    x0, y0, x1, y1 = box
    w, h = (x1 - x0) - 2 * pad, (y1 - y0) - 14
    d = ImageDraw.Draw(img)
    for lines_allowed, floor in ((1, single_line_min), (max_lines, min_size)):
        found = False
        for size in range(max_size, floor - 1, -1):
            font = ImageFont.truetype(FONT, size)
            lines = wrap(d, text, font, w)
            lh = int(size * 1.25)
            if len(lines) <= lines_allowed and lh * len(lines) <= h and \
                    all(d.textlength(l, font=font) <= w for l in lines):
                found = True
                break
        if found:
            break
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    top = cy - lh * len(lines) / 2 + lh / 2

    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for i, line in enumerate(lines):
        ld.text((cx, top + i * lh), line, font=font, anchor="mm", fill=glow + (255,))
    glow_layer = layer.filter(ImageFilter.GaussianBlur(5))
    img.alpha_composite(glow_layer)

    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    for i, line in enumerate(lines):
        sd.text((cx + 1.5, top + i * lh + 2), line, font=font, anchor="mm", fill=(0, 0, 0, 230))
    img.alpha_composite(shadow)

    # vertical silver gradient inside the text
    mask = Image.new("L", img.size, 0)
    md = ImageDraw.Draw(mask)
    for i, line in enumerate(lines):
        md.text((cx, top + i * lh), line, font=font, anchor="mm", fill=255)
    grad = Image.new("RGBA", img.size)
    gd = ImageDraw.Draw(grad)
    gy0, gy1 = int(top - lh), int(top + lh * len(lines))
    for y in range(max(gy0, 0), min(gy1, img.size[1])):
        t = (y - gy0) / max(gy1 - gy0, 1)
        v = int(255 - 90 * abs(t - 0.4) * 1.6)
        gd.line([(0, y), (img.size[0], y)], fill=(v, v, min(255, v + 6), 255))
    img.paste(grad, (0, 0), mask)


def slug(s):
    return s.replace(" ", "_").replace("'", "")


def main():
    os.makedirs(os.path.join(HERE, "output"), exist_ok=True)
    for place, team, nom in DIPLOMAS:
        t = TEMPLATES[place]
        img = Image.open(os.path.join(HERE, "templates", t["file"])).convert("RGBA")
        draw_block(img, t["name_box"], team, 44, 22, t["glow"], 1)
        draw_block(img, t["nom_box"], nom, 24, 14, t["glow"], 2, pad=28, single_line_min=20)
        kind = "command" if nom == NOM_COMMAND else "teams"
        out = os.path.join(HERE, "output", f"diploma_{kind}_place{place}_{slug(team)}.png")
        img.convert("RGB").save(out)
        print(out)


if __name__ == "__main__":
    main()
