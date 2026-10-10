#!/usr/bin/env python3
"""
UWAIS INternet CAfe - Passport & Aadhaar Studio
build by UWAIS GHosi
Ultra-Modern, Fluid & Fully-Responsive GTK 3 Native Desktop Suite
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
/* Global Reset & Futuristic Typography */
* {
    font-family: 'Outfit', 'Segoe UI', 'Inter', 'Ubuntu', sans-serif;
}

window {
    background: #090d16;
    color: #f8fafc;
}

/* Header & Branding Bar */
.brand-title {
    font-size: 24px;
    font-weight: 900;
    color: #38bdf8;
}

.brand-badge {
    background: rgba(56, 189, 248, 0.12);
    border: 1px solid rgba(56, 189, 248, 0.4);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 11px;
    font-weight: 800;
    color: #38bdf8;
}

.brand-credit {
    font-size: 13px;
    color: #c084fc;
    font-weight: 700;
}

/* Tab Navigation */
notebook {
    background: transparent;
    border: none;
}

notebook header {
    background: transparent;
    border: none;
    padding-bottom: 6px;
}

notebook tab {
    background: #0f172a;
    color: #94a3b8;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: 700;
    border-radius: 12px 12px 0 0;
    border: 1px solid #1e293b;
    border-bottom: none;
    margin-right: 6px;
}

notebook tab:hover {
    background: #1e293b;
    color: #38bdf8;
}

notebook tab:checked {
    background: #2563eb;
    color: #ffffff;
    border-color: #3b82f6;
}

/* Card Panels */
.card-panel {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 16px;
    padding: 18px;
}

.section-label {
    font-size: 13px;
    font-weight: 700;
    color: #93c5fd;
}

/* Inputs & Combos */
entry, combobox button {
    background: #090e1a;
    color: #f8fafc;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 8px 12px;
    font-size: 13px;
    transition: all 150ms ease;
}

entry:focus, combobox button:focus {
    border-color: #38bdf8;
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.25);
}

/* Sliders */
scale trough {
    background: #0b1120;
    border: 1px solid #1e293b;
    border-radius: 8px;
    min-height: 8px;
}

scale highlight {
    background: linear-gradient(90deg, #38bdf8, #818cf8);
    border-radius: 8px;
}

scale slider {
    background: #ffffff;
    border-radius: 50%;
    min-width: 18px;
    min-height: 18px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.6);
}

/* Action Buttons */
.btn-primary {
    background: linear-gradient(135deg, #0284c7 0%, #2563eb 50%, #4f46e5 100%);
    color: #ffffff;
    font-size: 14px;
    font-weight: 800;
    padding: 12px 20px;
    border-radius: 12px;
    border: none;
    box-shadow: 0 4px 16px rgba(37, 99, 235, 0.4);
    transition: all 200ms ease;
}

.btn-primary:hover {
    background: linear-gradient(135deg, #38bdf8 0%, #3b82f6 50%, #6366f1 100%);
    box-shadow: 0 6px 22px rgba(56, 189, 248, 0.55);
}

.btn-print {
    background: linear-gradient(135deg, #059669 0%, #10b981 100%);
    color: #ffffff;
    font-size: 15px;
    font-weight: 900;
    padding: 14px 24px;
    border-radius: 12px;
    border: none;
    box-shadow: 0 4px 16px rgba(16, 185, 129, 0.4);
    transition: all 200ms ease;
}

.btn-print:hover {
    background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
    box-shadow: 0 6px 24px rgba(16, 185, 129, 0.6);
}

.btn-print:disabled {
    background: #1e293b;
    color: #64748b;
    box-shadow: none;
}

/* Preview Canvas Container */
.preview-card {
    background: rgba(3, 7, 18, 0.9);
    border: 1px solid #1e293b;
    border-radius: 16px;
    padding: 16px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
}

.status-badge {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.4);
    border-radius: 20px;
    padding: 4px 14px;
    color: #34d399;
    font-size: 12px;
    font-weight: 700;
}
"""

class UwaisCafeStudio(Gtk.Window):
    def __init__(self):
        super().__init__(title="UWAIS INternet CAfe - Passport & Aadhaar Studio")
        self.set_default_size(1140, 780)
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
        self.current_png_path = None

        self.build_ui()

        # Connect size-allocate to make preview fluid and auto-scaling
        self.preview_scroll.connect("size-allocate", self.on_preview_resize)

    def build_ui(self):
        # Top-level vertical container
        root_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        root_vbox.set_border_width(18)
        self.add(root_vbox)

        # 🌟 Header Bar with Glowing Brand Badge
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        
        title_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        lbl_title = Gtk.Label()
        lbl_title.set_markup("<span weight='heavy' size='xx-large' foreground='#38bdf8'>⚡ UWAIS INternet CAfe</span>")
        lbl_title.set_xalign(0)
        
        lbl_credit = Gtk.Label()
        lbl_credit.set_markup("<span weight='bold' size='medium' foreground='#c084fc'>build by UWAIS GHosi</span> • <span style='italic' foreground='#94a3b8'>Passport Photos &amp; Aadhaar Print Suite</span>")
        lbl_credit.set_xalign(0)

        title_vbox.pack_start(lbl_title, False, False, 0)
        title_vbox.pack_start(lbl_credit, False, False, 0)
        header_box.pack_start(title_vbox, True, True, 0)

        # Right header badges
        badge_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lbl_b1 = Gtk.Label()
        lbl_b1.set_markup("<span weight='bold' foreground='#38bdf8' background='#0f172a'> [PRO STUDIO] </span>")
        lbl_b2 = Gtk.Label()
        lbl_b2.set_markup("<span weight='bold' foreground='#34d399' background='#0f172a'> [100% TRUE SCALE] </span>")
        badge_box.pack_start(lbl_b1, False, False, 0)
        badge_box.pack_start(lbl_b2, False, False, 0)
        header_box.pack_start(badge_box, False, False, 0)

        root_vbox.pack_start(header_box, False, False, 0)

        # Main Dynamic Resizing Paned (Left Controls | Right HD Live Preview)
        self.main_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_paned.set_position(440)
        root_vbox.pack_start(self.main_paned, True, True, 0)

        # === LEFT PANEL: CONTROLS IN SCROLLED WINDOW ===
        left_scroll = Gtk.ScrolledWindow()
        left_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        left_scroll.set_size_request(420, -1)
        self.main_paned.pack1(left_scroll, resize=False, shrink=False)

        left_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        left_content.set_margin_end(12)
        left_scroll.add(left_content)

        # Notebook Tabs
        self.notebook = Gtk.Notebook()
        left_content.pack_start(self.notebook, False, False, 0)

        # ---------------- TAB 1: Passport Photos ----------------
        tab_pass = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        tab_pass.get_style_context().add_class('card-panel')

        lbl_p1 = Gtk.Label(label="1. Customer Photo Source", xalign=0)
        lbl_p1.get_style_context().add_class('section-label')
        tab_pass.pack_start(lbl_p1, False, False, 0)

        btn_pass = Gtk.FileChooserButton(title="Select Customer Photo", action=Gtk.FileChooserAction.OPEN)
        btn_pass.connect("file-set", self.on_passport_file_set)
        tab_pass.pack_start(btn_pass, False, False, 0)

        lbl_p2 = Gtk.Label(label="2. Quantity & Space-Saver Layout", xalign=0)
        lbl_p2.get_style_context().add_class('section-label')
        tab_pass.pack_start(lbl_p2, False, False, 0)

        self.combo_qty = Gtk.ComboBoxText()
        self.combo_qty.append("6", "6 Photos (1 Single Row - 1.5mm Gap & Cut Guide)")
        self.combo_qty.append("8", "8 Photos (2 Rows of 4)")
        self.combo_qty.append("10", "10 Photos (2 Rows of 5)")
        self.combo_qty.append("12", "12 Photos (2 Rows of 6)")
        self.combo_qty.append("30", "30 Photos (Full A4 Page)")
        self.combo_qty.set_active(0)
        tab_pass.pack_start(self.combo_qty, False, False, 0)

        lbl_p3 = Gtk.Label(label="3. Live Photo Tuning", xalign=0)
        lbl_p3.get_style_context().add_class('section-label')
        tab_pass.pack_start(lbl_p3, False, False, 0)

        box_tune = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        
        # Brightness Slider
        b_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        b_box.pack_start(Gtk.Label(label="Brightness:"), False, False, 0)
        self.adj_b = Gtk.Adjustment(value=1.0, lower=0.6, upper=1.5, step_increment=0.05)
        scale_b = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.adj_b)
        scale_b.set_digits(2)
        b_box.pack_start(scale_b, True, True, 0)
        box_tune.pack_start(b_box, False, False, 0)

        # Contrast Slider
        c_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        c_box.pack_start(Gtk.Label(label="Contrast:"), False, False, 0)
        self.adj_c = Gtk.Adjustment(value=1.0, lower=0.6, upper=1.5, step_increment=0.05)
        scale_c = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.adj_c)
        scale_c.set_digits(2)
        c_box.pack_start(scale_c, True, True, 0)
        box_tune.pack_start(c_box, False, False, 0)

        tab_pass.pack_start(box_tune, False, False, 0)

        self.btn_gen_pass = Gtk.Button(label="⚡ Generate Passport Sheet")
        self.btn_gen_pass.get_style_context().add_class('btn-primary')
        self.btn_gen_pass.connect("clicked", self.on_gen_passport)
        tab_pass.pack_start(self.btn_gen_pass, False, False, 4)

        self.notebook.append_page(tab_pass, Gtk.Label(label="📷 Passport Photos"))

        # ---------------- TAB 2: Aadhaar Card ----------------
        tab_aadh = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        tab_aadh.get_style_context().add_class('card-panel')

        lbl_a1 = Gtk.Label(label="1. e-Aadhaar PDF Source", xalign=0)
        lbl_a1.get_style_context().add_class('section-label')
        tab_aadh.pack_start(lbl_a1, False, False, 0)

        btn_aadh = Gtk.FileChooserButton(title="Select e-Aadhaar PDF", action=Gtk.FileChooserAction.OPEN)
        btn_aadh.connect("file-set", self.on_aadhaar_file_set)
        tab_aadh.pack_start(btn_aadh, False, False, 0)

        lbl_a2 = Gtk.Label(label="2. PDF Password (Visible)", xalign=0)
        lbl_a2.get_style_context().add_class('section-label')
        tab_aadh.pack_start(lbl_a2, False, False, 0)

        self.entry_pw = Gtk.Entry()
        self.entry_pw.set_visibility(True)
        self.entry_pw.set_placeholder_text("e.g. MOHD1998 (Enter password directly)")
        tab_aadh.pack_start(self.entry_pw, False, False, 0)

        lbl_a3 = Gtk.Label(label="3. Aadhaar Photo & Text Tuning", xalign=0)
        lbl_a3.get_style_context().add_class('section-label')
        tab_aadh.pack_start(lbl_a3, False, False, 0)

        box_tune_a = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        
        ba_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        ba_box.pack_start(Gtk.Label(label="Brightness:"), False, False, 0)
        self.adj_ba = Gtk.Adjustment(value=1.0, lower=0.6, upper=1.5, step_increment=0.05)
        scale_ba = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.adj_ba)
        scale_ba.set_digits(2)
        ba_box.pack_start(scale_ba, True, True, 0)
        box_tune_a.pack_start(ba_box, False, False, 0)

        ca_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        ca_box.pack_start(Gtk.Label(label="Contrast:"), False, False, 0)
        self.adj_ca = Gtk.Adjustment(value=1.0, lower=0.6, upper=1.5, step_increment=0.05)
        scale_ca = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.adj_ca)
        scale_ca.set_digits(2)
        ca_box.pack_start(scale_ca, True, True, 0)
        box_tune_a.pack_start(ca_box, False, False, 0)

        tab_aadh.pack_start(box_tune_a, False, False, 0)

        lbl_note = Gtk.Label()
        lbl_note.set_markup("<span color='#38bdf8' font='11px'>ℹ️ Calibrated for 65 × 95 mm Pouch (Solid 3.5mm Seal)</span>")
        lbl_note.set_xalign(0)
        tab_aadh.pack_start(lbl_note, False, False, 0)

        self.btn_gen_aadh = Gtk.Button(label="⚡ Extract & Format Aadhaar Card")
        self.btn_gen_aadh.get_style_context().add_class('btn-primary')
        self.btn_gen_aadh.connect("clicked", self.on_gen_aadhaar)
        tab_aadh.pack_start(self.btn_gen_aadh, False, False, 4)

        self.notebook.append_page(tab_aadh, Gtk.Label(label="🪪 Aadhaar Card (65 × 95mm)"))

        # ---------------- PRINTER CONTROLS PANEL ----------------
        print_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        print_box.get_style_context().add_class('card-panel')

        lbl_pr_title = Gtk.Label()
        lbl_pr_title.set_markup("<span weight='bold' size='large' foreground='#34d399'>🖨️ Universal Printer Engine</span>")
        lbl_pr_title.set_xalign(0)
        print_box.pack_start(lbl_pr_title, False, False, 0)

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
        self.combo_color.append("Mono", "B&W (Mono)")
        self.combo_color.set_active(0)
        p_row1.pack_start(self.combo_color, True, True, 0)
        print_box.pack_start(p_row1, False, False, 0)

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

        self.btn_print = Gtk.Button(label="🖨️ Direct Fast Print (100% True Scale)")
        self.btn_print.get_style_context().add_class('btn-print')
        self.btn_print.set_sensitive(False)
        self.btn_print.connect("clicked", self.on_print_clicked)
        print_box.pack_start(self.btn_print, False, False, 4)

        left_content.pack_start(print_box, False, False, 0)

        # === RIGHT PANEL: FLUID LIVE PREVIEW ===
        right_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        right_panel.set_margin_start(10)
        self.main_paned.pack2(right_panel, resize=True, shrink=True)

        prev_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        lbl_prev_title = Gtk.Label()
        lbl_prev_title.set_markup("<span weight='bold' font='15px'>📄 A4 Sheet Live Canvas</span>")
        lbl_prev_title.set_xalign(0)
        prev_header.pack_start(lbl_prev_title, True, True, 0)

        self.lbl_status = Gtk.Label(label="Ready for input")
        self.lbl_status.get_style_context().add_class('status-badge')
        prev_header.pack_start(self.lbl_status, False, False, 0)
        right_panel.pack_start(prev_header, False, False, 0)

        # Scrolled Window with Centered Image
        self.preview_scroll = Gtk.ScrolledWindow()
        self.preview_scroll.get_style_context().add_class('preview-card')
        self.preview_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        right_panel.pack_start(self.preview_scroll, True, True, 0)

        self.preview_align = Gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0, yscale=0)
        self.img_preview = Gtk.Image()
        self.preview_align.add(self.img_preview)
        self.preview_scroll.add(self.preview_align)

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
            self.current_png_path = out_png
            GLib.idle_add(self._update_preview, out_png, "✓ Passport Sheet Ready (6 in 1 Row)!")
        except Exception as e:
            GLib.idle_add(self.lbl_status.set_text, f"❌ Error: {str(e)}")

    def on_gen_aadhaar(self, widget):
        if not self.aadhaar_file:
            self.lbl_status.set_text("❌ Please select an Aadhaar PDF first!")
            return
        pw = self.entry_pw.get_text()
        ba = self.adj_ba.get_value()
        ca = self.adj_ca.get_value()
        self.lbl_status.set_text("⏳ Extracting 65 × 95 mm Pouch Aadhaar Card...")

        threading.Thread(target=self._process_aadh_thread, args=(pw, ba, ca)).start()

    def _process_aadh_thread(self, pw, ba, ca):
        out_png = "/tmp/craft_gui_aadhaar.png"
        out_pdf = "/tmp/craft_gui_aadhaar.pdf"
        try:
            res = process_aadhaar_pdf(self.aadhaar_file, out_png, out_pdf, password=pw, brightness=ba, contrast=ca)
            if res.get("status") == "error":
                GLib.idle_add(self.lbl_status.set_text, f"❌ {res.get('message')}")
                return
            self.current_result = res
            self.current_png_path = out_png
            GLib.idle_add(self._update_preview, out_png, "✓ Pouch-Sized Aadhaar Sheet Ready!")
        except Exception as e:
            GLib.idle_add(self.lbl_status.set_text, f"❌ Error: {str(e)}")

    def _update_preview(self, png_path, status_text):
        try:
            self.current_png_path = png_path
            self._render_scaled_pixbuf()
            self.btn_print.set_sensitive(True)
            self.lbl_status.set_text(status_text)
        except Exception as e:
            self.lbl_status.set_text(f"Error loading preview: {e}")

    def on_preview_resize(self, widget, allocation):
        # Debounced or direct resize for fluid responsiveness
        if self.current_png_path and os.path.exists(self.current_png_path):
            self._render_scaled_pixbuf()

    def _render_scaled_pixbuf(self):
        if not self.current_png_path:
            return
        alloc = self.preview_scroll.get_allocation()
        target_w = max(alloc.width - 40, 300)
        target_h = max(alloc.height - 40, 400)

        # Standard A4 ratio is ~1:1.414
        ratio = 2480 / 3508
        if (target_w / target_h) > ratio:
            scaled_h = target_h
            scaled_w = int(scaled_h * ratio)
        else:
            scaled_w = target_w
            scaled_h = int(scaled_w / ratio)

        scaled_w = max(scaled_w, 200)
        scaled_h = max(scaled_h, 280)

        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(self.current_png_path, scaled_w, scaled_h, True)
            self.img_preview.set_from_pixbuf(pixbuf)
        except Exception:
            pass

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
    app = UwaisCafeStudio()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
