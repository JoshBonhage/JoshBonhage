"""Turn the GitHub avatar into the ASCII portrait for update_profile.py's ART block.

    pip install pillow
    python avatar_to_ascii.py            # prints the art, paste it into ART
    python avatar_to_ascii.py 66 40 0.82 # cols rows keep

Knobs, because no photo maps cleanly to 9 grey levels:
  COLS/ROWS  more cells = more face, smaller type (ART_SIZE in update_profile.py)
  KEEP       fraction of the subject's height to keep; 0.82 drops most of the shirt
  P          percentile trimmed off each end of the head's tone band

Background is found by flood-filling in from the corners, not by brightness, so a
bright forehead never gets mistaken for the white cutout. Contrast is then
stretched across the *head's* own tone band -- a black shirt would otherwise eat
the whole ramp and flatten the face to two characters.
"""
import sys
import urllib.request
from PIL import Image, ImageDraw, ImageOps

USER = "JoshBonhage"
COLS = int(sys.argv[1]) if len(sys.argv) > 1 else 66
ROWS = int(sys.argv[2]) if len(sys.argv) > 2 else 40
KEEP = float(sys.argv[3]) if len(sys.argv) > 3 else 0.82
P = 0.05
RAMP = " .:-=+*#%"  # light -> dark

with urllib.request.urlopen(f"https://github.com/{USER}.png?size=460") as r:
    open("avatar.png", "wb").write(r.read())

im = Image.open("avatar.png").convert("L")
flood = im.point(lambda v: 255 if v > 240 else 0)
for corner in [(0, 0), (im.width - 1, 0), (0, im.height - 1), (im.width - 1, im.height - 1)]:
    ImageDraw.floodfill(flood, corner, 128, thresh=10)
bg = flood.point(lambda v: 255 if v == 128 else 0)

im, bg = im.crop(box := ImageOps.invert(bg).getbbox()), bg.crop(box)
im, bg = (i.crop((0, 0, im.width, int(im.height * KEEP))) for i in (im, bg))
im, bg = im.resize((COLS, ROWS), Image.LANCZOS), bg.resize((COLS, ROWS), Image.LANCZOS)
px, bgp = im.load(), bg.load()

head = sorted(px[x, y] for y in range(int(ROWS * 0.7)) for x in range(COLS) if bgp[x, y] < 128)
lo, hi = head[int(len(head) * P)], head[int(len(head) * (1 - P))]
for y in range(ROWS):
    row = ""
    for x in range(COLS):
        if bgp[x, y] >= 128:
            row += " "
        else:
            v = min(max(px[x, y], lo), hi)
            row += RAMP[min(int((hi - v) / (hi - lo) * (len(RAMP) - 1)) + 1, len(RAMP) - 1)]
    print(row.rstrip())
