#!/bin/sh
# Create a folder (named dmg) to prepare our DMG in (if it doesn't already exist).
mkdir -p dist/dmg
# Empty the dmg folder.
rm -r dist/dmg/*
# Copy the app bundle to the dmg folder.
cp -r "dist/ZingMPre.app" dist/dmg
# If the DMG already exists, delete it.
test -f "dist/ZingMPre.dmg" && rm "dist/ZingMPre.dmg"
create-dmg \
  --volname "ZingMPre" \
  --volicon "assets/logo600.icns" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --icon "ZingMPre.app" 175 120 \
  --hide-extension "ZingMPre.app" \
  --app-drop-link 425 120 \
  "dist/ZingMPre.dmg" \
  "dist/dmg/"