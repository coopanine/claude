"""map outlined glyph objects of the humanist-font text groups to characters"""
from labelkit import Source, ELEMENTS as E
from precise import ink, flat_edges, _clusters

TEXTS = {
    'dist1': ['Distributed by Lucid Metabolic Labs, Inc.'],
    'dist2': ['Miami, FL 33131 • luciddaily.com'],
    'p_stor_text': ['Store in a cool, dry place.'],
    'p_fda_text': ['*These statements have not been evaluated by the Food',
                   'and Drug Administration. This product is not intended',
                   'to diagnose, treat, cure, or prevent any disease.'],
    'p_warn_body': None,
}

def lines_of(src, pl, ids, tol=0.6):
    """group glyph ids into lines by ink bottom (robust: cluster on ink centre y)"""
    B = {i: ink(src, pl, [i]) for i in ids}
    ys = sorted(set(round((B[i][1] + B[i][3]) / 2, 3) for i in ids))
    groups = _clusters(ys, tol)
    out = []
    for g in groups:
        lo, hi = min(g) - 1e-6, max(g) + 1e-6
        row = [i for i in ids if lo <= round((B[i][1] + B[i][3]) / 2, 3) <= hi]
        out.append(sorted(row, key=lambda i: B[i][0]))
    return out, B

def charmap(src, pl, key):
    ids = list(E[key])
    rows, B = lines_of(src, pl, ids)
    texts = TEXTS[key]
    res = []
    assert len(rows) == len(texts), (key, len(rows), len(texts), [len(r) for r in rows])
    for row, t in zip(rows, texts):
        chars = [c for c in t if c != ' ']
        assert len(chars) == len(row), (key, t, len(chars), len(row))
        # word boundaries: index positions where a space precedes
        k = 0; words = []
        for w in t.split(' '):
            words.append(list(range(k, k + len(w)))); k += len(w)
        res.append({'ids': row, 'chars': chars, 'words': words, 'text': t})
    return res, B

if __name__ == '__main__':
    from final_c import make
    src = Source('src.pdf'); pl, geo = make(src, 'thirds')
    for key in ('dist1', 'dist2', 'p_stor_text', 'p_fda_text'):
        res, B = charmap(src, pl, key)
        for r in res:
            print(key, r['text'], 'OK', len(r['ids']))
