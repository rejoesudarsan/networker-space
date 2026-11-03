# Fourthspace founding sponsorship redesign

Deliverable: `Fourthspace-Founding-Sponsorship-Redesigned.pdf` (11 pages, 1440 × 810).

Matching introduction: `Fourthspace-Introduction-One-Pager.pdf` (one A4 portrait page). Explains the public café, founder membership, gatherings and HSR Founders Club origin without membership pricing or a sponsorship pitch. `build_one_pager.py` rebuilds both PDFs using the same green/paper palette and typography. Created at the user's request to retain the current design; new logo concepts were not applied. The one-pager was rendered and checked for layout, one-page length and source-consistent positioning.

The original PDF and the membership / Mild Atta decks remain unchanged.

## Build

Run `build_sponsorship.py` with Python containing ReportLab and Pillow. Local bundled interpreter used:

```
/Users/rejoesudarsan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 output/pdf/fourthspace-decks/redesign/build_sponsorship.py
```

Render with `pdftoppm -scale-to 1440 -png` for visual verification. Preview pages live in `preview/`.

## Inputs and decisions

- Commercial truth: parent `model.json`, `SPONSORSHIP-OPERATING-PLAN.md`, current deck and its build source.
- Three new OpenAI built-in image-generation assets: signature drink, merchandise bay, branded cup. Exact prompts and provenance are under `assets/`.
- Three fresh CPU Cycles views of existing baked room models: café, courtyard, event space. These depict proposed fit-outs, not current built conditions. Source baked textures retain some dark fixture faces.
- `render_baked_rooms.py` reproduces the camera compositions from repository glTFs; no model or bake source was edited.
- Corgi homepage and `/partnerships` read live on 3 November 2026. Applied lesson: make the drink and sponsor attribution tangible. Its partnerships, operating figures, hours and pricing were not adopted as Fourthspace claims.
- Newsreader / Schibsted Latin font files were instantiated from the existing site packages because the older deck font files lacked the needed Latin glyphs. A local Ubuntu symbol fallback supplies rupee and comparison glyphs.
- `DESIGN.md` scopes the visual direction to this PDF; older website context was not treated as current commercial truth.

## Verification

`layout-check.json`: page count and text bounds. `verification.json`: extracted commercial phrase checks. Rendered page review checks visual readability and asset placement independently of extraction.

No contact email or booking URL was supplied, so the closing action names a category-fit conversation with HSR Founders Club without inventing contact information.
