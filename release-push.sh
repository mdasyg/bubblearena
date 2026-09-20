#!/bin/bash
#
# release-push.sh
# Created: 2026-09-20
#
# Usage:
#   ./release-push.sh [release_file] [version]
#
# Examples:
#   ./release-push.sh
#   ./release-push.sh Releases/BubbleArena.exe
#   ./release-push.sh Releases/BubbleArena.exe 1.0.0
#

set -e

FILE="$1"
VERSION="$2"

# Auto-detect release file if not supplied
if [ -z "$FILE" ]; then
    if [ -f "Releases/BubbleArena.exe" ]; then
        FILE="Releases/BubbleArena.exe"
    elif [ -f "dist/BubbleArena.exe" ]; then
        FILE="dist/BubbleArena.exe"
    else
        echo "Usage: $0 <release_file> [version]"
        echo "Error: Release file not specified and no default found in Releases/ or dist/."
        exit 1
    fi
fi

[ -f "$FILE" ] || {
    echo "Release file not found: $FILE"
    exit 1
}

# Auto-detect version if not supplied
if [ -z "$VERSION" ]; then
    if [ -f "constants.py" ]; then
        VERSION=$(sed -n 's/^VERSION[[:space:]]*=[[:space:]]*["\x27]\([^"\x27]*\)["\x27].*/\1/p' constants.py | head -n1)
    fi
    if [ -z "$VERSION" ]; then
        VERSION=$(python3 -c "import constants; print(constants.VERSION)" 2>/dev/null || python -c "import constants; print(constants.VERSION)" 2>/dev/null || true)
    fi
fi

[ -n "$VERSION" ] || {
    echo "Could not determine version."
    echo "Specify it explicitly:"
    echo "  $0 $FILE 1.0.0"
    exit 1
}

TAG="v$VERSION"

echo "File:    $FILE"
echo "Version: $VERSION"
echo "Tag:     $TAG"

if ! command -v gh >/dev/null 2>&1; then
    echo "Error: GitHub CLI ('gh') is not installed or not in PATH."
    echo "Install it via: https://cli.github.com/ or your package manager."
    exit 1
fi

git add .
git diff --cached --quiet || git commit -m "Release $TAG"

git push origin main

git tag -f "$TAG"
git push origin "$TAG" --force

if gh release view "$TAG" >/dev/null 2>&1; then
    gh release upload "$TAG" "$FILE" --clobber
else
    gh release create "$TAG" "$FILE" \
        --title "$TAG" \
        --notes "Release $TAG"
fi

echo
echo "Release $TAG published successfully."
