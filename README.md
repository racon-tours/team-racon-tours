# team-racon-tours

Guide & employee profile pages (link-in-bio style) for Racon Tours.
Lives at **team.racon.tours**, deployed via Netlify. **All pages are noindex.**

## Architecture

- **Source of truth:** Google Sheet `team-racon-tours` in the default Drive folder.
  Sheet ID is recorded in `.sheet_id` (gitignored). Two tabs:
  - **`people`** — slug, name, tagline, image_filename, meta_description, footer_html, published
  - **`links`** — slug, section, title, subtitle, url, published
- **Build:** `./publish.sh` reads the sheet, writes:
  - `/index.html` (hub, lists every published person)
  - `/<slug>/index.html` (profile shells — name/photo/tagline/meta, baked in)
  - `/data/roster.json` (link/section content for client-side fetch)
  - `/robots.txt` (full disallow — pages are noindex)
- **Runtime:** each profile page fetches `/data/roster.json` and renders its
  sections + buttons via `/js/profile.js`.
- **Nightly cron:** `~/Library/LaunchAgents/com.racon.team-publish.plist`
  runs `./publish.sh` on the Mac mini once nightly.

## Editing

1. Open the sheet (`https://docs.google.com/spreadsheets/d/<id>/edit`).
2. Add/edit rows. Drag rows to reorder — **row order = display order.**
3. For a new person, also drop a 256×256 square JPG at `img/<slug>.jpg`.
4. Either wait until tomorrow morning (nightly cron) or `./publish.sh` now.

### Schema notes

- **`slug`** — URL-safe (lowercase, no spaces). The page lives at `/<slug>/`.
- **`section`** — used verbatim as the heading. Same section name → same group.
  Section order is determined by *first appearance* in the sheet.
- **HTML allowed** in `tagline`, `title`, `subtitle`, `footer_html` — use
  `&mdash;`, `&nbsp;`, `&rsquo;`, `<em>` etc.
- **`url`** must start with `http://` or `https://` (others are dropped).
- **`published`** — leave blank (defaults TRUE) or set FALSE/0 to hide.

## Adding a person — checklist

1. Drop a square headshot at `img/<slug>.jpg` (256×256 or 480×480, optimized).
2. Add a row to `people`. Most rows can have `meta_description` and
   `footer_html` blank — defaults are sensible.
3. Add `links` rows for that slug — sections by first-appearance.
4. Run `./publish.sh` (or wait for the nightly cron).

## Manual deploys

```
./publish.sh              # build + deploy
./publish.sh --no-deploy  # build only, locally (writes generated files)
```

## Files

- `publish.py` / `publish.sh` — the generator + deploy wrapper
- `js/profile.js` — client-side renderer of `roster.json`
- `css/profile.css` — shared art-deco styles
- `img/` — avatars (one per slug)
- `assets/logo/` — brand marks, favicons
- `.sheet_id` — local-only, the spreadsheet ID
