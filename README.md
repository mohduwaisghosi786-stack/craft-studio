# ⚡ Craft Studio

**Craft Studio** is an automated Passport Photo Sheet & Aadhaar ID Card generation studio tailored for A4 printing on **Brother DCP-T710W** (USB / Wi-Fi) and PhotoCraft integration.

---

## 🌟 Key Features

1. **📷 Passport Photos Automation:**
   * Select quantities: **6, 8, 10, 12, or 30 (Full A4)** photos.
   * **Space-Saving Layout:** Automatically aligns 6/8/10 photos to the top of the A4 page so the rest of the sheet remains clean and reusable.
   * **Ultra-Faint Cutting Guides:** Subtle 1px dotted/faint guide borders that consume negligible ink.
   * Generates exact **595 × 842 pt (A4)** print-ready PDFs.

2. **🪪 Aadhaar Card to PVC/ID Card Converter:**
   * Automatically decrypts password-protected e-Aadhaar PDFs (`qpdf`).
   * Extracts Front and Back ID sections at 300 DPI.
   * Prepares standard 8.6cm × 5.4cm side-by-side ID card layout on A4.

3. **🖨️ Direct Brother Printer Integration:**
   * **Glossy Mode:** Photo paper, vibrant color, high resolution (`BrotherGlossyR`, `Color`, `Normal`).
   * **Fast Draft Mode:** Plain paper, black & white, ink saver (`Plain`, `Mono`, `PlainFast`).
   * One-click direct printing via CUPS to `Brother-DCP-T710W-USB` or `Brother-DCP-T710W-WiFi`.

4. **🖥️ Dual Interfaces:**
   * **Web GUI:** Beautiful browser interface (drag-and-drop, live preview, print controls).
   * **CLI:** Lightning-fast terminal commands.

---

## 🚀 Quick Usage

### 1. Launch Web GUI
```bash
python3 /home/fahad/craft-studio/app.py
```
Open [http://localhost:8090](http://localhost:8090) in your browser.

### 2. Use via Command Line (CLI)

#### Create 6 Passport Photos (Space-Saver Mode):
```bash
craft-studio passport "/path/to/photo.jpg" -q 6 -o output.png --pdf output.pdf
```

#### Create & Directly Print to Brother Printer (Glossy Color):
```bash
craft-studio passport "/path/to/photo.jpg" -q 6 --print --glossy --color
```

#### Create & Print Draft (Plain Paper B&W):
```bash
craft-studio passport "/path/to/photo.jpg" -q 6 --print
```

#### Extract & Format Aadhaar Card:
```bash
craft-studio aadhaar "/path/to/aadhaar.pdf" -p "MOHD1998" -o aadhaar_id.png --pdf aadhaar_id.pdf
```

---

## 📂 Project Structure
* `engine.py`: Image composition, cropping, borders, CUPS PDF filters.
* `app.py`: Embedded web server & UI (Zero external dependencies).
* `cli.py`: Terminal interface (`craft-studio`).
