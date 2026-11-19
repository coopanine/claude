"""
precise.py - exact measurements for the TESTIDE artwork.

  * exact ink bounds of every subpath (cubic Bezier extrema, not control-point boxes)
  * flat baseline / flat cap top of a text row (most common flat glyph edge; round-letter overshoot
    and descenders excluded)
  * refine(src, pl): re-solves the Protocol stack with these exact metrics so the seven equal gaps and the
    WARNING/STORAGE baseline-to-text gaps are exactly equal, and centres the POWERED BY text in its frame.
    Every move is a pure vertical translation of a whole text group (all well under 0.05 mm).
"""
import math
from labelkit import PT, X0, YTOP, ELEMENTS as E


def _ext(p0, p1, p2, p3):
    vals = [p0, p3]
    d0, d1, d2 = p1 - p0, p2 - p1, p3 - p2
    A, B, C = d0 - 2 * d1 + d2, 2 * (d1 - d0), d0
    ts = []
    if abs(A) < 1e-12:
        if abs(B) > 1e-12:
            ts.append(-C / B)
    else:
        disc = B * B - 4 * A * C
        if disc >= 0:
            r = math.sqrt(disc)
            ts += [(-B + r) / (2 * A), (-B - r) / (2 * A)]
    for t in ts:
        if 0.0 < t < 1.0:
            m = 1 - t
            vals.append(m ** 3 * p0 + 3 * m * m * t * p1 + 3 * m * t * t * p2 + t ** 3 * p3)
    return min(vals), max(vals)


def subpaths_src(src, i, flags=False):
    """exact (l, t, r, b) of each subpath of source object i, in SOURCE label mm.
    flags=True adds (flat_top, flat_bottom): whether the subpath's top / bottom edge is a horizontal segment"""
    o = src.objs[i]
    e, f = o['ctm'][4], o['ctm'][5]

    def mm(x, y):
        return ((x + e - X0) / PT, (YTOP - (y + f)) / PT)

    out, cur = [], None
    st = {'bx': None, 'flat': []}

    def add(x0, x1, y0, y1):
        b = st['bx']
        st['bx'] = [x0, y0, x1, y1] if b is None else [min(b[0], x0), min(b[1], y0), max(b[2], x1), max(b[3], y1)]

    def flush():
        b = st['bx']
        if b is not None:
            if flags:
                ft = any(abs(v - b[1]) < 1e-4 for v in st['flat'])
                fb = any(abs(v - b[3]) < 1e-4 for v in st['flat'])
                out.append((b[0], b[1], b[2], b[3], ft, fb))
            else:
                out.append(tuple(b))
        st['bx'], st['flat'] = None, []

    for k in range(o['start'], o['end']):
        ins = src.ops[k]
        op = str(ins.operator)
        a = [float(v) for v in ins.operands]
        if op == 'm':
            flush()
            cur = mm(a[0], a[1]); add(cur[0], cur[0], cur[1], cur[1])
        elif op == 'l':
            p = mm(a[0], a[1]); add(min(cur[0], p[0]), max(cur[0], p[0]), min(cur[1], p[1]), max(cur[1], p[1]))
            if abs(p[1] - cur[1]) < 1e-6 and abs(p[0] - cur[0]) > 1e-4:
                st['flat'].append(p[1])
            cur = p
        elif op in ('c', 'v', 'y'):
            if op == 'c':
                p1, p2, p3 = mm(a[0], a[1]), mm(a[2], a[3]), mm(a[4], a[5])
            elif op == 'v':
                p1, p2, p3 = cur, mm(a[0], a[1]), mm(a[2], a[3])
            else:
                p1, p2, p3 = mm(a[0], a[1]), mm(a[2], a[3]), mm(a[2], a[3])
            xl, xh = _ext(cur[0], p1[0], p2[0], p3[0])
            yl, yh = _ext(cur[1], p1[1], p2[1], p3[1])
            add(xl, xh, yl, yh)
            if max(cur[1], p1[1], p2[1], p3[1]) - min(cur[1], p1[1], p2[1], p3[1]) < 1e-6 and abs(p3[0] - cur[0]) > 1e-4:
                st['flat'].append(p3[1])
            cur = p3
        elif op == 're':
            flush()
            p, q = mm(a[0], a[1]), mm(a[0] + a[2], a[1] + a[3])
            r = (min(p[0], q[0]), min(p[1], q[1]), max(p[0], q[0]), max(p[1], q[1]))
            out.append(r + (True, True) if flags else r)
    flush()
    return out


def subpaths(src, pl, ids):
    """exact subpath bounds after the placer transforms, label mm"""
    res = []
    for i in ids:
        sx, sy, tx, ty = pl.tf(i)
        for (l, t, r, b) in subpaths_src(src, i):
            res.append((sx * l + tx, sy * t + ty, sx * r + tx, sy * b + ty))
    return res


def ink(src, pl, ids):
    s = subpaths(src, pl, ids)
    return (min(b[0] for b in s), min(b[1] for b in s), max(b[2] for b in s), max(b[3] for b in s))


def _clusters(vals, tol=0.004):
    vals = sorted(vals)
    groups = [[vals[0]]]
    for v in vals[1:]:
        if v - groups[-1][-1] <= tol:
            groups[-1].append(v)
        else:
            groups.append([v])
    return groups


def flat_edges(src, pl, ids, which='bottom', line='only', tol=0.004, min_count=2):
    """flat baseline ('bottom') or flat top ('top') of a row, from glyph contours whose bottom / top edge is a
    horizontal segment (round-letter overshoot, descenders, dots and counters excluded).
    line='last' -> lowest line of a multi-line block, 'first' -> top line"""
    vals = []
    for i in ids:
        sx, sy, tx, ty = pl.tf(i)
        for (l, t, r, b, ft, fb) in subpaths_src(src, i, flags=True):
            if which == 'bottom' and fb:
                vals.append(sy * b + ty)
            elif which == 'top' and ft:
                vals.append(sy * t + ty)
    groups = [g for g in _clusters(vals, tol) if len(g) >= min_count]
    if line == 'only':
        g = max(groups, key=len)
    else:
        big = max(len(g) for g in groups)
        cand = [g for g in groups if len(g) >= max(min_count, 0.25 * big)]
        g = (max if line == 'last' else min)(cand, key=lambda g: sum(g) / len(g))
    return sum(g) / len(g)


def flat_top_first(src, pl, ids, band=0.3, tol=0.001):
    """top of the first line of a text block, read on the ascenders / capitals: the most common glyph top within
    `band` mm of the ink top (a lone arched f or round overshoot does not count)"""
    top = ink(src, pl, ids)[1]
    vals = []
    for i in ids:
        sx, sy, tx, ty = pl.tf(i)
        for (l, t, r, b) in subpaths_src(src, i):
            y = sy * t + ty
            if y <= top + band:
                vals.append(y)
    g = max(_clusters(vals, tol), key=lambda g: (len(g), -sum(g) / len(g)))   # most common; tie -> higher
    return sum(g) / len(g)


# ------------------------------------------------------------------------------------------------
def protocol_metrics(src, pl, box_half=0.98 * 25.4 / 72 / 2, fda_half=0.471 * 25.4 / 72 / 2):
    from labelkit import Source  # noqa
    M = {}
    pb = ink(src, pl, E['p_box'])                      # stroke centre path (rect)
    M['inner_top'] = pb[1] + box_half
    M['inner_bot'] = pb[3] - box_half
    M['title_top'] = flat_edges(src, pl, E['p_title'], 'top')
    M['title_base'] = flat_edges(src, pl, E['p_title'], 'bottom')
    M['dir_top'] = flat_edges(src, pl, E['p_dir'], 'top')
    M['dir_base'] = flat_edges(src, pl, E['p_dir'], 'bottom')
    n = ink(src, pl, E['p_num']); M['num_top'], M['num_bot'] = n[1], n[3]
    M['steps_top'] = flat_top_first(src, pl, E['p_steps'])
    M['steps_base'] = flat_edges(src, pl, E['p_steps'], 'bottom', line='last')
    M['warn_top'] = flat_edges(src, pl, E['p_warn'], 'top')
    M['warn_base'] = flat_edges(src, pl, E['p_warn'], 'bottom')
    M['body_top'] = flat_top_first(src, pl, E['p_body'])
    M['body_base'] = flat_edges(src, pl, E['p_body'], 'bottom', line='last')
    M['stor_top'] = flat_edges(src, pl, E['p_stor'], 'top')
    M['stor_base'] = flat_edges(src, pl, E['p_stor'], 'bottom')
    M['stxt_top'] = flat_top_first(src, pl, E['p_stor_text'])
    M['stxt_base'] = flat_edges(src, pl, E['p_stor_text'], 'bottom')
    fd = ink(src, pl, E['p_fda_box']); M['fda_top'], M['fda_bot'] = fd[1] - fda_half, fd[3] + fda_half
    up = ink(src, pl, E['upc']); M['upc_top'], M['upc_bot'] = up[1], up[3]
    return M


ORDER = [  # (gap name, top key of next element, bottom key of next element, element ids to move)
    ('a', 'title_top', 'title_base', 'p_title'),
    ('b', 'dir_top', 'dir_base', 'p_dir'),
    ('c', 'num_top', 'num_bot', 'p_num'),
    ('d', 'steps_top', 'steps_base', 'p_steps'),
    ('e', 'warn_top', 'warn_base', 'p_warn'),
    ('f', 'body_top', 'body_base', 'p_body'),
    ('g', 'stor_top', 'stor_base', 'p_stor'),
    ('h', 'stxt_top', 'stxt_base', 'p_stor_text'),
    ('i', 'fda_top', 'fda_bot', ('p_fda_box', 'p_fda_text')),
    ('j', 'upc_top', 'upc_bot', 'upc'),
]


def gaps_of(M):
    prev, out = M['inner_top'], {}
    for g, tk, bk, _ in ORDER:
        out[g] = M[tk] - prev
        prev = M[bk]
    out['k'] = M['inner_bot'] - prev
    return out


def refine(src, pl, **metrics_kw):
    """re-solve the Protocol stack on exact metrics; centre the POWERED BY text in its frame"""
    # 1. POWERED BY text: centre its ink box vertically in the frame's outer box
    fr, tx = ink(src, pl, E['powered_frame']), ink(src, pl, E['powered_text'])
    pl.shift(E['powered_text'], 0.0, (fr[1] + fr[3]) / 2 - (tx[1] + tx[3]) / 2)
    # 2. Protocol stack
    M = protocol_metrics(src, pl, **metrics_kw)
    G0 = gaps_of(M)
    fixed = {'c': G0['c'], 'd': G0['d'], 'f': G0['f'], 'h': G0['f']}       # STORAGE->text = WARNING->text
    heights = {g: M[bk] - M[tk] for g, tk, bk, _ in ORDER}
    inner = M['inner_bot'] - M['inner_top']
    eq = (inner - sum(heights.values()) - sum(fixed.values())) / 7.0
    y = M['inner_top']
    moves = {}
    for g, tk, bk, grp in ORDER:
        y += fixed.get(g, eq)
        dy = y - M[tk]
        grps = grp if isinstance(grp, tuple) else (grp,)
        for gname in grps:
            pl.shift(E[gname], 0.0, dy)
        moves[g] = dy
        y += heights[g]
    return {'equal_gap': eq, 'fixed': fixed, 'moves': moves, 'before': G0}
