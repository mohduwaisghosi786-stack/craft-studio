#!/usr/bin/env bash
# ==============================================================================
# UWAIS INternet CAfe Studio - 1-Line Universal Linux Installer
# build by UWAIS GHosi
# Supported Distros: Arch Linux, Ubuntu, Debian, Linux Mint, Fedora, Pop!_OS
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/mohduwaisghosi786-stack/craft-studio/main/install.sh | bash
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "=========================================================="
echo "   ⚡ UWAIS INternet CAfe Studio - Universal Installer    "
echo "              build by UWAIS GHosi                        "
echo "=========================================================="
echo -e "${NC}"

INSTALL_DIR="$HOME/.local/share/uwais-cafe-studio"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"

mkdir -p "$BIN_DIR" "$DESKTOP_DIR"

# 1. Detect Package Manager and Install Dependencies
echo -e "${YELLOW}>> [1/5] Detecting Linux Distribution & Dependencies...${NC}"

if command -v pacman &>/dev/null; then
    echo -e "${GREEN}Detected Arch Linux / EndeavourOS / Manjaro${NC}"
    sudo pacman -S --needed --noconfirm python python-pillow poppler qpdf cups gtk3 python-gobject
elif command -v apt-get &>/dev/null; then
    echo -e "${GREEN}Detected Debian / Ubuntu / Mint / Pop!_OS${NC}"
    sudo apt-get update -qq
    sudo apt-get install -y -qq python3 python3-pil poppler-utils qpdf cups libcups2-dev python3-gi gir1.2-gtk-3.0 git
elif command -v dnf &>/dev/null; then
    echo -e "${GREEN}Detected Fedora / RHEL${NC}"
    sudo dnf install -y python3 python3-pillow poppler-utils qpdf cups-client python3-gobject gtk3 git
else
    echo -e "${RED}Warning: Unknown package manager. Please ensure Python3, Pillow, Poppler, and QPDF are installed.${NC}"
fi

# 2. Clone or Update Application Repository
echo -e "${YELLOW}>> [2/5] Downloading latest software from GitHub...${NC}"

if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Updating existing installation in $INSTALL_DIR..."
    git -C "$INSTALL_DIR" pull origin main
else
    rm -rf "$INSTALL_DIR"
    git clone https://github.com/mohduwaisghosi786-stack/craft-studio.git "$INSTALL_DIR"
fi

chmod +x "$INSTALL_DIR/gui.py"
chmod +x "$INSTALL_DIR/app.py"

# 3. Create CLI Command Symlinks
echo -e "${YELLOW}>> [3/5] Setting up Terminal command 'uwais-cafe'...${NC}"

ln -sf "$INSTALL_DIR/gui.py" "$BIN_DIR/uwais-cafe"

# 4. Create Desktop Application Shortcut
echo -e "${YELLOW}>> [4/5] Installing Desktop App Menu entry...${NC}"

cat <<EOF > "$DESKTOP_DIR/uwais-cafe.desktop"
[Desktop Entry]
Type=Application
Name=UWAIS INternet CAfe
GenericName=Passport & Aadhaar Print Suite
Comment=build by UWAIS GHosi - Passport photos & 65x95mm Pouch Aadhaar Cards
Exec=$INSTALL_DIR/gui.py
Icon=applications-graphics
Terminal=false
StartupNotify=true
Categories=Graphics;Photography;Office;
Keywords=owais;uwais;passport;aadhaar;cafe;photo;print;brother;
EOF

chmod +x "$DESKTOP_DIR/uwais-cafe.desktop"

# 5. Enable Web Server Service (Optional User Service)
echo -e "${YELLOW}>> [5/5] Configuring Web UI Background Service (Port 8091)...${NC}"
SERVICE_DIR="$HOME/.config/systemd/user"
mkdir -p "$SERVICE_DIR"

cat <<EOF > "$SERVICE_DIR/uwais-cafe.service"
[Unit]
Description=UWAIS INternet CAfe Web GUI Server
After=network.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/app.py
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now uwais-cafe.service || true

echo -e "${GREEN}"
echo "=========================================================="
echo "   ✅ Installation Completed Successfully!                "
echo "=========================================================="
echo -e "${NC}"
echo "1. Run from Desktop Menu: Search for 'UWAIS INternet CAfe'"
echo "2. Run from Terminal:     uwais-cafe"
echo "3. Open in Web Browser:   http://localhost:8091"
echo ""
