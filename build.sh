#!/bin/bash

PATH=$PATH:/c/Python27/:/opt/local/bin/
VER=`git describe`
ARCH=`uname -m`

if [ "`uname -s`" = "Darwin" ] ; then
	export VERSIONER_PYTHON_PREFER_32_BIT=yes
	PYTHON="arch -i386 python2.7"
	ICON="--icon images/context-icon.icns"
else
	PYTHON=python
	ICON="--icon images/context-icon.ico"
fi

echo "VERSION='$VER'" > ctx_ver.py
echo "!define VERSION '${VER}'" > ctx_ver.nsh

function svg2icons() {
	rsvg -w 128 -h 128 images/$1.svg images/$1.png
	convert -background none images/$1.png \
			\( -clone 0 -resize 64x64 \) \
			\( -clone 0 -resize 48x48 \) \
			\( -clone 0 -resize 32x32 \) \
			\( -clone 0 -resize 16x16 \) \
			-delete 0 images/$1.ico
	convert -background none images/$1.png \
			\( -clone 0 -resize 128x128 \) \
			\( -clone 0 -resize 64x64 \) \
			\( -clone 0 -resize 48x48 \) \
			\( -clone 0 -resize 32x32 \) \
			\( -clone 0 -resize 16x16 \) \
			-delete 0 images/$1.icns
}

svg2icons tools-icon
svg2icons context-icon

$PYTHON ../pyinstaller-1.5.1/pyinstaller.py --tk --onefile --windowed --upx $ICON context

if [ "`uname -s`" = "Linux" ] || [ "`uname -s`" = "Darwin" ] ; then
	rm -rf context-$VER
	mkdir context-$VER
	cp -rv api context-$VER/
	cp -rv images context-$VER/
	cp -rv docs context-$VER/
	cp dist/* context-$VER/
	if [ "`uname -s`" = "Linux" ] ; then
		tar cvzf context-$VER-$ARCH.tgz --exclude "*.pyc" context-$VER
	fi
	if [ "`uname -s`" = "Darwin" ] ; then
		hdiutil create context-$VER-$ARCH.dmg -srcfolder ./context-$VER/ -ov
	fi
fi
