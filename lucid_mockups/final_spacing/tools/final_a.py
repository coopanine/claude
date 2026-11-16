"""
final_a.py - the final Option A artwork: v3cap.make2('A') + precise.refine()
(Protocol stack re-solved on exact flat-glyph metrics, POWERED BY text centred in its frame).
"""
import os, sys
from labelkit import Source, build_pdf
from v3cap import make2, GOLD_RULE, DASH
from precise import refine

HERE = os.path.dirname(os.path.abspath(__file__))


def make_final(src):
    pl, extra, geo = make2(src, 'A')
    R = refine(src, pl)
    return pl, extra, geo, R


def build_final(out_pdf):
    src = Source(os.path.join(HERE, 'src.pdf'))
    pl, extra, geo, R = make_final(src)
    build_pdf(src, pl, out_pdf, title='TESTIDE label - Option A, final spacing', recolor=GOLD_RULE,
              drop_ids=DASH, **extra)
    return R


if __name__ == '__main__':
    R = build_final(sys.argv[1] if len(sys.argv) > 1 else 'final_A.pdf')
    print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in R.items() if k != 'before'})
