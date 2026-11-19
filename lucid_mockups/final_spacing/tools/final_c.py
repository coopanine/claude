"""
final_c.py - Option C (Nov 19): no back logo.
  cap front : Lucid logo (original size) + TESTIDE + gold tagline, equal gaps, stack centred in the 45 mm cap
  body      : POWERED BY badge back under the cap, top on the body top line; statue lowered (scaled about its
              bottom edge so the statue -> rule -> DIETARY SUPPLEMENT spacing is unchanged); rule and bottom text
              keep their relationship to the statue width
  back      : blank cap (the logo split at the glue seam on the physical sample)
  sides     : Supplement Facts and Protocol panels exactly as final_b (not moved)
"""
import json, os
from labelkit import Source, build_pdf, render, PT, ELEMENTS as E
from layout import solve
from v3cap import GOLD_RULE, DASH, WRAP_PAGE, CAP_T, CAP_B, TOPLINE, _tagline_optical
from precise import ink, refine
import final_b

HERE = os.path.dirname(os.path.abspath(__file__))


def make(src):
    pl, G = solve(src, json.load(open(os.path.join(HERE, 'params_v2.json'))))
    ax = G['axis_front']
    geo = {'axis': ax}
    # ---- cap: logo / TESTIDE / tagline, equal gaps (the approved TESTIDE -> tagline gap), centred ----
    lg, t, tg = ink(src, pl, E['logo']), ink(src, pl, E['testide']), ink(src, pl, E['tagline'])
    gap = tg[1] - t[3]
    H = (lg[3] - lg[1]) + gap + (t[3] - t[1]) + gap + (tg[3] - tg[1])
    y0 = (CAP_T + CAP_B) / 2 - H / 2
    pl.shift(E['logo'], ax - (lg[0] + lg[2]) / 2, y0 - lg[1])
    y1 = y0 + (lg[3] - lg[1]) + gap
    pl.shift(E['testide'], ax - (t[0] + t[2]) / 2, y1 - t[1])
    y2 = y1 + (t[3] - t[1]) + gap
    pl.shift(E['tagline'], 0.0, y2 - tg[1])
    _tagline_optical(src, pl, ax)
    geo.update(cap_gap=gap, cap_margin_top=y0 - CAP_T, cap_margin_bottom=CAP_B - (y0 + H))
    # ---- body: badge top on the body top line, centred on the axis ----
    fr = ink(src, pl, E['powered_frame'])
    pl.shift(E['powered_frame'] + E['powered_text'], ax - (fr[0] + fr[2]) / 2, TOPLINE - fr[1])
    fr = ink(src, pl, E['powered_frame'])
    # statue: badge sits centred between the cap line and the statue top; statue bottom edge stays
    gap_b = TOPLINE - CAP_B
    st = ink(src, pl, E['statue']); ru = ink(src, pl, E['rule'])
    ins = ru[0] - st[0]                                   # v2 rule inset inside the statue width (0.70)
    top = fr[3] + gap_b
    s = (st[3] - top) / (st[3] - st[1])
    pl.place(E['statue'], s, ((st[0] + st[2]) / 2, st[3]), (ax, st[3]))
    st2 = ink(src, pl, E['statue'])
    # rule + bottom text: rule = statue width minus the same inset each side; text at the rule ends
    nl, nr = st2[0] + ins, st2[2] - ins
    k = (nr - nl) / (ru[2] - ru[0])
    pl.affine(E['rule'], k, 1.0, nl - k * ru[0], 0.0)
    g_left, g_right = src.split_x(E['btext'], 3.0)
    bl, br = ink(src, pl, g_left), ink(src, pl, g_right)
    pl.shift(g_left, nl - bl[0], 0.0)
    pl.shift(g_right, nr - br[2], 0.0)
    # Protocol stack on exact metrics + POWERED BY text centred in its frame (same as the approved files)
    refine(src, pl)
    # ---- side panels: identical to final_b ----
    left = E['facts_box'] + E['facts_content'] + E['other1'] + E['other2'] + E['dist1'] + E['dist2']
    pl.shift(left, 5.3355 - final_b.SHIFT, 0)
    b = ink(src, pl, E['facts_box']); pl.set_rect(E['facts_box'][0], b[0] + final_b.NARROW, b[1], b[2] - final_b.NARROW, b[3])
    prot = [i for n in ('p_box', 'p_title', 'p_dir', 'p_num', 'p_steps', 'p_warn', 'p_body', 'p_stor', 'p_stor_text',
                        'p_fda_box', 'p_fda_text', 'upc') for i in E[n]]
    pl.shift(prot, final_b.SHIFT, 0)
    b = ink(src, pl, E['p_box']); pl.set_rect(E['p_box'][0], b[0] + final_b.NARROW, b[1], b[2] - final_b.NARROW, b[3])
    geo.update(statue=ink(src, pl, E['statue']), statue_scale_vs_v2=s, badge=ink(src, pl, E['powered_frame']),
               rule=ink(src, pl, E['rule']), logo=ink(src, pl, E['logo']), testide=ink(src, pl, E['testide']),
               tagline=ink(src, pl, E['tagline']))
    return pl, geo


def build(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    src = Source(os.path.join(HERE, 'src.pdf'))
    pl, geo = make(src)
    build_pdf(src, pl, os.path.join(out_dir, 'label.pdf'), title='TESTIDE label - Option C', recolor=GOLD_RULE, drop_ids=DASH)
    build_pdf(src, pl, os.path.join(out_dir, 'art.pdf'), recolor=GOLD_RULE, page_mm=WRAP_PAGE, keep_mm=(-5, 0, 196, 157),
              drop_layers=('/MC2', '/MC3'), drop_ids=DASH)
    render(os.path.join(out_dir, 'art.pdf'), os.path.join(out_dir, 'tex.png'), zoom=20.0 / PT)
    return src, pl, geo


if __name__ == '__main__':
    import sys
    src, pl, geo = build(sys.argv[1] if len(sys.argv) > 1 else 'vC')
    for k, v in geo.items():
        print(k, [round(x, 3) for x in v] if isinstance(v, tuple) else round(v, 4))
