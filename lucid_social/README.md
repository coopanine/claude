# TESTIDE pre-launch social kit (proposed)

- `plan/plan.json`: the campaign ("Thousands of Years"), every post's on-image copy, caption, hashtags, posting day and claim note.
- `out/posts/`: PNG masters. F01-F09 feed (1080x1350; F05a-f is the carousel), S01-S04 stories (1080x1920),
  AVATAR, HL1-HL4 highlight covers, PROFILE (grid preview).
- `out/reel/TESTIDE_teaser_reel.mp4`: 10.5 s 360-degree reveal (1080x1920, 30 fps) + cover.
- `out/review/`: the review page (published as a private artifact).
- `tools/`: `render_tube.py` (3D renders of the final rev6 label), `social.py` (brand templates, Chromium render),
  `reel.py`, `board.py` (profile preview), `page.py` (review page). `brief/BRIEF.md`: creative brief and claim rules.

Fonts are not committed (Ashcroft is licensed): set LUCID_FONTS to a folder with the Ashcroft woff2 files from the
packaging handoff email, and LUCID_MONO to Share Tech Mono (stand-in for Mono45 Headline).
