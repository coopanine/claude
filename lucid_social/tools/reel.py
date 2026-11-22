"""
reel.py - 10.5 s vertical reel (1080 x 1920, 30 fps): title card -> 360 degree spin of the final tube -> end card.
All type is set by social.py (brand fonts); the tube frames come from the rev6 artwork (render_tube.AlphaScene).
usage: python3 reel.py OUT_DIR
"""
import os, sys, math, subprocess, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import social
from render_tube import AlphaScene, LID
import spin3d

FPS = 30


def main(out):
    os.makedirs(out, exist_ok=True)
    cards = [
        dict(id='reel_title', kind='story', layout='type_hero', background='cream', eyebrow='The Lucid Institute',
             corner='MMXXVI', headline="We've been waiting *thousands* of *years* for this", footer='', footer_right=''),
        dict(id='reel_spin_bg', kind='story', layout='reel_bg', background='cobalt', eyebrow='Introducing',
             corner='TESTIDE', footer='Coming soon', footer_right='luciddaily.com'),
        dict(id='reel_end', kind='story', layout='logo_reveal', background='navy', eyebrow='Coming soon',
             headline='TESTIDE', hsize=120, sub='Join the waitlist at *luciddaily.com*', ssize=46, footer='The Lucid Institute', footer_right='MMXXVI'),
    ]
    social.render_items(cards, out)
    title = Image.open(os.path.join(out, 'reel_title.png')).convert('RGB')
    spin_bg = Image.open(os.path.join(out, 'reel_spin_bg.png')).convert('RGB')
    end = Image.open(os.path.join(out, 'reel_end.png')).convert('RGB')
    W, H = spin_bg.size
    tex = os.path.join(social.ASSETS, 'renders', 'rev6_tex.png')
    S = 7.6
    sc = AlphaScene(tex, LID, S, (int(70 * S), int(160 * S)), ss=2, tex_pxmm=30.0)
    # soft floor shadow, same for every frame
    probe = sc.rgba(spin3d.X_FRONT)
    tw, th = probe.size
    ox, oy = (W - tw) // 2, (H - th) // 2 + 40
    sh = Image.new('L', (W, H), 0)
    ImageDraw.Draw(sh).ellipse([ox - tw * 0.10, oy + th - 60, ox + tw * 1.10, oy + th + 40], fill=120)
    sh = sh.filter(ImageFilter.GaussianBlur(28))
    base = Image.composite(Image.new('RGB', (W, H), (8, 18, 80)), spin_bg, sh)
    frames = os.path.join(out, '_frames'); shutil.rmtree(frames, ignore_errors=True); os.makedirs(frames)
    n = 0

    def put(im):
        nonlocal n
        im.save(os.path.join(frames, f'{n:05d}.png')); n += 1

    blank = Image.new('RGB', (W, H), social.C['cream'])
    for k in range(int(0.5 * FPS)):                       # fade in title
        put(Image.blend(blank, title, (k + 1) / (0.5 * FPS)))
    for k in range(int(1.6 * FPS)):
        put(title)
    spin_n = int(6.0 * FPS)
    first = None
    for k in range(spin_n):                                # one full turn, eased
        t = k / spin_n
        e = 0.5 - 0.5 * math.cos(math.pi * t)
        xc = spin3d.X_FRONT + 188.0 * e
        tube = sc.rgba(xc)
        fr = base.copy(); fr.paste(tube, (ox, oy), tube)
        if k == 0:
            first = fr
            for j in range(int(0.5 * FPS)):                # cross-fade title -> spin
                put(Image.blend(title, fr, (j + 1) / (0.5 * FPS)))
        put(fr)
    last = fr
    for j in range(int(0.5 * FPS)):
        put(Image.blend(last, end, (j + 1) / (0.5 * FPS)))
    for j in range(int(1.4 * FPS)):
        put(end)
    mp4 = os.path.join(out, 'TESTIDE_teaser_reel.mp4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(frames, '%05d.png'),
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '17', '-preset', 'slow', '-movflags', '+faststart', mp4], check=True)
    first.save(os.path.join(out, 'TESTIDE_teaser_reel_cover.png'))
    shutil.rmtree(frames)
    print('frames', n, 'seconds', round(n / FPS, 2), mp4)


if __name__ == '__main__':
    main(os.path.abspath(sys.argv[1]))
