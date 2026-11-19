"""
protocol2.py - Protocol panel re-set (rev6): every text element except the FDA box gets bigger, the WARNING paragraph is
re-broken, the Directions columns are re-spaced, and the vertical stack is re-solved. The FDA box and its text keep their
size, weight and width (they only move vertically with the stack).

All moves are uniform scales / translations of the label's own outlined glyphs (letter spacing scales with the size).
Units: label mm (x right, y down).
"""
from itertools import combinations
from labelkit import ELEMENTS as E
from precise import ink, flat_edges, protocol_metrics, ORDER
from glyphmap import lines_of, charmap, TEXTS
import spacing

TEXTS.update({
    'p_steps': ['Three capsules With food, For ninety', 'each morning every day days'],
    'p_body': ['For adult men only. Consult your physician before', 'use if you have a medical condition or take',
               'medication. Do not use if seal is broken. Keep out', 'of reach of children.'],
})
K_BODY = 1.0498            # WARNING paragraph size / Distributed-by size (spacing model size)
PANEL_CX = None            # set from the panel frame at run time


def _scale_about(pl, ids, s, ox, oy):
    pl.affine(list(ids), s, s, ox - s * ox, oy - s * oy)


def _segments(src, pl, ids, gap=1.5):
    """split each text line of a group into horizontal segments (columns) separated by > gap"""
    rows, B = lines_of(src, pl, list(ids))
    out = []
    for r in rows:
        segs, cur = [], [r[0]]
        for a, b in zip(r, r[1:]):
            if B[b][0] - B[a][2] > gap:
                segs.append(cur); cur = [b]
            else:
                cur.append(b)
        segs.append(cur)
        out.append(segs)
    return out


def scale_line(src, pl, ids, s, cx_new):
    """single-line group: scale about its ink centre / baseline, then centre on cx_new"""
    b = ink(src, pl, ids); base = flat_edges(src, pl, ids, 'bottom', min_count=1)
    cx = (b[0] + b[2]) / 2
    _scale_about(pl, ids, s, cx, base)
    pl.shift(ids, cx_new - cx, 0.0)


def body_words(src, pl):
    res, B = charmap(src, pl, 'p_body')
    words = []
    for li, r in enumerate(res):
        base = flat_edges(src, pl, r['ids'], 'bottom')
        for w in r['words']:
            words.append({'ids': [r['ids'][k] for k in w], 'chars': ''.join(r['chars'][k] for k in w), 'line': li,
                          'base': base})
    return words


def body_metrics(src, pl, model):
    words = body_words(src, pl)
    L, R, S = model
    widths, gaps = [], []
    for w in words:
        b = ink(src, pl, w['ids']); widths.append(b[2] - b[0])
    for a, b in zip(words, words[1:]):
        if a['line'] == b['line']:
            gaps.append(ink(src, pl, [b['ids'][0]])[0] - ink(src, pl, [a['ids'][-1]])[2])
        else:
            gaps.append(K_BODY * (R[a['chars'][-1]] + S + L[b['chars'][0]]))
    return words, widths, gaps


def body_breaks(src, pl, s, measure, n_lines, model, top=8):
    """candidate line breaks for the WARNING paragraph at scale s within `measure` (ink width), best first"""
    words, widths, gaps = body_metrics(src, pl, model)
    n = len(words)
    out = []
    for cuts in combinations(range(1, n), n_lines - 1):
        lines = [list(range(a, b)) for a, b in zip((0,) + cuts, cuts + (n,))]
        lw = [s * (sum(widths[k] for k in ln) + sum(gaps[k] for k in ln[:-1])) for ln in lines]
        mx = max(lw)
        if mx > measure:
            continue
        last = lw[-1]
        rag = sum((mx - w) ** 2 for w in lw[:-1])
        widow = 8.0 if len(lines[-1]) == 1 else 0.0
        short = 6.0 if last < 0.4 * mx else 0.0
        # reward line ends at sentence ends, penalise ending a line on a short function word
        ends = [words[ln[-1]]['chars'] for ln in lines[:-1]]
        punct = -1.5 * sum(e.endswith('.') for e in ends)
        weak = 2.0 * sum(e.lower() in ('a', 'if', 'or', 'of', 'do', 'not', 'use', 'your', 'for', 'is') for e in ends)
        out.append((rag + widow + short + punct + weak, mx, lw, cuts,
                    [' '.join(words[k]['chars'] for k in ln) for ln in lines]))
    out.sort(key=lambda t: t[0])
    return out[:top]


def body_apply(src, pl, s, cuts, cx, model):
    words, widths, gaps = body_metrics(src, pl, model)
    L, R, S = model
    bases = sorted(set(w['base'] for w in words))
    pitch = (bases[-1] - bases[0]) / (len(bases) - 1)
    n = len(words)
    lines = [list(range(a, b)) for a, b in zip((0,) + tuple(cuts), tuple(cuts) + (n,))]
    for li, ln in enumerate(lines):
        # advance-box width (centred like set type: ink + the first glyph's lsb + the last glyph's rsb)
        ink_w = s * (sum(widths[k] for k in ln) + sum(gaps[k] for k in ln[:-1]))
        lsb = s * K_BODY * L[words[ln[0]]['chars'][0]]
        rsb = s * K_BODY * R[words[ln[-1]]['chars'][-1]]
        x = cx - (lsb + ink_w + rsb) / 2 + lsb
        base_t = bases[0] + li * pitch * s
        for j, k in enumerate(ln):
            w = words[k]
            b = ink(src, pl, w['ids'])
            _scale_about(pl, w['ids'], s, b[0], w['base'])
            pl.shift(w['ids'], x - b[0], base_t - w['base'])
            x += s * widths[k] + (s * gaps[k] if j < len(ln) - 1 else 0.0)
    return lines


def steps_apply(src, pl, s_steps, s_num, D, cx):
    """Directions row: each column (numeral + two lines) scaled about its own centre and moved to cx + (-D, 0, +D)"""
    num = _segments(src, pl, E['p_num'])[0]                       # [I], [I, I], [I, I, I]
    st = _segments(src, pl, E['p_steps'])                          # 2 lines x 3 columns
    num_base = flat_edges(src, pl, E['p_num'], 'bottom', min_count=1)
    base1 = flat_edges(src, pl, sum(st[0], []), 'bottom')
    targets = [cx - D, cx, cx + D]
    for c in range(3):
        nb = ink(src, pl, num[c]); ncx = (nb[0] + nb[2]) / 2
        _scale_about(pl, num[c], s_num, ncx, num_base)
        pl.shift(num[c], targets[c] - ncx, 0.0)
        col = st[0][c] + st[1][c]
        c1 = ink(src, pl, st[0][c]); c2 = ink(src, pl, st[1][c])
        ccx = ((c1[0] + c1[2]) / 2 + (c2[0] + c2[2]) / 2) / 2
        _scale_about(pl, col, s_steps, ccx, base1)
        pl.shift(col, targets[c] - ccx, 0.0)


def restack(src, pl, fixed, fda_half):
    """Protocol stack: the gaps in `fixed` as given, all others equal (7 equal gaps incl. top and bottom margins)"""
    M = protocol_metrics(src, pl, fda_half=fda_half)
    heights = {g: M[bk] - M[tk] for g, tk, bk, _ in ORDER}
    inner = M['inner_bot'] - M['inner_top']
    eq = (inner - sum(heights.values()) - sum(fixed.values())) / 7.0
    y = M['inner_top']
    for g, tk, bk, grp in ORDER:
        y += fixed.get(g, eq)
        dy = y - M[tk]
        for gname in (grp if isinstance(grp, tuple) else (grp,)):
            pl.shift(E[gname], 0.0, dy)
        y += heights[g]
    return eq


def solve_model(src):
    """side-bearing model of the humanist font, solved on the untouched source geometry (3-line FDA text)"""
    from labelkit import Placer
    L, R, S, _, _ = spacing.solve(src, Placer(src))
    return (L, R, S)


def apply(src, pl, P, fda_half):
    """P: dict(title, head, num, steps, body, stor_text, D, measure, n_lines, cuts=None, gaps={c,d,f,h})"""
    pb = ink(src, pl, E['p_box'])
    cx = (pb[0] + pb[2]) / 2
    model = solve_model(src)
    info = {}
    # body breaks first (needs the original word geometry)
    P = dict(P)
    cuts = P.get('cuts')
    s_try = P['body'] if P['body'] != 'fit' else P.get('body_try', 1.16)
    if cuts is None:
        cand = body_breaks(src, pl, s_try, P['measure'], P['n_lines'], model)
        if not cand:
            raise ValueError('WARNING paragraph does not fit %d lines in %.2f mm at x%.3f' % (P['n_lines'], P['measure'], s_try))
        cuts = cand[0][3]
        info['body_lines'] = cand[0][4]
        if P['body'] == 'fit':                    # longest line exactly as wide as the measure (= the FDA box)
            P['body'] = s_try * P['measure'] / cand[0][1]
        info['body_widths'] = [w * P['body'] / s_try for w in cand[0][2]]
    for k in ('head', 'stor_text', 'num', 'steps'):
        if P.get(k) == 'body':
            P[k] = P['body']
    info['scales'] = {k: P[k] for k in ('body', 'head', 'stor_text', 'num', 'steps')}
    body_apply(src, pl, P['body'], cuts, cx, model)
    title_s = P['title']
    if title_s == 'measure':                      # title as wide as the FDA box / WARNING measure
        tb = ink(src, pl, E['p_title']); fb = ink(src, pl, E['p_fda_box'])
        lw_half = fda_half
        title_s = ((fb[2] + lw_half) - (fb[0] - lw_half)) / (tb[2] - tb[0])
    info['title_scale'] = title_s
    scale_line(src, pl, E['p_title'], title_s, cx)
    for k in ('p_dir', 'p_warn', 'p_stor'):
        scale_line(src, pl, E[k], P['head'], cx)
    scale_line(src, pl, E['p_stor_text'], P['stor_text'], cx)
    steps_apply(src, pl, P['steps'], P['num'], P['D'], cx)
    info['equal_gap'] = restack(src, pl, P['gaps'], fda_half)
    info['cuts'] = cuts
    return info
