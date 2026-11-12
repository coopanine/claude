"""
layout.py - turns a small parameter set into exact placements for every label element.

All numbers are label mm (x from the left cut edge, y DOWN from the top cut edge).
See DEFAULTS for every knob.  solve(src, params) returns (placer, geometry_report).
"""
import copy, json
from labelkit import ELEMENTS, Placer, PT

CREASE_TOP = 8.4999
CREASE_MID = 53.5000
CREASE_BOT = 148.1495
CREASE_X = 188.000
CREASE_HALF = 0.709 / PT / 2          # crease line half thickness (mm)
DASH_TOP, DASH_BOT = 28.680, 29.033   # dashed "proposed cap line" (filled, 1 pt thick)

DEFAULTS = {
    # ---- left column: the designers' latest arrangement (measured from their screenshot); user says it is perfect
    "left": {
        "facts_box_bottom": 131.41,     # Supplement Facts box now ends under the DV footnote (path/centre of stroke)
        "other_dy": 1.38,                # "Other Ingredients" two lines moved down by this much
        "dist1_left": 7.367, "dist1_baseline": 142.256,   # "Distributed by Lucid Metabolic Labs, Inc."
        "dist2_left": 7.283, "dist2_baseline": 144.688,   # "Miami, FL 33131 . luciddaily.com"
    },
    # ---- lid zone (between top fold crease y=8.5 and lid/body crease y=53.5)
    "lid": {
        "logo_dx": "auto",               # "auto" = centre the logo on the front axis; or a number (mm, + = right)
        "logo_dy": 0.0,                  # number (mm, + = down) or "center" = centred between top crease and dashed cap line
        "title_scale": 1.0,              # TESTIDE + tagline scaled together about the front axis
        "title_pos": "center",           # "center" = equal white space to dashed cap line above and crease below
                                         # "keep" = keep the block's vertical centre where it is; or number = dy (mm, + = down)
    },
    # ---- body zone, centre column: POWERED BY box / statue / rule / DIETARY SUPPLEMENT - 90 CAPSULES
    "center": {
        "top": "outer",                  # "outer" = frame's outer top edge level with the side boxes' outer top edge
                                         # "path"  = leave the frame top where it is (58.50); or a number (mm)
        "powered_scale": "ks",           # number, or "ks" = same factor as the statue
        "gap_powered_statue": "kp",      # number (mm) or "kp"/"ks" = source gap (4.753) x that factor
        "statue_scale": "solve",         # number, or "solve" = whatever lands the bottom text on `baseline`
        "gap_statue_rule": "ks",         # number (mm) or "ks" = source gap (3.980) x ks
        "gap_rule_text": "ks",           # number (mm) or "ks" = source gap (3.169, rule centre -> text top) x ks
        "text_scale": "ks",              # number, or "ks"
        "baseline": "left",              # "left" = baseline of the last left-column line; or number (mm)
    },
    # ---- protocol panel
    "protocol": {
        "box_bottom": "centered",        # "centered" = same margin to the bottom crease as the top has to the mid crease; or number
        "scale": 1.05,                   # type scale for ALL protocol text + FDA box
        "upc_scale": 1.0,                # UPC placeholder block
        "steps_on_axis": True,           # put the middle step (II) exactly on the panel's centre axis
        "steps_pitch_scale": 1.0,        # spacing between the three step columns (1.0 = unchanged 16.8 mm)
        # vertical gaps, all measured on what the eye sees (stroke edges / cap tops / baselines):
        #  a box inner top -> title cap top        b title baseline -> DIRECTIONS cap top
        #  c DIRECTIONS baseline -> numerals top   d numerals bottom -> step captions top
        #  e step captions baseline -> WARNING     f WARNING baseline -> body top
        #  g body baseline -> STORAGE              h STORAGE baseline -> storage text top
        #  i storage text baseline -> FDA box      j FDA box -> UPC block      k UPC block -> box inner bottom
        # value: number (mm) | "s" (source gap x scale) | "auto" (equal share of what is left) | name of another gap
        "gaps": {"a": "auto", "b": "auto", "c": "s", "d": "s", "e": "auto", "f": "s", "g": "auto", "h": "f",
                 "i": "auto", "j": "auto", "k": "auto"},
    },
    # ---- free-form fine tuning applied last: {"element_name": {"dx":0,"dy":0}}
    "overrides": {},
}


def merge(base, upd):
    out = copy.deepcopy(base)
    for k, v in (upd or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge(out[k], v)
        else:
            out[k] = v
    return out


def solve(src, params=None):
    P = merge(DEFAULTS, params)
    pl = Placer(src)
    G = {}                                   # geometry report
    E = ELEMENTS

    st = src.bbox('statue')
    axis = (st[0] + st[2]) / 2               # front-panel axis (94.935)
    G['axis_front'] = axis

    # =========================== LEFT COLUMN ===========================
    L = P['left']
    fb = src.bbox('facts_box')
    facts_half = 1.0 / PT / 2
    pl.set_rect(413, fb[0], fb[1], fb[2], L['facts_box_bottom'])
    pl.shift(E['other1'], 0, L['other_dy'])
    pl.shift(E['other2'], 0, L['other_dy'])
    d1 = src.row('dist1')
    d2 = src.row('dist2')
    pl.place(E['dist1'], 1.0, (d1['l'], d1['baseline']), (L['dist1_left'], L['dist1_baseline']))
    pl.place(E['dist2'], 1.0, (d2['l'], d2['baseline']), (L['dist2_left'], L['dist2_baseline']))
    left_last_baseline = L['dist2_baseline']
    o1 = src.row('other1'); o2 = src.row('other2')
    G['left'] = {
        'facts_box': [fb[0], fb[1], fb[2], L['facts_box_bottom']],
        'facts_box_outer_top': fb[1] - facts_half,
        'other1_top': o1['t'] + L['other_dy'], 'other2_baseline': o2['baseline'] + L['other_dy'],
        'other2_bottom': o2['b'] + L['other_dy'],
        'dist1_top': d1['t'] - d1['baseline'] + L['dist1_baseline'], 'dist1_baseline': L['dist1_baseline'],
        'dist2_baseline': L['dist2_baseline'], 'dist2_bottom': d2['b'] - d2['baseline'] + L['dist2_baseline'],
        'gap_box_to_other': (o1['t'] + L['other_dy']) - (L['facts_box_bottom'] + facts_half),
        'gap_last_baseline_to_crease': CREASE_BOT - CREASE_HALF - L['dist2_baseline'],
    }

    # =========================== LID ZONE ===========================
    D = P['lid']
    lg = src.bbox('logo')
    dx = (axis - (lg[0] + lg[2]) / 2) if D['logo_dx'] == 'auto' else float(D['logo_dx'])
    if D['logo_dy'] == 'center':            # equal white space to the top fold crease and the dashed cap line
        lband_top, lband_bot = CREASE_TOP + CREASE_HALF, DASH_TOP
        ldy = lband_top + (lband_bot - lband_top - (lg[3] - lg[1])) / 2 - lg[1]
    else:
        ldy = float(D['logo_dy'])
    pl.shift(E['logo'], dx, ldy)
    te = src.bbox('testide'); tg = src.bbox('tagline')
    t = float(D['title_scale'])
    blk_top, blk_bot = te[1], tg[3]
    h = (blk_bot - blk_top) * t
    band_top, band_bot = DASH_BOT, CREASE_MID - CREASE_HALF
    if D['title_pos'] == 'center':
        new_top = band_top + (band_bot - band_top - h) / 2
    elif D['title_pos'] == 'keep':
        new_top = (blk_top + blk_bot) / 2 - h / 2
    else:
        new_top = (blk_top + blk_bot) / 2 - h / 2 + float(D['title_pos'])
    pl.place(E['testide'] + E['tagline'], t, (axis, blk_top), (axis, new_top))
    fl = pl.final_bbox(E['logo']); ft = pl.final_bbox(E['testide']); fg = pl.final_bbox(E['tagline'])
    G['lid'] = {
        'logo': list(fl), 'logo_cx': (fl[0] + fl[2]) / 2, 'logo_dx': dx,
        'testide': list(ft), 'tagline': list(fg), 'title_scale': t, 'title_dy': new_top - blk_top,
        'ws_topcrease_to_logo': fl[1] - (CREASE_TOP + CREASE_HALF),
        'ws_logo_to_dash': DASH_TOP - fl[3],
        'ws_dash_to_testide': ft[1] - DASH_BOT,
        'ws_testide_to_tagline': fg[1] - ft[3],
        'ws_tagline_to_crease': (CREASE_MID - CREASE_HALF) - fg[3],
        'testide_width': ft[2] - ft[0], 'testide_cap_height': 10.699 * t, 'tagline_cap_height': 1.970 * t,
    }

    # =========================== CENTRE COLUMN (body zone) ===========================
    C = P['center']
    pf = src.bbox('powered_frame'); ptx = src.bbox('powered_text')
    ru = src.bbox('rule')
    bt = src.row('btext')
    hp = pf[3] - pf[1]                         # 5.681 frame outer height
    hs = st[3] - st[1]                         # 58.257
    g1s = st[1] - pf[3]                        # 4.753
    g2s = ru[1] - st[3]                        # 3.980 (statue bottom -> rule centre)
    g3s = bt['t'] - ru[1]                      # 3.169 (rule centre -> text bbox top)
    hts = bt['baseline'] - bt['t']             # 1.332 (text bbox top -> baseline)
    protocol_half = 0.98 / PT / 2
    if C['top'] == 'outer':
        top = fb[1] - facts_half
    elif C['top'] == 'path':
        top = pf[1]
    else:
        top = float(C['top'])
    baseline = left_last_baseline if C['baseline'] == 'left' else float(C['baseline'])

    def stack(ks):
        kp = ks if C['powered_scale'] == 'ks' else float(C['powered_scale'])
        kt = ks if C['text_scale'] == 'ks' else float(C['text_scale'])
        g1 = C['gap_powered_statue']
        g1 = g1s * kp if g1 == 'kp' else (g1s * ks if g1 == 'ks' else float(g1))
        g2 = g2s * ks if C['gap_statue_rule'] == 'ks' else float(C['gap_statue_rule'])
        g3 = g3s * ks if C['gap_rule_text'] == 'ks' else float(C['gap_rule_text'])
        y_st = top + hp * kp + g1
        y_rule = y_st + hs * ks + g2
        y_txt = y_rule + g3
        y_base = y_txt + hts * kt
        return dict(kp=kp, ks=ks, kt=kt, g1=g1, g2=g2, g3=g3, y_st=y_st, y_rule=y_rule, y_txt=y_txt, y_base=y_base)

    if C['statue_scale'] == 'solve':
        lo, hi = 0.5, 2.0
        for _ in range(80):
            mid = (lo + hi) / 2
            if stack(mid)['y_base'] < baseline:
                lo = mid
            else:
                hi = mid
        S = stack((lo + hi) / 2)
    else:
        S = stack(float(C['statue_scale']))
    kp, ks, kt = S['kp'], S['ks'], S['kt']
    pl.place(E['powered_frame'] + E['powered_text'], kp, (axis, pf[1]), (axis, top))
    pl.place(E['statue'], ks, (axis, st[1]), (axis, S['y_st']))
    # rule: centred on the axis, width = source width x ks, stroke weight untouched
    rw = (ru[2] - ru[0]) * ks
    pl.set_rect_x = None
    sx = rw / (ru[2] - ru[0])
    pl.affine(E['rule'], sx, 1.0, (axis - rw / 2) - sx * ru[0], S['y_rule'] - ru[1])
    # bottom text: two pieces, flush with the rule ends
    pieces = src.split_x(E['btext'], 3.0)
    assert len(pieces) == 2, len(pieces)
    bl = src.bbox(pieces[0]); br = src.bbox(pieces[1])
    pl.place(pieces[0], kt, (bl[0], bt['baseline']), (axis - rw / 2, S['y_base']))
    pl.place(pieces[1], kt, (br[2], bt['baseline']), (axis + rw / 2, S['y_base']))
    fpf = pl.final_bbox(E['powered_frame']); fptx = pl.final_bbox(E['powered_text'])
    fst = pl.final_bbox(E['statue']); fru = pl.final_bbox(E['rule']); fbt = pl.final_bbox(E['btext'])
    G['center'] = {
        'powered_scale': kp, 'statue_scale': ks, 'text_scale': kt,
        'powered_frame': list(fpf), 'powered_text': list(fptx), 'powered_text_cap_height': 2.229 * kp,
        'statue': list(fst), 'statue_w': fst[2] - fst[0], 'statue_h': fst[3] - fst[1],
        'rule_y': fru[1], 'rule_x': [fru[0], fru[2]], 'rule_w': fru[2] - fru[0],
        'btext': list(fbt), 'btext_baseline': S['y_base'], 'btext_cap_height': 1.314 * kt,
        'gap_crease_to_frame': fpf[1] - (CREASE_MID + CREASE_HALF),
        'gap_frame_to_statue': fst[1] - fpf[3], 'gap_statue_to_rule': fru[1] - fst[3],
        'gap_rule_to_text': fbt[1] - fru[1], 'gap_baseline_to_crease': (CREASE_BOT - CREASE_HALF) - S['y_base'],
        'gap_tagline_to_frame': fpf[1] - fg[3],
        'clear_facts_to_statue': fst[0] - (fb[2] + facts_half),
    }

    # =========================== PROTOCOL PANEL ===========================
    R = P['protocol']
    s = float(R['scale']); u = float(R['upc_scale'])
    pb = src.bbox('p_box')
    paxis = (pb[0] + pb[2]) / 2
    fda_half = 0.471 / PT / 2
    top_margin = pb[1] - CREASE_MID                      # path top to crease centre (4.9995)
    box_bottom = (CREASE_BOT - top_margin) if R['box_bottom'] == 'centered' else float(R['box_bottom'])
    pl.set_rect(44, pb[0], pb[1], pb[2], box_bottom)
    rt = src.row('p_title'); rd = src.row('p_dir'); rn = src.bbox('p_num')
    cols = src.split_x(E['p_steps'], 3.0)
    assert len(cols) == 3
    ncols = src.split_x(E['p_num'], 5.0)
    assert len(ncols) == 3
    steps_all = src.bbox('p_steps')
    l2_ids = [i for i in E['p_steps'] if (src.objs[i]['mm'][1] + src.objs[i]['mm'][3]) / 2 >= 79.3]
    steps_base = src.row(l2_ids)['baseline']
    rw_ = src.row('p_warn'); rb = src.bbox('p_body'); rb4 = src.row(ids_range(174, 191))
    rs = src.row('p_stor'); rst = src.row('p_stor_text')
    fd = src.bbox('p_fda_box'); up = src.bbox('upc')
    heights = {
        'title': (rt['baseline'] - rt['flat_top']) * s, 'dir': (rd['baseline'] - rd['flat_top']) * s,
        'num': (rn[3] - rn[1]) * s, 'steps': (steps_base - steps_all[1]) * s,
        'warn': (rw_['baseline'] - rw_['flat_top']) * s, 'body': (rb4['baseline'] - rb[1]) * s,
        'stor': (rs['baseline'] - rs['flat_top']) * s, 'stor_text': (rst['baseline'] - rst['t']) * s,
        'fda': (fd[3] - fd[1]) * s + 2 * fda_half, 'upc': (up[3] - up[1]) * u,
    }
    src_gaps = {
        'a': rt['flat_top'] - (pb[1] + protocol_half), 'b': rd['flat_top'] - rt['baseline'],
        'c': rn[1] - rd['baseline'], 'd': steps_all[1] - rn[3], 'e': rw_['flat_top'] - steps_base,
        'f': rb[1] - rw_['baseline'], 'g': rs['flat_top'] - rb4['baseline'], 'h': rst['t'] - rs['baseline'],
        'i': (fd[1] - fda_half) - rst['baseline'], 'j': up[1] - (fd[3] + fda_half),
        'k': (pb[3] - protocol_half) - up[3],
    }
    inner = (box_bottom - protocol_half) - (pb[1] + protocol_half)
    gaps = {}
    spec = R['gaps']
    for k_, v in spec.items():
        if v == 's':
            gaps[k_] = src_gaps[k_] * s
        elif isinstance(v, (int, float)):
            gaps[k_] = float(v)
    for k_, v in spec.items():                    # references to other fixed gaps
        if isinstance(v, str) and v in src_gaps and v in gaps:
            gaps[k_] = gaps[v]
    autos = [k_ for k_, v in spec.items() if v == 'auto']
    rest = inner - sum(heights.values()) - sum(gaps.values())
    for k_, v in spec.items():                    # references to an auto gap count as auto
        if isinstance(v, str) and v in src_gaps and v not in gaps and k_ not in gaps:
            autos.append(k_)
    if autos:
        for k_ in autos:
            gaps[k_] = rest / len(autos)
    slack = inner - sum(heights.values()) - sum(gaps.values())
    y = pb[1] + protocol_half + gaps['a']
    Y = {}
    Y['title_top'] = y; y += heights['title']; Y['title_base'] = y
    y += gaps['b']; Y['dir_top'] = y; y += heights['dir']; Y['dir_base'] = y
    y += gaps['c']; Y['num_top'] = y; y += heights['num']; Y['num_bot'] = y
    y += gaps['d']; Y['steps_top'] = y; y += heights['steps']; Y['steps_base'] = y
    y += gaps['e']; Y['warn_top'] = y; y += heights['warn']; Y['warn_base'] = y
    y += gaps['f']; Y['body_top'] = y; y += heights['body']; Y['body_base'] = y
    y += gaps['g']; Y['stor_top'] = y; y += heights['stor']; Y['stor_base'] = y
    y += gaps['h']; Y['stxt_top'] = y; y += heights['stor_text']; Y['stxt_base'] = y
    y += gaps['i']; Y['fda_outer_top'] = y; y += heights['fda']; Y['fda_outer_bot'] = y
    y += gaps['j']; Y['upc_top'] = y; y += heights['upc']; Y['upc_bot'] = y
    y += gaps['k']; Y['inner_bottom'] = y
    # rows centred on the panel axis
    pl.place(E['p_title'], s, (paxis, rt['flat_top']), (paxis, Y['title_top']))
    pl.place(E['p_dir'], s, (paxis, rd['flat_top']), (paxis, Y['dir_top']))
    pl.place(E['p_warn'], s, (paxis, rw_['flat_top']), (paxis, Y['warn_top']))
    pl.place(E['p_body'], s, (paxis, rb[1]), (paxis, Y['body_top']))
    pl.place(E['p_stor'], s, (paxis, rs['flat_top']), (paxis, Y['stor_top']))
    pl.place(E['p_stor_text'], s, (paxis, rst['t']), (paxis, Y['stxt_top']))
    # three step columns: numeral + caption scale about their own column centre
    ncent = []
    for c in ncols:
        b = src.bbox(c); ncent.append((b[0] + b[2]) / 2)
    pitch = (ncent[2] - ncent[0]) / 2 * float(R['steps_pitch_scale'])
    mid = paxis if R['steps_on_axis'] else ncent[1]
    newc = [mid - pitch, mid, mid + pitch]
    for j in range(3):
        pl.place(ncols[j], s, (ncent[j], rn[1]), (newc[j], Y['num_top']))
        pl.place(cols[j], s, (ncent[j], steps_all[1]), (newc[j], Y['steps_top']))
    # FDA box + its three lines
    fw = (fd[2] - fd[0]) * s
    fda_top = Y['fda_outer_top'] + fda_half
    pl.set_rect(411, paxis - fw / 2, fda_top, paxis + fw / 2, fda_top + (fd[3] - fd[1]) * s)
    pl.place(E['p_fda_text'], s, ((fd[0] + fd[2]) / 2, fd[1]), (paxis, fda_top))
    # UPC placeholder
    uw = (up[2] - up[0]) * u
    pl.set_rect(412, paxis - uw / 2, Y['upc_top'], paxis + uw / 2, Y['upc_top'] + (up[3] - up[1]) * u)
    fsteps = pl.final_bbox(E['p_steps']); ffda = pl.final_bbox(E['p_fda_box'])
    G['protocol'] = {
        'scale': s, 'box': [pb[0], pb[1], pb[2], box_bottom], 'axis': paxis,
        'margin_top_to_crease': (pb[1] - protocol_half) - (CREASE_MID + CREASE_HALF),
        'margin_bottom_to_crease': (CREASE_BOT - CREASE_HALF) - (box_bottom + protocol_half),
        'gaps': gaps, 'src_gaps': src_gaps, 'heights': heights, 'Y': Y, 'slack': slack,
        'step_centres': newc, 'steps_margin_left': fsteps[0] - (pb[0] + protocol_half),
        'steps_margin_right': (pb[2] - protocol_half) - fsteps[2],
        'fda_box': list(ffda), 'fda_margin_side': ffda[0] - fda_half - (pb[0] + protocol_half),
        'upc': list(pl.final_bbox(E['upc'])),
        'title_cap_height': heights['title'], 'body_x_range': list(pl.final_bbox(E['p_body']))[0:3:2],
    }

    # =========================== OVERRIDES ===========================
    for name, ov in (P.get('overrides') or {}).items():
        pl.shift(E[name], float(ov.get('dx', 0)), float(ov.get('dy', 0)))
    G['params'] = P
    return pl, G


def ids_range(a, b):
    return list(range(a, b + 1))


def report(G):
    """human-readable summary of the geometry"""
    L, D, C, R = G['left'], G['lid'], G['center'], G['protocol']
    out = []
    w = out.append
    w("LID ZONE (y 8.50 -> 53.50)")
    w(f"  logo            y {D['logo'][1]:.3f}-{D['logo'][3]:.3f}  cx {D['logo_cx']:.3f}  (axis {G['axis_front']:.3f}, moved dx {D['logo_dx']:+.3f})")
    w(f"  TESTIDE         y {D['testide'][1]:.3f}-{D['testide'][3]:.3f}  w {D['testide_width']:.2f}  cap h {D['testide_cap_height']:.2f}  scale {D['title_scale']:.4f}  dy {D['title_dy']:+.3f}")
    w(f"  tagline         y {D['tagline'][1]:.3f}-{D['tagline'][3]:.3f}  cap h {D['tagline_cap_height']:.2f}")
    w(f"  white space: top crease->logo {D['ws_topcrease_to_logo']:.3f} | logo->dashed {D['ws_logo_to_dash']:.3f} | dashed->TESTIDE {D['ws_dash_to_testide']:.3f} | TESTIDE->tagline {D['ws_testide_to_tagline']:.3f} | tagline->crease {D['ws_tagline_to_crease']:.3f}")
    w("CENTRE COLUMN (body zone y 53.50 -> 148.15)")
    w(f"  scales: powered {C['powered_scale']:.4f}  statue {C['statue_scale']:.4f}  bottom text {C['text_scale']:.4f}")
    w(f"  POWERED frame   y {C['powered_frame'][1]:.3f}-{C['powered_frame'][3]:.3f}  x {C['powered_frame'][0]:.3f}-{C['powered_frame'][2]:.3f}  ({C['powered_frame'][2]-C['powered_frame'][0]:.2f} x {C['powered_frame'][3]-C['powered_frame'][1]:.2f})  text cap h {C['powered_text_cap_height']:.2f}")
    w(f"  statue          y {C['statue'][1]:.3f}-{C['statue'][3]:.3f}  x {C['statue'][0]:.3f}-{C['statue'][2]:.3f}  ({C['statue_w']:.2f} x {C['statue_h']:.2f})")
    w(f"  rule            y {C['rule_y']:.3f}  x {C['rule_x'][0]:.3f}-{C['rule_x'][1]:.3f}  (w {C['rule_w']:.2f})")
    w(f"  bottom text     y {C['btext'][1]:.3f}-{C['btext'][3]:.3f}  baseline {C['btext_baseline']:.3f}  x {C['btext'][0]:.3f}-{C['btext'][2]:.3f}  cap h {C['btext_cap_height']:.3f}")
    w(f"  gaps: crease->frame {C['gap_crease_to_frame']:.3f} | frame->statue {C['gap_frame_to_statue']:.3f} | statue->rule {C['gap_statue_to_rule']:.3f} | rule->text {C['gap_rule_to_text']:.3f} | baseline->crease {C['gap_baseline_to_crease']:.3f}")
    w(f"  tagline->frame (across crease) {C['gap_tagline_to_frame']:.3f} | facts box -> statue clearance {C['clear_facts_to_statue']:.2f}")
    w("LEFT COLUMN")
    w(f"  facts box       y {L['facts_box'][1]:.3f}-{L['facts_box'][3]:.3f}  x {L['facts_box'][0]:.3f}-{L['facts_box'][2]:.3f}")
    w(f"  other ingr.     top {L['other1_top']:.3f}  last baseline {L['other2_baseline']:.3f}")
    w(f"  distributed by  top {L['dist1_top']:.3f}  baselines {L['dist1_baseline']:.3f} / {L['dist2_baseline']:.3f}  (last baseline -> crease {L['gap_last_baseline_to_crease']:.3f})")
    w("PROTOCOL PANEL")
    w(f"  box             y {R['box'][1]:.3f}-{R['box'][3]:.3f}  x {R['box'][0]:.3f}-{R['box'][2]:.3f}   margins to creases: top {R['margin_top_to_crease']:.3f} / bottom {R['margin_bottom_to_crease']:.3f}")
    w(f"  type scale {R['scale']:.4f}")
    Y = R['Y']
    for k in ('title_top', 'title_base', 'dir_top', 'dir_base', 'num_top', 'num_bot', 'steps_top', 'steps_base', 'warn_top', 'warn_base', 'body_top', 'body_base', 'stor_top', 'stor_base', 'stxt_top', 'stxt_base', 'fda_outer_top', 'fda_outer_bot', 'upc_top', 'upc_bot'):
        w(f"    {k:14s} {Y[k]:8.3f}")
    w("  gaps (mm):  " + "  ".join(f"{k}={v:.3f}" for k, v in sorted(R['gaps'].items())))
    w("  source gaps: " + "  ".join(f"{k}={v:.3f}" for k, v in sorted(R['src_gaps'].items())))
    w(f"  step column centres {', '.join(f'{c:.3f}' for c in R['step_centres'])} (panel axis {R['axis']:.3f}); side margins L {R['steps_margin_left']:.2f} / R {R['steps_margin_right']:.2f}")
    w(f"  FDA box x {R['fda_box'][0]:.3f}-{R['fda_box'][2]:.3f}  side margin {R['fda_margin_side']:.3f}   UPC y {R['upc'][1]:.3f}-{R['upc'][3]:.3f}")
    return "\n".join(out)
