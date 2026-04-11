#!/usr/bin/env bash
# Strict-ish mode (portable across older shells).
# NOTE: If you run this script via `sh ...`, the shebang is ignored; always use `bash ./build_mac.sh`.
set -e
set -u
{ set -o pipefail; } 2>/dev/null || true

# Profesor Abelton — macOS build script (.app + Gumroad ZIP)
# Run on macOS:
#   chmod +x build_mac.sh
#   ./build_mac.sh
#
# Output:
#   dist/ProfesorAbelton.app
#   release/ProfesorAbelton_macOS_v<version>.zip

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

APP_NAME="ProfesorAbelton"
VERSION="${VERSION:-2.0.0}"
VENV_DIR="${VENV_DIR:-.venv-build-mac}"
PY="$VENV_DIR/bin/python"

echo "[i] Root: $ROOT_DIR"

if [[ ! -f "launch_profesor_ableton.py" ]]; then
  echo "[X] Ne mogu naći launch_profesor_ableton.py. Pokreni skriptu iz root foldera projekta."
  exit 1
fi

if [[ ! -d "$VENV_DIR" ]]; then
  echo "[i] Kreiram build venv: $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

echo "[i] Aktiviram venv i instaliram dependencies..."
"$PY" -m pip install --upgrade pip setuptools wheel >/dev/null

# pyaudio je često problematičan na macOS-u (portaudio). Za build nam nije kritičan.
# Instaliraj sve iz requirements.txt osim pyaudio; voice feature može ostati "optional".
TMP_REQ="$(mktemp)"
"$PY" - "$TMP_REQ" <<'PY'
from pathlib import Path
import re, sys

src = Path("requirements.txt").read_text(encoding="utf-8").splitlines()
out = []
for line in src:
    raw = line.strip()
    if not raw or raw.startswith("#"):
        continue
    # remove inline comments (na siguran način)
    raw = re.split(r"\s+#", raw, maxsplit=1)[0].strip()
    if not raw:
        continue
    if raw.lower().startswith("pyaudio"):
        continue
    out.append(raw)
Path(sys.argv[1]).write_text("\n".join(out) + "\n", encoding="utf-8")
PY

"$PY" -m pip install -r "$TMP_REQ"
rm -f "$TMP_REQ"

echo "[i] Building .app (PyInstaller, windowed)..."
rm -rf build dist

"$PY" -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name "$APP_NAME" \
  --add-data "Config:Config" \
  --add-data "RemoteScript:RemoteScript" \
  --add-data "Docs:Docs" \
  --add-data "FAQ.md:." \
  --add-data "USER_MANUAL.md:." \
  --add-data "README.md:." \
  --add-data "LICENSE.txt:." \
  --add-data "README FIRST MAC.txt:." \
  --hidden-import "GUI.profesor_ableton_gui" \
  --hidden-import "GUI.first_launch_wizard" \
  --hidden-import "Server.ai_copilot_server" \
  --hidden-import "Utils.api_key_manager" \
  --hidden-import "Utils.ableton_detector" \
  --hidden-import "Utils.license_manager" \
  launch_profesor_ableton.py

APP_PATH="dist/$APP_NAME.app"
if [[ ! -d "$APP_PATH" ]]; then
  echo "[X] Build gotov, ali .app nije pronađen: $APP_PATH"
  echo "[DEBUG] Sadržaj dist foldera:"
  ls -la dist/
  exit 1
fi

# PyInstaller ponekad preimenjuje __init__.py u _init_.py unutar bundlanih data foldera
# jer ga tretira specijalno kao Python package marker.
# PyInstaller 6+ (Python 3.13+) stavlja data fajlove u Contents/MacOS/_internal/.
# Koristimo process substitution umjesto pipe-a — izbjegavamo subshell + set -e probleme.
echo "[i] Provjera i ispravak __init__.py u bundlanom RemoteScript folderu..."
_found_bad=0
while IFS= read -r -d '' f; do
  target="$(dirname "$f")/__init__.py"
  mv "$f" "$target"
  echo "    Ispravljen: $f → $target"
  _found_bad=1
done < <(find "$APP_PATH" -name "_init_.py" -path "*/RemoteScript/*" -print0 2>/dev/null)

if [[ "$_found_bad" -eq 0 ]]; then
  echo "    [i] Nema _init_.py za preimenovati (PyInstaller već ispravno bundlao)."
fi

# Provjera da __init__.py postoji — bez pipe-a, -quit vraća prvi pogodak
_found_init="$(find "$APP_PATH" -name "__init__.py" -path "*/RemoteScript/*" -print -quit 2>/dev/null)"
if [[ -n "$_found_init" ]]; then
  echo "    [OK] RemoteScript/__init__.py je prisutan u bundlu: $_found_init"
else
  echo "    [WARN] RemoteScript/__init__.py nije pronađen — sadržaj RemoteScript foldera:"
  find "$APP_PATH" -path "*/RemoteScript/*" 2>/dev/null | head -20 || true
  echo "    Provjeri PyInstaller verziju i putanju _internal/ ručno!"
fi

mkdir -p release
ZIP_PATH="release/${APP_NAME}_macOS_v${VERSION}.zip"

echo "[i] Zipping .app za Gumroad..."
rm -f "$ZIP_PATH"

# ditto je najbolji način za zipanje .app bundle-a (čuva resurse kako treba)
ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$ZIP_PATH"

echo ""
echo "[OK] macOS build gotov:"
echo "     $APP_PATH"
echo "     $ZIP_PATH"
echo ""
echo "[i] Napomena:"
echo " - Ako macOS blokira app (Gatekeeper): desni klik → Open → Open."
echo " - Za 'bez upozorenja' treba code signing + notarization (kasnije)."

