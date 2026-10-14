# Fido Brand Guide (working reference)

Owner: Cooper Allen, Chief Brand Officer
Source of truth: Figma "Daily Fido | Final Pack" (Refinements / World Buildout), file key `vHgeif3QsOUhLnkWJ7oQtE`, nodes `59:408` and `1:884`. Proto password held by Cooper.
Status: Built from Cooper's stated system + licensed font files. Figma content not yet ingested (MCP needs edit access). Items marked TBD come from the Figma pack.

Specimen: `fido/fido_brand_sheet.png` (rendered with the real fonts)

---

## Typography

| Role | Typeface | Notes |
|---|---|---|
| Wordmark | Bugrino Black | Studio Muhittin Güneş |
| Headlines | Bugrino Black | Upper + lowercase both available |
| Flavor stickers | Bugrino Black | Short, punchy names |
| Supporting | ABC Diatype Mono Bold | Body, labels, specs, legal, callouts |

Observed in the files:
- Bugrino Black: ultra-heavy geometric grotesk, small counters, deep descenders (y, g, p). Set tight leading (0.85 to 1.0). Needs room below lines with descenders.
- Diatype Mono Bold: only the Bold weight is licensed in the pack. No Regular, so hierarchy comes from size, case and color, not weight.
- Mono looks best for small caps-style labels: uppercase, +6 to 8% tracking.

Rules:
- Two typefaces only. No third font, no fallback system font in final work.
- Bugrino never for long body copy.
- Diatype Mono never for the wordmark.

Licensing (Bugrino EULA, Studio Muhittin Güneş):
- License tiers: Desktop, Web, App, Broadcasting, Social Media, Logo/Wordmark. Confirm which tiers Fido bought before using on web, app, or paid social. TBD.
- Do not share, upload, or send font files to vendors without their own license. Vendors under direct supervision who do not keep the files are OK.
- Font files are intentionally NOT stored in this repo.
- ABC Diatype Mono (Dinamo) license terms: TBD, assume same caution.

---

## Color

| Name | Hex | Role |
|---|---|---|
| Fido Black | `#16171F` | Core |
| Cream | `#F2EDE2` | Core |
| Beige | `#F6EBD8` | Support |
| True White | `#FFFFFF` | Support |
| Green | `#61C554` | Accent, selective |
| Salmon | `#F57E6C` | Accent, selective |

Usage:
- Default canvas is Cream with Fido Black type, or the reverse.
- Beige and White support layouts, they do not lead.
- Green and Salmon are for flavor stickers and moments that need distinction. Not backgrounds for whole layouts, not body text color.

Contrast (WCAG ratio, 4.5 needed for small text):
| Pair | Ratio | Verdict |
|---|---|---|
| Black on Cream | 15.3 | Pass |
| Black on White | 17.9 | Pass |
| Black on Beige | 15.1 | Pass |
| Black on Green | 8.2 | Pass |
| Black on Salmon | 6.9 | Pass |
| Cream/White on Green | 1.9 / 2.2 | Fail |
| Cream/White on Salmon | 2.2 / 2.6 | Fail |
| Green on Salmon | 1.2 | Never |

Takeaway: type on Green or Salmon is always Fido Black. Never put Green and Salmon directly against each other.
Beige vs Cream is only 1.0 contrast. They read as near-identical, so do not rely on them to separate elements.

CSS tokens:
```css
:root{
  --fido-black:#16171F; --fido-cream:#F2EDE2; --fido-beige:#F6EBD8;
  --fido-white:#FFFFFF; --fido-green:#61C554; --fido-salmon:#F57E6C;
}
```

---

## Brand checklist (for reviewing any asset)
- Only Bugrino Black + Diatype Mono Bold
- Bugrino on wordmark, headlines, flavor stickers only
- Core palette carries the layout; accents used sparingly
- Any text on Green/Salmon is Fido Black
- Green and Salmon not touching
- Font licensing tier covers the channel (web, social, app, broadcast)

---

## TBD (pull from Figma pack)
- What Fido / Daily Fido is (product category, SKUs, flavors)
- Wordmark lockup, case, clear space, minimum size
- Sticker shapes and flavor-to-color mapping
- Photography / illustration / "world" direction
- Voice, tone, tagline, messaging pillars
- Packaging specs
