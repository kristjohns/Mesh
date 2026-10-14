"""Contact sheet of stills: python3 tools_sheet.py out.png file1 file2 ..."""
import sys
from PIL import Image
out, files = sys.argv[1], sys.argv[2:]
cols = 2
ims = [Image.open(f).convert('RGB').resize((960, 540)) for f in files]
rows = (len(ims) + cols - 1) // cols
W = Image.new('RGB', (960 * cols, 540 * rows))
for i, im in enumerate(ims):
    W.paste(im, ((i % cols) * 960, (i // cols) * 540))
W.save(out)
