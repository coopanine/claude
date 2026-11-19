"""rank candidate fonts against outlined label text, allowing horizontal scaling (fits sx from glyph widths)"""
import sys, glob, numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen
from labelkit import Source, ELEMENTS as E
from final_c import make
from precise import ink, flat_edges
from fontrank import flatten, raster, label_polys, PX

LINES = {
 'other': [('OtherIngredients:Hydroxypropylmethylcellulose', list(range(473, 518)), 5),
           ('(vegetablecapsule).L-leucine.', list(range(518, 547)), 19)],
 'dist':  [('DistributedbyLucidMetabolicLabs,Inc.', None, 0), ('Miami,FL33131\u2022luciddaily.com', None, 0)],
}

def load(path):
    f = TTFont(path); return f, f.getGlyphSet(), f.getBestCmap(), f['head'].unitsPerEm

def gb(gs, g):
    bp = BoundsPen(gs); gs[g].draw(bp); return bp.bounds

def score(path, src, pl, lines, fit_x=True, skip=':'):
    f, gs, cmap, upm = load(path)
    # vertical scale from the cap reference of the first line
    text, ids, ci = lines[0]
    base = flat_edges(src, pl, ids, 'bottom')
    cap_lab = base - ink(src, pl, [ids[ci]])[1]
    b = gb(gs, cmap[ord(text[ci])]); sy = cap_lab / ((b[3] - b[1]) / upm)
    # horizontal scale from ink widths (median ratio)
    ratios = []
    for text, ids, ci in lines:
        for ch, i in zip(text, ids):
            g = cmap.get(ord(ch))
            if g is None or ch in skip + '.,-()\u2022': continue
            fb = gb(gs, g); lb = ink(src, pl, [i])
            if fb and fb[2] > fb[0]: ratios.append((lb[2] - lb[0]) / ((fb[2] - fb[0]) / upm))
    sx = float(np.median(ratios)) if fit_x else sy
    res = []
    for text, ids, ci in lines:
        base = flat_edges(src, pl, ids, 'bottom')
        for ch, i in zip(text, ids):
            if ch in skip: continue
            g = cmap.get(ord(ch))
            if g is None: res.append((ch, 0.0)); continue
            lb = ink(src, pl, [i]); fb = gb(gs, g)
            if fb is None: res.append((ch, 0.0)); continue
            ox = lb[0] - fb[0] / upm * sx
            pen = RecordingPen(); gs[g].draw(pen)
            fp = flatten(pen.value, lambda p: ((ox + p[0] / upm * sx) * PX, (base - p[1] / upm * sy) * PX))
            lp = label_polys(src, pl, i)
            x0, y0 = lb[0] - 0.3, lb[1] - 0.4
            size = (int((lb[2] - lb[0] + 0.8) * PX), int((lb[3] - lb[1] + 0.8) * PX))
            A, B = raster(lp, x0, y0, size), raster(fp, x0, y0, size)
            res.append((ch, (A & B).sum() / max(1, (A | B).sum())))
    return float(np.mean([r[1] for r in res])), res, sx, sy

if __name__ == '__main__':
    which = sys.argv[1]; paths = sys.argv[2:]
    src = Source('src.pdf'); pl, geo = make(src, 'thirds')
    if which == 'dist':
        from glyphmap import charmap
        L = []
        for key in ('dist1', 'dist2'):
            r = charmap(src, pl, key)[0][0]
            L.append((''.join(r['chars']), r['ids'], 0))
        LINES['dist'] = L
    rows = []
    fitx = '--fitx' in paths; paths = [p for p in paths if p != '--fitx']
    for p in paths:
        try:
            m, res, sx, sy = score(p, src, pl, LINES[which], fit_x=fitx)
            d = {}
            for ch, v in res: d.setdefault(ch, []).append(v)
            dig = sum(d.get('3', [0]) + d.get('1', [0])) / max(1, len(d.get('3', [])) + len(d.get('1', [])))
            rows.append((m, p.split('/')[-1] + f'  digits {dig:.3f}', sx, sy))
        except Exception as ex:
            rows.append((0, p.split('/')[-1] + ' ERR ' + str(ex)[:50], 0, 1))
    for m, n, sx, sy in sorted(rows, reverse=True)[:25]:
        print(f'{m:.3f}  {n:50s} sy(em) {sy:.3f} mm  x-scale {sx/sy*100:5.1f}%')
