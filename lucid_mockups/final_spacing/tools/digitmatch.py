import sys, glob, numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen
from labelkit import Source
from final_c import make
from precise import ink, flat_edges
from fontrank import flatten, raster, label_polys, PX
from glyphmap import charmap

def glyph_polys(gs, g, upm, s, ox, base):
    pen = RecordingPen(); gs[g].draw(pen)
    return flatten(pen.value, lambda p: ((ox + p[0] / upm * s) * PX, (base - p[1] / upm * s) * PX))

def gname(f, ch, lf=True):
    cmap = f.getBestCmap(); g = cmap[ord(ch)]
    if lf and g + '.lf' in f.getGlyphOrder(): g = g + '.lf'
    return g

def run(paths):
    src = Source('src.pdf'); pl, geo = make(src, 'thirds')
    r = charmap(src, pl, 'dist2')[0][0]
    base = flat_edges(src, pl, r['ids'], 'bottom')
    digs = [(c, i) for c, i in zip(r['chars'], r['ids']) if c in '31']
    i3 = [i for c, i in digs if c == '3'][0]
    b3 = ink(src, pl, [i3]); h3 = b3[3] - b3[1]
    lab_area = {}
    out = []
    for p in paths:
        f = TTFont(p); gs = f.getGlyphSet(); upm = f['head'].unitsPerEm
        bp = BoundsPen(gs); gs[gname(f, '3')].draw(bp); fb = bp.bounds
        s = h3 / ((fb[3] - fb[1]) / upm)
        ious, arat = [], []
        for c, i in digs:
            g = gname(f, c); bp = BoundsPen(gs); gs[g].draw(bp); fb = bp.bounds
            lb = ink(src, pl, [i])
            ox = lb[0] - fb[0] / upm * s
            oy = lb[3] + fb[1] / upm * s         # align ink bottoms
            fp = glyph_polys(gs, g, upm, s, ox, oy)
            lp = label_polys(src, pl, i)
            x0, y0 = lb[0] - 0.3, lb[1] - 0.4
            size = (int((lb[2] - lb[0] + 0.8) * PX), int((lb[3] - lb[1] + 0.8) * PX))
            A, B = raster(lp, x0, y0, size), raster(fp, x0, y0, size)
            ious.append((A & B).sum() / max(1, (A | B).sum())); arat.append(B.sum() / max(1, A.sum()))
        out.append((float(np.mean(ious)), p.split('/')[-1], float(np.mean(arat)), s))
    for m, n, a, s in sorted(out, reverse=True):
        print(f'{m:.3f}  {n:45s} ink-area ratio {a:.2f}  em {s:.3f} mm')

if __name__ == '__main__':
    run(sys.argv[1:])
