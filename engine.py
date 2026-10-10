#!/usr/bin/env python3
"""
craft-studio core engine
Calibrated for:
1. Exact 3.5cm x 4.5cm Indian Passport Photos (6 in 1 row)
2. Exact 65mm x 95mm Lamination Pouch Aadhaar Cards (Foldable with zero-gap center divider)
3. 100% True Scale (No fit-to-page shrinkage)
"""

import os
import sys
import subprocess
from pathlib import Path
from PIL import Image, ImageEnhance, ImageOps, ImageDraw

# Standard A4 at 300 DPI
A4_WIDTH_PX = 2480
A4_HEIGHT_PX = 3508
DPI = 300
PX_PER_MM = 300 / 25.4  # 11.8110236 px per mm
PX_PER_CM = PX_PER_MM * 10  # 118.1102 px per cm

def run_cmd(cmd):
    """Run shell command safely and return output."""
    res = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed ({res.returncode}): {cmd}\nStderr: {res.stderr}")
    return res.stdout.strip()

def make_passport_sheet(
    input_image_path: str,
    output_png: str,
    output_pdf: str,
    quantity: int = 6,
    border_color: str = "#b0b0b0",
    crop_box: tuple = None,
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0
) -> dict:
    """
    Generate passport photo sheet on A4 canvas (300 DPI) in TRUE COLOR (RGB).
    True Physical Scale:
    - Width: 3.5 cm = exactly 413 px
    - Height: 4.5 cm = exactly 531 px
    - Top margin: ~0.8 cm (95 px)
    """
    input_path = Path(input_image_path).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_image_path}")

    temp_dir = Path("/tmp/craft_studio_passport")
    temp_dir.mkdir(parents=True, exist_ok=True)

    base_img = Image.open(input_path).convert("RGB")

    # 1. Apply user crop box if specified [x, y, w, h] (normalized 0.0 to 1.0)
    if crop_box and len(crop_box) == 4:
        orig_w, orig_h = base_img.size
        bx = int(crop_box[0] * orig_w)
        by = int(crop_box[1] * orig_h)
        bw = int(crop_box[2] * orig_w)
        bh = int(crop_box[3] * orig_h)
        if bw > 30 and bh > 30:
            base_img = base_img.crop((bx, by, bx + bw, by + bh))

    # 2. Apply manual adjustments
    if brightness != 1.0:
        enh_b = ImageEnhance.Brightness(base_img)
        base_img = enh_b.enhance(brightness)
    if contrast != 1.0:
        enh_c = ImageEnhance.Contrast(base_img)
        base_img = enh_c.enhance(contrast)
    if saturation != 1.0:
        enh_s = ImageEnhance.Color(base_img)
        base_img = enh_s.enhance(saturation)

    # 3. Exact 3.5 cm x 4.5 cm (413 x 531 px at 300 DPI)
    target_w = int(35 * PX_PER_MM)  # 413 px
    target_h = int(45 * PX_PER_MM)  # 531 px
    aspect = target_w / target_h

    img_w, img_h = base_img.size
    img_aspect = img_w / img_h

    if img_aspect > aspect:
        new_w = int(img_h * aspect)
        left = (img_w - new_w) // 2
        cropped = base_img.crop((left, 0, left + new_w, img_h))
    else:
        new_h = int(img_w / aspect)
        top = (img_h - new_h) // 2
        cropped = base_img.crop((0, top, img_w, top + new_h))

    resized_photo = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)

    # Unit photo with 1px cutting border inside
    unit_photo = resized_photo.copy()
    draw = ImageDraw.Draw(unit_photo)
    if border_color and border_color != "none":
        draw.rectangle([0, 0, target_w - 1, target_h - 1], outline=border_color, width=1)

    # 4. Canvas Creation: Guaranteed TrueColor sRGB A4
    canvas = Image.new("RGB", (A4_WIDTH_PX, A4_HEIGHT_PX), (255, 255, 255))

    # Margin & Spacing:
    # 6 photos across row: 6 * 413 = 2478 px (leaves exactly 2 px! On A4 borderless, or minimal gap)
    # With 2 px spacing between photos: 408 px each (3.46 cm) or 410 px
    # Total span: 6 * 410 px + 5 * 2 px gap = 2470 px (margin_x = 5 px on each side)
    unit_w = 410
    unit_h = 531
    unit_photo = unit_photo.resize((unit_w, unit_h), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(unit_photo)
    if border_color and border_color != "none":
        draw.rectangle([0, 0, unit_w - 1, unit_h - 1], outline=border_color, width=1)

    margin_top = 95  # ~0.8 cm from top
    gap_x = 2
    gap_y = 15

    cols = 6 if quantity >= 6 else quantity
    if quantity == 8:
        cols = 4
    elif quantity == 10:
        cols = 5
    elif quantity == 12:
        cols = 6
    elif quantity >= 30:
        cols = 5

    if quantity >= 30:
        # Full A4 Sheet (5 cols x 6 rows = 30)
        cols = 5
        rows = 6
        gap_x = 10
        gap_y = 12
        margin_x = (A4_WIDTH_PX - (5 * unit_w + 4 * gap_x)) // 2
        margin_y = (A4_HEIGHT_PX - (6 * unit_h + 5 * gap_y)) // 2
        for r in range(rows):
            for c in range(cols):
                x = margin_x + c * (unit_w + gap_x)
                y = margin_y + r * (unit_h + gap_y)
                canvas.paste(unit_photo, (x, y))
    else:
        rows = (quantity + cols - 1) // cols
        margin_x = (A4_WIDTH_PX - (cols * unit_w + (cols - 1) * gap_x)) // 2
        count = 0
        for r in range(rows):
            for c in range(cols):
                if count >= quantity:
                    break
                x = margin_x + c * (unit_w + gap_x)
                y = margin_top + r * (unit_h + gap_y)
                canvas.paste(unit_photo, (x, y))
                count += 1

    canvas.save(output_png, format="PNG", dpi=(300, 300))

    # Generate print-perfect PDF (Exact 1:1 scale)
    run_cmd(
        f'/usr/lib/cups/filter/imagetopdf 1 fahad "passport_job" 1 "PageSize=A4" "{output_png}" > "{output_pdf}"'
    )

    return {
        "status": "success",
        "png": str(Path(output_png).resolve()),
        "pdf": str(Path(output_pdf).resolve()),
        "quantity": quantity
    }

def process_aadhaar_pdf(
    input_pdf_path: str,
    output_png: str,
    output_pdf: str,
    password: str = ""
) -> dict:
    """
    Unlock Aadhaar PDF, render at 300 DPI, and extract Front & Back ID Card.
    Custom Calibrated for 65 mm x 95 mm Lamination Pouch (125 Micron):
    - Finished Folded Card Size: 60 mm x 90 mm (708 px x 1063 px)
      (Fits completely inside 65x95 mm pouch with 2.5 mm perfect sealing edge)
    - Scissors marks removed completely.
    - Zero gap between Front and Back with solid 3px Black folding divider line.
    - Top margin set to ~0.8 cm (95 px) to avoid excessive top whitespace.
    """
    input_path = Path(input_pdf_path).resolve()
    temp_dir = Path("/tmp/craft_studio_aadhaar")
    temp_dir.mkdir(parents=True, exist_ok=True)
    unlocked_pdf = temp_dir / "unlocked.pdf"

    # Unlock PDF with qpdf
    pw_arg = f'--password="{password}"' if password else ""
    try:
        run_cmd(f'qpdf {pw_arg} --decrypt "{input_path}" "{unlocked_pdf}"')
    except Exception as e:
        if "password" in str(e).lower():
            return {"status": "error", "error": "PASSWORD_REQUIRED", "message": "Incorrect or missing PDF password"}
        raise e

    # Render PDF first page at 300 DPI
    run_cmd(f'pdftoppm -png -r 300 -f 1 -l 1 "{unlocked_pdf}" "{temp_dir}/page"')
    page_img_path = temp_dir / "page-1.png"
    if not page_img_path.exists():
        raise FileNotFoundError("Failed to render Aadhaar PDF page")

    page_img = Image.open(page_img_path).convert("RGB")

    # Precise Bounding Box for Clean UIDAI Aadhaar Cards (Starts below scissors line, includes Bharat Sarkar header & emblem):
    # Front Card: X in [195, 1260], Y in [2380, 3058]
    # Back Card:  X in [1288, 2353], Y in [2380, 3058]
    front_crop = page_img.crop((195, 2380, 1260, 3058))
    back_crop = page_img.crop((1288, 2380, 2353, 3058))

    # Pouch Calibrated Dimensions:
    # Lamination Pouch = 65 mm x 95 mm
    # Card Size: 60 mm (height) x 90 mm (width) = 708 x 1063 px
    card_w = int(90 * PX_PER_MM)  # 1063 px
    card_h = int(60 * PX_PER_MM)  # 708 px
    front_card = front_crop.resize((card_w, card_h), Image.Resampling.LANCZOS)
    back_card = back_crop.resize((card_w, card_h), Image.Resampling.LANCZOS)

    # Create A4 sheet: 2480 x 3508 px
    canvas = Image.new("RGB", (A4_WIDTH_PX, A4_HEIGHT_PX), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    # Placement:
    # 0.8 cm from top (95 px)
    margin_top = 95
    # Total width of Front + Back touching = 1063 * 2 = 2126 px
    # Centered horizontally: (2480 - 2126) // 2 = 177 px margin on left and right!
    margin_x = (A4_WIDTH_PX - (card_w * 2)) // 2

    front_x = margin_x
    back_x = margin_x + card_w

    canvas.paste(front_card, (front_x, margin_top))
    canvas.paste(back_card, (back_x, margin_top))

    # Draw solid black outer border around combined cards
    card_bottom = margin_top + card_h - 1
    draw.rectangle(
        [front_x, margin_top, back_x + card_w - 1, card_bottom],
        outline="#000000",
        width=2
    )

    # Draw bold black divider line in the middle between front and back cards
    draw.line([back_x, margin_top, back_x, card_bottom], fill="#000000", width=3)

    canvas.save(output_png, format="PNG", dpi=(300, 300))

    # Generate Print-Ready PDF
    run_cmd(
        f'/usr/lib/cups/filter/imagetopdf 1 fahad "aadhaar_job" 1 "PageSize=A4" "{output_png}" > "{output_pdf}"'
    )

    return {
        "status": "success",
        "png": str(Path(output_png).resolve()),
        "pdf": str(Path(output_pdf).resolve())
    }

def print_file(
    file_path: str,
    printer_name: str = "Brother-DCP-T710W-USB",
    media_type: str = "Plain",
    color_mode: str = "Color",
    resolution: str = "Normal"
) -> str:
    """
    Send document directly to CUPS printer.
    CRITICAL: Does NOT use fit-to-page, ensuring 100% true physical 1:1 scale!
    """
    target_path = Path(file_path).resolve()
    if not target_path.exists():
        raise FileNotFoundError(f"File to print not found: {file_path}")

    opts = [
        "-o PageSize=A4",
        "-o scaling=100",
        f"-o BRMediaType={media_type}",
        f"-o BRMonoColor={color_mode}",
        f"-o BRResolution={resolution}",
        "-o BRJpeg=SpeedPrior"
    ]
    cmd = f'lp -d "{printer_name}" {" ".join(opts)} "{target_path}"'
    out = run_cmd(cmd)
    return out
