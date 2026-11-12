"""
v3cap.py - "cap layout" concept built on the approved v2 spacing.

  cap   (y 8.5 to 53.5, the 45 mm zone): TESTIDE + gold tagline + POWERED BY TST-01 badge as one stack,
        centred in the cap zone on the front axis
  body  statue enlarged (uniform scale, bottom edge fixed) so its top sits on the common top line of the
        Supplement Facts and Protocol boxes; rule and bottom text keep the v2 vertical spacing and the rule
        keeps its v2 relationship to the statue width (optional)
  logo  THE LUCID INSTITUTE logo moved to the back of the cap, directly opposite the front axis.
        The back of the tube is the wrap seam (x = 0 / 188), so the logo is printed in two pieces:
        right part at the left end of the sheet, left part at the right end (overlap strip left blank).
  the dashed 'Proposed Cap Line' is removed (cap confirmed at the 45 mm crease)

Nothing else moves. Outlines, inks, stroke weights and the dieline are untouched.
"""
import json, os
from labelkit import Source, build_pdf, render, ELEMENTS, PT
from layout import solve

HERE = os.path.dirname(os.path.abspath(__file__))
CAP_T, CAP_B = 8.4999, 53.5
TOPLINE = 58.324           # outer top edge of the Facts / Protocol box strokes (1.0 pt and 0.98 pt)
WRAP_MM = 188.0
WRAP_PAGE = (0.0, 8.4999, 188.0, 148.1495)
DASH = (9, 10, 11)
GOLD_RULE = {16: '/CS2'}


def make(src, gap_b=5.5, widen_rule=True, logo='back', logo_offset=0.0):
    """returns placer, extra build kwargs (clip / clones), geometry dict"""
    pl, G = solve(src, json.load(open(os.path.join(HERE, 'params_v2.json'))))
    E, fb = ELEMENTS, pl.final_bbox
    ax = G['axis_front'] if isinstance(G.get('axis_front'), float) else 94.936
    geo = {'axis_front': ax}

    # ---- cap stack: TESTIDE / tagline / POWERED BY badge, centred in the 45 mm cap ----
    t, tg, fr = fb(E['testide']), fb(E['tagline']), fb(E['powered_frame'])
    gap_a = tg[1] - t[3]                                   # v2 TESTIDE -> tagline gap, kept
    H = (t[3] - t[1]) + gap_a + (tg[3] - tg[1]) + gap_b + (fr[3] - fr[1])
    y0 = (CAP_T + CAP_B) / 2 - H / 2
    pl.shift(E['testide'], 0.0, y0 - t[1])
    y1 = y0 + (t[3] - t[1]) + gap_a
    pl.shift(E['tagline'], 0.0, y1 - tg[1])
    y2 = y1 + (tg[3] - tg[1]) + gap_b
    pl.shift(E['powered_frame'] + E['powered_text'], 0.0, y2 - fr[1])
    geo.update(cap_stack_top=y0, cap_stack_bottom=y0 + H, cap_margin_top=y0 - CAP_T,
               cap_margin_bottom=CAP_B - (y0 + H), gap_testide_tagline=gap_a, gap_tagline_badge=gap_b)

    # ---- statue: bottom edge fixed, top up to the box top line ----
    st = fb(E['statue'])
    s = (st[3] - TOPLINE) / (st[3] - st[1])
    cx = (st[0] + st[2]) / 2
    pl.place(E['statue'], s, (cx, st[3]), (cx, st[3]))
    st2 = fb(E['statue'])
    geo.update(statue_scale_vs_v2=s, statue=st2)

    # ---- rule + bottom text ----
    ru = fb(E['rule'])
    inset_l, inset_r = ru[0] - st[0], st[2] - ru[2]
    if widen_rule:
        nl, nr = st2[0] + inset_l, st2[2] - inset_r
        k = (nr - nl) / (ru[2] - ru[0])
        pl.affine(E['rule'], k, 1.0, nl - k * ru[0], 0.0)
        g_left, g_right = src.split_x(E['btext'], 3.0)
        bl, br = fb(g_left), fb(g_right)
        pl.shift(g_left, nl - bl[0], 0.0)
        pl.shift(g_right, nr - br[2], 0.0)
    geo.update(rule=fb(E['rule']), btext=fb(E['btext']))

    # ---- Lucid logo on the back of the cap ----
    lg = fb(E['logo'])
    lcx, lcy = (lg[0] + lg[2]) / 2, (lg[1] + lg[3]) / 2
    back = ax + WRAP_MM / 2 - WRAP_MM                     # back point on the left end of the sheet (~0.94)
    cap_mid = (CAP_T + CAP_B) / 2
    extra = {}
    if logo == 'back':
        pl.shift(E['logo'], back + logo_offset - lcx, cap_mid - lcy)
        sx, sy, tx, ty = pl.tf(E['logo'][0])
        big = (-20.0, -20.0, 220.0, 180.0)
        extra['clip'] = {E['logo'][0]: (0.0, big[1], 120.0, big[3])}               # right part, left end of sheet
        extra['clones'] = [(E['logo'][0], (sx, sy, tx + WRAP_MM, ty), (60.0, big[1], WRAP_MM, big[3]))]  # left part
    elif logo == 'front':
        pass
    geo['logo'] = fb(E['logo'])
    geo['logo_center_x_on_wrap'] = (back + logo_offset) % WRAP_MM
    geo['cap_front'] = {'testide': fb(E['testide']), 'tagline': fb(E['tagline']),
                        'badge': fb(E['powered_frame']), 'badge_text': fb(E['powered_text'])}
    return pl, extra, geo


def build_all(out_dir, **kw):
    os.makedirs(out_dir, exist_ok=True)
    src = Source(os.path.join(HERE, 'src.pdf'))
    pl, extra, geo = make(src, **kw)
    flat = os.path.join(out_dir, 'label.pdf')
    build_pdf(src, pl, flat, title='TESTIDE label - cap layout concept', recolor=GOLD_RULE,
              drop_ids=DASH, **extra)
    art = os.path.join(out_dir, 'art.pdf')
    build_pdf(src, pl, art, recolor=GOLD_RULE, page_mm=WRAP_PAGE, keep_mm=(-5, 0, 196, 157),
              drop_layers=('/MC2', '/MC3'), drop_ids=DASH, **extra)
    json.dump(geo, open(os.path.join(out_dir, 'geometry.json'), 'w'), indent=1)
    return src, pl, geo, flat, art


if __name__ == '__main__':
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else 'v3'
    kw = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    src, pl, geo, flat, art = build_all(out, **kw)
    render(flat, os.path.join(out, 'label.png'), zoom=3.2)
    render(art, os.path.join(out, 'tex.png'), zoom=20.0 / PT, page_mm=WRAP_PAGE)
    print(json.dumps(geo, indent=1))
