# TESTIDE label spacing: rebuild tools

Rebuilds `TESTIDE_Label_Spacing_Final.pdf` from the factory proof (`src.pdf`) by rewriting
coordinates only. Outlines, Pantone spot colors, line weights, dieline and dimension marks are untouched.

- `python3 build.py - out/` builds with the default spacing (see DEFAULTS in `layout.py`)
- `python3 build.py params.json out/` builds a variant (any DEFAULTS key can be overridden)
- `python3 verify.py out/label.pdf` runs the integrity and alignment checks
- `python3 register.py out/label.pdf` compares the left column to the designers' screenshot (`shot.png`)

Needs: `pip install pikepdf pymupdf pillow numpy`. Units are mm from the top-left cut corner, y down.
