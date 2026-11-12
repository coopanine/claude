"""
spin3d.py - renders the flat TESTIDE label wrapped on its real tube (label wrap 188 mm -> 59.8 mm diameter, 139.65 mm visible height).
Orthographic camera tilted slightly down, soft studio lighting, cap seam, lid top with the head icon, contact shadow.
Geometry is exact (true proportions); lighting is a simple paper-like model, not a photoreal render.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W_MM = 188.0
H_MM = 148.1495 - 8.4999
R = W_MM / (2 * math.pi)
X_FRONT = 94.936
PHI = math.radians(11.0)
L = np.array([-0.50, 0.55, 0.85]); L = L / np.linalg.norm(L)
V = np.array([0.0, math.sin(PHI), math.cos(PHI)])
HH = (L + V) / np.linalg.norm(L + V)
BG_TOP, BG_BOT = (246, 243, 238), (236, 232, 225)


def _sample(tex, x, y, wrap_x=True):
    h, w, _ = tex.shape
    x0 = np.floor(x).astype(np.int32); fx = (x - x0)[..., None].astype(np.float32)
    y0 = np.clip(np.floor(y).astype(np.int32), 0, h - 2); fy = np.clip(y - y0, 0, 1)[..., None].astype(np.float32)
    if wrap_x:
        x1 = (x0 + 1) % w; x0 = x0 % w
    else:
        x0 = np.clip(x0, 0, w - 2); x1 = x0 + 1
    y1 = y0 + 1
    return (tex[y0, x0] * (1 - fx) + tex[y0, x1] * fx) * (1 - fy) + (tex[y1, x0] * (1 - fx) + tex[y1, x1] * fx) * fy


class Scene:
    def __init__(self, tex_png, lid_png, S, size, ss=2, seam_mm=45.0, tex_pxmm=20.0, x_offset_mm=0.0):
        """S = output px per mm; size = (w, h) output px; seam_mm = cap height (mm below the top edge)"""
        self.S, self.ss, (self.Wp, self.Hp), self.seam = S, ss, size, seam_mm
        Sx = S * ss
        tex = Image.open(tex_png).convert('RGB')
        self.tpx = min(tex_pxmm, max(Sx * 1.2, 8.0))
        tw, th = int(round(W_MM * self.tpx)), int(round(H_MM * self.tpx))
        self.tex = np.asarray(tex.resize((tw, th), Image.LANCZOS)).astype(np.float32)
        lw = int(round(58.0 * self.tpx))
        self.lid = np.asarray(Image.open(lid_png).convert('RGB').resize((lw, lw), Image.LANCZOS)).astype(np.float32)
        w, h = self.Wp * ss, self.Hp * ss
        top_ext = H_MM / 2 * math.cos(PHI) + R * math.sin(PHI)
        bot_ext = H_MM / 2 * math.cos(PHI) + R * math.sin(PHI)
        cx = w / 2 + x_offset_mm * Sx
        cy = h / 2 - 0.035 * h + (top_ext - bot_ext) / 2 * Sx
        self.cx, self.cy, self.Sx = cx, cy, Sx
        xs = (np.arange(w) + 0.5 - cx) / Sx
        ys = (cy - (np.arange(h) + 0.5)) / Sx
        SX, SY = np.meshgrid(xs.astype(np.float32), ys.astype(np.float32))
        inside = np.abs(SX) < R
        Zf = np.sqrt(np.clip(R * R - SX * SX, 0, None))
        Y = SY / math.cos(PHI) + Zf * math.tan(PHI)
        side = inside & (Y <= H_MM / 2) & (Y >= -H_MM / 2)
        Zt = (H_MM / 2 * math.cos(PHI) - SY) / math.sin(PHI)
        rho = np.sqrt(SX * SX + Zt * Zt)
        top = rho <= R
        theta = np.arcsin(np.clip(SX / R, -1, 1))
        v = H_MM / 2 - Y
        nx, nz = np.sin(theta), np.cos(theta)
        lam = np.clip((nx * L[0] + nz * L[2] + 0.35) / 1.35, 0, 1)
        I = 0.74 + 0.28 * lam
        I += 0.05 * np.clip(nx * HH[0] + nz * HH[2], 0, 1) ** 40
        I *= 0.90 + 0.10 * np.clip(nz * V[2], 0, 1) ** 0.6
        # cap seam: thin shadow line with a faint highlight under it
        d = v - seam_mm
        I *= 1 - 0.30 * np.exp(-(d / 0.11) ** 2)
        I *= 1 + 0.035 * np.exp(-((d - 0.32) / 0.16) ** 2)
        # rolled top edge and bottom edge
        I *= 1 - 0.10 * np.exp(-(v / 0.35) ** 2)
        I *= 1 - 0.10 * np.exp(-((H_MM - v) / 0.45) ** 2)
        self.side_idx = np.nonzero(side)
        self.theta = theta[side]
        self.v = v[side]
        self.I_side = I[side].astype(np.float32)[:, None]
        lam_t = max(0.0, min(1.0, (L[1] + 0.35) / 1.35))
        It = (0.845 + 0.16 * lam_t) * (1 - 0.13 * np.exp(-((R - rho) / 0.55) ** 2))
        self.top_idx = np.nonzero(top)
        self.top_psi = np.arctan2(SX[top], Zt[top])
        self.top_rho = rho[top]
        self.I_top = It[top].astype(np.float32)[:, None]
        # background + shadows (frame independent)
        bg = np.zeros((h, w, 3), np.float32)
        t = np.linspace(0, 1, h)[:, None, None]
        bg[:] = np.array(BG_TOP, np.float32) * (1 - t) + np.array(BG_BOT, np.float32) * t
        sh = Image.new('L', (w, h), 0)
        dr = ImageDraw.Draw(sh)
        by = cy + H_MM / 2 * math.cos(PHI) * Sx
        rx, ry = R * Sx, R * math.sin(PHI) * Sx
        dr.ellipse([cx - 1.30 * rx + 0.35 * rx, by - 1.9 * ry + 0.4 * ry, cx + 1.30 * rx + 0.35 * rx, by + 1.9 * ry + 0.4 * ry], fill=70)
        sh = sh.filter(ImageFilter.GaussianBlur(0.42 * rx))
        sh2 = Image.new('L', (w, h), 0)
        ImageDraw.Draw(sh2).ellipse([cx - 1.03 * rx, by - 1.05 * ry + 0.25 * ry, cx + 1.03 * rx, by + 1.05 * ry + 0.25 * ry], fill=120)
        sh2 = sh2.filter(ImageFilter.GaussianBlur(0.07 * rx))
        a = np.maximum(np.asarray(sh, np.float32), np.asarray(sh2, np.float32))[..., None] / 255.0
        self.bg = bg * (1 - a) + np.array([60, 58, 62], np.float32) * a

    def frame(self, xc_mm=X_FRONT, cap_rot_deg=0.0):
        """xc_mm = label x that faces the camera; cap_rot_deg = cap turned relative to the body"""
        img = self.bg.copy()
        alpha = (xc_mm - X_FRONT) / R
        delta = math.radians(cap_rot_deg)
        th = self.theta + np.where(self.v < self.seam, delta, 0.0)
        u = (xc_mm + R * th) % W_MM
        col = _sample(self.tex, u * self.tpx - 0.5, self.v * self.tpx - 0.5)
        # faint label seam at x = 0
        ds = np.minimum(u, W_MM - u)
        col = col * (1 - 0.10 * np.exp(-(ds / 0.10) ** 2))[:, None]
        img[self.side_idx] = col * self.I_side
        psi = self.top_psi + alpha + delta
        xl = 29.0 + self.top_rho * np.sin(psi)
        yl = 29.0 + self.top_rho * np.cos(psi)
        ct = _sample(self.lid, xl * self.tpx - 0.5, yl * self.tpx - 0.5, wrap_x=False)
        img[self.top_idx] = ct * self.I_top
        out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
        if self.ss > 1:
            out = out.resize((self.Wp, self.Hp), Image.LANCZOS)
        return out
