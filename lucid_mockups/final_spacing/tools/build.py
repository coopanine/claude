#!/usr/bin/env python3
"""
build.py PARAMS.json OUTDIR   (PARAMS.json may be '-' or missing for defaults)

Writes into OUTDIR:
  label.pdf          vector PDF, 1:1 scale, dieline + dimension marks untouched
  label.png          full page render (MuPDF)
  crop_lid.png crop_center.png crop_left.png crop_protocol.png crop_bottom.png   zoomed crops
  geometry.json      every position / gap in label mm
  report.txt         readable summary of the same
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from labelkit import Source, build_pdf, render
from layout import solve, report


def main():
    params = {}
    if len(sys.argv) > 1 and sys.argv[1] not in ('-', ''):
        params = json.load(open(sys.argv[1]))
    out = sys.argv[2] if len(sys.argv) > 2 else 'out'
    os.makedirs(out, exist_ok=True)
    src = Source(os.path.join(HERE, 'src.pdf'))
    pl, G = solve(src, params)
    pdf = os.path.join(out, 'label.pdf')
    build_pdf(src, pl, pdf)
    render(pdf, os.path.join(out, 'label.png'), zoom=3.2)
    crops = {
        'crop_lid': (55, 6, 135, 56), 'crop_center': (60, 50, 130, 152), 'crop_left': (0, 52, 56, 152),
        'crop_protocol': (130, 52, 192, 152), 'crop_bottom': (0, 120, 196, 152),
    }
    for name, c in crops.items():
        render(pdf, os.path.join(out, name + '.png'), zoom=7.0, clip_mm=c)
    json.dump(G, open(os.path.join(out, 'geometry.json'), 'w'), indent=1)
    txt = report(G)
    open(os.path.join(out, 'report.txt'), 'w').write(txt + "\n")
    print(txt)


if __name__ == '__main__':
    main()
