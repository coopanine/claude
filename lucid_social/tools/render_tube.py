"""
render_tube.py - transparent 3D renders of the final TESTIDE tube (rev6 artwork) for social assets.
Builds the wrap texture straight from the rev6 artwork (dieline and dimension layers removed), wraps it on the real tube
geometry (spin3d.Scene: 188 mm wrap, 139.65 mm tall, cap seam 45 mm) and writes RGBA PNGs (no background, no shadow).
usage: python3 render_tube.py OUT_DIR
"""
import os, sys, math
import numpy as np
from PIL import Image

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lucid_mockups', 'final_spacing', 'tools')
sys.path.insert(0, os.path.abspath(TOOLS))
os.chdir(os.path.abspath(TOOLS))
from labelkit import Source, build_pdf, render, ELEMENTS as E, PT   # noqa: E402
import addr, spin3d                                                  # noqa: E402
from v3cap import DASH, WRAP_PAGE                                     # noqa: E402

LID = '/tmp/claude-0/-home-user-claude/86cbe00f-c61a-5cb5-8dc6-e187390f6093/scratchpad/work/tex_lid.png'


def build_texture(out_dir, pxmm=30.0):
    src = Source('src.pdf')
    pl, clones, extra, info = addr.make(src)
    art = os.path.join(out_dir, 'rev6_wrap.pdf')
    build_pdf(src, pl, art, title='TESTIDE rev6 wrap', recolor=addr.RECOLOR, page_mm=WRAP_PAGE,
              keep_mm=(-5, 0, 196, 157), drop_layers=('/MC2', '/MC3'), drop_ids=list(DASH) + [addr.PERIOD],
              clones=clones, extra=extra, embolden=info.pop('embolden'), outline=info.pop('outline'),
              linewidth={E['p_fda_box'][0]: info['fda_lw_pt']})
    tex = os.path.join(out_dir, 'rev6_tex.png')
    render(art, tex, zoom=pxmm / PT)
    return tex


class AlphaScene(spin3d.Scene):
    """Scene that also returns the tube's coverage, so the render can sit on any background"""
    def rgba(self, xc_mm=spin3d.X_FRONT):
        h, w = self.bg.shape[:2]
        img = np.zeros((h, w, 3), np.float32)
        u = (xc_mm + spin3d.R * self.theta) % spin3d.W_MM
        col = spin3d._sample(self.tex, u * self.tpx - 0.5, self.v * self.tpx - 0.5)
        ds = np.minimum(u, spin3d.W_MM - u)
        col = col * (1 - 0.10 * np.exp(-(ds / 0.10) ** 2))[:, None]
        img[self.side_idx] = col * self.I_side
        alpha = (xc_mm - spin3d.X_FRONT) / spin3d.R
        psi = self.top_psi + alpha
        xl = 29.0 + self.top_rho * np.sin(psi); yl = 29.0 + self.top_rho * np.cos(psi)
        img[self.top_idx] = spin3d._sample(self.lid, xl * self.tpx - 0.5, yl * self.tpx - 0.5, wrap_x=False) * self.I_top
        a = np.zeros((h, w), np.float32); a[self.side_idx] = 1.0; a[self.top_idx] = 1.0
        # premultiplied downsample, then un-premultiply (no halo on dark backgrounds)
        pre = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
        A = Image.fromarray((a * 255).astype(np.uint8))
        pre = pre.resize((self.Wp, self.Hp), Image.LANCZOS); A = A.resize((self.Wp, self.Hp), Image.LANCZOS)
        p = np.asarray(pre, np.float32); al = np.asarray(A, np.float32)[..., None] / 255.0
        c = np.where(al > 0.004, p / np.maximum(al, 1e-3), 0)
        out = np.concatenate([np.clip(c, 0, 255), al * 255], axis=2).astype(np.uint8)
        im = Image.fromarray(out, 'RGBA')
        return im.crop(im.getbbox())


if __name__ == '__main__':
    out = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else '.'
    os.makedirs(out, exist_ok=True)
    tex = build_texture(out)
    S = 12.0                                   # output px per mm -> tube ~720 px wide, ~1700 px tall
    sc = AlphaScene(tex, LID, S, (int(70 * S), int(160 * S)), ss=2, tex_pxmm=30.0)
    views = {'front': spin3d.X_FRONT, 'quarter_facts': spin3d.X_FRONT - 32.0, 'quarter_protocol': spin3d.X_FRONT + 32.0,
             'protocol': 161.76, 'facts': 30.6}
    for name, xc in views.items():
        im = sc.rgba(xc)
        im.save(os.path.join(out, f'tube_{name}.png'))
        print(name, im.size)
