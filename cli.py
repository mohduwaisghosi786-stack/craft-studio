#!/usr/bin/env python3
"""
craft-studio CLI
Direct command-line automation for passport photos and Aadhaar ID cards.
"""

import argparse
import sys
from pathlib import Path
from engine import make_passport_sheet, process_aadhaar_pdf, print_file

def main():
    parser = argparse.ArgumentParser(description="Craft Studio Automation CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Passport subcommand
    p_pass = subparsers.add_parser("passport", help="Generate Passport photo sheet on A4")
    p_pass.add_argument("input", help="Path to input photo (JPG/PNG)")
    p_pass.add_argument("-q", "--quantity", type=int, default=6, help="Photo quantity (6, 8, 10, 12, 30)")
    p_pass.add_argument("-o", "--output", default="passport_sheet.png", help="Output PNG path")
    p_pass.add_argument("--pdf", default="passport_sheet.pdf", help="Output PDF path")
    p_pass.add_argument("--print", action="store_true", help="Send direct print after generation")
    p_pass.add_argument("--printer", default="Brother-DCP-T710W-USB", help="Printer name")
    p_pass.add_argument("--glossy", action="store_true", help="Use Glossy Photo Paper mode")
    p_pass.add_argument("--color", action="store_true", help="Print in color")

    # Aadhaar subcommand
    p_aadh = subparsers.add_parser("aadhaar", help="Extract and format Aadhaar PDF into ID Card")
    p_aadh.add_argument("input", help="Path to Aadhaar PDF")
    p_aadh.add_argument("-p", "--password", default="", help="PDF unlock password")
    p_aadh.add_argument("-o", "--output", default="aadhaar_id.png", help="Output PNG path")
    p_aadh.add_argument("--pdf", default="aadhaar_id.pdf", help="Output PDF path")
    p_aadh.add_argument("--print", action="store_true", help="Send direct print after generation")
    p_aadh.add_argument("--printer", default="Brother-DCP-T710W-USB", help="Printer name")
    p_aadh.add_argument("--glossy", action="store_true", help="Use Glossy Photo Paper mode")
    p_aadh.add_argument("--color", action="store_true", help="Print in color")

    # Direct Print subcommand
    p_pr = subparsers.add_parser("print", help="Direct print an existing file")
    p_pr.add_argument("file", help="File to print (PDF/PNG)")
    p_pr.add_argument("--printer", default="Brother-DCP-T710W-USB", help="Printer name")
    p_pr.add_argument("--glossy", action="store_true", help="Use Glossy Photo Paper mode")
    p_pr.add_argument("--color", action="store_true", help="Print in color")
    p_pr.add_argument("--fast", action="store_true", help="Fast draft mode")

    args = parser.parse_args()

    if args.command == "passport":
        print(f"📷 Processing passport photos ({args.quantity} photos)...")
        res = make_passport_sheet(args.input, args.output, args.pdf, quantity=args.quantity)
        print(f"✓ Generated PNG: {res['png']}")
        print(f"✓ Generated PDF: {res['pdf']}")

        if args.print:
            media = "BrotherGlossyR" if args.glossy else "Plain"
            color = "Color" if args.color else "Mono"
            resolution = "Normal" if args.glossy else "PlainFast"
            print(f"🖨️ Printing to {args.printer}...")
            out = print_file(res["pdf"], printer_name=args.printer, media_type=media, color_mode=color, resolution=resolution)
            print(f"✓ Print sent: {out}")

    elif args.command == "aadhaar":
        print("🪪 Extracting Aadhaar ID card...")
        res = process_aadhaar_pdf(args.input, args.output, args.pdf, password=args.password)
        if res.get("status") == "error":
            print(f"❌ Error: {res.get('message')}")
            sys.exit(1)
        print(f"✓ Generated ID PNG: {res['png']}")
        print(f"✓ Generated ID PDF: {res['pdf']}")

        if args.print:
            media = "BrotherGlossyR" if args.glossy else "Plain"
            color = "Color" if args.color else "Mono"
            resolution = "Normal" if args.glossy else "PlainFast"
            print(f"🖨️ Printing to {args.printer}...")
            out = print_file(res["pdf"], printer_name=args.printer, media_type=media, color_mode=color, resolution=resolution)
            print(f"✓ Print sent: {out}")

    elif args.command == "print":
        media = "BrotherGlossyR" if args.glossy else "Plain"
        color = "Color" if args.color else "Mono"
        resolution = "PlainFast" if args.fast else ("Normal" if args.glossy else "PlainNormal")
        print(f"🖨️ Printing {args.file} to {args.printer}...")
        out = print_file(args.file, printer_name=args.printer, media_type=media, color_mode=color, resolution=resolution)
        print(f"✓ Print sent: {out}")

if __name__ == "__main__":
    main()
