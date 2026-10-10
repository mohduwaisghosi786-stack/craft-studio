#!/usr/bin/env python3
"""
UWAIS INternet CAfe Studio - Brand New Next-Gen Desktop App
build by UWAIS GHosi
Embedded WebKit2 Modern Engine: 100% Responsive, Glassmorphic Animations & True 1:1 Scale Print.
"""

import sys
import os
import signal
import threading
import socket
import http.client
from pathlib import Path

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, WebKit2, GLib, Gio, Gdk

PORT = 8091
URL = f"http://127.0.0.1:{PORT}"

def is_server_running():
    try:
        conn = http.client.HTTPConnection("127.0.0.1", PORT, timeout=1)
        conn.request("GET", "/")
        res = conn.getresponse()
        return res.status == 200
    except Exception:
        return False

class NextGenStudioWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="UWAIS INternet CAfe Studio - build by UWAIS GHosi")
        self.set_default_size(1200, 820)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon_name("applications-graphics")

        # Top-level Box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_box)

        # Embedded WebKit2 Modern Web View
        self.webview = WebKit2.WebView()
        
        # Web Settings for hardware acceleration and smooth canvas
        settings = self.webview.get_settings()
        settings.set_enable_developer_extras(False)
        settings.set_enable_webgl(True)
        settings.set_enable_smooth_scrolling(True)
        settings.set_enable_javascript(True)

        # Scrolled wrapper
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(self.webview)
        main_box.pack_start(scrolled, True, True, 0)

        # Load Studio URL
        self.webview.load_uri(URL)

def main():
    # If the user service isn't active for any reason, launch background server
    if not is_server_running():
        import subprocess
        subprocess.Popen([sys.executable, "/home/fahad/craft-studio/app.py"])
        # Wait shortly for bind
        import time
        for _ in range(20):
            if is_server_running():
                break
            time.sleep(0.1)

    app = NextGenStudioWindow()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
