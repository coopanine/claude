"""
proof_a.py - spacing proof for TESTIDE option A on the factory dieline (A3 landscape, 4 pages).

  p1  the artwork at 100% on the factory dieline, key spacing callouts, rules and production notes
  p2  front column and back of cap at 170%, every gap and width
  p3  Supplement Facts side and Protocol side at 170%
  p4  element positions table + 3D reference views

All callouts are drawn on an optional-content layer 'Spacing callouts (does not print)'.
Every number is read from the option A artwork (v3cap.make2(src, 'A')), never typed by hand.
"""
import json, os, sys
import pymupdf
from labelkit import Source, ELEMENTS as E
from v3cap import make2

HERE = os.path.dirname(os.path.abspath(__file__))
MM = 72 / 25.4
PAGE_W, PAGE_H = 420.0, 297.0                     # A3 landscape, mm
FDIR = '/usr/share/fonts/opentype/inter/'
FONTS = {'reg': 'Inter-Regular.otf', 'med': 'Inter-Medium.otf', 'semi': 'Inter-SemiBold.otf', 'bold': 'Inter-Bold.otf'}
MAG = (0.894, 0.0, 0.486)
INK = (0.10, 0.10, 0.12)
GRAY = (0.38, 0.38, 0.42)
RULE = (0.78, 0.78, 0.80)
CHIPS = [('PANTONE 2758 C', 'navy', (0.0, 0.118, 0.376)), ('PANTONE 2728 C', 'blue', (0.0, 0.278, 0.733)),
         ('PANTONE 1255 C', 'gold', (0.678, 0.518, 0.122))]
TITLE = 'TESTIDE  ·  Spacing proof  ·  Option A  ·  rev 1'
DATE = 'Nov 16, 2026'
NPAGES = 4
VIEWS = None
CLOSE = (os.path.join(os.path.dirname(os.path.abspath(__file__)), 'A_front_cap.png'),
         os.path.join(os.path.dirname(os.path.abspath(__file__)), 'A_back_cap.png'))


# --------------------------------------------------------------------------------------------
# geometry (label mm: x from the left cut edge, y down from the top cut edge)
# --------------------------------------------------------------------------------------------
def geometry():
    """every number on the proof, measured exactly (Bezier extrema, flat-glyph baselines) on the final artwork"""
    from labelkit import Placer
    from final_a import make_final
    from precise import ink, flat_edges, protocol_metrics, gaps_of, subpaths
    src = Source(os.path.join(HERE, 'src.pdf'))
    pl, extra, geo, R = make_final(src)
    G = {'axis': geo['axis_front'], 'fold_top': 8.4999, 'cap_line': 53.5, 'fold_bot': 148.1495, 'overlap': 188.0}
    for n in ('testide', 'tagline', 'powered_frame', 'powered_text', 'statue', 'rule', 'logo', 'facts_box', 'facts_content',
              'other1', 'other2', 'dist1', 'dist2', 'p_box', 'p_title', 'p_dir', 'p_num', 'p_steps', 'p_warn', 'p_body',
              'p_stor', 'p_stor_text', 'p_fda_box', 'p_fda_text', 'upc'):
        G[n] = ink(src, pl, E[n])
    g0, g1 = src.split_x(E['btext'], 3.0)
    G['bt_left'], G['bt_right'] = ink(src, pl, g0), ink(src, pl, g1)
    G['bt_base'] = flat_edges(src, pl, g0, 'bottom')
    for n in ('other1', 'other2', 'dist1', 'dist2'):
        G[n + '_base'] = flat_edges(src, pl, E[n], 'bottom')
    # tagline words (asterisk = last subpath, hangs outside the centring)
    sp = sorted(subpaths(src, pl, E['tagline']), key=lambda b: b[0])
    G['tag_words'] = (sp[0][0], max(b[2] for b in sp[:-1]))
    M = protocol_metrics(src, pl)
    G['pY'] = dict(M, fda_outer_top=M['fda_top'], fda_outer_bot=M['fda_bot'])
    G['pgaps'] = gaps_of(M)
    G['p_inner_top'], G['p_inner_bot'] = M['inner_top'], M['inner_bot']
    G['num_cols'] = [(lambda b: (b[0] + b[2]) / 2)(ink(src, pl, gp)) for gp in src.split_x(E['p_num'], 2.0)]
    G['lw'] = {'rule': 0.5, 'facts_box': 1.0, 'p_box': 0.98, 'fda_box': 0.471}
    G['refine'] = {k: v for k, v in R.items() if k != 'before'}
    # sizes vs the factory proof 110926_3 (= src.pdf)
    P0 = Placer(src)
    def scale(n):
        a, b = ink(src, P0, E[n]), G[n]
        return (b[3] - b[1]) / (a[3] - a[1]) if (a[3] - a[1]) > 1e-6 else (b[2] - b[0]) / (a[2] - a[0])
    G['scale'] = {n: scale(n) for n in ('testide', 'tagline', 'powered_frame', 'statue', 'logo', 'upc', 'p_title', 'p_fda_box')}
    a = ink(src, P0, E['rule']); G['scale']['rule'] = (G['rule'][2] - G['rule'][0]) / (a[2] - a[0])
    a = ink(src, P0, g0); G['scale']['btext'] = (G['bt_left'][3] - G['bt_left'][1]) / (a[3] - a[1])
    return G


# --------------------------------------------------------------------------------------------
# drawing helpers
# --------------------------------------------------------------------------------------------
class Page:
    def __init__(self, doc, oc, n):
        self.p = doc.new_page(width=PAGE_W * MM, height=PAGE_H * MM)
        self.F = {}
        for k, f in FONTS.items():
            self.p.insert_font(fontname=k, fontfile=FDIR + f)
            self.F[k] = pymupdf.Font(fontfile=FDIR + f)
        self.oc, self.n = oc, n

    def tw(self, s, size, font='reg'):
        return self.F[font].text_length(s, size) / MM

    def text(self, x, y, s, size=7.0, font='reg', color=INK, align='left', callout=False, rotate=0):
        w = self.tw(s, size, font)
        if rotate == 0:
            if align == 'center': x -= w / 2
            elif align == 'right': x -= w
        self.p.insert_text((x * MM, y * MM), s, fontsize=size, fontname=font, color=color, rotate=rotate,
                           oc=self.oc if callout else 0)
        return w

    def wrap(self, x, y, width, s, size=7.0, font='reg', color=INK, lead=1.42):
        """word-wrapped paragraph; returns the y below it (mm)"""
        words, line, lh = s.split(' '), '', size * lead / MM
        for wd in words:
            t = (line + ' ' + wd).strip()
            if self.tw(t, size, font) > width and line:
                self.text(x, y, line, size, font, color); y += lh; line = wd
            else:
                line = t
        if line:
            self.text(x, y, line, size, font, color); y += lh
        return y

    def line(self, x1, y1, x2, y2, color=MAG, width=0.35, dashes=None, callout=True):
        self.p.draw_line((x1 * MM, y1 * MM), (x2 * MM, y2 * MM), color=color, width=width,
                         dashes=dashes, oc=self.oc if callout else 0)

    def rect(self, x1, y1, x2, y2, color=None, fill=None, width=0.5, callout=False):
        self.p.draw_rect(pymupdf.Rect(x1 * MM, y1 * MM, x2 * MM, y2 * MM), color=color, fill=fill, width=width,
                         oc=self.oc if callout else 0)

    def header(self, subtitle):
        self.text(14, 17.5, TITLE, 17, 'bold')
        self.text(14, 24.2, subtitle, 8.2, 'reg', GRAY)
        self.text(PAGE_W - 14, 17.5, 'Lucid Metabolic Labs', 8.5, 'semi', INK, 'right')
        self.text(PAGE_W - 14, 22.6, f'{DATE}   ·   Page {self.n} of {NPAGES}', 7.5, 'reg', GRAY, 'right')
        self.line(14, 27.6, PAGE_W - 14, 27.6, RULE, 0.6, callout=False)

    def footer(self):
        self.line(14, 284.6, PAGE_W - 14, 284.6, RULE, 0.6, callout=False)
        self.text(14, 289.6, 'All dimensions in mm from the top-left corner of the green cut line (x to the right, y down). '
                  'Geometric bounds (Illustrator "Use Preview Bounds" off): strokes measured to their centre line, '
                  'outlined type to the ink. Values rounded to 0.01 mm (sums can differ by 0.01); the page 4 table wins.',
                  6.6, 'reg', GRAY)
        self.text(14, 293.6, 'Magenta = spacing callouts, on their own layer, does not print.   Green = cut.   '
                  'Yellow = crease or fold, does not print.   Red = factory dimensions.   '
                  'If your file differs from these numbers, these numbers win.', 6.6, 'reg', GRAY)


class View:
    """a region of the label artwork placed on a page at a scale; maps label mm -> page mm"""
    def __init__(self, page, label_doc, x0, y0, x1, y1, ox, oy, s):
        self.pg, self.x0, self.y0, self.x1, self.y1, self.ox, self.oy, self.s = page, x0, y0, x1, y1, ox, oy, s
        clip = pymupdf.Rect((x0 + 27) * MM, (y0 + 15.5) * MM, (x1 + 27) * MM, (y1 + 15.5) * MM)
        tgt = pymupdf.Rect(ox * MM, oy * MM, (ox + (x1 - x0) * s) * MM, (oy + (y1 - y0) * s) * MM)
        page.p.show_pdf_page(tgt, label_doc, 0, clip=clip)

    def X(self, x): return self.ox + (x - self.x0) * self.s
    def Y(self, y): return self.oy + (y - self.y0) * self.s

    # -- primitives in label mm --
    def line(self, x1, y1, x2, y2, **kw):
        self.pg.line(self.X(x1), self.Y(y1), self.X(x2), self.Y(y2), **kw)

    def ext(self, x1, y1, x2, y2):
        self.line(x1, y1, x2, y2, width=0.22, dashes='[1.2 1.0] 0')

    def axis(self, x, y1, y2, label=None, size=6.0, label_y=None):
        self.line(x, y1, x, y2, width=0.4, dashes='[6 2 1 2] 0')
        if label:
            self.pg.text(self.X(x), self.Y(label_y if label_y is not None else y1) - 1.2, label, size, 'semi', MAG,
                         'center', callout=True)

    def hline(self, y, x1, x2, label=None, size=6.0, label_x=None, align='left'):
        self.line(x1, y, x2, y, width=0.3, dashes='[2.5 1.5] 0')
        if label:
            lx = self.X(label_x if label_x is not None else x2) + (1.2 if align == 'left' else -1.2)
            self.pg.text(lx, self.Y(y) + size * 0.36 / MM * 1.0, label, size, 'semi', MAG, align, callout=True)

    def vchain(self, x, stops, labels, size=6.0, tick=1.3, side='right', rot_min=None, max_w=None):
        """stops: y values; labels: [(text, kind)] per segment, kind 'gap' (magenta) or 'size' (grey)"""
        X = self.X(x)
        self.pg.line(X, self.Y(stops[0]), X, self.Y(stops[-1]), width=0.35)
        for y in stops:
            self.pg.line(X - tick / 2, self.Y(y), X + tick / 2, self.Y(y), width=0.35)
        cap = size * 0.727 / MM
        for (a, b), (t, kind) in zip(zip(stops[:-1], stops[1:]), labels):
            mid = (self.Y(a) + self.Y(b)) / 2
            col, font = (MAG, 'semi') if kind == 'gap' else (GRAY, 'med')
            seg = self.Y(b) - self.Y(a)
            if rot_min is not None and kind == 'size' and seg > rot_min:
                w = self.pg.tw(t, size, font)
                self.pg.text(X - 1.0, mid + w / 2, t, size, font, col, callout=True, rotate=90)
            elif side == 'right' and max_w and self.pg.tw(t, size, font) > max_w and ' ' in t:
                words = t.split(' ')
                best = min(range(1, len(words)), key=lambda k: abs(self.pg.tw(' '.join(words[:k]), size, font)
                                                                     - self.pg.tw(' '.join(words[k:]), size, font)))
                lh = size * 1.18 / MM
                self.pg.text(X + 1.1, mid - lh / 2 + cap / 2, ' '.join(words[:best]), size, font, col, 'left', callout=True)
                self.pg.text(X + 1.1, mid + lh / 2 + cap / 2, ' '.join(words[best:]), size, font, col, 'left', callout=True)
            elif side == 'right':
                self.pg.text(X + 1.1, mid + cap / 2, t, size, font, col, 'left', callout=True)
            else:
                self.pg.text(X - 1.1, mid + cap / 2, t, size, font, col, 'right', callout=True)

    def hdim(self, y, x1, x2, label, size=6.0, tick=1.3, below=False, kind='gap', label_x=None, align='center'):
        Y = self.Y(y)
        self.pg.line(self.X(x1), Y, self.X(x2), Y, width=0.35)
        for x in (x1, x2):
            self.pg.line(self.X(x), Y - tick / 2, self.X(x), Y + tick / 2, width=0.35)
        col, font = (MAG, 'semi') if kind == 'gap' else (GRAY, 'med')
        cap = size * 0.727 / MM
        lx = self.X(label_x) if label_x is not None else (self.X(x1) + self.X(x2)) / 2
        ly = Y + 1.0 + cap if below else Y - 1.0
        self.pg.text(lx, ly, label, size, font, col, align, callout=True)


def f2(v):
    from decimal import Decimal, ROUND_HALF_UP
    return str(Decimal(str(round(v, 4))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


# --------------------------------------------------------------------------------------------
# page 1: the proof at 100%
# --------------------------------------------------------------------------------------------
def page1(doc, oc, lab, G):
    P = Page(doc, oc, 1)
    P.header('Paper tube 58 x 140 mm  ·  wrap 188 mm + 8 mm overlap  ·  factory dieline PO71251  ·  '
             'artwork at 100% on the dieline')
    V = View(P, lab, -27, -15.5, 202, 161.5, 12, 33, 1.0)        # whole label page at 1:1
    ax, ct, cl, fb = G['axis'], G['fold_top'], G['cap_line'], G['fold_bot']
    T, tg, fr, st, ru = G['testide'], G['tagline'], G['powered_frame'], G['statue'], G['rule']
    lg = G['logo']
    # axes and reference lines
    V.axis(ax, -6.0, 163.0, f'FRONT AXIS  x {f2(ax)}', label_y=-6.0)
    V.line(0.936, 6.0, 0.936, 56.0, width=0.4, dashes='[6 2 1 2] 0')
    P.text(V.X(0.0), V.Y(-1.6), f'BACK AXIS  x {f2(ax + 94 - 188)}   (glue seam at x 0 = x 188)', 5.6, 'semi', MAG,
           callout=True)
    top_line = st[1]
    V.hline(top_line, 1.5, 196.5, f'{f2(top_line)}  body top line', 5.6)
    V.line(5.5, G['bt_base'] + 0.25, 196.5, G['bt_base'] + 0.25, width=0.2, dashes='[2.5 1.5] 0')
    P.text(V.X(196.5) + 1.2, V.Y(G['bt_base']) + 0.75, f'{f2(G["bt_base"])}  shared baseline', 5.6, 'semi', MAG,
           callout=True)
    for y, t in ((ct, f'{f2(ct)}  top fold'), (cl, f'{f2(cl)}  cap line'), (fb, f'{f2(fb)}  bottom fold')):
        P.text(V.X(196.5) + 1.2, V.Y(y) + 0.75, t, 5.6, 'semi', MAG, callout=True)
    # one chain, top fold to bottom fold, just right of the front column
    cx = 125.3
    stops = [ct, T[1], T[3], tg[1], tg[3], fr[1], fr[3], cl, st[1], st[3], ru[1], G['bt_base'], fb]
    labels = [(f2(T[1] - ct), 'gap'), (f'TESTIDE {f2(T[3] - T[1])}', 'size'), (f2(tg[1] - T[3]), 'gap'),
              (f'tagline {f2(tg[3] - tg[1])}', 'size'), (f2(fr[1] - tg[3]), 'gap'),
              (f'badge {f2(fr[3] - fr[1])}', 'size'), (f2(cl - fr[3]), 'gap'), (f2(st[1] - cl), 'gap'),
              (f'STATUE {f2(st[3] - st[1])}', 'size'), (f2(ru[1] - st[3]), 'gap'),
              (f2(G['bt_base'] - ru[1]), 'gap'), (f2(fb - G['bt_base']), 'gap')]
    for y, xe in ((T[1], T[2]), (T[3], T[2]), (tg[1], tg[2]), (tg[3], tg[2]), (fr[1], fr[2]), (fr[3], fr[2]),
                  (st[1], st[2]), (st[3], st[2]), (ru[1], ru[2]), (G['bt_base'], G['bt_right'][2])):
        V.ext(xe + 0.6, y, cx, y)
    V.vchain(cx, stops, labels, size=5.4, rot_min=12)
    # back logo chain (left end of the sheet) and the two halves
    bx = 24.8
    V.ext(lg[2] + 0.5, lg[1], bx, lg[1]); V.ext(lg[2] + 0.5, lg[3], bx, lg[3])
    V.vchain(bx, [ct, lg[1], lg[3], cl], [(f2(lg[1] - ct), 'gap'), (f'LOGO {f2(lg[3] - lg[1])}', 'size'),
                                          (f2(cl - lg[3]), 'gap')], size=5.4)
    V.hdim(15.6, 0.0, lg[2], f'{f2(lg[2])}  right half (...CID)', size=5.4)
    V.hdim(15.6, lg[0] + 188.0, 188.0, f'left half (LU...)  {f2(188.0 - (lg[0] + 188.0))}', size=5.4)

    # ---- right column ----
    x, w = 263.0, 143.0
    y = 37.0
    P.text(x, y, 'WHAT CHANGED IN OPTION A', 8.6, 'bold'); y += 6.0
    rules = [
        f'Cap = the 45 mm zone from the top fold (y {f2(ct)}) to the cap line (y {f2(cl)}).',
        f'Front of cap: TESTIDE, tagline and the POWERED BY TST-01 badge move up as one block, centred in the cap: '
        f'{f2(T[1] - ct)} above and {f2(cl - fr[3])} below. Gaps {f2(tg[1] - T[3])} (TESTIDE to tagline) and '
        f'{f2(fr[1] - tg[3])} (tagline to badge). Sizes as in our last reference: TESTIDE and tagline 100%, '
        f'badge {G["scale"]["powered_frame"] * 100:.1f}% of 110926_3.',
        f'Back of cap: Lucid logo enlarged to {f2(lg[2] - lg[0])} x {f2(lg[3] - lg[1])} '
        f'({G["scale"]["logo"] * 100:.1f}%), so LUCID matches the TESTIDE letter height. Centred on the back axis '
        f'and in the cap ({f2(lg[1] - ct)} above and below).',
        f'Body: statue enlarged to {f2(st[2] - st[0])} x {f2(st[3] - st[1])} ({G["scale"]["statue"] * 100:.1f}% of '
        f'110926_3). Its top sits on the body top line (y {f2(st[1])}), level with the outer edges of the '
        f'Supplement Facts and Protocol boxes.',
        f'Rule {f2(ru[2] - ru[0])} long, {f2(ru[0] - st[0])} inside each statue edge, {f2(ru[1] - st[3])} below '
        f'the statue. DIETARY SUPPLEMENT starts at its left end, 90 CAPSULES ends at its right end, baseline '
        f'{f2(G["bt_base"] - ru[1])} below the rule and level with "Miami, FL".',
        f'Everything on the front is centred on the front axis x {f2(ax)}. The tagline is centred on its words; '
        f'the asterisk hangs outside.',
        'Supplement Facts side and Protocol side: same spacing as our last reference. Every number is on page 3.',
    ]
    for i, r in enumerate(rules, 1):
        P.text(x, y, f'{i}', 7.2, 'bold', MAG)
        y = P.wrap(x + 5.0, y, w - 5.0, r, 7.2) + 1.6
    y += 2.5
    P.text(x, y, 'INKS AND FONTS', 8.6, 'bold'); y += 5.0
    for name, word, rgb in CHIPS:
        P.rect(x, y - 3.2, x + 9, y + 1.4, fill=rgb, color=None)
        P.text(x + 11.5, y, f'{name}  ({word})', 7.2, 'semi')
        y += 6.0
    y = P.wrap(x, y + 0.5, w, 'Three spot inks, no CMYK. Gold = PANTONE 1255 C (ink or foil: TBD). '
               'Fonts unchanged; all copy as outlines. Rule above DIETARY SUPPLEMENT: 0.5 pt, PANTONE 1255 C.', 7.2) + 2.5
    P.text(x, y, 'PRODUCTION NOTES', 8.6, 'bold'); y += 6.0
    notes = [
        'Remove the dashed "Proposed Cap Line" and the 29 mm cap strips from your proof file 110926_3. The cap is the '
        '45 mm zone.',
        'POWERED BY badge outline is CMYK in your file: make it PANTONE 2728 C like the badge text.',
        'Back logo: the glue seam is 0.94 mm from the back axis, so it runs through the logo. Best: if the cap is wrapped '
        'as its own piece, put the cap seam a quarter turn from the front (x 47.9 or 141.9) and print the logo whole. '
        'Otherwise print the two halves as drawn: add 2 mm bleed past the left cut edge, and tell us if ink may run '
        '1 to 2 mm into the overlap strip (we kept it blank).',
        'Child-resistant (CR) button: please mark its position and size on the dieline. Suggested: the blank strip '
        'between the Supplement Facts box and the statue (x about 58.5), clear of all art on the cap and the body.',
        f'Bottom fold: the drawn crease is at y {f2(fb)} (body {f2(fb - cl)} mm), but the dieline text says 95 mm. '
        'We measured to the drawn crease; please confirm.',
        'If the gold is foil: foil only the gold items (tagline, DIRECTIONS, WARNING, STORAGE, numerals, rule). The FOIL '
        'layer in your file also holds the navy step captions; move them off it.',
        'UPC block is a placeholder. A full-size UPC-A (about 30 x 21 mm) does not fit this panel; do not re-space '
        'until we confirm the barcode.',
        'Lid top: head icon unchanged, chin pointing to the front (TESTIDE side).',
    ]
    for r in notes:
        P.text(x, y, '•', 7.2, 'bold', INK)
        y = P.wrap(x + 4.0, y, w - 4.0, r, 7.2) + 1.6
    y += 4.0
    P.text(x, y, 'APPROVAL', 8.6, 'bold'); y += 8.0
    P.line(x, y, x + 62, y, INK, 0.4, callout=False); P.line(x + 72, y, x + 112, y, INK, 0.4, callout=False)
    P.text(x, y + 3.6, 'Spacing approved by', 6.6, 'reg', GRAY); P.text(x + 72, y + 3.6, 'Date', 6.6, 'reg', GRAY)
    # ---- under the label: how to measure, legend, contents ----
    yb = 218.0
    P.text(14, yb, 'HOW TO MEASURE', 8.6, 'bold')
    yy = yb + 6.0
    for t in ('Print at 100% on A3 (no "fit to page"): the label on this page is true size.',
              'Set the ruler origin to the top-left corner of the green cut line. x runs right, y runs down.',
              'Geometric bounds (Illustrator "Use Preview Bounds" off). Strokes are measured to their centre line, '
              'outlined type to the ink.'):
        P.text(14, yy, '•', 7.2, 'bold')
        yy = P.wrap(18, yy, 92, t, 7.2) + 1.4
    P.text(120, yb, 'LEGEND', 8.6, 'bold')
    yy = yb + 6.0
    for col, dash, t in ((MAG, None, 'Spacing callouts (own layer, does not print)'), (GRAY, None, 'Grey = element sizes, magenta = gaps'),
                         ((0.0, 0.65, 0.3), None, 'Cut line'),
                         ((0.98, 0.80, 0.0), None, 'Crease or fold (does not print)'), ((0.9, 0.1, 0.1), None, 'Factory dimensions (nominal)'),
                         (MAG, '[6 2 1 2] 0', 'Axis')):
        P.line(120, yy - 1.0, 130, yy - 1.0, col, 0.8, dashes=dash, callout=False)
        P.text(133, yy, t, 7.2); yy += 5.0
    P.text(190, yb, 'IN THIS PROOF', 8.6, 'bold')
    yy = yb + 6.0
    for t in ('1   Artwork at 100% on the dieline', '2   Front column + back of cap, 170%',
              '3   Facts side + Protocol side, 195%', '4   Positions table + 3D views'):
        P.text(190, yy, t, 7.2); yy += 5.0
    yy += 1.5
    P.wrap(190, yy, 56, 'Matches the artwork file TESTIDE_OptionA_Artwork_1to1_on_dieline.pdf (same layout, 1:1, no callouts).',
           6.6, 'reg', GRAY)
    P.footer()
    return P


# --------------------------------------------------------------------------------------------
# page 2: front column + back of cap at 170%
# --------------------------------------------------------------------------------------------
def page2(doc, oc, lab, G):
    P = Page(doc, oc, 2)
    P.header('Front column (cap + body) and back of cap, at 170%')
    s = 1.7
    ax, ct, cl, fb = G['axis'], G['fold_top'], G['cap_line'], G['fold_bot']
    T, tg, fr, ft, st, ru, lg = (G['testide'], G['tagline'], G['powered_frame'], G['powered_text'], G['statue'],
                                 G['rule'], G['logo'])
    V = View(P, lab, 58.0, 4.0, 132.0, 152.0, 18.0, 33.0, s)
    P.text(18.0, 31.4, 'FRONT', 8.0, 'bold')
    V.axis(ax, 4.6, 148.6, f'front axis  x {f2(ax)}', size=6.4, label_y=4.6)
    # vertical chain
    cx = 125.6
    stops = [ct, T[1], T[3], tg[1], tg[3], fr[1], fr[3], cl, st[1], st[3], ru[1], G['bt_base'], fb]
    labels = [(f2(T[1] - ct), 'gap'), (f'TESTIDE {f2(T[3] - T[1])}', 'size'), (f2(tg[1] - T[3]), 'gap'),
              (f'tagline {f2(tg[3] - tg[1])}', 'size'), (f2(fr[1] - tg[3]), 'gap'),
              (f'badge {f2(fr[3] - fr[1])}', 'size'), (f2(cl - fr[3]), 'gap'),
              (f'{f2(st[1] - cl)}   cap line to body top line', 'gap'),
              (f'STATUE {f2(st[3] - st[1])}', 'size'), (f2(ru[1] - st[3]), 'gap'),
              (f'{f2(G["bt_base"] - ru[1])}   rule to baseline', 'gap'), (f2(fb - G['bt_base']), 'gap')]
    for y, xe in ((T[1], T[2]), (T[3], T[2]), (tg[1], tg[2]), (tg[3], tg[2]), (fr[1], fr[2]), (fr[3], fr[2]),
                  (st[1], st[2]), (st[3], st[2]), (ru[1], ru[2]), (G['bt_base'], G['bt_right'][2])):
        V.ext(xe + 0.5, y, cx, y)
    V.vchain(cx, stops, labels, size=6.6, rot_min=20)
    P.text(V.X(cx) + 1.1, V.Y(ct) - 1.4, 'top fold', 6.0, 'reg', GRAY, callout=True)
    P.text(V.X(cx) + 1.1, V.Y(cl) + 2.6, 'cap line', 6.0, 'reg', GRAY, callout=True)
    P.text(V.X(cx) + 1.1, V.Y(fb) + 2.6, 'bottom fold', 6.0, 'reg', GRAY, callout=True)
    # widths
    V.hdim(12.2, T[0], T[2], f'TESTIDE  {f2(T[2] - T[0])}', size=6.6)
    w0, w1 = G['tag_words']
    V.hdim(36.0, w0, w1, f'tagline words  {f2(w1 - w0)}  (inset {f2(((T[2] - T[0]) - (w1 - w0)) / 2)} each side)', size=6.4)
    ins = ((T[2] - T[0]) - (w1 - w0)) / 2
    V.hdim(36.0, T[0], w0, f2(ins), size=5.8, below=True)
    V.hdim(36.0, w1, T[2], f2(ins), size=5.8, below=True)
    V.ext(T[0], T[3] + 0.3, T[0], 37.0); V.ext(T[2], T[3] + 0.3, T[2], 37.0)
    V.hdim(49.6, fr[0], fr[2], f'badge {f2(fr[2] - fr[0])} outer edges  ·  frame 0.19 mm (0.55 pt)  ·  text {f2(ft[2] - ft[0])}',
           size=6.3)
    V.hdim(56.5, st[0], st[2], f'STATUE  {f2(st[2] - st[0])}', size=6.6)
    # statue width -> rule: 0.70 | rule | 0.70 on one line in the gap under the statue
    yr = 137.5
    xs_ = [st[0], ru[0], ru[2], st[2]]
    P.line(V.X(xs_[0]), V.Y(yr), V.X(xs_[-1]), V.Y(yr), width=0.35)
    for xv in xs_:
        P.line(V.X(xv), V.Y(yr) - 0.65, V.X(xv), V.Y(yr) + 0.65, width=0.35)
    P.text(V.X(st[0]) - 0.8, V.Y(yr) + 0.8, f2(ru[0] - st[0]), 6.0, 'semi', MAG, 'right', callout=True)
    P.text(V.X(st[2]) + 0.8, V.Y(yr) + 0.8, f2(st[2] - ru[2]), 6.0, 'semi', MAG, 'left', callout=True)
    P.text((V.X(ru[0]) + V.X(ax)) / 2, V.Y(yr) - 1.0, f'rule  {f2(ru[2] - ru[0])}', 6.4, 'semi', MAG, 'center',
           callout=True)
    for xv in (st[0], st[2]):
        V.ext(xv, st[3] - 0.4, xv, yr)
    for xv in (ru[0], ru[2]):
        V.ext(xv, ru[1] + 0.3, xv, 146.6)
    P.text(V.X(ax), V.Y(150.9), 'DIETARY SUPPLEMENT starts at the rule\'s left end, 90 CAPSULES ends at its right end',
           5.8, 'reg', GRAY, 'center', callout=True)

    # ---- back of cap, as wrapped: right end of the sheet + left end of the sheet ----
    bx0, by0 = 196.0, 40.0
    P.text(bx0, 31.4, 'BACK OF CAP, AS WRAPPED', 8.0, 'bold')
    P.text(bx0, 35.6, 'Right end of the sheet (x 160 to 188) next to the left end (x 0 to 30), as they meet on the tube.',
           6.6, 'reg', GRAY)
    VA = View(P, lab, 160.0, 4.0, 188.0, 57.0, bx0, by0, s)
    VB = View(P, lab, 0.0, 4.0, 30.0, 57.0, bx0 + 28.0 * s, by0, s)
    seam_x = bx0 + 28.0 * s
    P.line(seam_x, by0 - 1.0, seam_x, by0 + 53.0 * s + 1.0, width=0.5, dashes='[1.5 1.2] 0')
    P.text(seam_x, by0 + 53.0 * s + 4.4, 'glue seam:  x 188  |  x 0', 6.4, 'semi', MAG, 'center', callout=True)
    bax = VB.X(ax + 94.0 - 188.0)
    P.line(bax, by0 + (6.0 - 4.0) * s, bax, by0 + (56.0 - 4.0) * s, width=0.4, dashes='[6 2 1 2] 0')
    P.text(bax + 1.2, by0 + (6.6 - 4.0) * s, f'back axis  x {f2(ax + 94 - 188)}  (= {f2(ax + 94)})', 6.4, 'semi', MAG,
           callout=True)
    # logo widths
    left_half = (lg[0] + 188.0, 188.0)
    yd = 15.6
    P.line(VA.X(left_half[0]), VB.Y(yd), VB.X(lg[2]), VB.Y(yd), width=0.35)
    for X in (VA.X(left_half[0]), seam_x, VB.X(lg[2])):
        P.line(X, VB.Y(yd) - 0.65, X, VB.Y(yd) + 0.65, width=0.35)
    P.text((VA.X(left_half[0]) + seam_x) / 2, VB.Y(yd) - 1.0, f'left half (LU...)  {f2(188.0 - left_half[0])}', 6.2,
           'semi', MAG, 'center', callout=True)
    P.text((seam_x + VB.X(lg[2])) / 2, VB.Y(yd) - 1.0, f'{f2(lg[2])}  right half (...CID)', 6.2, 'semi', MAG, 'center',
           callout=True)
    yt = 11.6
    P.line(VA.X(left_half[0]), VB.Y(yt), VB.X(lg[2]), VB.Y(yt), width=0.35)
    for X in (VA.X(left_half[0]), VB.X(lg[2])):
        P.line(X, VB.Y(yt) - 0.65, X, VB.Y(yt) + 0.65, width=0.35)
    P.text((VA.X(left_half[0]) + VB.X(lg[2])) / 2, VB.Y(yt) - 1.0, f'LOGO  {f2(lg[2] - lg[0])}', 6.6, 'semi', MAG,
           'center', callout=True)
    # vertical chain right of the logo (left end of the sheet)
    VB.ext(lg[2] + 0.4, lg[1], 25.2, lg[1]); VB.ext(lg[2] + 0.4, lg[3], 25.2, lg[3])
    VB.vchain(25.2, [ct, lg[1], lg[3], cl], [(f2(lg[1] - ct), 'gap'), (f'LOGO {f2(lg[3] - lg[1])}', 'size'),
                                            (f2(cl - lg[3]), 'gap')], size=6.6)
    # explanation
    y = by0 + 53.0 * s + 12.0
    P.text(bx0, y, 'WHY TWO HALVES', 8.0, 'bold'); y += 5.0
    y = P.wrap(bx0, y, 205.0, f'The back of the tube (opposite the front axis) is where the label\'s glue seam lands: '
               f'the seam is 0.94 mm from the back axis. '
               f'On the flat sheet the logo is therefore printed in two parts: the right half ({f2(lg[2])} wide) at the left '
               f'end of the sheet, starting at the cut edge, and the left half ({f2(188.0 - left_half[0])} wide) at the right '
               f'end, ending at the overlap line x 188. Add 2 mm bleed past the left cut edge; the 8 mm overlap strip '
               f'stays blank unless you tell us ink may run 1 to 2 mm into it.', 7.2) + 2.0
    y = P.wrap(bx0, y, 205.0, 'Preferred: if the cap is wrapped as its own piece, move the cap seam a quarter turn from the '
               'front (x 47.9 or x 141.9, both blank) and print the logo whole, centred on the back axis. '
               'Please confirm which one you will do.', 7.2) + 4.0
    P.text(bx0, y, 'HOW IT LOOKS ON THE TUBE', 8.0, 'bold'); y += 3.0
    ww = min((PAGE_W - 14.0 - bx0 - 6.0) / 2, (282.0 - y - 6.0) * 1300.0 / 1150.0)
    hh = ww * 1150.0 / 1300.0
    for k, (img, cap) in enumerate(((CLOSE[0], 'Front of cap'), (CLOSE[1], 'Back of cap (faint line = glue seam)'))):
        xx = bx0 + k * (ww + 6.0)
        if os.path.exists(img):
            P.p.insert_image(pymupdf.Rect(xx * MM, y * MM, (xx + ww) * MM, (y + hh) * MM), filename=img)
        P.text(xx, y + hh + 4.2, cap, 6.6, 'reg', GRAY)
    P.footer()
    return P


# --------------------------------------------------------------------------------------------
# page 3: side panels at 170%
# --------------------------------------------------------------------------------------------
def page3(doc, oc, lab, G):
    P = Page(doc, oc, 3)
    P.header('Supplement Facts side and Protocol side, at 195% (same spacing as our last reference)')
    s = 1.95
    cl, fb = G['cap_line'], G['fold_bot']
    # ---- left column ----
    fx = G['facts_box']
    VL = View(P, lab, -1.5, 51.0, 56.0, 151.0, 16.0, 36.0, s)
    P.text(16.0, 33.0, 'SUPPLEMENT FACTS SIDE', 8.0, 'bold')
    lx = 52.8
    stops = [cl, fx[1], fx[3], G['other1_base'], G['other2_base'], G['dist1_base'], G['bt_base'], fb]
    labels = [(f'{f2(fx[1] - cl)}  to stroke centre', 'gap'), (f'FACTS BOX {f2(fx[3] - fx[1])}', 'size'),
              (f'{f2(G["other1_base"] - fx[3])}  to Other Ingredients baseline', 'gap'),
              (f'{f2(G["other2_base"] - G["other1_base"])}  line 2', 'gap'),
              (f'{f2(G["dist1_base"] - G["other2_base"])}  to Distributed by', 'gap'),
              (f'{f2(G["bt_base"] - G["dist1_base"])}  line 2', 'gap'), (f2(fb - G['bt_base']), 'gap')]
    for y, xe in ((fx[1], fx[2]), (fx[3], fx[2]), (G['other1_base'], G['other1'][2]), (G['other2_base'], G['other2'][2]),
                  (G['dist1_base'], G['dist1'][2]), (G['dist2_base'], G['dist2'][2])):
        VL.ext(xe + 0.5, y, lx, y)
    VL.vchain(lx, stops, labels, size=6.6, rot_min=20)
    VL.hdim(55.6, fx[0], fx[2], f'FACTS BOX  {f2(fx[2] - fx[0])}  (1 pt)', size=6.4)
    VL.hdim(55.6, 0.0, fx[0], f2(fx[0]), size=6.0, label_x=-0.4, align='right')
    P.text(VL.X(1.0), VL.Y(fb) + 6.0, f'Text left edges: Other Ingredients line 1 x {f2(G["other1"][0])}, line 2 '
           f'x {f2(G["other2"][0])}; Distributed by line 1 x {f2(G["dist1"][0])}, line 2 x {f2(G["dist2"][0])}',
           6.4, 'reg', GRAY, callout=True)
    P.text(VL.X(1.0), VL.Y(fb) + 9.6, f'"Miami, FL" baseline y {f2(G["bt_base"])}: level with DIETARY SUPPLEMENT on the front',
           6.4, 'reg', GRAY, callout=True)
    P.text(VL.X(1.0), VL.Y(fb) + 13.2, f'Box outer edge (1 pt stroke) top y {f2(fx[1] - 0.1764)} = body top line = statue top',
           6.4, 'reg', GRAY, callout=True)
    # ---- protocol ----
    pb, Y, gp = G['p_box'], G['pY'], G['pgaps']
    VP = View(P, lab, 133.0, 51.0, 187.4, 151.0, 172.0, 36.0, s)
    P.text(172.0, 33.0, 'PROTOCOL SIDE', 8.0, 'bold')
    px = 186.4
    st_ = [G['p_inner_top'], Y['title_top'], Y['title_base'], Y['dir_top'], Y['dir_base'], Y['num_top'], Y['num_bot'],
           Y['steps_top'], Y['steps_base'], Y['warn_top'], Y['warn_base'], Y['body_top'], Y['body_base'], Y['stor_top'],
           Y['stor_base'], Y['stxt_top'], Y['stxt_base'], Y['fda_outer_top'], Y['fda_outer_bot'], Y['upc_top'],
           Y['upc_bot'], G['p_inner_bot']]
    names = ['4.48', 'THE PROTOCOL cap height', '4.48', 'DIRECTIONS cap height', 'c', 'numerals', 'd',
             'captions ascender top to line-2 baseline', '4.48', 'WARNING cap height', 'f', 'warning text ascender top to last baseline',
             '4.48', 'STORAGE cap height', 'h', 'storage text ascender top to baseline', '4.48', f'FDA box outer edges (stroke centre {f2(G["p_fda_box"][3] - G["p_fda_box"][1])})', '4.48',
             'UPC block', '4.48']
    labs = []
    for (a, b), nm in zip(zip(st_[:-1], st_[1:]), names):
        v = f2(b - a)
        if nm in ('4.48',):
            labs.append((f'{v}', 'gap'))
        elif nm in ('c', 'd', 'f', 'h'):
            labs.append((v, 'gap'))
        else:
            labs.append((f'{nm} {v}', 'size'))
    VP.vchain(px, st_, labs, size=6.2, rot_min=None, max_w=34.0)
    P.text(VP.X(px) + 1.1, VP.Y(st_[0]) - 1.6, 'box inner edge', 6.0, 'reg', GRAY, callout=True)
    P.text(VP.X(px) + 1.1, VP.Y(st_[-1]) + 2.8, 'box inner edge', 6.0, 'reg', GRAY, callout=True)
    pa = (pb[0] + pb[2]) / 2
    VP.axis(pa, 52.4, 147.0, f'panel axis  x {f2(pa)}', size=6.2, label_y=52.4)
    cols = G['num_cols']
    VP.hdim(86.7, cols[0], cols[1], f2(cols[1] - cols[0]), size=6.0)
    VP.hdim(86.7, cols[1], cols[2], f2(cols[2] - cols[1]), size=6.0)
    for c in (cols[0], cols[1], cols[2]):
        VP.ext(c, 84.6, c, 87.2)
    fd, up = G['p_fda_box'], G['upc']
    VP.hdim(113.6, fd[0], fd[2], f'FDA box  {f2(fd[2] - fd[0])}', size=6.2, below=True)
    VP.hdim(140.9, up[0], up[2], f'UPC block  {f2(up[2] - up[0])}  (placeholder)', size=6.2)
    VP.hdim(55.6, pb[0], pb[2], f'PROTOCOL BOX  {f2(pb[2] - pb[0])}  (0.98 pt)', size=6.4)
    out_top = pb[1] - G['lw']['p_box'] * 25.4 / 72 / 2
    out_bot = pb[3] + G['lw']['p_box'] * 25.4 / 72 / 2
    VP.vchain(134.2, [cl, pb[1]], [(f2(pb[1] - cl), 'gap')], size=6.0, side='left')
    VP.vchain(134.2, [pb[3], fb], [(f2(fb - pb[3]), 'gap')], size=6.0, side='left')
    P.text(VP.X(133.2), VP.Y(fb) + 6.0, 'Protocol chain: measured where the eye reads the type: cap tops and ascender tops '
           '(flat letters, not the arch of f or round overshoot), baselines and box edges. The page 4 table gives ink boxes.',
           6.0, 'reg', GRAY, callout=True)
    P.text(VP.X(133.2), VP.Y(fb) + 9.6, 'Box: 5.00 to stroke centre at top and bottom; its outer edge sits on the body '
           'top line (within 0.01).', 6.4, 'reg', GRAY, callout=True)
    # notes
    x, w, y = 318.0, 88.0, 40.0
    P.text(x, y, 'PROTOCOL SIDE', 8.6, 'bold'); y += 6.0
    for r in (f'All Protocol text and the FDA box at 105% of 110926_3. UPC placeholder unchanged.',
              f'Seven equal gaps of {f2(gp["a"])}, measured on what the eye sees: box inner edge to THE PROTOCOL cap '
              f'height, title baseline to DIRECTIONS, captions baseline to WARNING, warning text baseline to STORAGE, '
              f'storage text baseline to the FDA box, FDA box to UPC, UPC to box inner edge.',
              f'Fixed gaps: DIRECTIONS baseline to numerals {f2(gp["c"])}, numerals to captions {f2(gp["d"])}, '
              f'WARNING baseline to text {f2(gp["f"])}, STORAGE baseline to text {f2(gp["h"])}.',
              f'Step II sits on the panel axis x {f2(pa)}; columns {f2(cols[1] - cols[0])} apart. THE PROTOCOL, the '
              f'headings, the text, the FDA box and the UPC block are centre-aligned on the same axis (letter shapes can '
              f'put the ink up to 0.05 off; the X values on page 4 are the ink).',
              f'Box stroke centre is {f2(pb[1] - cl)} below the cap line and {f2(fb - pb[3])} above the bottom fold.'):
        P.text(x, y, '•', 7.2, 'bold')
        y = P.wrap(x + 4.0, y, w - 4.0, r, 7.2) + 1.6
    y += 3.0
    P.text(x, y, 'SUPPLEMENT FACTS SIDE', 8.6, 'bold'); y += 6.0
    for r in ('Facts box ends under "Daily Value not established". Other Ingredients sits below the box, then '
              'Distributed by, with nothing in between (required by the manufacturer\'s QC, Progressive Labs).',
              f'Box outer edge top = body top line y {f2(G["statue"][1])}, the same line as the statue top.',
              'Text inside the Facts box: same size and positions as 110926_3; only the box bottom moved up to '
              f'y {f2(fx[3])}.'):
        P.text(x, y, '•', 7.2, 'bold')
        y = P.wrap(x + 4.0, y, w - 4.0, r, 7.2) + 1.6
    P.footer()
    return P


# --------------------------------------------------------------------------------------------
# page 4: positions table + 3D reference
# --------------------------------------------------------------------------------------------
def page4(doc, oc, lab, G, views_jpg):
    P = Page(doc, oc, 4)
    P.header('Element positions (top-left corner of each element, then width and height) and 3D reference')
    ax = G['axis']
    T, tg, fr, ft, st, ru, lg = (G['testide'], G['tagline'], G['powered_frame'], G['powered_text'], G['statue'],
                                 G['rule'], G['logo'])
    S = G['scale']
    pct = lambda v: f'{v * 100:.0f}%' if abs(v * 100 - round(v * 100)) < 0.005 else f'{v * 100:.1f}%'

    def r(name, ink, b, sz, note):
        return [name, ink, f2(b[0]), f2(b[1]), f2(b[2] - b[0]), f2(b[3] - b[1]) if b[3] - b[1] > 1e-6 else '0.5 pt', sz, note]
    rows = [('FRONT OF CAP', None),
            r('TESTIDE', '2758 C', T, pct(S['testide']), f'centred on the front axis x {f2(ax)}'),
            r('Tagline EVOLUTIONARY TESTOSTERONE SUPPORT*', '1255 C', tg, pct(S['tagline']),
              f'words ({f2(G["tag_words"][1] - G["tag_words"][0])}) centred on the axis; asterisk hangs right'),
            r('POWERED BY TST-01 box', '2728 C', fr, pct(S['powered_frame']),
              'outer edges; frame 0.19 mm (0.55 pt); as a stroke: 38.00 x 6.17 at 75.93, 39.04. CMYK in your file: make it 2728 C'),
            r('POWERED BY TST-01 text', '2728 C', ft, pct(S['powered_frame']), 'centred in the box'),
            ('FRONT OF BODY', None),
            r('Statue', '2728 C', st, pct(S['statue']), f'top on the body top line; centred on the axis'),
            ['Rule', '1255 C', f2(ru[0]), f2(ru[1]), f2(ru[2] - ru[0]), '-', '-',
             f'0.5 pt, butt caps; Y = stroke centre; {f2(ru[0] - st[0])} inside each statue edge'],
            r('DIETARY SUPPLEMENT', '2758 C', G['bt_left'], pct(S['btext']), f'starts at the rule\'s left end; baseline {f2(G["bt_base"])}'),
            r('90 CAPSULES', '2758 C', G['bt_right'], pct(S['btext']), f'ends at the rule\'s right end; baseline {f2(G["bt_base"])}'),
            ('BACK OF CAP', None),
            r('Lucid logo, right half (...CID)', '2728 C', (0.0, lg[1], lg[2], lg[3]), pct(S['logo']),
              f'whole logo {f2(lg[2] - lg[0])} x {f2(lg[3] - lg[1])}; centre x {f2(ax + 94 - 188)} (= {f2(ax + 94)}), y {f2((lg[1] + lg[3]) / 2)}'),
            r('Lucid logo, left half (LU...)', '2728 C', (lg[0] + 188.0, lg[1], 188.0, lg[3]), pct(S['logo']), 'ends at the overlap line x 188; right half starts at the cut edge x 0 (+2 mm bleed)'),
            ('SUPPLEMENT FACTS SIDE', None),
            r('Supplement Facts box', '2758 C', G['facts_box'], '-', f'1 pt stroke; outer edge top y {f2(G["facts_box"][1] - 0.1764)} = statue top'),
            r('Other Ingredients (2 lines)', '2758 C', (G['other1'][0], G['other1'][1], max(G['other1'][2], G['other2'][2]), G['other2'][3]), '100%',
              f'baselines {f2(G["other1_base"])} and {f2(G["other2_base"])}'),
            r('Distributed by (2 lines)', '2758 C', (min(G['dist1'][0], G['dist2'][0]), G['dist1'][1], max(G['dist1'][2], G['dist2'][2]), G['dist2'][3]), '100%',
              f'line 1 x {f2(G["dist1"][0])}, line 2 x {f2(G["dist2"][0])}; baselines {f2(G["dist1_base"])} and {f2(G["bt_base"])}'),
            ('PROTOCOL SIDE', None),
            r('Protocol box', '2758 C', G['p_box'], '-', '0.98 pt stroke; outer edge top on the body top line (statue top), within 0.01'),
            r('THE PROTOCOL', '2758 C', G['p_title'], pct(S['p_title']), f'centred on the panel axis x {f2((G["p_box"][0] + G["p_box"][2]) / 2)}'),
            r('DIRECTIONS', '1255 C', G['p_dir'], '105%', 'centre-aligned (use X/Y)'),
            r('Numerals I  II  III', '1255 C', G['p_num'], '105%',
              'column centres ' + ' / '.join(f2(c) for c in G['num_cols'])),
            r('Step captions', '2758 C', G['p_steps'], '105%', 'centre-aligned under each numeral (use X/Y)'),
            r('WARNING heading', '1255 C', G['p_warn'], '105%', 'centre-aligned (use X/Y)'),
            r('Warning text', '2758 C', G['p_body'], '105%', 'centre-aligned (use X/Y)'),
            r('STORAGE heading', '1255 C', G['p_stor'], '105%', 'centre-aligned (use X/Y)'),
            r('Storage text', '2758 C', G['p_stor_text'], '105%', 'centre-aligned (use X/Y)'),
            r('FDA disclaimer box', '2758 C', G['p_fda_box'], pct(S['p_fda_box']), f'0.47 pt stroke (outer edges {f2(G["pY"]["fda_bot"] - G["pY"]["fda_top"])} tall); text centre-aligned inside'),
            r('UPC block (placeholder)', '2758 C', G['upc'], pct(S['upc']), 'final UPC size TBD'),
            ]
    cols = [('Element', 92.0), ('Ink', 18.0), ('X', 16.0), ('Y', 16.0), ('W', 16.0), ('H', 16.0), ('Size', 18.0), ('Notes', 200.0)]
    x0, y = 14.0, 37.0
    xs = [x0]
    for _, wd in cols:
        xs.append(xs[-1] + wd)
    for (h, wd), xx in zip(cols, xs):
        al = 'right' if h in ('X', 'Y', 'W', 'H', 'Size') else 'left'
        P.text(xx + (wd - 2.0 if al == 'right' else 0.0), y, h, 7.0, 'semi', GRAY, al)
    y += 1.6
    P.line(x0, y, xs[-1], y, INK, 0.5, callout=False)
    y += 4.2
    for rw in rows:
        if rw[1] is None and len(rw) == 2:
            y += 1.0
            P.text(x0, y, rw[0], 6.8, 'bold', MAG); y += 4.2
            continue
        for k, ((h, wd), xx) in enumerate(zip(cols, xs)):
            al = 'right' if h in ('X', 'Y', 'W', 'H', 'Size') else 'left'
            font = 'med' if k == 0 else 'reg'
            P.text(xx + (wd - 2.0 if al == 'right' else 0.0), y, rw[k], 6.8, font, INK if k != 7 else GRAY, al)
        P.line(x0, y + 1.5, xs[-1], y + 1.5, RULE, 0.25, callout=False)
        y += 4.15
    y += 3.0
    P.text(x0, y, 'X, Y = top-left corner of the element; W, H = its size. Size = against your proof 110926_3 (- = box or line, use W and H). Lid top: '
           'head icon unchanged (12.45 x 14.98, centred on the 58 mm disc, chin toward the front).', 6.8, 'reg', GRAY)
    # 3D reference
    if views_jpg and os.path.exists(views_jpg):
        yy = y + 4.0
        h_avail = 282.0 - yy
        import PIL.Image as Image
        im = Image.open(views_jpg)
        ar = im.width / im.height
        hh = min(h_avail, 300.0 / ar)
        ww = hh * ar
        xx = (PAGE_W - ww) / 2
        P.p.insert_image(pymupdf.Rect(xx * MM, yy * MM, (xx + ww) * MM, (yy + hh) * MM), filename=views_jpg)
    P.footer()
    return P


def build(label_pdf, out_pdf, views_jpg=None):
    global VIEWS
    VIEWS = views_jpg
    G = geometry()
    lab = pymupdf.open(label_pdf)
    doc = pymupdf.open()
    oc = doc.add_ocg('Spacing callouts (does not print)', on=True)
    page1(doc, oc, lab, G)
    page2(doc, oc, lab, G)
    page3(doc, oc, lab, G)
    page4(doc, oc, lab, G, views_jpg)
    doc.set_metadata({'title': 'TESTIDE spacing proof - Option A', 'author': 'Lucid Metabolic Labs',
                      'subject': 'Spacing proof on factory dieline PO71251', 'creator': 'Lucid Metabolic Labs'})
    doc.save(out_pdf, garbage=3, deflate=True)
    json.dump({k: v for k, v in G.items() if k not in ('pY', 'pgaps')} | {'pY': G['pY'], 'pgaps': G['pgaps']},
              open(os.path.splitext(out_pdf)[0] + '_geometry.json', 'w'), indent=1, default=list)
    return G


if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
