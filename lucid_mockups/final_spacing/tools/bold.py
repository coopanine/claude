"""
bold.py - FDA disclaimer in bold (outline bold: each glyph filled + stroked in its own ink, width W mm).
Letters are re-spaced by W per glyph so the visual gaps stay as set; the three lines are re-broken to fit the box
and centred on it. Baselines, box and the Protocol stack do not move.
"""
from itertools import combinations
from labelkit import ELEMENTS as E
from precise import ink, flat_edges
from glyphmap import charmap
import spacing

K_FDA = 0.964          # FDA text size / Distributed-by size (spacing model is at the Distributed-by size)


def words_of(src, pl):
    res, B = charmap(src, pl, 'p_fda_text')
    out = []
    for li, r in enumerate(res):
        base = flat_edges(src, pl, r['ids'], 'bottom')
        for w in r['words']:
            out.append({'ids': [r['ids'][k] for k in w], 'chars': ''.join(r['chars'][k] for k in w), 'line': li, 'base': base})
    return out


def word_gap(src, pl, a, b, model):
    """regular ink-to-ink gap between word a and the next word b (measured if they were neighbours, else modelled)"""
    if a['line'] == b['line']:
        return ink(src, pl, [b['ids'][0]])[0] - ink(src, pl, [a['ids'][-1]])[2]
    L, R, S = model
    return K_FDA * (R[a['chars'][-1]] + S + L[b['chars'][0]])


def plan(src, pl, W, box_inner, centre, n_lines=3, prefer=None):
    words = words_of(src, pl)
    L, R, S, _, _ = spacing.solve(src, pl)
    model = (L, R, S)
    widths = []           # bold ink width of each word (stroke adds W/2 at each end, W per extra glyph)
    for w in words:
        b = ink(src, pl, w['ids']); widths.append((b[2] - b[0]) + W * len(w['ids']))
    gaps = [word_gap(src, pl, a, b, model) for a, b in zip(words, words[1:])]
    n = len(words)
    best = []
    for cuts in combinations(range(1, n), n_lines - 1):
        lines = [list(range(s, e)) for s, e in zip((0,) + cuts, cuts + (n,))]
        lw = [sum(widths[k] for k in ln) + sum(gaps[k] for k in ln[:-1]) for ln in lines]
        if max(lw) > box_inner:
            continue
        best.append((max(lw), lw, cuts, [' '.join(words[k]['chars'] for k in ln) for ln in lines]))
    best.sort()
    return words, widths, gaps, best


def apply(src, pl, W, cuts, centre):
    """shift every FDA glyph to its bold position for the given line breaks; returns {id: W} for build_pdf(embolden=)"""
    words = words_of(src, pl)
    L, R, S, _, _ = spacing.solve(src, pl)
    model = (L, R, S)
    gaps = [word_gap(src, pl, a, b, model) for a, b in zip(words, words[1:])]
    b0 = sorted(set(w['base'] for w in words))
    pitch = (b0[-1] - b0[0]) / (len(b0) - 1)
    n = len(words)
    lines = [list(range(s, e)) for s, e in zip((0,) + tuple(cuts), tuple(cuts) + (n,))]
    bases = [b0[0] + li * pitch for li in range(len(lines))]
    moves = {}
    for li, ln in enumerate(lines):
        # positions relative to the line's (bold) ink left = 0
        x = 0.0; place = []
        for j, k in enumerate(ln):
            w = words[k]
            first_left = ink(src, pl, [w['ids'][0]])[0]
            for g, gid in enumerate(w['ids']):
                b = ink(src, pl, [gid])
                # regular glyph left relative to word's first glyph, + W per preceding glyph, + W/2 for the stroke
                place.append((gid, x + (b[0] - first_left) + g * W + W / 2, w['base']))
            wb = ink(src, pl, w['ids'])
            x += (wb[2] - wb[0]) + W * len(w['ids'])
            if j < len(ln) - 1:
                x += gaps[k]
        left = centre - x / 2
        for gid, rel, base in place:
            b = ink(src, pl, [gid])
            moves[gid] = (left + rel - b[0], bases[li] - base)
    for gid, (dx, dy) in moves.items():
        pl.shift([gid], dx, dy)
    return {gid: W for gid in moves}, lines, pitch


def expand(src, pl, ids, W, tol=0.0003):
    """outline bold as plain filled outlines (strokes expanded): each glyph's final outline grown by W/2 with round
    corners (exactly fill + round-join stroke of width W). Returns {id: contours in final label mm}"""
    from fontrank import label_polys, PX
    from shapely.geometry import Polygon
    from shapely.geometry.polygon import orient
    out = {}
    for i in ids:
        g = None
        for p in label_polys(src, pl, i):
            if len(p) < 3:
                continue
            q = Polygon([(x / PX, y / PX) for x, y in p]).buffer(0)
            g = q if g is None else g.symmetric_difference(q)
        e = g.buffer(W / 2, quad_segs=16, join_style='round').simplify(tol)
        cons = []
        for pg in ([e] if e.geom_type == 'Polygon' else list(e.geoms)):
            pg = orient(pg, 1.0)
            for ring in [pg.exterior] + list(pg.interiors):
                c = list(ring.coords)[:-1]
                cons.append([('m', c[0])] + [('l', q) for q in c[1:]] + [('h',)])
        out[i] = cons
    return out
