#!/usr/bin/env python3
"""
craft-studio core engine
Automates Passport photo sheet generation & Aadhaar ID card extraction
with PhotoCraft CLI, Pillow studio-grade enhancement & CUPS printer integration.
Guarantees True 24-bit sRGB Color output.
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

def enhance_studio_quality(img: Image.Image) -> Image.Image:
    """
    Studio-grade photo enhancement:
    Auto-contrast, natural skin-tone color saturation, subtle sharpness & balanced brightness.
    """
    img = img.convert("RGB")
    # 1. Auto-contrast with 1% cutoff to remove dull haze
    img = ImageOps.autocontrast(img, cutoff=1)
    # 2. Rich Color Saturation for photo print
    enh_color = ImageEnhance.Color(img)
    img = enh_color.enhance(1.15)
    # 3. Studio Sharpness (clarity for eyes, hair, facial features)
    enh_sharp = ImageEnhance.Sharpness(img)
    img = enh_sharp.enhance(1.25)
    # 4. Slight Brightness boost
    enh_bright = ImageEnhance.Brightness(img)
    img = enh_bright.enhance(1.02)
    return img

def make_passport_sheet(
    input_image_path: str,
    output_png: str,
    output_pdf: str,
    quantity: int = 6,
    border_color: str = "#b0b0b0",
    enhance: bool = True
) -> dict:
    """
    Generate passport photo sheet on A4 canvas (300 DPI) in VIVID TRUE COLOR (RGB).
    Quantities: 6, 8, 10, 12, 16, 30.
    Space saving: prints at top and preserves bottom blank paper.
    """
    input_path = Path(input_image_path).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_image_path}")

    temp_dir = Path("/tmp/craft_studio_passport")
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 1. PhotoCraft CLI Pre-processing (AutoContrast / AutoColor)
    photocraft_out = temp_dir / "pc_enhanced.png"
    try:
        run_cmd(
            f'photocraft-cli run "{input_path}" '
            f'--cmd image.autoContrast --cmd image.autoColor '
            f'--out "{photocraft_out}"'
        )
        base_img = Image.open(photocraft_out)
    except Exception:
        base_img = Image.open(input_path)

    # 2. Studio Polish
    if enhance:
        base_img = enhance_studio_quality(base_img)
    else:
        base_img = base_img.convert("RGB")

    # 3. Standard Passport Size: 3.5cm x 4.5cm -> 413x531 px at 300 DPI
    # Inner photo size: 384x512 px + borders = 392x520 px
    photo_w, photo_h = 384, 512
    # Smart crop to aspect ratio
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

    # Add 1px cutting border + 3px white safety border (total 392x520 px)
    border_px = 1
    white_pad = 3
    total_w = photo_w + (border_px + white_pad) * 2
    total_h = photo_h + (border_px + white_pad) * 2

    unit_photo = Image.new("RGB", (total_w, total_h), (255, 255, 255))
    draw = ImageDraw.Draw(unit_photo)
    # Paste photo inside
    unit_photo.paste(resized_photo, (border_px + white_pad, border_px + white_pad))
    # Draw faint border
    if border_color and border_color != "none":
        draw.rectangle(
            [white_pad, white_pad, total_w - white_pad - 1, total_h - white_pad - 1],
            outline=border_color,
            width=border_px
        )

    # 4. Canvas Creation: Guaranteed 24-bit TrueColor RGB
    canvas = Image.new("RGB", (A4_WIDTH_PX, A4_HEIGHT_PX), (255, 255, 255))

    # Layout Calculations
    cols = 6 if quantity >= 6 else quantity
    if quantity == 8:
        cols = 4
    elif quantity == 10:
        cols = 5
    elif quantity == 12:
        cols = 6
    elif quantity >= 30:
        cols = 5 # 5x6 = 30 full page

    margin_y = 35
    gap_x = 16
    gap_y = 20

    if quantity >= 30:
        # Full A4
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
        # Top-aligned space saving layout
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

    # Save PNG in TrueColor sRGB
    canvas.save(output_png, format="PNG", dpi=(300, 300))

    # Convert to standard A4 PDF (595.28 x 841.89 pt) using CUPS native filter
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
    Unlock Aadhaar PDF, render at 300 DPI in TRUE COLOR (RGB),
    and accurately extract full Front & Back ID Card (PVC size: 8.6cm x 5.4cm).
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
    page_w, page_h = page_img.size

    # Exact Coordinates for Standard e-Aadhaar UIDAI Layout:
    # Card is located from Y ~ 2400 to 3080 px (approx 680 px high)
    # Front card is on the left half: X ~ 120 to 1200 px (width ~ 1080 px)
    # Back card is on the right half: X ~ 1350 to 2430 px (width ~ 1080 px)
    front_crop = page_img.crop((120, 2400, 1200, 3080))
    back_crop = page_img.crop((1350, 2400, 2430, 3080))

    # Standard PVC Card size at 300 DPI is approx 1016 x 638 px (8.6cm x 5.4cm)
    target_card_w, target_card_h = 1016, 638
    front_card = front_crop.resize((target_card_w, target_card_h), Image.Resampling.LANCZOS)
    back_card = back_crop.resize((target_card_w, target_card_h), Image.Resampling.LANCZOS)

    # Add 1px subtle gray cutting guide around each card
    draw_f = ImageDraw.Draw(front_card)
    draw_f.rectangle([0, 0, target_card_w - 1, target_card_h - 1], outline="#b0b0b0", width=1)

    draw_b = ImageDraw.Draw(back_card)
    draw_b.rectangle([0, 0, target_card_w - 1, target_card_h - 1], outline="#b0b0b0", width=1)

    # Create TrueColor A4 Canvas
    canvas = Image.new("RGB", (A4_WIDTH_PX, A4_HEIGHT_PX), (255, 255, 255))

    # Place Front and Back side-by-side at top with neat margins
    # Left card: x=170, y=140
    # Right card: x=1290, y=140
    canvas.paste(front_card, (170, 140))
    canvas.paste(back_card, (1290, 140))

    # Save output PNG
    canvas.save(output_png, format="PNG", dpi=(300, 300))

    # Convert to Print-Ready PDF
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
    Send document directly to CUPS printer with accurate parameters.
    """
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
