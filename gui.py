#!/usr/bin/env python3
"""
craft-studio Native Desktop GUI
Built using PyGObject (GTK 3) - Native Linux Desktop Application.
Supports exact 3.5x4.5cm Passport photos and 65x95mm Lamination Pouch Aadhaar Cards.
"""

import sys
import os
import threading
from pathlib import Path

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GdkPixbuf

from engine import make_passport_sheet, process_aadhaar_pdf, print_file

class CraftStudioWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Craft Studio - Passport & Aadhaar")
        self.set_default_size(880, 720)
        self.set_border_width(15)
        self.set_position(Gtk.WindowPosition.CENTER)

        self.passport_file = None
        self.aadhaar_file = None
        self.current_result = None

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.add(main_box)

        # Header Title
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        lbl_title = Gtk.Label()
        lbl_title.set_markup("<span size='xx-large' weight='bold' foreground='#3b82f6'>⚡ Craft Studio</span>")
        lbl_sub = Gtk.Label(label="Indian Passport (3.5 × 4.5 cm) & 65 × 95 mm Pouch Aadhaar System")
        title_box.pack_start(lbl_title, False, False, 0)
        title_box.pack_start(lbl_sub, False, False, 0)
        main_box.pack_start(title_box, False, False, 0)

        # Notebook (Tabs)
        self.notebook = Gtk.Notebook()
        main_box.pack_start(self.notebook, False, False, 0)

        # TAB 1: Passport Photos
        tab1_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        tab1_box.set_border_width(15)

        btn_pass_file = Gtk.FileChooserButton(title="Select Passport Photo", action=Gtk.FileChooserAction.OPEN)
        btn_pass_file.connect("file-set", self.on_passport_file_set)
        tab1_box.pack_start(Gtk.Label(label="Select Source Photo (JPG, PNG, WebP):", xalign=0), False, False, 0)
        tab1_box.pack_start(btn_pass_file, False, False, 0)

        # Quantity choice
        box_qty = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box_qty.pack_start(Gtk.Label(label="Quantity:"), False, False, 0)
        self.combo_qty = Gtk.ComboBoxText()
        self.combo_qty.append("6", "6 Photos (Exact 3.5 × 4.5 cm Row - Top Aligned)")
        self.combo_qty.append("8", "8 Photos (2 Rows)")
        self.combo_qty.append("10", "10 Photos (2 Rows)")
        self.combo_qty.append("12", "12 Photos (2 Rows)")
        self.combo_qty.append("30", "30 Photos (Full A4 Page)")
        self.combo_qty.set_active(0)
        box_qty.pack_start(self.combo_qty, True, True, 0)
        tab1_box.pack_start(box_qty, False, False, 0)

        # Manual Tuning Sliders in GUI
        box_tune = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        
        # Brightness
        box_tune.pack_start(Gtk.Label(label="Brightness:"), False, False, 0)
        self.adj_b = Gtk.Adjustment(value=1.0, lower=0.6, upper=1.5, step_increment=0.05)
        scale_b = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.adj_b)
        scale_b.set_digits(2)
        box_tune.pack_start(scale_b, True, True, 0)

        # Contrast
        box_tune.pack_start(Gtk.Label(label="Contrast:"), False, False, 0)
        self.adj_c = Gtk.Adjustment(value=1.0, lower=0.6, upper=1.5, step_increment=0.05)
        scale_c = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.adj_c)
        scale_c.set_digits(2)
        box_tune.pack_start(scale_c, True, True, 0)

        tab1_box.pack_start(box_tune, False, False, 0)

        # Generate Button
        self.btn_gen_passport = Gtk.Button(label="⚡ Generate Passport Sheet (Exact 3.5 × 4.5 cm)")
        self.btn_gen_passport.connect("clicked", self.on_generate_passport)
        tab1_box.pack_start(self.btn_gen_passport, False, False, 0)

        self.notebook.append_page(tab1_box, Gtk.Label(label="📷 Passport Photos"))

        # TAB 2: Aadhaar Card
        tab2_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        tab2_box.set_border_width(15)

        btn_aadh_file = Gtk.FileChooserButton(title="Select Aadhaar PDF", action=Gtk.FileChooserAction.OPEN)
        btn_aadh_file.connect("file-set", self.on_aadhaar_file_set)
        tab2_box.pack_start(Gtk.Label(label="Select e-Aadhaar PDF:", xalign=0), False, False, 0)
        tab2_box.pack_start(btn_aadh_file, False, False, 0)

        # Visible Password Entry
        box_pw = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box_pw.pack_start(Gtk.Label(label="PDF Password (Visible):"), False, False, 0)
        self.entry_pw = Gtk.Entry()
        self.entry_pw.set_visibility(True)
        self.entry_pw.set_placeholder_text("e.g. MOHD1998 (Enter directly)")
        box_pw.pack_start(self.entry_pw, True, True, 0)
        tab2_box.pack_start(box_pw, False, False, 0)

        # Generate Aadhaar Button
        self.btn_gen_aadhaar = Gtk.Button(label="⚡ Extract ID Card (Calibrated for 65 × 95 mm Pouch)")
        self.btn_gen_aadhaar.connect("clicked", self.on_generate_aadhaar)
        tab2_box.pack_start(self.btn_gen_aadhaar, False, False, 0)

        self.notebook.append_page(tab2_box, Gtk.Label(label="🪪 Aadhaar Card (65 × 95 mm)"))

        # Preview Area
        frame_preview = Gtk.Frame(label="Preview & Brother Printer Controls")
        frame_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        frame_box.set_border_width(12)
        frame_preview.add(frame_box)

        # Scrolled Window for Preview
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_min_content_height(280)
        self.img_preview = Gtk.Image()
        scrolled.add(self.img_preview)
        frame_box.pack_start(scrolled, True, True, 0)

        # Printer settings box
        print_opts_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        print_opts_box.pack_start(Gtk.Label(label="Printer:"), False, False, 0)
        self.combo_printer = Gtk.ComboBoxText()
        self.combo_printer.append("Brother-DCP-T710W-USB", "Brother DCP-T710W (USB)")
        self.combo_printer.append("Brother-DCP-T710W-WiFi", "Brother DCP-T710W (WiFi)")
        self.combo_printer.set_active(0)
        print_opts_box.pack_start(self.combo_printer, False, False, 0)

        print_opts_box.pack_start(Gtk.Label(label="Media:"), False, False, 0)
        self.combo_media = Gtk.ComboBoxText()
        self.combo_media.append("BrotherGlossyR", "Glossy Photo Paper")
        self.combo_media.append("Plain", "Plain Paper")
        self.combo_media.set_active(0)
        print_opts_box.pack_start(self.combo_media, False, False, 0)

        print_opts_box.pack_start(Gtk.Label(label="Quality:"), False, False, 0)
        self.combo_quality = Gtk.ComboBoxText()
        self.combo_quality.append("Normal", "Normal (Recommended)")
        self.combo_quality.append("High", "High Quality")
        self.combo_quality.append("PlainFast", "Fast Draft")
        self.combo_quality.set_active(0)
        print_opts_box.pack_start(self.combo_quality, True, True, 0)

        frame_box.pack_start(print_opts_box, False, False, 0)

        # Print & Status
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        self.btn_print = Gtk.Button(label="🖨️ Direct Print Sheet (100% True Scale)")
        self.btn_print.set_sensitive(False)
        self.btn_print.connect("clicked", self.on_print_clicked)
        action_box.pack_start(self.btn_print, True, True, 0)

        self.lbl_status = Gtk.Label(label="Ready")
        action_box.pack_start(self.lbl_status, True, True, 0)
        frame_box.pack_start(action_box, False, False, 0)

        main_box.pack_start(frame_preview, True, True, 0)

    def on_passport_file_set(self, widget):
        self.passport_file = widget.get_filename()

    def on_aadhaar_file_set(self, widget):
        self.aadhaar_file = widget.get_filename()

    def on_generate_passport(self, widget):
        if not self.passport_file:
            self.lbl_status.set_text("❌ Please select a photo first!")
            return
        qty = int(self.combo_qty.get_active_id())
        b = self.adj_b.get_value()
        c = self.adj_c.get_value()
        self.lbl_status.set_text("⏳ Generating 3.5 × 4.5 cm passport sheet...")

        threading.Thread(target=self._process_passport_thread, args=(qty, b, c)).start()

    def _process_passport_thread(self, qty, b, c):
        out_png = "/tmp/craft_gui_passport.png"
        out_pdf = "/tmp/craft_gui_passport.pdf"
        try:
            res = make_passport_sheet(self.passport_file, out_png, out_pdf, quantity=qty, brightness=b, contrast=c)
            self.current_result = res
            GLib.idle_add(self._update_preview, out_png, "✓ Passport Sheet Ready (3.5 × 4.5 cm)!")
        except Exception as e:
            GLib.idle_add(self.lbl_status.set_text, f"❌ Error: {str(e)}")

    def on_generate_aadhaar(self, widget):
        if not self.aadhaar_file:
            self.lbl_status.set_text("❌ Please select an Aadhaar PDF first!")
            return
        pw = self.entry_pw.get_text()
        self.lbl_status.set_text("⏳ Extracting 65 × 95 mm Pouch Aadhaar Card...")

        threading.Thread(target=self._process_aadhaar_thread, args=(pw,)).start()

    def _process_aadhaar_thread(self, pw):
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
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(png_path, 420, 320, True)
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

        self.lbl_status.set_text(f"⏳ Printing to {printer} (100% True Scale)...")
        threading.Thread(target=self._print_thread, args=(self.current_result["pdf"], printer, media, "Color", quality)).start()

    def _print_thread(self, pdf_path, printer, media, color, res_mode):
        try:
            out = print_file(pdf_path, printer_name=printer, media_type=media, color_mode=color, resolution=res_mode)
            GLib.idle_add(self.lbl_status.set_text, f"✅ Sent: {out}")
        except Exception as e:
            GLib.idle_add(self.lbl_status.set_text, f"❌ Print Error: {str(e)}")

def main():
    app = CraftStudioWindow()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
