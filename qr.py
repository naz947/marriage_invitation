# Requires: pip install pillow qrcode[pil]
from PIL import Image, ImageOps
import qrcode
import numpy as np
from PIL import ImageFilter, ImageDraw

URL = "https://naz947.github.io/marriage_invitation/index.html"
background_path = "images/marriage.png"   # your image file (PNG/JPG)
output_path = "final_with_qr.png"

qr_relative_size = 0.5   # QR width relative to min(bg_w, bg_h). 0.3-0.6 typical
module_pixel = None      # if None, computed from qr pixel count to fit relative size
finder_force_contrast = True
quiet_zone_modules = 4    # keep border of empty modules
dark_patch_strength = 0.55  # 0..1, how dark to make dark modules (1 = full black)
sharpen_finders = True
# ---------------------------------------------------

# 1) load background
bg = Image.open(background_path).convert("RGBA")
bg_w, bg_h = bg.size
min_side = min(bg_w, bg_h)

# 2) make QR (matrix) with high error correction (so small occlusions tolerated)
qrobj = qrcode.QRCode(
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=quiet_zone_modules
)
qrobj.add_data(URL)
qrobj.make(fit=True)
qr_img = qrobj.make_image(fill_color="black", back_color="white").convert("L")

# Convert QR image to numpy boolean matrix (1=dark, 0=light)
qr_arr = np.array(qr_img)
# threshold to boolean
qr_bool = (qr_arr < 128).astype(np.uint8)  # 1 for dark module

n_modules = qr_bool.shape[0]  # square
# 3) decide size: compute module_pixel so QR fits desired relative size
target_qr_px = int(min_side * qr_relative_size)
module_pixel = int(round(target_qr_px / n_modules))
if module_pixel < 2:
    module_pixel = 2
qr_px = module_pixel * n_modules

# 4) pick QR placement (center)
pos_x = (bg_w - qr_px) // 2
pos_y = (bg_h - qr_px) // 2

# 5) prepare working canvas (copy background)
out = bg.copy()

# 6) create a darker version of the area to use for dark modules
#    This lets modules look like part of the image but darker
area = out.crop((pos_x, pos_y, pos_x + qr_px, pos_y + qr_px)).convert("RGBA")
# Optionally blur slightly for blending
area_blur = area.filter(ImageFilter.GaussianBlur(radius=1)).convert("RGBA")
area_np = np.array(area_blur).astype(np.float32) / 255.0

# darken factor: lower brightness on dark modules
dark_factor = 1.0 - dark_patch_strength  # e.g. 0.45 if strength=0.55

# 7) build QR patch by iterating modules
patch = Image.new("RGBA", (qr_px, qr_px))
patch_np = np.array(patch).astype(np.float32) / 255.0

for r in range(n_modules):
    for c in range(n_modules):
        x0 = c * module_pixel
        y0 = r * module_pixel
        block = area_np[y0:y0+module_pixel, x0:x0+module_pixel, :].copy()
        if qr_bool[r, c] == 1:
            # dark module -> reduce brightness (but keep color/hue)
            # convert RGB to perceived luminance, scale down, preserve alpha
            rgb = block[..., :3]
            alpha = block[..., 3:]
            # multiply rgb channels
            rgb = rgb * dark_factor
            block[..., :3] = rgb
        else:
            # light module -> keep as is (maybe slightly brighten)
            pass
        patch_np[y0:y0+module_pixel, x0:x0+module_pixel, :] = block

# 8) ensure quiet zone is light (set to near-white) to help detection
bz = quiet_zone_modules * module_pixel
if bz > 0:
    # left, right, top, bottom
    patch_np[:bz, :, :3] = np.clip(patch_np[:bz, :, :3] * 1.1 + 0.95 - 0.95, 0, 1)
    patch_np[-bz:, :, :3] = np.clip(patch_np[-bz:, :, :3] * 1.1 + 0.95 - 0.95, 0, 1)
    patch_np[:, :bz, :3] = np.clip(patch_np[:, :bz, :3] * 1.1 + 0.95 - 0.95, 0, 1)
    patch_np[:, -bz:, :3] = np.clip(patch_np[:, -bz:, :3] * 1.1 + 0.95 - 0.95, 0, 1)

# 9) force-contrast finder patterns (top-left, top-right, bottom-left)
def force_finder(patch_np, module_pixel, n_modules, which='tl'):
    # find top-left finder center (at module coords [3..7] depending on QR version),
    # but simpler: standard finder is 7x7 modules at each corner (starting at 0)
    size = 7 * module_pixel
    if which == 'tl':
        rx, ry = 0, 0
    elif which == 'tr':
        rx, ry = (n_modules - 7) * module_pixel, 0
    else:  # bl
        rx, ry = 0, (n_modules - 7) * module_pixel
    # draw nested squares: black(outer), white(inner), black(center)
    # outer black
    patch_np[ry:ry+size, rx:rx+size, :3] = 0.0
    # inner white (remove 2 modules border)
    inner = module_pixel * 2
    patch_np[ry+inner:ry+size-inner, rx+inner:rx+size-inner, :3] = 1.0
    # center black (3x3 modules)
    center_size = module_pixel * 3
    cs = (size - center_size) // 2
    patch_np[ry+cs:ry+cs+center_size, rx+cs:rx+cs+center_size, :3] = 0.0

if finder_force_contrast:
    force_finder(patch_np, module_pixel, n_modules, 'tl')
    force_finder(patch_np, module_pixel, n_modules, 'tr')
    force_finder(patch_np, module_pixel, n_modules, 'bl')

# 10) convert patch back to image and paste into out
patch_img = (np.clip(patch_np, 0, 1) * 255).astype(np.uint8)
patch_img = Image.fromarray(patch_img, 'RGBA')
out.paste(patch_img, (pos_x, pos_y), patch_img)

# 11) optionally draw a faint border or hint (comment out if undesired)
draw = ImageDraw.Draw(out)
hint = False
if hint:
    margin = int(module_pixel * 0.8)
    draw.rectangle([pos_x - margin, pos_y - margin, pos_x + qr_px + margin, pos_y + qr_px + margin],
                   outline=(255,255,255,80), width=2)

# 12) save
out.save(output_path)
print("Saved:", output_path)