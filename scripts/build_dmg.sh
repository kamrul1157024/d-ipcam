#!/bin/bash
# Build D-IPCam.dmg for macOS distribution

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/build"
DIST_DIR="$PROJECT_ROOT/dist"
APP_NAME="D-IPCam"
DMG_NAME="$APP_NAME.dmg"
VOLUME_NAME="$APP_NAME Installer"

cd "$PROJECT_ROOT"

echo "=== Building $APP_NAME ==="
echo ""

# Clean previous builds
echo "1. Cleaning previous builds..."
rm -rf "$BUILD_DIR" "$DIST_DIR"

# Build with PyInstaller
echo "2. Building application with PyInstaller..."
uv run pyinstaller d-ipcam.spec --noconfirm

# Check if app was created
if [ ! -d "$DIST_DIR/$APP_NAME.app" ]; then
    echo "Error: $APP_NAME.app was not created"
    exit 1
fi

echo "3. Application built successfully at $DIST_DIR/$APP_NAME.app"

# Create DMG
echo "4. Creating DMG..."

# Remove existing DMG
rm -f "$DIST_DIR/$DMG_NAME"

# Create a temporary directory for DMG contents
DMG_TEMP="$BUILD_DIR/dmg_temp"
rm -rf "$DMG_TEMP"
mkdir -p "$DMG_TEMP"

# Copy app to temp directory
cp -R "$DIST_DIR/$APP_NAME.app" "$DMG_TEMP/"

# Create symbolic link to Applications folder
ln -s /Applications "$DMG_TEMP/Applications"

# Create the DMG
hdiutil create -volname "$VOLUME_NAME" \
    -srcfolder "$DMG_TEMP" \
    -ov -format UDZO \
    "$DIST_DIR/$DMG_NAME"

# Clean up
rm -rf "$DMG_TEMP"

echo ""
echo "=== Build Complete ==="
echo "DMG created at: $DIST_DIR/$DMG_NAME"
echo ""

# Show DMG size
ls -lh "$DIST_DIR/$DMG_NAME"
