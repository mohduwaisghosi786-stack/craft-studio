# ⚡ UWAIS INternet CAfe Studio
### Professional Passport Photos & 65×95mm Pouch ID Print Suite
**build by UWAIS GHosi**

[![Linux Compatible](https://img.shields.io/badge/OS-Linux%20%7C%20Windows-blue.svg)](https://github.com/mohduwaisghosi786-stack/craft-studio)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Freeware-orange.svg)](#)

---

## 🌟 Key Highlights

1. **📷 6 Passport Photos (Exact 1 Single Row):**
   - **True 1:1 Scale:** 3.5 cm × 4.5 cm proportion with 1.5 mm cutting gap.
   - **Space Saving:** Perfectly placed in one single row at the top (1.0 cm top margin, 0.5 cm side margins) leaving the rest of the A4 page completely clean.
   - **Faint Dashed Cutting Guides:** Ultra low-ink guide lines above and below photos for scissors.
   - **Live Cropper & Tuning:** Interactive 3.5:4.5 crop tool, brightness, contrast, and saturation controls.

2. **🪪 Aadhaar Card (Calibrated for 125 Micron 65×95mm Lamination Pouch):**
   - **Guaranteed Waterproof Seal:** Scaled to **58 mm × 88 mm** folded card (leaving solid 3.5 mm plastic thermal weld all around).
   - **No Scissors Mark:** Automatically trimmed below the UIDAI scissor icon, preserving the Ashoka emblem and Bharat Sarkar header.
   - **Center Divider:** 2px solid folding guideline with zero gap between front and back.
   - **Fine-Tuning:** Brightness and contrast controls to adjust dim/dark Aadhaar photos before printing.

3. **🖨️ Universal 100% True Scale Printing:**
   - Eliminates CUPS driver margin shrinkage by generating exact 300 DPI borderless A4 (`BrA4_B`) raster PDF.
   - True Color mode enforcement (`print-color-mode=color` & `BRMonoColor=Color`).
   - Supports Brother DCP-T710W, Epson L-series, Canon Pixma, and HP Ink Tank printers.

---

## 🚀 1-Line Universal Linux Installation (Any Distro)

Run this single command in your terminal on **Ubuntu, Debian, Arch Linux, Linux Mint, Fedora, Pop!_OS**:

```bash
curl -fsSL https://raw.githubusercontent.com/mohduwaisghosi786-stack/craft-studio/main/install.sh | bash
```

This script automatically:
* Installs system dependencies (`python-pillow`, `poppler`, `qpdf`, `cups`, `gtk3`).
* Sets up the terminal command `uwais-cafe`.
* Creates a desktop application shortcut in your app menu.
* Launches the web GUI service on `http://localhost:8091`.

---

## 🖥️ How to Run

### Option 1: Native Desktop GUI App
Run from terminal or application launcher:
```bash
uwais-cafe
```
Features a split-pane layout with controls on the left and full-height live HD preview on the right.

### Option 2: Web Browser Interface
Open in any browser:
```
http://localhost:8091
```

---

## 🪟 Windows (.EXE / .MSI) Installation
* Windows standalone package can be compiled using PyInstaller:
```bash
pyinstaller --noconfirm --onedir --windowed --add-data "templates:templates" app.py
```
* See the [Universal Studio Roadmap](https://github.com/mohduwaisghosi786-stack/craft-studio/blob/main/universal_studio_roadmap.md) for details on upcoming Ayushman Bharat (PMJAY) and e-Shram Card integrations.

---

## 👨‍💻 Author & Credits
- **Software:** UWAIS INternet CAfe Studio
- **Creator / Maintainer:** UWAIS GHosi
- **Repository:** [mohduwaisghosi786-stack/craft-studio](https://github.com/mohduwaisghosi786-stack/craft-studio)
