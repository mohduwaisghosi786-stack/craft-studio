#!/usr/bin/env python3
"""
craft-studio core engine
Calibrated for:
1. 6 Passport Photos in 1 Single Row:
   - 1.5 mm Cutting Gap between photos
   - Top and Bottom faint dashed cutting guide lines (very low ink)
   - Left Margin: 0.5 cm (59 px), Right Margin: 0.5 cm (59 px)
   - Top Margin: 1.0 cm (118 px)
   - Height: 4.5 cm (531 px), Width: ~3.2 cm (378 px)
2. Exact 65mm x 95mm Lamination Pouch (125 Micron):
   - Folded Card: 88 mm x 58 mm (Leaves solid 3.5mm thermal seal border all around so lamination never peels off)
   - 2px Center Folding Divider Line (Black)
   - 1.0 cm Top Margin
3. 100% True Scale Direct 300 DPI PDF (Borderless A4)
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

def save_exact_pdf(img: Image.Image, output_pdf_path: str):
    """
    Saves image as 300 DPI True A4 PDF directly using Pillow.
    Guarantees exact 595.2 x 841.9 pt dimensions with 0% shrinkage.
    """
    img.save(output_pdf_path, "PDF", resolution=300.0)

def draw_dashed_line(draw, start, end, color="#cccccc", dash_len=8, gap_len=6, width=1):
    """Draw a subtle, low-ink dashed cutting guideline."""
    x1, y1 = start
    x2, y2 = end
    if y1 == y2:
        # Horizontal dashed line
        cur_x = x1
        while cur_x < x2:
            next_x = min(cur_x + dash_len, x2)
            draw.line([(cur_x, y1), (next_x, y1)], fill=color, width=width)
            cur_x += dash_len + gap_len
    elif x1 == x2:
        # Vertical dashed line
        cur_y = y1
        while cur_y < y2:
            next_y = min(cur_y + dash_len, y2)
            draw.line([(x1, cur_y), (x1, next_y)], fill=color, width=width)
            cur_y += dash_len + gap_len

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
    6 Photos Configuration:
    - Exactly 1 Single Row
    - Top Margin: 1.0 cm (118 px)
    - Left Margin: 0.5 cm (59 px)
    - Right Margin: 0.5 cm (59 px)
    - Gap between photos: Exactly 1.5 mm (18 px)
    - Photo Height: Exactly 4.5 cm (531 px)
    - Photo Width: 378 px (~3.2 cm)
    - Top & Bottom Faint Dashed Cutting Guide Lines
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

    # 3. Canvas Creation: Guaranteed TrueColor sRGB A4 (2480 x 3508 px)
    canvas = Image.new("RGB", (A4_WIDTH_PX, A4_HEIGHT_PX), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    if quantity == 6:
        photo_w = 378
        photo_h = int(45 * PX_PER_MM)       # 531 px (4.5 cm)
        gap_x = int(1.5 * PX_PER_MM)        # 18 px (1.5 mm)
        margin_left = int(5.0 * PX_PER_MM)  # 59 px (0.5 cm)
        margin_top = int(10.0 * PX_PER_MM)  # 118 px (1.0 cm)

        aspect = photo_w / photo_h
        img_w, img_h = base_img.size
        if (img_w / img_h) > aspect:
            new_w = int(img_h * aspect)
            left = (img_w - new_w) // 2
            cropped = base_img.crop((left, 0, left + new_w, img_h))
        else:
            new_h = int(img_w / aspect)
            top = (img_h - new_h) // 2
            cropped = base_img.crop((0, top, img_w, top + new_h))

        unit_photo = cropped.resize((photo_w, photo_h), Image.Resampling.LANCZOS)
        unit_draw = ImageDraw.Draw(unit_photo)
        if border_color and border_color != "none":
            unit_draw.rectangle([0, 0, photo_w - 1, photo_h - 1], outline=border_color, width=1)

        # Paste all 6 photos in 1 single row
        total_row_width = 6 * photo_w + 5 * gap_x
        row_right = margin_left + total_row_width

        for i in range(6):
            x = margin_left + i * (photo_w + gap_x)
            y = margin_top
            canvas.paste(unit_photo, (x, y))

        # Top & Bottom Faint Dashed Cutting Guide Lines
        # Top guide line (3 px above photos)
        draw_dashed_line(draw, (margin_left - 30, margin_top - 3), (row_right + 30, margin_top - 3), color="#c5c5c5", dash_len=8, gap_len=6, width=1)
        # Bottom guide line (3 px below photos)
        draw_dashed_line(draw, (margin_left - 30, margin_top + photo_h + 3), (row_right + 30, margin_top + photo_h + 3), color="#c5c5c5", dash_len=8, gap_len=6, width=1)

    elif quantity >= 30:
        photo_w = 413
        photo_h = 531
        gap_x = 12
        gap_y = 15
        aspect = photo_w / photo_h
        img_w, img_h = base_img.size
        if (img_w / img_h) > aspect:
            new_w = int(img_h * aspect)
            left = (img_w - new_w) // 2
            cropped = base_img.crop((left, 0, left + new_w, img_h))
        else:
            new_h = int(img_w / aspect)
            top = (img_h - new_h) // 2
            cropped = base_img.crop((0, top, img_w, top + new_h))

        unit_photo = cropped.resize((photo_w, photo_h), Image.Resampling.LANCZOS)
        unit_draw = ImageDraw.Draw(unit_photo)
        if border_color and border_color != "none":
            unit_draw.rectangle([0, 0, photo_w - 1, photo_h - 1], outline=border_color, width=1)

        margin_x = (A4_WIDTH_PX - (5 * photo_w + 4 * gap_x)) // 2
        margin_y = (A4_HEIGHT_PX - (6 * photo_h + 5 * gap_y)) // 2
        for r in range(6):
            for c in range(5):
                x = margin_x + c * (photo_w + gap_x)
                y = margin_y + r * (photo_h + gap_y)
                canvas.paste(unit_photo, (x, y))

    else:
        # 8, 10, 12 photos
        cols = quantity // 2
        photo_w = (A4_WIDTH_PX - (2 * int(5.0 * PX_PER_MM)) - (cols - 1) * int(1.5 * PX_PER_MM)) // cols
        photo_h = int(45 * PX_PER_MM)
        gap_x = int(1.5 * PX_PER_MM)
        gap_y = int(2.0 * PX_PER_MM)
        margin_left = int(5.0 * PX_PER_MM)
        margin_top = int(10.0 * PX_PER_MM)

        aspect = photo_w / photo_h
        img_w, img_h = base_img.size
        if (img_w / img_h) > aspect:
            new_w = int(img_h * aspect)
            left = (img_w - new_w) // 2
            cropped = base_img.crop((left, 0, left + new_w, img_h))
        else:
            new_h = int(img_w / aspect)
            top = (img_h - new_h) // 2
            cropped = base_img.crop((0, top, img_w, top + new_h))

        unit_photo = cropped.resize((photo_w, photo_h), Image.Resampling.LANCZOS)
        unit_draw = ImageDraw.Draw(unit_photo)
        if border_color and border_color != "none":
            unit_draw.rectangle([0, 0, photo_w - 1, photo_h - 1], outline=border_color, width=1)

        for r in range(2):
            for c in range(cols):
                x = margin_left + c * (photo_w + gap_x)
                y = margin_top + r * (photo_h + gap_y)
                canvas.paste(unit_photo, (x, y))

    canvas.save(output_png, format="PNG", dpi=(300, 300))

    # Generate print-perfect 300 DPI PDF directly via Pillow (NO scaling distortion)
    save_exact_pdf(canvas, output_pdf)

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
    password: str = "",
    brightness: float = 1.0,
    contrast: float = 1.0,
    photo_brightness: float = 1.0,
    photo_contrast: float = 1.0
) -> dict:
    """
    Unlock Aadhaar PDF, render at 300 DPI, and extract Front & Back ID Card.
    Custom Calibrated for 65 mm x 95 mm Lamination Pouch (125 Micron):
    - Finished Folded Card Size: 58 mm x 88 mm (685 px x 1039 px)
      (Leaves exactly 3.5 mm solid plastic weld seal on all sides so lamination NEVER peels off)
    - Zero gap between Front and Back with solid 2px Black folding divider line.
    - Top margin set to exactly 1.0 cm (118 px).
    - Centered horizontally across A4 page.
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

    # Isolate and enhance person's portrait photo specifically on the front card
    # Portrait coordinates in front_crop: X [88, 245], Y [140, 345]
    if photo_brightness != 1.0 or photo_contrast != 1.0:
        px1, py1, px2, py2 = 86, 138, 248, 348
        person_photo = front_crop.crop((px1, py1, px2, py2))
        if photo_brightness != 1.0:
            person_photo = ImageEnhance.Brightness(person_photo).enhance(photo_brightness)
        if photo_contrast != 1.0:
            person_photo = ImageEnhance.Contrast(person_photo).enhance(photo_contrast)
        front_crop.paste(person_photo, (px1, py1))

    # Pouch Calibrated Dimensions:
    # 65 mm x 95 mm Pouch -> Card: 58 mm (height) x 88 mm (width) = 685 x 1039 px
    card_w = int(88 * PX_PER_MM)  # 1039 px
    card_h = int(58 * PX_PER_MM)  # 685 px
    front_card = front_crop.resize((card_w, card_h), Image.Resampling.LANCZOS)
    back_card = back_crop.resize((card_w, card_h), Image.Resampling.LANCZOS)

    # Apply manual card brightness / contrast tuning if requested
    if brightness != 1.0:
        front_card = ImageEnhance.Brightness(front_card).enhance(brightness)
        back_card = ImageEnhance.Brightness(back_card).enhance(brightness)
    if contrast != 1.0:
        front_card = ImageEnhance.Contrast(front_card).enhance(contrast)
        back_card = ImageEnhance.Contrast(back_card).enhance(contrast)

    # Create A4 sheet: 2480 x 3508 px
    canvas = Image.new("RGB", (A4_WIDTH_PX, A4_HEIGHT_PX), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    # Placement:
    # 1.0 cm from top = 118 px
    margin_top = int(10.0 * PX_PER_MM)
    # Total width of Front + Back touching = 1039 * 2 = 2078 px
    # Centered horizontally: (2480 - 2078) // 2 = 201 px margin on left and right
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

    # Draw 2px solid black divider line in the middle between front and back cards
    draw.line([back_x, margin_top, back_x, card_bottom], fill="#000000", width=2)

    canvas.save(output_png, format="PNG", dpi=(300, 300))

    # Generate Print-Ready 300 DPI PDF via Pillow
    save_exact_pdf(canvas, output_pdf)

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
    Uses BrA4_B (Borderless A4) to prevent Brother driver from shrinking margins!
    Guarantees True Color mode by enforcing both CUPS standard and Brother-specific color flags.
    """
    target_path = Path(file_path).resolve()
    if not target_path.exists():
        raise FileNotFoundError(f"File to print not found: {file_path}")

    # Map color_mode to standard cups and brother options
    cups_color = "color" if color_mode.lower() == "color" else "monochrome"
    br_color = "Color" if color_mode.lower() == "color" else "Mono"

    opts = [
        "-o PageSize=BrA4_B",
        "-o scaling=100",
        f"-o print-color-mode={cups_color}",
        f"-o BRMonoColor={br_color}",
        f"-o BRMediaType={media_type}",
        f"-o BRResolution={resolution}",
        "-o BRJpeg=Recommended",
        "-o BRColorMatching=Natural"
    ]
    # Check if running on Windows
    if sys.platform.startswith('win'):
        try:
            # On Windows, os.startfile with 'print' sends to default or selected printer with native properties dialog
            os.startfile(str(target_path), "print")
            return f"Printed via Windows Print Spooler: {target_path.name}"
        except Exception as e:
            # Fallback to opening file in default viewer if direct print verb isn't registered
            os.startfile(str(target_path))
            return f"Opened PDF in Windows Viewer for 100% True Scale Print ({e})"

    cmd = f'lp -d "{printer_name}" {" ".join(opts)} "{target_path}"'
    out = run_cmd(cmd)
    return out
