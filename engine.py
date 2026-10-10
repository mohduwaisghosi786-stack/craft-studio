#!/usr/bin/env python3
"""
craft-studio core engine
Automates Passport photo sheet generation & Aadhaar ID card extraction
with PhotoCraft CLI & CUPS printer integration.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

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
    dotted_cut_lines: bool = True
) -> dict:
    """
    Generate passport photo sheet on A4 canvas (300 DPI).
    Supports 6, 8, 10, 12, 16, 30 (full sheet) photos.
    Space saving: prints at top and preserves bottom blank paper.
    """
    input_path = Path(input_image_path).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_image_path}")

    temp_dir = Path("/tmp/craft_studio_passport")
    temp_dir.mkdir(parents=True, exist_ok=True)
    single_photo = temp_dir / "single_photo.png"

    # Enhance image using PhotoCraft CLI engine (Auto-Contrast, Auto-Color, Clean Rendering)
    photocraft_enhanced = temp_dir / "enhanced_photocraft.png"
    try:
        run_cmd(
            f'photocraft-cli run "{input_path}" '
            f'--cmd image.autoContrast --cmd image.autoColor '
            f'--out "{photocraft_enhanced}"'
        )
        source_img = photocraft_enhanced
    except Exception as e:
        # Fallback to direct input if photocraft-cli throws
        source_img = input_path

    # Standard Passport size: 3.5cm x 4.5cm -> ~413x531 px at 300 DPI
    # Border: 1px subtle gray cutting guide, 3px white safety margin
    crop_w, crop_h = 384, 512
    cmd_crop = (
        f'magick "{source_img}" -resize {crop_w}x{crop_h}^ -gravity center -extent {crop_w}x{crop_h} '
        f'-bordercolor "{border_color}" -border 1 -bordercolor white -border 3 "{single_photo}"'
    )
    run_cmd(cmd_crop)

    # Base A4 canvas
    base_canvas = temp_dir / "canvas.png"
    run_cmd(f'magick -size {A4_WIDTH_PX}x{A4_HEIGHT_PX} xc:white "{base_canvas}"')

    # Layout calculation
    # Row width allows max 6 photos across: 6 * 392 = 2352 px
    cols = 6 if quantity >= 6 else quantity
    if quantity == 8:
        cols = 4
    elif quantity == 10:
        cols = 5
    elif quantity == 12:
        cols = 6
    elif quantity >= 30:
        cols = 5 # 5x6 = 30 full page

    composite_ops = []
    margin_x = 35
    margin_y = 35
    photo_w = 392
    photo_h = 520
    gap_x = 16
    gap_y = 20

    if quantity >= 30:
        # Full A4 (5 cols x 6 rows = 30)
        cols = 5
        rows = 6
        gap_x = 24
        gap_y = 24
        margin_x = (A4_WIDTH_PX - (5 * photo_w + 4 * gap_x)) // 2
        margin_y = (A4_HEIGHT_PX - (6 * photo_h + 5 * gap_y)) // 2
        for r in range(rows):
            for c in range(cols):
                x = margin_x + c * (photo_w + gap_x)
                y = margin_y + r * (photo_h + gap_y)
                composite_ops.append(f'"{single_photo}" -geometry +{x}+{y} -composite')
    else:
        # Top-aligned space saving layout
        rows = (quantity + cols - 1) // cols
        margin_x = (A4_WIDTH_PX - (cols * photo_w + (cols - 1) * gap_x)) // 2
        count = 0
        for r in range(rows):
            for c in range(cols):
                if count >= quantity:
                    break
                x = margin_x + c * (photo_w + gap_x)
                y = margin_y + r * (photo_h + gap_y)
                composite_ops.append(f'"{single_photo}" -geometry +{x}+{y} -composite')
                count += 1

    # Apply composites
    comp_cmd = f'magick "{base_canvas}" {" ".join(composite_ops)} -density 300 -units PixelsPerInch "{output_png}"'
    run_cmd(comp_cmd)

    # Convert to true A4 points PDF (595.28 x 841.89 pt) using CUPS native filter
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
    Unlock Aadhaar PDF if needed, extract high-res 300 DPI page,
    and crop into standard Front & Back ID Card (PVC size: 8.6cm x 5.4cm).
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
    page_img = temp_dir / "page-1.png"
    if not page_img.exists():
        raise FileNotFoundError("Failed to render Aadhaar PDF page")

    # In standard e-Aadhaar letters (UIDAI):
    # Dimensions ~ 2480 x 3508 px at 300 DPI
    # ID card is located at the bottom half of the page:
    # Front is on the bottom left/middle, Back is on the bottom right/middle.
    # Front size: ~ 1016 x 640 px (8.6cm x 5.4cm)
    # Back size: ~ 1016 x 640 px
    front_card = temp_dir / "aadhaar_front.png"
    back_card = temp_dir / "aadhaar_back.png"

    # Crop Front (Left bottom) and Back (Right bottom)
    # Coordinates for standard e-Aadhaar layout:
    # Y is around 2680-3320 px
    run_cmd(f'magick "{page_img}" -crop 1030x650+175+2680 +repage -bordercolor "#b0b0b0" -border 1 "{front_card}"')
    run_cmd(f'magick "{page_img}" -crop 1030x650+1275+2680 +repage -bordercolor "#b0b0b0" -border 1 "{back_card}"')

    # Create A4 sheet with Front and Back side-by-side with faint cut border
    base_canvas = temp_dir / "aadhaar_a4.png"
    run_cmd(f'magick -size {A4_WIDTH_PX}x{A4_HEIGHT_PX} xc:white "{base_canvas}"')

    # Composite side-by-side at top
    run_cmd(
        f'magick "{base_canvas}" '
        f'"{front_card}" -geometry +160+150 -composite '
        f'"{back_card}" -geometry +1280+150 -composite '
        f'-density 300 -units PixelsPerInch "{output_png}"'
    )

    # Generate print-perfect PDF
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
    color_mode: str = "Mono",
    resolution: str = "PlainFast"
) -> str:
    """
    Send document directly to CUPS printer with accurate parameters.
    """
    target_path = Path(file_path).resolve()
    if not target_path.exists():
        raise FileNotFoundError(f"File to print not found: {file_path}")

    # Build options
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
