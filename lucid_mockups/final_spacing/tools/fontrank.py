import sys, glob, numpy as np
from PIL import Image, ImageDraw
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.basePen import decomposeQuadraticSegment
from labelkit import Source, ELEMENTS as E, PT, X0, YTOP
from final_c import make
from precise import ink, flat_edges
PX = 100.0

def flatten(pen_value, P):
    polys, cur, last = [], [], None
    for op, a in pen_value:
        if op == 'moveTo':
            if cur: polys.append(cur)
            cur = [P(a[0])]; last = a[0]
        elif op == 'lineTo':
            cur.append(P(a[0])); last = a[0]
        elif op == 'curveTo':
            p0 = last; p1, p2, p3 = a
            for i in range(1, 17):
                t = i / 16; m = 1 - t
                cur.append(P((m**3*p0[0] + 3*m*m*t*p1[0] + 3*m*t*t*p2[0] + t**3*p3[0],
                              m**3*p0[1] + 3*m*m*t*p1[1] + 3*m*t*t*p2[1] + t**3*p3[1])))
            last = p3
        elif op == 'qCurveTo':
            pts = list(a)
            if pts[-1] is None:   # closed contour of off-curve points only
                pts = pts[:-1]
            for (c, on) in decomposeQuadraticSegment(pts):
                p0 = last
                for i in range(1, 13):
                    t = i / 12; m = 1 - t
                    cur.append(P((m*m*p0[0] + 2*m*t*c[0] + t*t*on[0], m*m*p0[1] + 2*m*t*c[1] + t*t*on[1])))
                last = on
        elif op in ('closePath', 'endPath'):
            if cur: polys.append(cur); cur = []
    if cur: polys.append(cur)
    return polys

def raster(polys, x0, y0, size):
    acc = np.zeros(size[::-1], bool)
    for poly in polys:
        if len(poly) < 3: continue
        im = Image.new('1', size, 0)
        ImageDraw.Draw(im).polygon([(x - x0 * PX, y - y0 * PX) for x, y in poly], fill=1)
        acc ^= np.array(im, bool)
    return acc

def label_polys(src, pl, i):
    o = src.objs[i]; e, fo = o['ctm'][4], o['ctm'][5]
    sx, sy, tx, ty = pl.tf(i)
    rec = []
    for k in range(o['start'], o['end']):
        ins = src.ops[k]; op = str(ins.operator); a = [float(v) for v in ins.operands]
        if op == 'm': rec.append(('moveTo', [(a[0], a[1])]))
        elif op == 'l': rec.append(('lineTo', [(a[0], a[1])]))
        elif op == 'c': rec.append(('curveTo', [(a[0], a[1]), (a[2], a[3]), (a[4], a[5])]))
        elif op == 'v': rec.append(('curveTo', [None, (a[0], a[1]), (a[2], a[3])]))
        elif op == 'y': rec.append(('curveTo', [(a[0], a[1]), (a[2], a[3]), (a[2], a[3])]))
        elif op == 'h': rec.append(('closePath', []))
    # resolve 'v' (first control = current point)
    last = None; out = []
    for op, a in rec:
        if op == 'curveTo' and a[0] is None: a = [last] + a[1:]
        if a: last = a[-1]
        out.append((op, a))
    def P(p):
        xm = (p[0] + e - X0) / PT; ym = (YTOP - (p[1] + fo)) / PT
        return ((sx * xm + tx) * PX, (sy * ym + ty) * PX)
    return flatten(out, P)

def score(font_path, src, pl, text, ids):
    f = TTFont(font_path); gs = f.getGlyphSet(); cmap = f.getBestCmap(); upm = f['head'].unitsPerEm
    base = flat_edges(src, pl, ids, 'bottom')
    D = ink(src, pl, [ids[0]]); capD = base - D[1]
    bp = BoundsPen(gs); gs[cmap[ord(text[0])]].draw(bp)
    s = capD / ((bp.bounds[3] - bp.bounds[1]) / upm)
    res = []
    for ch, i in zip(text, ids):
        g = cmap.get(ord(ch))
        if g is None: res.append((ch, 0.0)); continue
        b = ink(src, pl, [i])
        bp = BoundsPen(gs); gs[g].draw(bp)
        if bp.bounds is None: res.append((ch, 0.0)); continue
        ox = b[0] - bp.bounds[0] / upm * s
        pen = RecordingPen(); gs[g].draw(pen)
        fp = flatten(pen.value, lambda p: ((ox + p[0] / upm * s) * PX, (base - p[1] / upm * s) * PX))
        lp = label_polys(src, pl, i)
        x0, y0 = b[0] - 0.3, b[1] - 0.4
        size = (int((b[2] - b[0] + 0.8) * PX), int((b[3] - b[1] + 0.8) * PX))
        A, B = raster(lp, x0, y0, size), raster(fp, x0, y0, size)
        res.append((ch, (A & B).sum() / max(1, (A | B).sum())))
    return float(np.mean([r[1] for r in res])), res, s

if __name__ == '__main__':
    src = Source('src.pdf'); pl, geo = make(src, 'thirds')
    text = 'DistributedbyLucidMetabolicLabs,Inc.'
    ids = E['dist1']
    paths = sys.argv[1:]
    rows = []
    for p in paths:
        try:
            m, res, s = score(p, src, pl, text, ids)
            rows.append((m, p.split('/')[-1], s))
        except Exception as ex:
            rows.append((0, p.split('/')[-1] + ' ERR ' + str(ex)[:60], 0))
    for m, n, s in sorted(rows, reverse=True):
        print(f'{m:.3f}  {n}  em {s:.3f} mm')
