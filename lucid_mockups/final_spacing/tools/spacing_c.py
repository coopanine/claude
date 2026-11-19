"""space width of the condensed Supplement Facts font, from lines whose text is known"""
import numpy as np
from labelkit import Source
from precise import ink

LINES = [  # (ids in reading order, text)
    (list(range(473, 518)), 'Other Ingredients: Hydroxypropyl methylcellulose'),
    (list(range(518, 547)), '(vegetable capsule). L-leucine.'),
    (list(range(627, 652)), 'Zinc (as ALBION ® TRAACS® zinc'),
    (list(range(744, 775)), 'Fenugreek seed extract ( Trigonella'),
]

def obs_of(src, pl):
    obs = []
    for ids, t in LINES:
        chars = [c for c in t if c != ' ']
        assert len(chars) == len(ids), (t, len(chars), len(ids))
        B = sorted([ink(src, pl, [i]) for i in ids], key=lambda b: b[0])
        k = 0; words = []
        for w in t.split(' '):
            words.append(list(range(k, k + len(w)))); k += len(w)
        for wi, w in enumerate(words):
            for a, b in zip(w, w[1:]):
                obs.append((chars[a], chars[b], False, B[b][0] - B[a][2]))
            if wi + 1 < len(words):
                a, b = w[-1], words[wi + 1][0]
                obs.append((chars[a], chars[b], True, B[b][0] - B[a][2]))
    return obs

def solve(obs):
    chars = sorted(set([o[0] for o in obs] + [o[1] for o in obs])); ix = {c: n for n, c in enumerate(chars)}
    nv = 2 * len(chars) + 1; rows, rhs = [], []
    for a, b, sp, g in obs:
        v = np.zeros(nv); v[2 * ix[a] + 1] += 1; v[2 * ix[b]] += 1
        if sp: v[-1] = 1
        rows.append(v); rhs.append(g)
    for c in 'ol':
        v = np.zeros(nv); v[2 * ix[c]] = 3; v[2 * ix[c] + 1] = -3; rows.append(v); rhs.append(0)
    sol, *_ = np.linalg.lstsq(np.array(rows), np.array(rhs), rcond=None)
    L = {c: sol[2 * ix[c]] for c in chars}; R = {c: sol[2 * ix[c] + 1] for c in chars}
    res = np.array([g - (R[a] + L[b] + (sol[-1] if sp else 0)) for a, b, sp, g in obs])
    return L, R, sol[-1], res

if __name__ == '__main__':
    from final_c import make
    src = Source('src.pdf'); pl, geo = make(src, 'thirds')
    obs = obs_of(src, pl)
    L, R, S, res = solve(obs)
    print(f'condensed space {S:.4f}  rms {np.sqrt((res**2).mean()):.4f} max {abs(res).max():.4f}  n {len(obs)}')
    for a, b, sp, g in obs:
        if sp: print(f'   "{a} {b}" gap {g:.4f}  -> without space {g - S:.4f}')
    print('  (v', [round(g, 4) for a, b, sp, g in obs if a == '(' and b == 'v'], ' S®', [round(g, 4) for a, b, sp, g in obs if a == 'S' and b == '®'])
