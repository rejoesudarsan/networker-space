# Networker Space

This project documents the physical space shown in the supplied HSR building plans. Its intended use and any proposed changes are still to be defined.

## Existing layout

The PDF shows four levels:

- **Basement:** Parking, office spaces, storage/UPS, and courts.
- **Ground floor:** Living, dining, kitchen, family area, two bedrooms, puja room, caretaker room, and gardens.
- **First floor:** Living, dining, kitchen/utility, family area, library, one bedroom, and service rooms.
- **Second floor:** Two bedrooms, bathrooms, a dressing area, and terrace.

These are the drawing's existing room labels, not a proposed Networker Space layout. Dimensions and on-site conditions have not been verified.

## Source plans

- [HSR floor plans (PDF)](plans/HSR-plans-Model.pdf) — visually reviewed.
- [As-built drawing (DWG)](plans/plans-AS-BUILT.dwg) — supplied CAD file; not inspected yet.

Both files are saved in `plans/`, with the original attachments retained.

## Website (`site/`)

A single page, built with Vite and Three.js: the house from the as-built drawing, set on its street, living through one day. Scrolling runs the hours from dawn to late night:

1. The house opens, floor by floor.
2. Each room shows what it has become at that hour.
3. The house closes back up at night.

A "Who's inside" picker changes what the rooms are used for. People walk in and out of the gate throughout.

### Run

```sh
cd site
npm install
npm run dev      # local dev server
npm run build    # static output in site/dist/ (deploy to Vercel, Netlify, etc.)
npm run house    # rebuild public/models/ from plans/plans-AS-BUILT.dwg (needs libredwg)
```

### Edit

| File | What it holds |
|---|---|
| `src/world/program.js` | Rooms, the people options, and what each room becomes by hour and by who's inside |
| `src/world/world.js` | The 3D world: light through the day, floors, trees, people, the camera path |
| `src/world/characters.js` | Articulated characters, activity poses, and gathering furniture |
| `src/world/details.js` | Floor-attached architectural detail, basement access, planting, and neighbourhood detail |
| `src/world/windows.js` | Window frames and glazing placed from the CAD sill geometry, lowering with the cutaway walls |
| `src/world/traffic.js` | Moving autos and scooters with rolling wheels |
| `src/world/main.js` | Scroll and clock. `BOOKING_URL` sets every "Book a call" button |
| `index.html` | The chapter copy |

The previous five-page site (home, house walk, memberships, evenings, join) is kept in `archive/site-pages-2026-10-04/`.

The garage ramp and office court have separate openings through the ground-floor slab and front base wall, following the supplied plan. Floor-local details travel with their floor in the cutaway. Furnishings, people, and neighbourhood dressing are illustrative; they are not a survey of the finished property.
