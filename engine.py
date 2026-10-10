#!/usr/bin/env python3
"""
craft-studio core engine
Automates Passport photo sheet generation & Aadhaar ID card extraction.
"""

import os
import sys
import subprocess
from pathlib import Path
from PIL import Image, ImageEnhance, ImageOps, ImageDraw

A4_WIDTH_PX = 2480
A4_HEIGHT_PX = 3508
DPI = 300

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
    Uses user-specified manual adjustments (crop, brightness, contrast, saturation)
    without forcing artificial auto-enhancement filters.
    """
    input_path = Path(input_image_path).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_image_path}")

    temp_dir = Path("/tmp/craft_studio_passport")
    temp_dir.mkdir(parents=True, exist_ok=True)

    base_img = Image.open(input_path).convert("RGB")

    # 1. Manual Crop if user selected a crop box (x, y, w, h)
    if crop_box and len(crop_box) == 4:
        bx, by, bw, bh = crop_box
        if bw > 20 and bh > 20:
            base_img = base_img.crop((bx, by, bx + bw, by + bh))

    # 2. Manual Adjustments
    if brightness != 1.0:
        enh_b = ImageEnhance.Brightness(base_img)
        base_img = enh_b.enhance(brightness)
    if contrast != 1.0:
        enh_c = ImageEnhance.Contrast(base_img)
        base_img = enh_c.enhance(contrast)
    if saturation != 1.0:
        enh_s = ImageEnhance.Color(base_img)
        base_img = enh_s.enhance(saturation)

    # 3. Standard Passport Size: 3.5cm x 4.5cm -> 384x512 px + 1px guide border
    photo_w, photo_h = 384, 512
    aspect = photo_w / photo_h
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

    resized_photo = cropped.resize((photo_w, photo_h), Image.Resampling.LANCZOS)

    # Border: 1px cutting border + 3px white safety border (total 392x520 px)
    border_px = 1
    white_pad = 3
    total_w = photo_w + (border_px + white_pad) * 2
    total_h = photo_h + (border_px + white_pad) * 2

    unit_photo = Image.new("RGB", (total_w, total_h), (255, 255, 255))
    draw = ImageDraw.Draw(unit_photo)
    unit_photo.paste(resized_photo, (border_px + white_pad, border_px + white_pad))
    if border_color and border_color != "none":
        draw.rectangle(
            [white_pad, white_pad, total_w - white_pad - 1, total_h - white_pad - 1],
            outline=border_color,
            width=border_px
        )

    # 4. Canvas Creation: Guaranteed TrueColor sRGB
    canvas = Image.new("RGB", (A4_WIDTH_PX, A4_HEIGHT_PX), (255, 255, 255))

    cols = 6 if quantity >= 6 else quantity
    if quantity == 8:
        cols = 4
    elif quantity == 10:
        cols = 5
    elif quantity == 12:
        cols = 6
    elif quantity >= 30:
        cols = 5

    margin_y = 35
    gap_x = 16
    gap_y = 20

    if quantity >= 30:
        cols = 5
        rows = 6
        gap_x = 24
        gap_y = 24
        margin_x = (A4_WIDTH_PX - (5 * total_w + 4 * gap_x)) // 2
        margin_y = (A4_HEIGHT_PX - (6 * total_h + 5 * gap_y)) // 2
        for r in range(rows):
            for c in range(cols):
                x = margin_x + c * (total_w + gap_x)
                y = margin_y + r * (total_h + gap_y)
                canvas.paste(unit_photo, (x, y))
    else:
        rows = (quantity + cols - 1) // cols
        margin_x = (A4_WIDTH_PX - (cols * total_w + (cols - 1) * gap_x)) // 2
        count = 0
        for r in range(rows):
            for c in range(cols):
                if count >= quantity:
                    break
                x = margin_x + c * (total_w + gap_x)
                y = margin_y + r * (total_h + gap_y)
                canvas.paste(unit_photo, (x, y))
                count += 1

    canvas.save(output_png, format="PNG", dpi=(300, 300))

    # Generate print-perfect PDF
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
    Positions cards side-by-side with NO gap and a prominent black center divider line.
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

    # Precise Bounding Box for UIDAI Aadhaar Cards:
    # Front: X in [199, 1256], Y in [2405, 3056]
    # Back:  X in [1291, 2350], Y in [2405, 3056]
    front_crop = page_img.crop((199, 2405, 1256, 3056))
    back_crop = page_img.crop((1291, 2405, 2350, 3056))

    # Standard PVC ID Size: 8.6cm x 5.4cm -> 1016 x 638 px at 300 DPI
    target_card_w, target_card_h = 1016, 638
    front_card = front_crop.resize((target_card_w, target_card_h), Image.Resampling.LANCZOS)
    back_card = back_crop.resize((target_card_w, target_card_h), Image.Resampling.LANCZOS)

    # Create A4 sheet: 2480 x 3508 px
    canvas = Image.new("RGB", (A4_WIDTH_PX, A4_HEIGHT_PX), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    # Place Front and Back directly touching each other (NO blank gap)
    # Total width = 1016 * 2 = 2032 px
    margin_x = (A4_WIDTH_PX - (target_card_w * 2)) // 2  # 224 px centered
    margin_y = 150

    front_x = margin_x
    back_x = margin_x + target_card_w

    canvas.paste(front_card, (front_x, margin_y))
    canvas.paste(back_card, (back_x, margin_y))

    # Draw solid black outer border around combined ID cards
    card_bottom = margin_y + target_card_h - 1
    draw.rectangle(
        [front_x, margin_y, back_x + target_card_w - 1, card_bottom],
        outline="#000000",
        width=2
    )

    # Draw bold black divider line in the middle between front and back cards
    draw.line([back_x, margin_y, back_x, card_bottom], fill="#000000", width=3)

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
    """Send document directly to CUPS printer."""
    target_path = Path(file_path).resolve()
    if not target_path.exists():
        raise FileNotFoundError(f"File to print not found: {file_path}")

    opts = [
        "-o PageSize=A4",
        "-o fit-to-page",
        f"-o BRMediaType={media_type}",
        f"-o BRMonoColor={color_mode}",
        f"-o BRResolution={resolution}",
        "-o BRJpeg=SpeedPrior"
    ]
    cmd = f'lp -d "{printer_name}" {" ".join(opts)} "{target_path}"'
    out = run_cmd(cmd)
    return out
