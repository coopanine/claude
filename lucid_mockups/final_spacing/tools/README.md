# TESTIDE label spacing: rebuild tools

Rebuilds `TESTIDE_Label_Spacing_Final.pdf` from the factory proof (`src.pdf`) by rewriting
coordinates only. Outlines, Pantone spot colors, line weights, dieline and dimension marks are untouched.

- `python3 build.py - out/` builds with the default spacing (see DEFAULTS in `layout.py`)
- `python3 build.py params.json out/` builds a variant (any DEFAULTS key can be overridden)
- `python3 verify.py out/label.pdf` runs the integrity and alignment checks
- `python3 register.py out/label.pdf` compares the left column to the designers' screenshot (`shot.png`)

Needs: `pip install pikepdf pymupdf pillow numpy`. Units are mm from the top-left cut corner, y down.

Color variants: `build_pdf(src, placer, out, recolor={16: '/CS2'})` recolors object 16 (the rule above
DIETARY SUPPLEMENT) with a spot ink already in the file: `/CS0` Pantone 2728 C, `/CS1` 2758 C, `/CS2` 1255 C.

v2 (Lucid logo centered between the top fold crease and the dashed cap line, 0.96 mm lower):
`python3 build.py params_v2.json out/`. Earlier files are in `../previous/`.

Cap layout concept (Nov 12, `../../cap_layout_v3/`): `python3 v3cap.py out/` builds it on top of v2.
TESTIDE + tagline + POWERED BY badge centered in the 45 mm cap, statue scaled to the box top line,
rule and bottom text widened to the statue, Lucid logo on the back of the cap (split across the wrap seam:
`build_pdf(..., clip={...}, clones=[...])`), dashed cap line removed. `spin3d.py` renders the tube.
Round 2 (`make2` / `build_variant` in `v3cap.py`): option A = big Lucid logo on the back of the cap
(LUCID letters scaled to TESTIDE's letter height, x2.153), option B = logo + TESTIDE + tagline on the
front of the cap with the v2 body.

Final Option A (Nov 16, `../../option_a_proof/`):
- `python3 final_a.py out/final_A.pdf` builds the final artwork: option A plus `precise.refine()` (Protocol stack
  re-solved on exact flat-glyph metrics so its gaps are exactly equal; POWERED BY text centred in its frame).
- `python3 proof_a.py out/final_A.pdf out/proof.pdf [4views.jpg]` builds the 4-page A3 spacing proof. Every number
  is measured by `precise.py` (exact Bezier extrema, flat baselines and cap tops), never typed by hand.

Final Option C (Nov 18, `../../final_proof/`): `final_c.py` (logo + TESTIDE + tagline on the cap in even thirds,
POWERED BY badge back on the body, back of the cap blank, side panels as `final_b.py`).

Text corrections + address (Nov 19, `../../final_proof/TESTIDE_Final_Proof_Clean_rev2.pdf`):
`python3 addr.py out/TESTIDE_Final_Proof_Clean_rev2.pdf` builds Option C plus:
- "ALBION ®" -> "ALBION®" and "( Trigonella" -> "(Trigonella": the rest of each line closes up by one space of the
  Facts font (0.328 mm, solved from the label's own text by `spacing_c.py`, rms 0.004 mm).
- "(vegetable capsule). L-leucine." -> "(vegetable capsule), L-leucine.": the regular comma is not in the file; it is
  the label's bold comma (from "1,450") redrawn to the regular weight (head = the regular period, 0.158 x 0.336 mm).
- Address line: "68 SE 6th Street, Miami, FL 33131 • luciddaily.com" (line 2 of the Distributed-by block, same
  baseline 144.68, ends at x 49.14 inside the Facts column, 3.06 mm above the bottom fold). Every letter is a copy
  of the label's own outlines (`build_pdf(..., clones=[...])`): S from "Store", E = the label's F + L, h from the FDA
  box, t r e , from "Distributed" / "Miami,". The 6 and 8 exist nowhere in the file; they are Asul (SIL OFL,
  `fonts/`), the closest match to the label's 3 and 1 (`digitmatch.py`), inset 0.021 mm so the stroke weight
  matches (`strokew.py`), drawn with `build_pdf(..., extra=[...])`. Letter spacing comes from side bearings
  solved over the label's own text (`spacing.py`, rms 0.016 mm). The printer should reset this line in the
  label's real typeface; the proof shows the position and spacing.
