"""
composite.py - place the exact TESTIDE tube render (final rev6/V4 label) into a photographic background.
The background is AI-generated as an EMPTY scene; the product is never AI-drawn, so the label stays exact.
scene = dict(bg, x, y (contact point = front-bottom of the tube, bg px), h (tube height px), view, light ('left'|'right'),
             tint (r,g,b multipliers), shadow (0..1), out (w,h))
"""
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import social

PHI = math.radians(11.0)


def place(scene, out_path):
    bg = Image.open(scene['bg']).convert('RGB')
    if scene.get('flip'):
        bg = bg.transpose(Image.FLIP_LEFT_RIGHT)
    W, H = bg.size
    tube = Image.open(os.path.join(social.ASSETS, 'renders', f"tube_{scene.get('view', 'front')}.png")).convert('RGBA')
    h = scene['h']; w = int(round(tube.width * h / tube.height))
    tube = tube.resize((w, h), Image.LANCZOS)
    # colour match: warm tint, slightly lower contrast, gentle grain
    a = np.asarray(tube).astype(np.float32)
    rgb = a[..., :3] * np.array(scene.get('tint', (1.0, 0.975, 0.93)), np.float32)
    rgb = rgb * scene.get('gain', 0.97) + scene.get('lift', 4)
    # directional shading to match the scene light: shadow side darker, lit side slightly warmer
    xs = np.linspace(-1, 1, rgb.shape[1])[None, :, None]
    if scene.get('light', 'left') == 'right': xs = -xs
    k = scene.get('side_shade', 0.22)
    rgb = rgb * (1 - k * np.clip(xs, 0, 1) ** 1.5) * (1 + 0.04 * np.clip(-xs, 0, 1))
    rng = np.random.default_rng(1)
    rgb += rng.normal(0, scene.get('grain', 2.2), rgb.shape[:2])[..., None]
    tube = Image.fromarray(np.concatenate([np.clip(rgb, 0, 255), a[..., 3:]], 2).astype(np.uint8), 'RGBA')
    x0 = int(round(scene['x'] - w / 2)); y0 = int(round(scene['y'] - h))
    ry = w / 2 * math.sin(PHI)                      # half-height of the base ellipse
    cx, cy = scene['x'], scene['y'] - ry             # base ellipse centre
    # 1) cast shadow away from the light, lying on the surface
    sgn = 1 if scene.get('light', 'left') == 'left' else -1
    L = scene.get('cast_len', 1.6) * w
    sh = Image.new('L', (W, H), 0); d = ImageDraw.Draw(sh)
    pts = []
    for k in range(41):
        t = k / 40 * math.pi
        pts.append((cx + math.cos(t + math.pi / 2) * w / 2 * 0.98, cy + math.sin(t + math.pi / 2) * ry * 0.98))
    far = [(cx + sgn * L + math.cos(t) * w * 0.55, cy - ry * 0.8 + math.sin(t) * ry * 1.3) for t in np.linspace(-math.pi / 2, math.pi / 2, 30)]
    if sgn < 0:
        far = [(cx + sgn * L - math.cos(t) * w * 0.55, cy - ry * 0.8 + math.sin(t) * ry * 1.3) for t in np.linspace(-math.pi / 2, math.pi / 2, 30)]
    d.polygon([(cx - 0 * w, cy - ry)] + [(cx + sgn * w * 0.5, cy - ry)] + far + [(cx + sgn * w * 0.5, cy + ry)], fill=int(255 * 0.55 * scene.get('shadow', 1.0)))
    sh = sh.filter(ImageFilter.GaussianBlur(w * 0.22))
    # 2) contact occlusion
    oc = Image.new('L', (W, H), 0)
    ImageDraw.Draw(oc).ellipse([cx - w * 0.56, cy - ry * 1.25, cx + w * 0.56, cy + ry * 1.35], fill=int(255 * 0.75 * scene.get('shadow', 1.0)))
    oc = oc.filter(ImageFilter.GaussianBlur(w * 0.05))
    m = np.maximum(np.asarray(sh, np.float32), np.asarray(oc, np.float32)) / 255.0
    shade = np.array(scene.get('shadow_col', (70, 55, 40)), np.float32)
    b = np.asarray(bg, np.float32)
    b = b * (1 - m[..., None] * 0.85) + shade * m[..., None] * 0.85 * 0.35
    out = Image.fromarray(np.clip(b, 0, 255).astype(np.uint8))
    out.paste(tube, (x0, y0), tube)
    if scene.get('reflect'):                          # faint reflection on a polished counter
        r = tube.transpose(Image.FLIP_TOP_BOTTOM).crop((0, 0, w, int(h * 0.35)))
        ra = np.asarray(r).astype(np.float32); fade = np.linspace(scene['reflect'], 0, r.height)[:, None]
        ra[..., 3] *= fade
        r = Image.fromarray(ra.astype(np.uint8), 'RGBA')
        out.paste(r, (x0, int(scene['y'] - 2 * ry) + 2), r)
        out.paste(tube, (x0, y0), tube)
    if scene.get('out'):
        out = out.resize(scene['out'], Image.LANCZOS)
    out.save(out_path, quality=94) if out_path.endswith('.jpg') else out.save(out_path)
    return out
