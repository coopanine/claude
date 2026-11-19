"""
addr.py - final Option C artwork + text corrections (Nov 19):
  1. "ALBION ®" -> "ALBION®"            (stray space removed; rest of the line closes up by one space)
  2. "( Trigonella" -> "(Trigonella"      (same)
  3. "(vegetable capsule). L-leucine." -> "(vegetable capsule), L-leucine."
       the regular comma does not exist in the file; it is the label's bold comma (from "1,450") redrawn to the
       regular weight: head = the regular period's width and height, tail depth scaled by the same factor
  4. address: line 2 of the Distributed-by block becomes "68 SE 6th Street, Miami, FL 33131 • luciddaily.com"
       every letter is a copy of the label's own glyphs (S from "Store", E = the label's F + L, h from the FDA box
       text, t r e , from "Distributed" / "Miami,", scaled to this size); 6 and 8 are not in the file at all and are
       set in Asul (closest available match), sized to the label's figures
     spacing: side bearings solved from the label's own text (spacing.py, rms 0.016 mm)
"""
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from fontTools.pens.boundsPen import BoundsPen
from labelkit import Source, build_pdf, render, ELEMENTS as E
from final_c import make as make_c
from precise import ink, flat_edges
from glyphmap import charmap
import spacing, spacing_c
from v3cap import DASH

import os
ASUL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts', 'asul-latin-400-normal.woff')   # Asul, SIL OFL 1.1
RECOLOR = {16: '/CS2', 14: '/CS0'}
PERIOD, BOLD_COMMA, BOLD_ONE = 536, 725, 724
ZINC_TAIL = list(range(640, 652))          # ® TRAACS® zinc
TRIG = list(range(765, 775))               # Trigonella


def compose(A, P):
    """A after P, both (sx, sy, tx, ty) label-mm affines"""
    return (A[0] * P[0], A[1] * P[1], A[0] * P[2] + A[2], A[1] * P[3] + A[3])


class MMPen(BasePen):
    def __init__(self, gs, s, ox, base):
        super().__init__(gs); self.s, self.ox, self.base = s, ox, base; self.con = []; self.cur = None
    def P(self, p): return (self.ox + p[0] * self.s, self.base - p[1] * self.s)
    def _moveTo(self, p): self.cur = [('m', self.P(p))]; self.con.append(self.cur)
    def _lineTo(self, p): self.cur.append(('l', self.P(p)))
    def _curveToOne(self, p1, p2, p3): self.cur.append(('c', self.P(p1) + self.P(p2) + self.P(p3)))
    def _closePath(self): self.cur.append(('h',))
    def _endPath(self): self.cur.append(('h',))


THIN = 0.021      # mm inset per side: brings Asul's figure strokes (0.187 mm) down to the label's (~0.15 mm)


def asul_thin(gs, gname, sa, x_left, base, d):
    """Asul glyph outline in label mm, inset by d per side (lighter weight), rescaled so its ink height is unchanged,
    ink-left at x_left, ink bottom where the un-thinned glyph's bottom was (same baseline overshoot)"""
    from fontTools.pens.recordingPen import RecordingPen
    from fontrank import flatten
    from shapely.geometry import Polygon
    from shapely.geometry.polygon import orient
    from shapely import affinity
    pen = RecordingPen(); gs[gname].draw(pen)
    polys = flatten(pen.value, lambda p: (p[0] * sa, base - p[1] * sa))
    g = None
    for p in polys:
        if len(p) < 3: continue
        q = Polygon(p).buffer(0)
        g = q if g is None else g.symmetric_difference(q)
    l, t, r, b = g.bounds
    e = g.buffer(-d, quad_segs=24, join_style='round')
    el, et, er, eb = e.bounds
    k = (b - t) / (eb - et)
    e = affinity.scale(e, k, k, origin=(el, eb))
    el, et, er, eb = e.bounds
    e = affinity.translate(e, x_left - el, b - eb)
    e = e.simplify(0.0005)
    geoms = [e] if e.geom_type == 'Polygon' else list(e.geoms)
    cons = []
    for pg in geoms:
        pg = orient(pg, 1.0)
        for ring in [pg.exterior] + list(pg.interiors):
            c = list(ring.coords)[:-1]
            cons.append([('m', c[0])] + [('l', q) for q in c[1:]] + [('h',)])
    L, T, R, B = e.bounds
    return cons, R - L


def make(src):
    pl, geo = make_c(src, 'thirds')
    info = {}
    clones, extra = [], []

    # ---- 1 + 2: stray spaces (one space of the condensed Facts font) ----
    L_c, R_c, S_c, _ = spacing_c.solve(spacing_c.obs_of(src, pl))
    pl.shift(ZINC_TAIL, -S_c, 0.0)
    pl.shift(TRIG, -S_c, 0.0)
    info['facts_space'] = S_c

    # ---- 3: comma ----
    per = ink(src, pl, [PERIOD])
    bc = ink(src, pl, [BOLD_COMMA])
    bold_base = ink(src, pl, [BOLD_ONE])[3]            # bold '1' of "1,450" stands on the baseline
    # top edge of the bold comma = its ink top; its top corners from the outline
    top_y = bc[1]
    from precise import subpaths_src
    o = src.objs[BOLD_COMMA]
    # top-left / top-right x of the flat top edge (post-placer): the two points at top_y
    sx_, sy_, tx_, ty_ = pl.tf(BOLD_COMMA)
    from labelkit import PT, X0, YTOP
    pts = []
    for k in range(o['start'], o['end']):
        ins = src.ops[k]; a = [float(v) for v in ins.operands]
        for j in range(0, len(a) - 1, 2):
            x = sx_ * ((a[j] + o['ctm'][4] - X0) / PT) + tx_; y = sy_ * ((YTOP - (a[j + 1] + o['ctm'][5])) / PT) + ty_
            if abs(y - top_y) < 1e-3: pts.append(x)
    tl, tr = min(pts), max(pts)
    kx = (per[2] - per[0]) / (tr - tl)
    ky = (per[3] - per[1]) / (bold_base - top_y)
    A = (kx, ky, per[0] - kx * tl, per[1] - ky * top_y)
    clones.append((BOLD_COMMA, compose(A, pl.tf(BOLD_COMMA)), None))
    info['comma'] = dict(kx=kx, ky=ky, head=(per[2] - per[0], per[3] - per[1]), tail=ky * (bc[3] - bold_base))

    # ---- 4: address ----
    Lh, Rh, Sh, obs, res = spacing.solve(src, pl)
    groups = {k: charmap(src, pl, k)[0] for k in ('dist1', 'dist2', 'p_stor_text', 'p_fda_text')}
    def pick(key, line, ch, nth=0):
        r = groups[key][line]
        hits = [i for c, i in zip(r['chars'], r['ids']) if c == ch]
        return hits[nth], flat_edges(src, pl, r['ids'], 'bottom'), 1.0 / spacing.SCALE[key]
    d2 = groups['dist2'][0]
    base2 = flat_edges(src, pl, d2['ids'], 'bottom')
    m_id = d2['ids'][0]; m_box = ink(src, pl, [m_id])
    d1 = groups['dist1'][0]; d_box = ink(src, pl, [d1['ids'][0]])
    margin = 0.5 * ((m_box[0] - Lh['M']) + (d_box[0] - Lh['D']))

    # Asul figures, scaled so its 3 matches the label's 3 (ink height)
    f = TTFont(ASUL); gs = f.getGlyphSet(); cmap = f.getBestCmap(); upm = f['head'].unitsPerEm; hm = f['hmtx']
    def gbox(ch):
        bp = BoundsPen(gs); gs[cmap[ord(ch)]].draw(bp); return bp.bounds
    i3 = [i for c, i in zip(d2['chars'], d2['ids']) if c == '3'][0]
    b3 = ink(src, pl, [i3]); fb3 = gbox('3')
    sa = (b3[3] - b3[1]) / (fb3[3] - fb3[1])                 # mm per font unit
    def asul_lr(ch):
        b = gbox(ch); adv = hm[cmap[ord(ch)]][0]
        return b[0] * sa, (adv - b[2]) * sa, (b[2] - b[0]) * sa
    info['asul_vs_label'] = {p: ((asul_lr(p[0])[1] + asul_lr(p[1])[0]), Rh[p[0]] + Lh[p[1]]) for p in ('33', '31', '13')}

    L_S = 0.5 * (Lh['o'] + Lh['s'])        # S is never preceded by anything in the label: round-letter estimate
    direct = {('t', 'h'): 'th', ('S', 't'): 'St', ('t', 'r'): 'tr', ('r', 'e'): 're', ('e', 'e'): 'ee',
              ('e', 't'): 'et', ('t', ','): 't,'}
    def dgap(a, b):
        vals = [g for x, y, sp, g in obs if x == a and y == b and not sp]
        return float(np.median(vals)) if vals else Rh[a] + Lh[b]

    # glyph list: (char, kind, payload)
    seq = []
    def lab(ch, key, line=0, nth=0):
        i, base_s, k = pick(key, line, ch, nth); seq.append((ch, 'label', (i, base_s, k)))
    def asu(ch):
        seq.append((ch, 'asul', None))
    asu('6'); asu('8'); seq.append((' ', 'space', None))
    lab('S', 'p_stor_text'); seq.append(('E', 'E', None)); seq.append((' ', 'space', None))
    asu('6'); lab('t', 'dist1'); lab('h', 'p_fda_text'); seq.append((' ', 'space', None))
    lab('S', 'p_stor_text'); lab('t', 'dist1'); lab('r', 'dist1'); lab('e', 'dist1'); lab('e', 'dist1', nth=1)
    lab('t', 'dist1', nth=1); lab(',', 'dist2'); seq.append((' ', 'space', None))

    F_id, _, _ = pick('dist2', 0, 'F'); L_id, _, _ = pick('dist2', 0, 'L')
    Fb, Lb = ink(src, pl, [F_id]), ink(src, pl, [L_id])

    def lsb(ch):
        if ch in '68': return asul_lr(ch)[0]
        if ch == 'S': return L_S
        if ch == 'E': return Lh['F']
        return Lh[ch]
    def rsb(ch):
        if ch in '68': return asul_lr(ch)[1]
        if ch == 'E': return Rh['L'] if (Lb[2] - Lb[0]) >= (Fb[2] - Fb[0]) else Rh['F']
        return Rh[ch]

    x = None; prev = None; spaced = False; placed = []
    for ch, kind, pay in seq:
        if kind == 'space':
            spaced = True; continue
        if prev is None:
            xl = margin + lsb(ch)
        else:
            if not spaced and (prev, ch) in direct:
                g = dgap(prev, ch)
            else:
                g = rsb(prev) + lsb(ch) + (Sh if spaced else 0.0)
            xl = x + g
        if kind == 'asul':
            cons, w = asul_thin(gs, cmap[ord(ch)], sa, xl, base2, THIN)
            extra.append((m_id, '/CS1', cons))
        elif kind == 'label':
            i, base_s, k = pay
            b = ink(src, pl, [i])
            Aff = (k, k, xl - k * b[0], base2 - k * base_s)
            clones.append((i, compose(Aff, pl.tf(i)), None))
            w = k * (b[2] - b[0])
        elif kind == 'E':
            for gid, gb in ((F_id, Fb), (L_id, Lb)):
                Aff = (1.0, 1.0, xl - gb[0], 0.0)
                clones.append((gid, compose(Aff, pl.tf(gid)), None))
            w = max(Fb[2] - Fb[0], Lb[2] - Lb[0])
        placed.append((ch, xl, xl + w))
        x = xl + w; prev = ch; spaced = False
    # the existing "Miami, FL 33131 • luciddaily.com" moves right to follow the comma + space
    new_M = x + Rh[','] + Sh + Lh['M']
    dx = new_M - m_box[0]
    pl.shift(d2['ids'], dx, 0.0)
    line_end = ink(src, pl, d2['ids'])[2]
    info.update(margin=margin, asul_em_mm=sa * upm, space_h=Sh, L_S=L_S, shift_line2=dx, line2_end=line_end,
                placed=placed, base2=base2)
    return pl, clones, extra, info


def build(out_pdf, out_png=None, dpi=300):
    src = Source('src.pdf')
    pl, clones, extra, info = make(src)
    build_pdf(src, pl, out_pdf, title='TESTIDE label - final', recolor=RECOLOR, drop_ids=list(DASH) + [PERIOD],
              clones=clones, extra=extra)
    if out_png:
        render(out_pdf, out_png, zoom=dpi / 72.0)
    return info


if __name__ == '__main__':
    import json, sys
    out = sys.argv[1] if len(sys.argv) > 1 else 'finalD/TESTIDE_Final_Proof_Clean.pdf'
    import os; os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    info = build(out)
    for k, v in info.items():
        print(k, v if not isinstance(v, float) else round(v, 4))
