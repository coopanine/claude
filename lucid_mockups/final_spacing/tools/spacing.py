"""least-squares side bearings of the label's humanist font (dist size), from the label's own text"""
import numpy as np
from labelkit import Source
from precise import ink
from glyphmap import charmap

SCALE = {'dist1': 1.0, 'dist2': 1.0, 'p_stor_text': 1.0498, 'p_fda_text': 0.964}

def solve(src, pl):
    obs = []      # (a, b, spaced, gap_norm)
    for key, k in SCALE.items():
        for r in charmap(src, pl, key)[0]:
            ids, chars, words = r['ids'], r['chars'], r['words']
            B = [ink(src, pl, [i]) for i in ids]
            for wi, w in enumerate(words):
                for a, b in zip(w, w[1:]):
                    obs.append((chars[a], chars[b], False, (B[b][0] - B[a][2]) / k))
                if wi + 1 < len(words) and words[wi + 1]:
                    a, b = w[-1], words[wi + 1][0]
                    obs.append((chars[a], chars[b], True, (B[b][0] - B[a][2]) / k))
    chars = sorted(set([o[0] for o in obs] + [o[1] for o in obs]))
    ix = {c: n for n, c in enumerate(chars)}
    nv = 2 * len(chars) + 1          # L[c], R[c], S
    rows, rhs, wts = [], [], []
    for a, b, sp, g in obs:
        v = np.zeros(nv); v[2 * ix[a] + 1] += 1; v[2 * ix[b]] += 1
        if sp: v[-1] = 1
        rows.append(v); rhs.append(g); wts.append(1.0)
    for c in 'ol':                   # gauge: symmetric round / stem letters
        if c in ix:
            v = np.zeros(nv); v[2 * ix[c]] = 1; v[2 * ix[c] + 1] = -1
            rows.append(v); rhs.append(0.0); wts.append(3.0)
    A = np.array(rows) * np.array(wts)[:, None]; y = np.array(rhs) * np.array(wts)
    sol, *_ = np.linalg.lstsq(A, y, rcond=None)
    L = {c: sol[2 * ix[c]] for c in chars}; R = {c: sol[2 * ix[c] + 1] for c in chars}; S = sol[-1]
    res = [g - (R[a] + L[b] + (S if sp else 0)) for a, b, sp, g in obs]
    return L, R, S, obs, np.array(res)

if __name__ == '__main__':
    from final_c import make
    src = Source('src.pdf'); pl, geo = make(src, 'thirds')
    L, R, S, obs, res = solve(src, pl)
    print(f'space {S:.4f} mm   n_obs {len(obs)}  residual rms {np.sqrt((res**2).mean()):.4f}  max {abs(res).max():.4f}')
    for c in sorted(L):
        n = sum(1 for o in obs if c in (o[0], o[1]))
        print(f'  {c!r}: L {L[c]:+.4f}  R {R[c]:+.4f}  (n={n})')
    # direct observations of the pairs we need
    need = [('S','t'),('t','r'),('r','e'),('e','e'),('e','t'),('t',','),('t','h'),(',','F'),(',','M'),('3','3'),('3','1'),('1','3')]
    for a, b in need:
        d = [(round(g, 4), sp) for x, y, sp, g in obs if x == a and y == b]
        print(f'  {a}{b}: fit {R.get(a, float("nan")) + L.get(b, float("nan")):.4f}  direct {d}')
