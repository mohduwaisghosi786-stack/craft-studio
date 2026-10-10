#!/usr/bin/env python3
"""
craft-studio Web UI Server
Modern, lightweight local web GUI for generating Passport Photos and Aadhaar ID Cards.
Guarantees Full Color output, visible password entry, and granular printer options.
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

PORT = 8091
BASE_DIR = Path(__file__).parent.resolve()
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
TEMPLATE_PATH = BASE_DIR / "templates" / "index.html"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

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
            with open(TEMPLATE_PATH, "rb") as f:
                self.wfile.write(f.read())
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
            bright = float(fields.get('brightness', '1.0'))
            contrast = float(fields.get('contrast', '1.0'))
            sat = float(fields.get('saturation', '1.0'))

            input_path = UPLOAD_DIR / f"upload_{file_info['filename']}"
            with open(input_path, 'wb') as f:
                f.write(file_info['data'])

            out_png = OUTPUT_DIR / "passport_sheet.png"
            out_pdf = OUTPUT_DIR / "passport_sheet.pdf"

            try:
                res = make_passport_sheet(
                    str(input_path), str(out_png), str(out_pdf),
                    quantity=qty, border_color=border,
                    brightness=bright, contrast=contrast, saturation=sat
                )
                res["png_url"] = "/outputs/passport_sheet.png"
                res["pdf_url"] = "/outputs/passport_sheet.pdf"
                self.send_json(res)
            except Exception as e:
                self.send_json({"status": "error", "message": str(e)})

        elif parsed.path == "/api/aadhaar":
            fields, files = parse_multipart(self.headers, self.rfile)
            file_info = files.get('file')
            pw = fields.get('password', '').strip()

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
            media = data.get("media", "BrotherGlossyR")
            quality = data.get("quality", "Normal")
            color = data.get("color", "Color")

            try:
                out = print_file(file_to_print, printer_name=printer, media_type=media, color_mode=color, resolution=quality)
                self.send_json({"status": "success", "message": f"Print job sent successfully! ({out})"})
            except Exception as e:
                self.send_json({"status": "error", "message": str(e)})

    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def start_server():
    with ReusableTCPServer(("", PORT), CraftStudioHandler) as httpd:
        print(f"Craft Studio server running at http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    start_server()
