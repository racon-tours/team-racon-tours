#!/usr/bin/env python3
"""add-photo: prep a headshot for team.racon.tours.

Usage:  ./scripts/add-photo.py <input-image> <slug>
        ./scripts/add-photo.py ~/Desktop/scott-new.heic scott
        ./scripts/add-photo.py /path/to/photo.jpg amanda

Center-crops to square, resizes to 480px, optimizes JPEG, writes to img/<slug>.jpg.
Handles HEIC via macOS `sips` (no pillow_heif required).
"""
import os, subprocess, sys, tempfile
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    raise SystemExit("Pillow required: pip3 install --break-system-packages Pillow")

if len(sys.argv) != 3:
    print(__doc__, file=sys.stderr)
    raise SystemExit(2)

src = Path(sys.argv[1]).expanduser().resolve()
slug = sys.argv[2].strip().lower()
if not src.exists():
    raise SystemExit(f"not found: {src}")
if not slug.replace("-","").replace("_","").isalnum():
    raise SystemExit(f"invalid slug (use lowercase alphanumeric + - or _): {slug}")

repo = Path(__file__).resolve().parent.parent
out = repo / "img" / f"{slug}.jpg"
out.parent.mkdir(exist_ok=True)

# Convert HEIC → JPEG via sips first, into a temp file
work = src
tmp = None
if src.suffix.lower() in (".heic", ".heif"):
    tmp = Path(tempfile.mkstemp(suffix=".jpg")[1])
    subprocess.run(["/usr/bin/sips", "-s", "format", "jpeg", str(src),
                    "--out", str(tmp)], check=True, capture_output=True)
    work = tmp

try:
    im = Image.open(work)
    # Honor EXIF orientation
    try:
        from PIL import ImageOps
        im = ImageOps.exif_transpose(im)
    except Exception:
        pass
    im = im.convert("RGB")
    w, h = im.size
    s = min(w, h)
    left, top = (w - s) // 2, (h - s) // 2
    im = im.crop((left, top, left + s, top + s))
    target = 480 if s >= 480 else s   # don't upscale
    if im.size[0] != target:
        im = im.resize((target, target), Image.LANCZOS)
    im.save(out, "JPEG", quality=86, optimize=True, progressive=True)
finally:
    if tmp and tmp.exists():
        tmp.unlink()

size_kb = out.stat().st_size // 1024
print(f"wrote {out.relative_to(repo)} — {target}x{target}, {size_kb} KB")
print(f"next: add a row to the sheet's `people` tab with image_filename={slug}.jpg")
