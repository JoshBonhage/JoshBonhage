"""Turn the GitHub avatar into the ASCII portrait for update_profile.py's ART block.

    pip install pillow
    python avatar_to_ascii.py             # prints the art, paste it into ART
    python avatar_to_ascii.py 95 0.80 150 # cols keep sharpen

Three things this has to get right, learned the hard way on a white-cutout,
flat-lit photo:

  Aspect.  A character cell is ~1.93x taller than it is wide (ART_LEAD over
  ART_SIZE * the font's advance width), so ROWS is derived from the crop, not
  chosen. Picking it by hand is what makes ASCII portraits look stretched.

  Background.  Found by flood-filling in from the four corners, not by a
  brightness threshold -- lit skin is brighter than parts of the shirt, so a
  threshold eats the forehead.

  Tone band.  Contrast is stretched over the head's own percentile band. A
  black shirt otherwise claims the whole ramp and flattens the face to two
  characters. LOP/HIP trim the ends; drop HIP toward 0.9 to blow out the
  cheeks, raise LOP to keep more of the hair mass dark.
"""
import sys
import urllib.request
from PIL import Image, ImageDraw, ImageFilter, ImageOps

USER = "JoshBonhage"
COLS = int(sys.argv[1]) if len(sys.argv) > 1 else 95      # 95 is the widest that clears INFO_X
KEEP = float(sys.argv[2]) if len(sys.argv) > 2 else 0.80  # fraction of subject height; drops the shirt
SHARP = int(sys.argv[3]) if len(sys.argv) > 3 else 150
CELL = 8.7 / (0.6023 * 7.5)  # ART_LEAD / (Menlo advance * ART_SIZE) from update_profile.py
LOP, HIP = 0.04, 0.99
RAMP = " .:-=+*#%"  # light -> dark

with urllib.request.urlopen(f"https://github.com/{USER}.png?size=460") as r:
    open("avatar.png", "wb").write(r.read())

im = Image.open("avatar.png").convert("L")
flood = im.point(lambda v: 255 if v > 240 else 0)
for corner in [(0, 0), (im.width - 1, 0), (0, im.height - 1), (im.width - 1, im.height - 1)]:
    ImageDraw.floodfill(flood, corner, 128, thresh=10)
bg = flood.point(lambda v: 255 if v == 128 else 0)

im, bg = im.crop(box := ImageOps.invert(bg).getbbox()), bg.crop(box)
im, bg = [i.crop((0, 0, im.width, int(im.height * KEEP))) for i in (im, bg)]
rows = round(COLS * (im.height / im.width) / CELL)
cell_px = im.width / COLS

im = im.filter(ImageFilter.GaussianBlur(cell_px / 3))  # skin grain would just become speckle
im = im.filter(ImageFilter.UnsharpMask(radius=cell_px * 2, percent=SHARP, threshold=1))
im, bg = im.resize((COLS, rows), Image.LANCZOS), bg.resize((COLS, rows), Image.LANCZOS)
px, bgp = im.load(), bg.load()

head = sorted(px[x, y] for y in range(int(rows * 0.7)) for x in range(COLS) if bgp[x, y] < 128)
lo, hi = head[int(len(head) * LOP)], head[min(int(len(head) * HIP), len(head) - 1)]
print(f"{COLS}x{rows}, tone band {lo}-{hi}", file=sys.stderr)
for y in range(rows):
    row = ""
    for x in range(COLS):
        if bgp[x, y] >= 128:
            row += " "
        else:
            v = min(max(px[x, y], lo), hi)
            row += RAMP[min(int((hi - v) / (hi - lo) * (len(RAMP) - 1)) + 1, len(RAMP) - 1)]
    print(row.rstrip())
