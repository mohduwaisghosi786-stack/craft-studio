#!/usr/bin/env python3
"""
Owais Internet Cafe - Passport & Aadhaar Studio
Created by Mohd Uwais Ghosi
Native Linux Desktop Application (GTK 3 + Custom Modern Styling).
"""

import sys
import os
import threading
from pathlib import Path

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GdkPixbuf, Gdk

from engine import make_passport_sheet, process_aadhaar_pdf, print_file

CSS_STYLE = b"""
window {
    background-color: #0b0f19;
    color: #f1f5f9;
    font-family: 'Outfit', 'Inter', 'Noto Sans', sans-serif;
}

headerbar {
    background: #111827;
    border-bottom: 1px solid #1f2937;
}

.brand-title {
    font-size: 22px;
    font-weight: 800;
    color: #38bdf8;
}

.brand-credit {
    font-size: 11px;
    color: #a78bfa;
    font-weight: 600;
}

notebook {
    background: transparent;
    border: none;
}

notebook tab {
    background: #131b2e;
    color: #94a3b8;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: bold;
    border-radius: 8px 8px 0 0;
    border: 1px solid #23304d;
    margin-right: 4px;
}

notebook tab:checked {
    background: #2563eb;
    color: #ffffff;
    border-color: #3b82f6;
}

.card-panel {
    background-color: #131b2e;
    border: 1px solid #23304d;
    border-radius: 12px;
    padding: 16px;
}

.preview-container {
    background-color: #070b14;
    border: 2px dashed #334155;
    border-radius: 12px;
    padding: 12px;
}

.btn-primary {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    color: #ffffff;
    font-size: 14px;
    font-weight: 700;
    padding: 12px 20px;
    border-radius: 10px;
    border: none;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
}

.btn-primary:hover {
    background: linear-gradient(135deg, #3b82f6, #2563eb);
}

.btn-print {
    background: linear-gradient(135deg, #10b981, #059669);
    color: #ffffff;
    font-size: 15px;
    font-weight: 800;
    padding: 12px 24px;
    border-radius: 10px;
    border: none;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.35);
}

.btn-print:hover {
    background: linear-gradient(135deg, #34d399, #10b981);
}

entry, combobox, combobox text {
    background-color: #0c1424;
    color: #f8fafc;
    border: 1px solid #23304d;
    border-radius: 8px;
    padding: 8px;
}

entry:focus, combobox:focus {
    border-color: #38bdf8;
}

scale trough {
    background-color: #1e293b;
    border-radius: 6px;
    min-height: 8px;
}

scale highlight {
    background-color: #38bdf8;
    border-radius: 6px;
}
"""

class OwaisCafeStudio(Gtk.Window):
    def __init__(self):
        super().__init__(title="Owais Internet Cafe - Passport & Aadhaar Studio")
        self.set_default_size(1050, 780)
        self.set_border_width(18)
        self.set_position(Gtk.WindowPosition.CENTER)

        # Apply Modern Dark Theme CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(CSS_STYLE)
        screen = Gdk.Screen.get_default()
        style_ctx = Gtk.StyleContext()
        style_ctx.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.passport_file = None
        self.aadhaar_file = None
        self.current_result = None

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.add(main_box)

        # 🌟 Header Branding
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        title_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        
        lbl_title = Gtk.Label()
        lbl_title.set_markup("<span class='brand-title'>⚡ Owais Internet Cafe Studio</span>")
        lbl_title.set_xalign(0)
        
        lbl_credit = Gtk.Label()
        lbl_credit.set_markup("<span class='brand-credit'>Crafted by Mohd Uwais Ghosi</span> • <i>Passport Photos & Aadhaar Print Suite</i>")
        lbl_credit.set_xalign(0)

        title_vbox.pack_start(lbl_title, False, False, 0)
        title_vbox.pack_start(lbl_credit, False, False, 0)
        header_box.pack_start(title_vbox, True, True, 0)

        main_box.pack_start(header_box, False, False, 0)

        # 2-Column Split: Left Controls (Tabs) | Right Live HD Preview
        paned = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)
        main_box.pack_start(paned, True, True, 0)

        # === LEFT PANEL: CONTROLS ===
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        left_box.set_size_request(460, -1)
        paned.pack_start(left_box, False, False, 0)

        self.notebook = Gtk.Notebook()
        left_box.pack_start(self.notebook, False, False, 0)

        # --- TAB 1: Passport Photos ---
        tab_pass = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        tab_pass.set_border_width(12)
        tab_pass.get_style_context().add_class('card-panel')

        tab_pass.pack_start(Gtk.Label(label="1. Select Customer Photo:", xalign=0), False, False, 0)
        btn_pass = Gtk.FileChooserButton(title="Select Customer Photo", action=Gtk.FileChooserAction.OPEN)
        btn_pass.connect("file-set", self.on_passport_file_set)
        tab_pass.pack_start(btn_pass, False, False, 0)

        # Quantity
        tab_pass.pack_start(Gtk.Label(label="2. Quantity & Layout:", xalign=0), False, False, 0)
        self.combo_qty = Gtk.ComboBoxText()
        self.combo_qty.append("6", "6 Photos (1 Single Row - 1.5mm Gap & Cut Guide)")
        self.combo_qty.append("8", "8 Photos (2 Rows of 4)")
        self.combo_qty.append("10", "10 Photos (2 Rows of 5)")
        self.combo_qty.append("12", "12 Photos (2 Rows of 6)")
        self.combo_qty.append("30", "30 Photos (Full A4 Page)")
        self.combo_qty.set_active(0)
        tab_pass.pack_start(self.combo_qty, False, False, 0)

        # Tuning Sliders
        tab_pass.pack_start(Gtk.Label(label="3. Photo Tuning:", xalign=0), False, False, 0)
        box_tune = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        # Brightness
        b_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        b_box.pack_start(Gtk.Label(label="Brightness:"), False, False, 0)
        self.adj_b = Gtk.Adjustment(value=1.0, lower=0.6, upper=1.5, step_increment=0.05)
        scale_b = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.adj_b)
        scale_b.set_digits(2)
        b_box.pack_start(scale_b, True, True, 0)
        box_tune.pack_start(b_box, False, False, 0)

        # Contrast
        c_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        c_box.pack_start(Gtk.Label(label="Contrast:"), False, False, 0)
        self.adj_c = Gtk.Adjustment(value=1.0, lower=0.6, upper=1.5, step_increment=0.05)
        scale_c = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.adj_c)
        scale_c.set_digits(2)
        c_box.pack_start(scale_c, True, True, 0)
        box_tune.pack_start(c_box, False, False, 0)

        tab_pass.pack_start(box_tune, False, False, 0)

        # Generate Button
        self.btn_gen_pass = Gtk.Button(label="⚡ Generate Passport Sheet")
        self.btn_gen_pass.get_style_context().add_class('btn-primary')
        self.btn_gen_pass.connect("clicked", self.on_gen_passport)
        tab_pass.pack_start(self.btn_gen_pass, False, False, 0)

        self.notebook.append_page(tab_pass, Gtk.Label(label="📷 Passport Photos"))

        # --- TAB 2: Aadhaar Card ---
        tab_aadh = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        tab_aadh.set_border_width(12)
        tab_aadh.get_style_context().add_class('card-panel')

        tab_aadh.pack_start(Gtk.Label(label="1. Select e-Aadhaar PDF:", xalign=0), False, False, 0)
        btn_aadh = Gtk.FileChooserButton(title="Select e-Aadhaar PDF", action=Gtk.FileChooserAction.OPEN)
        btn_aadh.connect("file-set", self.on_aadhaar_file_set)
        tab_aadh.pack_start(btn_aadh, False, False, 0)

        tab_aadh.pack_start(Gtk.Label(label="2. PDF Password (Visible):", xalign=0), False, False, 0)
        self.entry_pw = Gtk.Entry()
        self.entry_pw.set_visibility(True)
        self.entry_pw.set_placeholder_text("e.g. MOHD1998 (Enter password directly)")
        tab_aadh.pack_start(self.entry_pw, False, False, 0)

        tab_aadh.pack_start(Gtk.Label(label="ℹ️ Calibrated for 65 × 95 mm Pouch (3.5mm Seal)", xalign=0), False, False, 0)

        self.btn_gen_aadh = Gtk.Button(label="⚡ Extract & Format Aadhaar Card")
        self.btn_gen_aadh.get_style_context().add_class('btn-primary')
        self.btn_gen_aadh.connect("clicked", self.on_gen_aadhaar)
        tab_aadh.pack_start(self.btn_gen_aadh, False, False, 0)

        self.notebook.append_page(tab_aadh, Gtk.Label(label="🪪 Aadhaar Card (65 × 95mm)"))

        # --- PRINTER SETTINGS BOX ---
        print_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        print_box.get_style_context().add_class('card-panel')
        
        lbl_pr_title = Gtk.Label()
        lbl_pr_title.set_markup("<span weight='bold' foreground='#34d399'>🖨️ Brother DCP-T710W Printer Controls</span>")
        lbl_pr_title.set_xalign(0)
        print_box.pack_start(lbl_pr_title, False, False, 0)

        # Printer Target & Color Mode
        p_row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        p_row1.pack_start(Gtk.Label(label="Target:"), False, False, 0)
        self.combo_printer = Gtk.ComboBoxText()
        self.combo_printer.append("Brother-DCP-T710W-USB", "Brother (USB)")
        self.combo_printer.append("Brother-DCP-T710W-WiFi", "Brother (WiFi)")
        self.combo_printer.set_active(0)
        p_row1.pack_start(self.combo_printer, True, True, 0)

        p_row1.pack_start(Gtk.Label(label="Mode:"), False, False, 0)
        self.combo_color = Gtk.ComboBoxText()
        self.combo_color.append("Color", "Color (Photo/Card)")
        self.combo_color.append("Mono", "Black & White (Mono)")
        self.combo_color.set_active(0)
        p_row1.pack_start(self.combo_color, True, True, 0)
        print_box.pack_start(p_row1, False, False, 0)

        # Media & Quality
        p_row2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        p_row2.pack_start(Gtk.Label(label="Paper:"), False, False, 0)
        self.combo_media = Gtk.ComboBoxText()
        self.combo_media.append("BrotherGlossyR", "Glossy Photo Paper")
        self.combo_media.append("Plain", "Plain Paper")
        self.combo_media.set_active(0)
        p_row2.pack_start(self.combo_media, True, True, 0)

        p_row2.pack_start(Gtk.Label(label="Quality:"), False, False, 0)
        self.combo_quality = Gtk.ComboBoxText()
        self.combo_quality.append("Normal", "Normal (Standard)")
        self.combo_quality.append("High", "High Quality")
        self.combo_quality.append("PlainFast", "Fast Draft")
        self.combo_quality.set_active(0)
        p_row2.pack_start(self.combo_quality, True, True, 0)
        print_box.pack_start(p_row2, False, False, 0)

        # Print Trigger Button
        self.btn_print = Gtk.Button(label="🖨️ Direct Print (100% True Scale)")
        self.btn_print.get_style_context().add_class('btn-print')
        self.btn_print.set_sensitive(False)
        self.btn_print.connect("clicked", self.on_print_clicked)
        print_box.pack_start(self.btn_print, False, False, 0)

        left_box.pack_start(print_box, False, False, 0)

        # === RIGHT PANEL: FULL PREVIEW WINDOW ===
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        paned.pack_start(right_box, True, True, 0)

        prev_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        lbl_prev_title = Gtk.Label()
        lbl_prev_title.set_markup("<span weight='bold' font='14px'>📄 A4 Sheet Live Preview</span>")
        lbl_prev_title.set_xalign(0)
        prev_header.pack_start(lbl_prev_title, True, True, 0)

        self.lbl_status = Gtk.Label(label="Ready for input")
        prev_header.pack_start(self.lbl_status, False, False, 0)
        right_box.pack_start(prev_header, False, False, 0)

        # Scrolled Preview Canvas
        self.preview_scrolled = Gtk.ScrolledWindow()
        self.preview_scrolled.get_style_context().add_class('preview-container')
        self.preview_scrolled.set_min_content_height(550)
        
        self.img_preview = Gtk.Image()
        self.preview_scrolled.add(self.img_preview)
        right_box.pack_start(self.preview_scrolled, True, True, 0)

    def on_passport_file_set(self, widget):
        self.passport_file = widget.get_filename()

    def on_aadhaar_file_set(self, widget):
        self.aadhaar_file = widget.get_filename()

    def on_gen_passport(self, widget):
        if not self.passport_file:
            self.lbl_status.set_text("❌ Please select a photo first!")
            return
        qty = int(self.combo_qty.get_active_id())
        b = self.adj_b.get_value()
        c = self.adj_c.get_value()
        self.lbl_status.set_text("⏳ Generating passport sheet...")

        threading.Thread(target=self._process_pass_thread, args=(qty, b, c)).start()

    def _process_pass_thread(self, qty, b, c):
        out_png = "/tmp/craft_gui_passport.png"
        out_pdf = "/tmp/craft_gui_passport.pdf"
        try:
            res = make_passport_sheet(self.passport_file, out_png, out_pdf, quantity=qty, brightness=b, contrast=c)
            self.current_result = res
            GLib.idle_add(self._update_preview, out_png, "✓ Passport Sheet Ready (6 in 1 Row)!")
        except Exception as e:
            GLib.idle_add(self.lbl_status.set_text, f"❌ Error: {str(e)}")

    def on_gen_aadhaar(self, widget):
        if not self.aadhaar_file:
            self.lbl_status.set_text("❌ Please select an Aadhaar PDF first!")
            return
        pw = self.entry_pw.get_text()
        self.lbl_status.set_text("⏳ Extracting 65 × 95 mm Pouch Aadhaar Card...")

        threading.Thread(target=self._process_aadh_thread, args=(pw,)).start()

    def _process_aadh_thread(self, pw):
        out_png = "/tmp/craft_gui_aadhaar.png"
        out_pdf = "/tmp/craft_gui_aadhaar.pdf"
        try:
            res = process_aadhaar_pdf(self.aadhaar_file, out_png, out_pdf, password=pw)
            if res.get("status") == "error":
                GLib.idle_add(self.lbl_status.set_text, f"❌ {res.get('message')}")
                return
            self.current_result = res
            GLib.idle_add(self._update_preview, out_png, "✓ Pouch-Sized Aadhaar Sheet Ready!")
        except Exception as e:
            GLib.idle_add(self.lbl_status.set_text, f"❌ Error: {str(e)}")

    def _update_preview(self, png_path, status_text):
        try:
            # Scale preview nicely to fit view
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(png_path, 520, 720, True)
            self.img_preview.set_from_pixbuf(pixbuf)
            self.btn_print.set_sensitive(True)
            self.lbl_status.set_text(status_text)
        except Exception as e:
            self.lbl_status.set_text(f"Error loading preview: {e}")

    def on_print_clicked(self, widget):
        if not self.current_result:
            return
        printer = self.combo_printer.get_active_id()
        media = self.combo_media.get_active_id()
        quality = self.combo_quality.get_active_id()
        color = self.combo_color.get_active_id()

        self.lbl_status.set_text(f"⏳ Printing to {printer} (100% True Scale)...")
        threading.Thread(target=self._print_thread, args=(self.current_result["pdf"], printer, media, color, quality)).start()

    def _print_thread(self, pdf_path, printer, media, color, res_mode):
        try:
            out = print_file(pdf_path, printer_name=printer, media_type=media, color_mode=color, resolution=res_mode)
            GLib.idle_add(self.lbl_status.set_text, f"✅ Sent: {out}")
        except Exception as e:
            GLib.idle_add(self.lbl_status.set_text, f"❌ Print Error: {str(e)}")

def main():
    app = OwaisCafeStudio()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
