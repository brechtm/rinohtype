#!/bin/sh

# Windows ico
convert rinoh_icon.png -define icon:auto-resize=128,64,48,32,16 rinoh.ico

# macOS icns
mkdir rinoh.iconset
convert rinoh_icon.png -resize 1024x1024 rinoh.iconset/icon_512x512@2x.png
convert rinoh_icon.png -resize 512x512 rinoh.iconset/icon_512x512.png
cp rinoh.iconset/icon_512x512.png rinoh.iconset/icon_256x256@2x.png
convert rinoh_icon.png -resize 256x256 rinoh.iconset/icon_256x256.png
cp rinoh.iconset/icon_256x256.png rinoh.iconset/icon_128x128@2x.png
convert rinoh_icon.png -resize 128x128 rinoh.iconset/icon_128x128.png
cp rinoh.iconset/icon_128x128.png rinoh.iconset/icon_64x64@2x.png
convert rinoh_icon.png -resize 64x64 rinoh.iconset/icon_64x64.png
cp rinoh.iconset/icon_64x64.png rinoh.iconset/icon_32x32@2x.png
convert rinoh_icon.png -resize 32x32 rinoh.iconset/icon_32x32.png
cp rinoh.iconset/icon_32x32.png rinoh.iconset/icon_16x16@2x.png
convert rinoh_icon.png -resize 16x16 rinoh.iconset/icon_16x16.png
iconutil --convert icns rinoh.iconset
rm -rf rinoh.iconset
