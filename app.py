#!/usr/bin/env python3
"""
craft-studio Web UI Server
Modern, lightweight local web GUI for generating Passport Photos and Aadhaar ID Cards.
Compatible with Python 3.12+ (no deprecated cgi module).
"""

import http.server
import socketserver
import json
import urllib.parse
import os
import sys
import email
from email.policy import default
from pathlib import Path
from engine import make_passport_sheet, process_aadhaar_pdf, print_file

PORT = 8090
BASE_DIR = Path(__file__).parent.resolve()
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

HTML_PAGE = """<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Craft Studio - Passport & Aadhaar Automation</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0b0f19;
            --surface: #131b2e;
            --border: #23304d;
            --primary: #3b82f6;
            --primary-glow: rgba(59, 130, 246, 0.35);
            --accent: #10b981;
            --text: #f8fafc;
            --muted: #94a3b8;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Outfit', sans-serif; }
        body { background: var(--bg); color: var(--text); padding: 30px 20px; min-height: 100vh; }
        .container { max-width: 980px; margin: 0 auto; }
        header { text-align: center; margin-bottom: 35px; }
        h1 { font-size: 2.3rem; font-weight: 700; background: linear-gradient(135deg, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        p.subtitle { color: var(--muted); margin-top: 6px; font-size: 1.05rem; }
        
        .tabs { display: flex; gap: 12px; margin-bottom: 25px; justify-content: center; }
        .tab-btn { background: var(--surface); border: 1px solid var(--border); color: var(--text); padding: 12px 28px; border-radius: 12px; font-size: 1.05rem; cursor: pointer; transition: 0.2s; font-weight: 600; }
        .tab-btn.active { background: var(--primary); border-color: var(--primary); box-shadow: 0 0 15px var(--primary-glow); }

        .card { background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 25px; margin-bottom: 25px; }
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        
        label { display: block; font-weight: 600; margin-bottom: 8px; color: #cbd5e1; font-size: 0.95rem; }
        select, input[type="text"], input[type="password"] { width: 100%; background: #0b0f19; border: 1px solid var(--border); padding: 12px 14px; border-radius: 10px; color: var(--text); font-size: 1rem; outline: none; transition: 0.2s; }
        select:focus, input:focus { border-color: var(--primary); }

        .dropzone { border: 2px dashed var(--border); border-radius: 14px; padding: 35px 20px; text-align: center; cursor: pointer; background: rgba(11, 15, 25, 0.5); transition: 0.2s; }
        .dropzone:hover { border-color: var(--primary); background: rgba(59, 130, 246, 0.05); }
        .dropzone p { color: var(--muted); margin-top: 8px; font-size: 0.95rem; }

        .btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px; width: 100%; padding: 14px; border-radius: 12px; font-size: 1.1rem; font-weight: 700; cursor: pointer; border: none; transition: 0.2s; }
        .btn-primary { background: linear-gradient(135deg, #3b82f6, #2563eb); color: #fff; box-shadow: 0 4px 15px var(--primary-glow); }
        .btn-primary:hover { opacity: 0.95; transform: translateY(-1px); }
        .btn-success { background: linear-gradient(135deg, #10b981, #059669); color: #fff; }
        
        .preview-area { display: none; margin-top: 25px; text-align: center; }
        .preview-img { max-width: 100%; max-height: 500px; border-radius: 12px; border: 1px solid var(--border); margin-bottom: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        .print-panel { background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 14px; padding: 20px; }
        .status-badge { display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; margin-bottom: 12px; }
        .status-ready { background: rgba(16, 185, 129, 0.2); color: #34d399; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>⚡ Craft Studio</h1>
            <p class="subtitle">Passport Photos & Aadhaar ID Card Auto-Layout and Print System</p>
        </header>

        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('passport')">📷 Passport Photos</button>
            <button class="tab-btn" onclick="switchTab('aadhaar')">🪪 Aadhaar to ID Card</button>
        </div>

        <!-- PASSPORT SECTION -->
        <div id="section-passport" class="card">
            <form id="form-passport" onsubmit="handlePassport(event)">
                <div class="dropzone" onclick="document.getElementById('file-passport').click()">
                    <span style="font-size: 2.2rem;">📁</span>
                    <h3 id="passport-file-label" style="margin-top: 8px;">Select Photo</h3>
                    <p>Click or Drop Photo (JPG, PNG, WebP)</p>
                    <input type="file" id="file-passport" accept="image/*" style="display:none" onchange="fileSelected('passport')">
                </div>

                <div class="grid-2" style="margin-top: 20px;">
                    <div>
                        <label>Photos Quantity (A4 Sheet):</label>
                        <select id="pass-qty">
                            <option value="6">6 Photos (Top Row - Maximum Space Saved)</option>
                            <option value="8">8 Photos (2 Rows)</option>
                            <option value="10">10 Photos (2 Rows)</option>
                            <option value="12">12 Photos (2 Rows)</option>
                            <option value="30">30 Photos (Full A4 Page)</option>
                        </select>
                    </div>
                    <div>
                        <label>Cutting Guide Border:</label>
                        <select id="pass-border">
                            <option value="#b0b0b0">Subtle Thin Gray Border (Low Ink)</option>
                            <option value="#dcdcdc">Very Faint Border</option>
                            <option value="none">No Border</option>
                        </select>
                    </div>
                </div>

                <button type="submit" class="btn btn-primary" style="margin-top: 25px;">⚡ Generate Passport Sheet</button>
            </form>
        </div>

        <!-- AADHAAR SECTION -->
        <div id="section-aadhaar" class="card" style="display:none;">
            <form id="form-aadhaar" onsubmit="handleAadhaar(event)">
                <div class="dropzone" onclick="document.getElementById('file-aadhaar').click()">
                    <span style="font-size: 2.2rem;">📑</span>
                    <h3 id="aadhaar-file-label" style="margin-top: 8px;">Select Aadhaar PDF</h3>
                    <p>Click or Drop e-Aadhaar PDF</p>
                    <input type="file" id="file-aadhaar" accept=".pdf" style="display:none" onchange="fileSelected('aadhaar')">
                </div>

                <div style="margin-top: 20px;">
                    <label>Aadhaar PDF Password (First 4 letters of Name + Birth Year):</label>
                    <input type="password" id="aadhaar-pw" placeholder="e.g. MOHD1998 (Leave empty if unlocked)">
                </div>

                <button type="submit" class="btn btn-primary" style="margin-top: 25px;">⚡ Extract & Format ID Card</button>
            </form>
        </div>

        <!-- RESULT & PRINT PANEL -->
        <div id="result-panel" class="card preview-area">
            <span class="status-badge status-ready">✓ Sheet Ready for Print</span>
            <img id="preview-image" class="preview-img" src="" alt="Preview">

            <div class="print-panel">
                <h3 style="margin-bottom: 15px; color: #34d399;">🖨️ One-Click Printer Options</h3>
                <div class="grid-2" style="text-align: left; margin-bottom: 20px;">
                    <div>
                        <label>Target Printer:</label>
                        <select id="print-printer">
                            <option value="Brother-DCP-T710W-USB">Brother DCP-T710W (USB)</option>
                            <option value="Brother-DCP-T710W-WiFi">Brother DCP-T710W (WiFi)</option>
                        </select>
                    </div>
                    <div>
                        <label>Paper & Ink Mode:</label>
                        <select id="print-mode">
                            <option value="glossy_color">🌟 Glossy Inkjet Paper (Color - High Quality)</option>
                            <option value="plain_mono">⚡ Plain Paper (Black & White - Fast Draft / Low Ink)</option>
                            <option value="plain_color">📄 Plain Paper (Color - Normal Quality)</option>
                        </select>
                    </div>
                </div>

                <div class="grid-2">
                    <button type="button" class="btn btn-success" onclick="triggerPrint()">🖨️ Send Direct Print</button>
                    <a id="btn-download" href="#" target="_blank" class="btn btn-primary" style="text-decoration:none;">📄 Open / Download PDF</a>
                </div>
                <p id="print-status" style="margin-top: 12px; font-weight: 600; font-size: 0.95rem;"></p>
            </div>
        </div>
    </div>

    <script>
        let currentResult = null;

        function switchTab(tab) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            if(tab === 'passport') {
                document.querySelectorAll('.tab-btn')[0].classList.add('active');
                document.getElementById('section-passport').style.display = 'block';
                document.getElementById('section-aadhaar').style.display = 'none';
            } else {
                document.querySelectorAll('.tab-btn')[1].classList.add('active');
                document.getElementById('section-passport').style.display = 'none';
                document.getElementById('section-aadhaar').style.display = 'block';
            }
        }

        function fileSelected(type) {
            const input = document.getElementById('file-' + type);
            if(input.files.length > 0) {
                document.getElementById(type + '-file-label').innerText = 'Selected: ' + input.files[0].name;
            }
        }

        async function handlePassport(e) {
            e.preventDefault();
            const fileInput = document.getElementById('file-passport');
            if(!fileInput.files.length) return alert('Please select a photo first');

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('quantity', document.getElementById('pass-qty').value);
            formData.append('border', document.getElementById('pass-border').value);

            const res = await fetch('/api/passport', { method: 'POST', body: formData });
            const data = await res.json();
            if(data.status === 'success') {
                showResult(data);
            } else {
                alert('Error: ' + data.message);
            }
        }

        async function handleAadhaar(e) {
            e.preventDefault();
            const fileInput = document.getElementById('file-aadhaar');
            if(!fileInput.files.length) return alert('Please select an Aadhaar PDF first');

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('password', document.getElementById('aadhaar-pw').value);

            const res = await fetch('/api/aadhaar', { method: 'POST', body: formData });
            const data = await res.json();
            if(data.status === 'success') {
                showResult(data);
            } else {
                alert('Error: ' + (data.message || data.error));
            }
        }

        function showResult(data) {
            currentResult = data;
            document.getElementById('result-panel').style.display = 'block';
            document.getElementById('preview-image').src = data.png_url + '?t=' + Date.now();
            document.getElementById('btn-download').href = data.pdf_url;
            document.getElementById('print-status').innerText = '';
            document.getElementById('result-panel').scrollIntoView({ behavior: 'smooth' });
        }

        async function triggerPrint() {
            if(!currentResult) return;
            const printer = document.getElementById('print-printer').value;
            const mode = document.getElementById('print-mode').value;
            document.getElementById('print-status').innerText = '⏳ Sending print job to ' + printer + '...';

            const res = await fetch('/api/print', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    file: currentResult.pdf,
                    printer: printer,
                    mode: mode
                })
            });
            const data = await res.json();
            if(data.status === 'success') {
                document.getElementById('print-status').innerText = '✅ ' + data.message;
            } else {
                document.getElementById('print-status').innerText = '❌ Error: ' + data.message;
            }
        }
    </script>
</body>
</html>
"""

def parse_multipart(headers, rfile):
    content_type = headers.get('Content-Type', '')
    length = int(headers.get('Content-Length', 0))
    data = rfile.read(length)
    msg_data = f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode('latin1') + data
    msg = email.message_from_bytes(msg_data, policy=default)

    fields = {}
    files = {}
    for part in msg.iter_parts():
        cd = part.get("Content-Disposition", "")
        name = part.get_param("name", header="content-disposition")
        filename = part.get_filename()
        if filename:
            files[name] = {"filename": filename, "data": part.get_payload(decode=True)}
        else:
            fields[name] = part.get_payload(decode=True).decode('utf-8')
    return fields, files

class CraftStudioHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif parsed.path.startswith("/outputs/"):
            file_name = os.path.basename(parsed.path)
            file_path = OUTPUT_DIR / file_name
            if file_path.exists():
                self.send_response(200)
                if file_name.endswith(".png"):
                    self.send_header("Content-Type", "image/png")
                elif file_name.endswith(".pdf"):
                    self.send_header("Content-Type", "application/pdf")
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "File not found")
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/passport":
            fields, files = parse_multipart(self.headers, self.rfile)
            file_info = files.get('file')
            qty = int(fields.get('quantity', '6'))
            border = fields.get('border', '#b0b0b0')

            input_path = UPLOAD_DIR / f"upload_{file_info['filename']}"
            with open(input_path, 'wb') as f:
                f.write(file_info['data'])

            out_png = OUTPUT_DIR / "passport_sheet.png"
            out_pdf = OUTPUT_DIR / "passport_sheet.pdf"

            try:
                res = make_passport_sheet(str(input_path), str(out_png), str(out_pdf), quantity=qty, border_color=border)
                res["png_url"] = "/outputs/passport_sheet.png"
                res["pdf_url"] = "/outputs/passport_sheet.pdf"
                self.send_json(res)
            except Exception as e:
                self.send_json({"status": "error", "message": str(e)})

        elif parsed.path == "/api/aadhaar":
            fields, files = parse_multipart(self.headers, self.rfile)
            file_info = files.get('file')
            pw = fields.get('password', '')

            input_path = UPLOAD_DIR / f"upload_{file_info['filename']}"
            with open(input_path, 'wb') as f:
                f.write(file_info['data'])

            out_png = OUTPUT_DIR / "aadhaar_id_sheet.png"
            out_pdf = OUTPUT_DIR / "aadhaar_id_sheet.pdf"

            try:
                res = process_aadhaar_pdf(str(input_path), str(out_png), str(out_pdf), password=pw)
                if res.get("status") == "success":
                    res["png_url"] = "/outputs/aadhaar_id_sheet.png"
                    res["pdf_url"] = "/outputs/aadhaar_id_sheet.pdf"
                self.send_json(res)
            except Exception as e:
                self.send_json({"status": "error", "message": str(e)})

        elif parsed.path == "/api/print":
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            data = json.loads(body.decode('utf-8'))
            file_to_print = data.get("file")
            printer = data.get("printer", "Brother-DCP-T710W-USB")
            mode = data.get("mode", "plain_mono")

            # Map presets
            if mode == "glossy_color":
                media = "BrotherGlossyR"
                color = "Color"
                res_mode = "Normal"
            elif mode == "plain_color":
                media = "Plain"
                color = "Color"
                res_mode = "PlainNormal"
            else: # plain_mono
                media = "Plain"
                color = "Mono"
                res_mode = "PlainFast"

            try:
                out = print_file(file_to_print, printer_name=printer, media_type=media, color_mode=color, resolution=res_mode)
                self.send_json({"status": "success", "message": f"Print job sent successfully! ({out})"})
            except Exception as e:
                self.send_json({"status": "error", "message": str(e)})

    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

def start_server():
    with socketserver.TCPServer(("", PORT), CraftStudioHandler) as httpd:
        print(f"Craft Studio server running at http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    start_server()
