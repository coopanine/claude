"""spin.py - seamless 360 degree loop of the final tube (rev6/V4 artwork) on a soft studio background. MP4 + GIF."""
import os, sys, math, subprocess, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import social
from render_tube import AlphaScene, LID
import spin3d

def main(out, W=1080, H=1350, secs=5.0, fps=30, bg_top=(250, 248, 246), bg_bot=(232, 226, 216)):
    os.makedirs(out, exist_ok=True)
    S = 7.4
    sc = AlphaScene(os.path.join(social.ASSETS, 'renders', 'rev6_tex.png'), LID, S, (int(70 * S), int(160 * S)), ss=2, tex_pxmm=30.0)
    t = np.linspace(0, 1, H)[:, None, None]
    bg = (np.array(bg_top) * (1 - t) + np.array(bg_bot) * t) * np.ones((1, W, 1))
    base = Image.fromarray(bg.astype(np.uint8))
    probe = sc.rgba(spin3d.X_FRONT); tw, th = probe.size
    ox, oy = (W - tw) // 2, (H - th) // 2 + 20
    sh = Image.new('L', (W, H), 0)
    ImageDraw.Draw(sh).ellipse([ox - tw * 0.12, oy + th - 55, ox + tw * 1.12, oy + th + 35], fill=110)
    sh = sh.filter(ImageFilter.GaussianBlur(26))
    base = Image.composite(Image.new('RGB', (W, H), (150, 140, 128)), base, sh)
    fr_dir = os.path.join(out, '_frames'); shutil.rmtree(fr_dir, ignore_errors=True); os.makedirs(fr_dir)
    n = int(secs * fps)
    for k in range(n):
        tube = sc.rgba(spin3d.X_FRONT + 188.0 * k / n)
        f = base.copy(); f.paste(tube, (ox, oy), tube); f.save(os.path.join(fr_dir, f'{k:05d}.png'))
    mp4 = os.path.join(out, 'TESTIDE_360_spin.mp4'); gif = os.path.join(out, 'TESTIDE_360_spin.gif')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(fps), '-i', os.path.join(fr_dir, '%05d.png'),
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '16', '-preset', 'slow', '-movflags', '+faststart', mp4], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(fps), '-i', os.path.join(fr_dir, '%05d.png'),
                    '-vf', 'fps=20,scale=540:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=192[p];[b][p]paletteuse=dither=sierra2_4a',
                    '-loop', '0', gif], check=True)
    shutil.copy(os.path.join(fr_dir, '00000.png'), os.path.join(out, 'TESTIDE_360_spin_poster.png'))
    shutil.rmtree(fr_dir)
    print('ok', mp4, os.path.getsize(mp4) // 1024, 'KB', gif, os.path.getsize(gif) // 1024, 'KB')

if __name__ == '__main__':
    main(os.path.abspath(sys.argv[1]))
