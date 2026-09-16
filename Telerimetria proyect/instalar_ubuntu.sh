#!/bin/bash
# instalar_ubuntu.sh
# Compila la app y crea un icono de doble clic en el Escritorio.
# Ejecutar UNA sola vez con:  bash instalar_ubuntu.sh

set -e
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "============================================"
echo "  Preparando entorno..."
echo "============================================"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

pip install --upgrade pip -q
pip install -r requirements.txt -q
pip install pyinstaller -q

echo ""
echo "============================================"
echo "  Compilando la aplicacion (puede tardar)..."
echo "============================================"
python -m PyInstaller --noconfirm --onefile --windowed --name "GameHWMonitor" main.py

EXE_PATH="$DIR/dist/GameHWMonitor"
chmod +x "$EXE_PATH"

# Detectar carpeta de Escritorio (puede llamarse Desktop o Escritorio)
if [ -d "$HOME/Escritorio" ]; then
    DESKTOP_DIR="$HOME/Escritorio"
elif [ -d "$HOME/Desktop" ]; then
    DESKTOP_DIR="$HOME/Desktop"
else
    DESKTOP_DIR="$HOME"
fi

DESKTOP_FILE="$DESKTOP_DIR/GameHWMonitor.desktop"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=GameHW Monitor
Comment=Monitor de rendimiento de hardware para videojuegos
Exec=$EXE_PATH
Icon=utilities-system-monitor
Terminal=false
Categories=Utility;System;
EOF

chmod +x "$DESKTOP_FILE"

# Marcar como confiable si el gestor de archivos lo requiere (GNOME/Nautilus)
if command -v gio &> /dev/null; then
    gio set "$DESKTOP_FILE" "metadata::trusted" true 2>/dev/null || true
fi

echo ""
echo "============================================"
echo "  LISTO!"
echo "  Se creo un icono en: $DESKTOP_FILE"
echo ""
echo "  Si al hacer doble clic te pregunta si confias"
echo "  en el archivo, o si no abre directo, haz clic"
echo "  derecho sobre el icono y elige:"
echo "  'Permitir ejecucion' o 'Ejecutar como programa'."
echo "============================================"
