"""
labelkit - vector re-layout engine for the TESTIDE label proof PDF.

Works directly on the PDF content stream of the factory proof (src.pdf):
  * every art object keeps its original outlines, spot colours (PANTONE 2728 C / 2758 C / 1255 C),
    stroke weights and layer; only coordinates are rewritten
  * the dieline (Cut / Crease separations), the dashed cap line and the dimension marks are never touched
  * everything outside the label (proof header, lid diagrams, swatches, thumbnail) is dropped and the
    page is cropped to the label at 1:1 scale

Coordinate system used everywhere in this module ("label mm"):
  x = mm from the LEFT cut edge, y = mm DOWN from the TOP cut edge.
  Creases: y=8.50 (top fold), y=53.50 (lid/body crease), y=148.15 (bottom fold); x=188.0 (overlap).
"""
import json, math, os, sys
from decimal import Decimal
import pikepdf
from interp import walk, apply

PT = 72 / 25.4
X0 = 1617.987          # left cut edge  (pt, source page space)
YTOP = 1063.782        # top cut edge   (pt, source page space)
PATH_OPS = {'m', 'l', 'c', 'v', 'y', 'h', 're'}

# page box of the output, in label mm (l, t, r, b)
PAGE_MM = (-27.0, -15.5, 202.0, 161.5)
# objects fully inside this region are kept (label mm)
KEEP_MM = (-30.0, -14.5, 204.0, 161.0)


def ids(a, b):
    return list(range(a, b + 1))


ELEMENTS = {
    'logo': [1026], 'dash': [9, 10, 11], 'testide': [12], 'tagline': [1121],
    'powered_frame': [14], 'powered_text': [15], 'statue': [13], 'rule': [16],
    'btext': ids(17, 43),
    'facts_box': [413],
    'facts_content': [i for i in ids(414, 1016) if not (473 <= i <= 546)],
    'other1': ids(473, 517), 'other2': ids(518, 546),
    'p_box': [44], 'p_title': ids(45, 55), 'p_dir': ids(1037, 1046), 'p_num': ids(1061, 1066),
    'p_steps': ids(1067, 1120), 'p_warn': ids(1047, 1053), 'p_body': ids(56, 191),
    'p_stor': ids(1054, 1060), 'p_stor_text': ids(256, 277),
    'p_fda_box': [411], 'p_fda_text': ids(278, 410),
    'dist1': ids(192, 227), 'dist2': ids(228, 255), 'upc': [412],
}


def to_mm(b):
    """pdf bbox (x0,y0,x1,y1; y up, pt) -> label mm (l,t,r,b; y down)"""
    return ((b[0] - X0) / PT, (YTOP - b[3]) / PT, (b[2] - X0) / PT, (YTOP - b[1]) / PT)


class Source:
    def __init__(self, path):
        self.path = path
        self.pdf = pikepdf.open(path)
        self.page = self.pdf.pages[0]
        self.ops = list(pikepdf.parse_content_stream(self.page))
        self.objs = walk(self.ops)
        for i, o in enumerate(self.objs):
            o['id'] = i
            o['mm'] = to_mm(o['bbox']) if 'bbox' in o else None
        self._check()

    def _check(self):
        o = self.objs
        assert len(o) == 1200, len(o)
        cut = o[1125]['bbox']
        assert abs(cut[0] - X0) < 1e-3 and abs(cut[3] - YTOP) < 1e-3, cut
        st = o[13]
        assert st['nsub'] == 39568
        for name, lst in ELEMENTS.items():
            for i in lst:
                assert o[i]['op'] in ('f', 'S'), (name, i, o[i]['op'])

    # ---- geometry helpers (label mm) ----
    def bbox(self, idlist):
        if isinstance(idlist, str):
            idlist = ELEMENTS[idlist]
        ms = [self.objs[i]['mm'] for i in idlist]
        return (min(m[0] for m in ms), min(m[1] for m in ms), max(m[2] for m in ms), max(m[3] for m in ms))

    def row(self, idlist):
        """text row metrics: bbox, flat top (most common glyph top), baseline (most common glyph bottom)"""
        if isinstance(idlist, str):
            idlist = ELEMENTS[idlist]
        ms = [self.objs[i]['mm'] for i in idlist]

        def mode(vals):
            best = None
            for v in vals:
                n = sum(1 for w in vals if abs(w - v) <= 0.03)
                if best is None or n > best[0]:
                    best = (n, v)
            grp = [w for w in vals if abs(w - best[1]) <= 0.03]
            return sum(grp) / len(grp)

        l, t, r, b = self.bbox(idlist)
        return {'ids': list(idlist), 'l': l, 't': t, 'r': r, 'b': b,
                'flat_top': mode([m[1] for m in ms]), 'baseline': mode([m[3] for m in ms])}

    def split_x(self, idlist, gap):
        """split objects into groups separated horizontally by more than `gap` mm"""
        os_ = sorted((self.objs[i] for i in idlist), key=lambda o: o['mm'][0])
        groups = [[os_[0]]]
        for o in os_[1:]:
            right = max(q['mm'][2] for q in groups[-1])
            if o['mm'][0] - right > gap:
                groups.append([o])
            else:
                groups[-1].append(o)
        return [[o['id'] for o in g] for g in groups]

    def subpaths(self, i):
        """bbox (label mm) of each subpath of object i"""
        o = self.objs[i]
        ctm = o['ctm']
        res, pts = [], []
        for k in range(o['start'], o['end']):
            op = str(self.ops[k].operator)
            a = [float(x) for x in self.ops[k].operands]
            if op == 'm':
                if pts:
                    res.append(pts)
                pts = [apply(ctm, a[0], a[1])]
            elif op == 'l':
                pts.append(apply(ctm, a[0], a[1]))
            elif op == 'c':
                pts += [apply(ctm, a[j], a[j + 1]) for j in (0, 2, 4)]
            elif op in ('v', 'y'):
                pts += [apply(ctm, a[j], a[j + 1]) for j in (0, 2)]
            elif op == 're':
                if pts:
                    res.append(pts)
                    pts = []
                x, y, w, h = a
                res.append([apply(ctm, x, y), apply(ctm, x + w, y + h)])
        if pts:
            res.append(pts)
        return [to_mm((min(q[0] for q in s), min(q[1] for q in s), max(q[0] for q in s), max(q[1] for q in s)))
                for s in res]


class Placer:
    """collects per-object affine transforms expressed in label mm:  x' = sx*x + tx ,  y' = sy*y + ty"""

    def __init__(self, src):
        self.src = src
        self.T = {}

    def affine(self, idlist, sx, sy, tx, ty):
        for i in idlist:
            if i in self.T:   # compose: new after old
                a, b, c, d = self.T[i]
                self.T[i] = (sx * a, sy * b, sx * c + tx, sy * d + ty)
            else:
                self.T[i] = (sx, sy, tx, ty)

    def shift(self, idlist, dx, dy):
        self.affine(idlist, 1.0, 1.0, dx, dy)

    def place(self, idlist, s, src_pt, dst_pt):
        """uniform scale s mapping src_pt -> dst_pt"""
        self.affine(idlist, s, s, dst_pt[0] - s * src_pt[0], dst_pt[1] - s * src_pt[1])

    def set_rect(self, i, l, t, r, b):
        """map the (current) bbox of single-rect object i onto the given rect"""
        ol, ot, or_, ob = self.final_bbox([i])
        sx = (r - l) / (or_ - ol)
        sy = (b - t) / (ob - ot)
        self.affine([i], sx, sy, l - sx * ol, t - sy * ot)

    def tf(self, i):
        return self.T.get(i, (1.0, 1.0, 0.0, 0.0))

    def final_bbox(self, idlist):
        out = []
        for i in idlist:
            l, t, r, b = self.src.objs[i]['mm']
            sx, sy, tx, ty = self.tf(i)
            out.append((sx * l + tx, sy * t + ty, sx * r + tx, sy * b + ty))
        return (min(m[0] for m in out), min(m[1] for m in out), max(m[2] for m in out), max(m[3] for m in out))

    def final_y(self, i, y):
        sx, sy, tx, ty = self.tf(i)
        return sy * y + ty

    def final_x(self, i, x):
        sx, sy, tx, ty = self.tf(i)
        return sx * x + tx


def _num(v):
    d = Decimal(f"{v:.4f}").normalize()
    if d == d.to_integral():
        d = d.quantize(Decimal(1))
    return d


def build_pdf(src, placer, out_path, title="TESTIDE label - spacing reference", recolor=None,
              page_mm=None, keep_mm=None, drop_layers=(), drop_ids=()):
    """write a new PDF: transformed art + untouched dieline, cropped to the label, 1:1 scale"""
    ops = src.ops
    objs = src.objs
    new_ops = list(ops)           # shallow copy; replaced entries are new instructions
    delete = set()

    # ---------- 1. drop the proof-sheet layers MC4 (original-file thumbnail) + MC5 (template) ----------
    idx_mc4 = next(i for i, o in enumerate(ops) if str(o.operator) == 'BDC' and str(o.operands[1]) == '/MC4')
    for i in range(idx_mc4, len(ops)):
        delete.add(i)

    # ---------- 2. drop objects outside the label region (lid diagrams, swatches, circles) ----------
    kl, kt, kr, kb = keep_mm or KEEP_MM
    drop_layers = set(drop_layers); drop_ids = set(drop_ids)

    def inside(m):
        return m[0] >= kl and m[2] <= kr and m[1] >= kt and m[3] <= kb

    for o in objs:
        if o['start'] >= idx_mc4:
            continue
        if o['op'] in ('f', 'S', 'B', 'F', 'f*', 'B*', 's', 'b'):
            if o.get('clip'):
                continue
            if (not inside(o['mm'])) or o.get('layer') in drop_layers or o['id'] in drop_ids:
                s, e = o['start'], o['end']
                wrapped = (s >= 2 and str(ops[s - 2].operator) == 'q' and str(ops[s - 1].operator) == 'cm'
                           and str(ops[e + 1].operator) == 'Q')
                rng = range(s - 2, e + 2) if wrapped else range(s, e + 1)
                delete.update(rng)
        elif o['op'] == 'TEXT':
            # delete only the show operators that fall outside; keep all state operators (Tf etc. persist)
            tm = None
            line = None
            for i in range(o['start'], o['end'] + 1):
                op = str(ops[i].operator)
                a = ops[i].operands
                if op == 'Tm':
                    tm = [float(x) for x in a]
                    line = list(tm)
                elif op in ('Td', 'TD'):
                    tx_, ty_ = float(a[0]), float(a[1])
                    line[4] += tx_ * line[0] + ty_ * line[2]
                    line[5] += tx_ * line[1] + ty_ * line[3]
                elif op in ('Tj', 'TJ', "'", '"'):
                    px, py = line[4], line[5]
                    m = ((px - X0) / PT, (YTOP - py) / PT)
                    if not (kl <= m[0] <= kr and kt <= m[1] <= kb) or o.get('layer') in drop_layers:
                        delete.add(i)

    # ---------- 3. rewrite coordinates of transformed objects ----------
    for i, T in placer.T.items():
        sx, sy, tx, ty = T
        if abs(sx - 1) < 1e-12 and abs(sy - 1) < 1e-12 and abs(tx) < 1e-12 and abs(ty) < 1e-12:
            continue
        o = objs[i]
        assert o['op'] in ('f', 'S'), o['op']
        e_, f_ = o['ctm'][4], o['ctm'][5]
        assert abs(o['ctm'][0] - 1) < 1e-9 and abs(o['ctm'][3] - 1) < 1e-9 and abs(o['ctm'][1]) < 1e-9 and abs(o['ctm'][2]) < 1e-9
        # page-space affine in pt:  X' = sx*X + TX ; Y' = sy*Y + TY
        TX = X0 * (1 - sx) + PT * tx
        TY = YTOP * (1 - sy) - PT * ty
        # local coords: x' = sx*x + (sx*e + TX - e)
        cx = sx * e_ + TX - e_
        cy = sy * f_ + TY - f_
        for k in range(o['start'], o['end']):
            ins = ops[k]
            op = str(ins.operator)
            a = [float(x) for x in ins.operands]
            if op in ('m', 'l'):
                b = [sx * a[0] + cx, sy * a[1] + cy]
            elif op == 'c':
                b = [sx * a[0] + cx, sy * a[1] + cy, sx * a[2] + cx, sy * a[3] + cy, sx * a[4] + cx, sy * a[5] + cy]
            elif op in ('v', 'y'):
                b = [sx * a[0] + cx, sy * a[1] + cy, sx * a[2] + cx, sy * a[3] + cy]
            elif op == 're':
                b = [sx * a[0] + cx, sy * a[1] + cy, sx * a[2], sy * a[3]]
            elif op == 'h':
                continue
            else:
                raise ValueError(op)
            new_ops[k] = pikepdf.ContentStreamInstruction([_num(v) for v in b], ins.operator)

    # ---------- 3b. optional recolour (uses the spot inks already defined in the file) ----------
    before, after = {}, {}
    for i, cs in (recolor or {}).items():
        o = objs[i]
        stroke = o['op'] == 'S'
        setc = [pikepdf.ContentStreamInstruction([pikepdf.Name(cs)], pikepdf.Operator('CS' if stroke else 'cs')),
                pikepdf.ContentStreamInstruction([1], pikepdf.Operator('SCN' if stroke else 'scn'))]
        s_, e_ = o['start'], o['end']
        wrapped = (s_ >= 2 and str(ops[s_ - 2].operator) == 'q' and str(ops[s_ - 1].operator) == 'cm'
                   and str(ops[e_ + 1].operator) == 'Q')
        if wrapped:
            before[s_] = setc                      # inside the object's own q ... Q, so nothing leaks
        else:
            before[s_] = [pikepdf.ContentStreamInstruction([], pikepdf.Operator('q'))] + setc
            after[e_] = [pikepdf.ContentStreamInstruction([], pikepdf.Operator('Q'))]

    # ---------- 4. assemble: origin shift + kept ops ----------
    pl, ptp, pr, pb = page_mm or PAGE_MM
    ox = X0 + pl * PT
    oy = YTOP - pb * PT
    W = (pr - pl) * PT
    H = (pb - ptp) * PT
    out = [pikepdf.ContentStreamInstruction([1, 0, 0, 1, _num(-ox), _num(-oy)], pikepdf.Operator('cm'))]
    for i, ins in enumerate(new_ops):
        if i in delete:
            continue
        if i in before:
            out += before[i]
        out.append(ins)
        if i in after:
            out += after[i]
    data = pikepdf.unparse_content_stream(out)

    pdf = pikepdf.open(src.path)
    page = pdf.pages[0]
    page.Contents = pdf.make_stream(data)
    box = pikepdf.Array([0, 0, _num(W), _num(H)])
    for k in ('/MediaBox', '/CropBox', '/TrimBox', '/BleedBox', '/ArtBox'):
        page[k] = box
    for k in ('/Thumb', '/PieceInfo', '/LastModified'):
        if k in page:
            del page[k]
    res = page.Resources
    # prune resources that belonged to the dropped proof-sheet layers
    for group, names in (('/XObject', ['/Im0']), ('/Font', ['/TT0', '/T1_0']), ('/ColorSpace', ['/CS5']),
                         ('/ExtGState', ['/GS2']), ('/Properties', ['/MC4', '/MC5'])):
        if group in res:
            for n in names:
                if n in res[group]:
                    del res[group][n]
            if len(res[group].keys()) == 0:
                del res[group]
    # layers: keep only the four used ones
    props = res.Properties
    used = [props['/MC0'], props['/MC1'], props['/MC2'], props['/MC3']]   # Artwork, FOIL, Dielnie, DIEMSION
    ocp = pdf.Root.OCProperties
    ocp.OCGs = pikepdf.Array(used)
    D = pikepdf.Dictionary(ON=pikepdf.Array(used), Order=pikepdf.Array(list(reversed(used))),
                           RBGroups=pikepdf.Array([]))
    if '/Name' in ocp.D:
        D.Name = ocp.D.Name
    ocp.D = D
    if '/Metadata' in pdf.Root:
        del pdf.Root['/Metadata']       # XMP carried thumbnails of the old sheet
    pdf.docinfo['/Title'] = title
    pdf.remove_unreferenced_resources()
    pdf.save(out_path, compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)
    return {'page_w_mm': (pr - pl), 'page_h_mm': (pb - ptp), 'origin_pt': (ox, oy)}


def render(pdf_path, png_path, zoom=4.0, clip_mm=None, page_mm=None):
    """render with MuPDF. clip_mm = (l,t,r,b) in label mm, or None for the full page"""
    import pymupdf
    doc = pymupdf.open(pdf_path)
    pg = doc[0]
    clip = None
    if clip_mm is not None:
        pl, ptp, pr, pb = page_mm or PAGE_MM
        l, t, r, b = clip_mm
        clip = pymupdf.Rect((l - pl) * PT, (t - ptp) * PT, (r - pl) * PT, (b - ptp) * PT)
    pix = pg.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip, alpha=False)
    pix.save(png_path)
    return pix.width, pix.height
