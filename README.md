# team-racon-tours

Guide & employee profile pages (link-in-bio style) for Racon Tours.
Lives at **team.racon.tours**, deployed via Netlify.

## URLs
- `/` — team hub (noindex)
- `/scott/` — Scott Pinson (TourCWE guide)

## Structure
- `css/profile.css` — shared art-deco link-in-bio styles (brand tokens mirror tourcwe.com)
- `img/` — avatars (square JPGs)
- `assets/logo/` — candelabra brand marks + favicons (copied from join-tourcwe)

## Adding a person
1. `cp -r scott <name>` and edit name, tagline, avatar, links.
2. Drop a square avatar in `img/<name>.jpg`.
3. Add a card to `index.html` under "Our Guides".
4. Add `/<name>/` to `robots.txt` (Allow) and `sitemap.xml`.

## Notes
- Profile pages are guide-agnostic in structure; review links point at the shared
  TourCWE listings (Google / Tripadvisor / GetYourGuide).
- The "Great CWE Spots" map link uses the **viewer** URL (not the editable map link).
