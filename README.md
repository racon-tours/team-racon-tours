# team-racon-tours

Guide & employee profile pages (link-in-bio style) for Racon Tours.
Lives at **team.racon.tours**, deployed via Netlify. **All pages are noindex.**

## Architecture

- **Source of truth:** Google Sheet `team-racon-tours` in the default Drive folder.
  Sheet ID is recorded in `.sheet_id` (gitignored). Two tabs:
  - **`people`** — slug, name, tagline, image_filename, meta_description, footer_html, published
  - **`links`** — slug, section, title, subtitle, url, published
    (Column A has a dropdown of valid slugs from `people` — typos rejected at input.)
- **Build:** `publish.py` reads the sheet, writes:
  - `/index.html` (hub)
  - `/<slug>/index.html` (profile shells — name/photo/tagline/meta baked in)
  - `/data/roster.json` (link/section content for client-side fetch)
  - `/robots.txt` (full disallow)
- **Runtime:** each profile page fetches `/data/roster.json` and renders its
  sections + buttons via `/js/profile.js`.
- **Cron:** **GitHub Actions** — `.github/workflows/nightly-publish.yml`
  runs daily at 08:15 UTC (03:15 CDT). Manual trigger:
  `gh workflow run nightly-publish.yml`. No Mac or local machine needed.
  Reads the sheet via the **public GET feed**
  (`sheets-endpoint`'s `doGet ?action=read_roster`) — no secrets required at
  build time. Netlify deploy uses the `NETLIFY_AUTH_TOKEN` GH Actions secret.

## Editing

1. Open the sheet (link in `.sheet_id`).
2. Add/edit rows. Drag rows to reorder — **row order = display order.**
3. For a new person, drop a 256×256+ square JPG at `img/<slug>.jpg` (use
   `scripts/add-photo.py` to crop/resize any input).
4. Either wait until tomorrow morning, hit "Run workflow" on the GH Actions
   page, or run `./publish.sh` locally.

### Schema notes

- **`slug`** — URL-safe (lowercase). Profile lives at `/<slug>/`.
- **`section`** — used verbatim as the heading. Same name → same group.
  Section order = first appearance in the sheet.
- **HTML allowed** in `tagline`, `title`, `subtitle`, `footer_html` — use
  `&mdash;`, `&nbsp;`, `&rsquo;`, `<em>` etc.
- **`url`** must start with `http(s)://` (others dropped silently).
- **`published`** — leave blank (defaults TRUE) or set FALSE to hide.

## Adding a person

```
./scripts/add-photo.py ~/Desktop/jane.heic jane
# then add rows to the sheet's `people` and `links` tabs
# then either wait, or:
./publish.sh                              # local build + deploy
# or:
gh workflow run nightly-publish.yml       # fire CI build
```

## Manual deploys

```
./publish.sh                   # build (auth POST) + deploy
./publish.sh --no-deploy       # local dry build
./publish.sh --from-public-feed --no-deploy  # build using the public feed (what CI uses)
```

## Files

- `publish.py` — generator. Run via `./publish.sh` locally.
- `js/profile.js` — client-side renderer of `roster.json`.
- `css/profile.css` — shared art-deco styles.
- `img/` — avatars (one per slug).
- `assets/logo/` — brand marks, favicons.
- `scripts/add-photo.py` — image prep helper (HEIC/PNG/JPG → 480px square JPG).
- `.github/workflows/nightly-publish.yml` — the cron.
- `.sheet_id` — local-only, the spreadsheet ID.
