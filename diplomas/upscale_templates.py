"""4x upscale of templates with Real-ESRGAN general-x4v3 (CPU, tiled).

Weights: https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth
Usage: python3 upscale_templates.py /path/to/realesr-general-x4v3.pth
"""
import os
import sys

import numpy as np
import torch
from PIL import Image
from torch import nn

HERE = os.path.dirname(os.path.abspath(__file__))


class SRVGGNetCompact(nn.Module):
    def __init__(self, num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=32, upscale=4):
        super().__init__()
        self.upscale = upscale
        self.body = nn.ModuleList([nn.Conv2d(num_in_ch, num_feat, 3, 1, 1), nn.PReLU(num_feat)])
        for _ in range(num_conv):
            self.body.append(nn.Conv2d(num_feat, num_feat, 3, 1, 1))
            self.body.append(nn.PReLU(num_feat))
        self.body.append(nn.Conv2d(num_feat, num_out_ch * upscale * upscale, 3, 1, 1))
        self.upsampler = nn.PixelShuffle(upscale)

    def forward(self, x):
        out = x
        for layer in self.body:
            out = layer(out)
        out = self.upsampler(out)
        return out + nn.functional.interpolate(x, scale_factor=self.upscale, mode="nearest")


def upscale(model, img, tile=128, pad=12, scale=4):
    x = torch.from_numpy(np.asarray(img.convert("RGB"), dtype=np.float32) / 255).permute(2, 0, 1)[None]
    _, _, h, w = x.shape
    out = torch.zeros(1, 3, h * scale, w * scale)
    with torch.no_grad():
        for y0 in range(0, h, tile):
            for x0 in range(0, w, tile):
                ys, xs = max(y0 - pad, 0), max(x0 - pad, 0)
                ye, xe = min(y0 + tile + pad, h), min(x0 + tile + pad, w)
                o = model(x[:, :, ys:ye, xs:xe])
                ty0, tx0 = (y0 - ys) * scale, (x0 - xs) * scale
                th, tw = min(tile, h - y0) * scale, min(tile, w - x0) * scale
                out[:, :, y0 * scale:y0 * scale + th, x0 * scale:x0 * scale + tw] = \
                    o[:, :, ty0:ty0 + th, tx0:tx0 + tw]
    arr = (out[0].clamp(0, 1).permute(1, 2, 0).numpy() * 255).round().astype(np.uint8)
    return Image.fromarray(arr)


def main(weights):
    model = SRVGGNetCompact()
    model.load_state_dict(torch.load(weights, map_location="cpu")["params"])
    model.eval()
    src = os.path.join(HERE, "templates")
    dst = os.path.join(HERE, "templates_hires")
    os.makedirs(dst, exist_ok=True)
    for name in sorted(os.listdir(src)):
        if not name.endswith(".jpg"):
            continue
        out = upscale(model, Image.open(os.path.join(src, name)))
        out.save(os.path.join(dst, name), quality=95, subsampling=0)
        print(name, out.size)


if __name__ == "__main__":
    main(sys.argv[1])
