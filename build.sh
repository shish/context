#!/bin/bash

PATH=$PATH:/c/Python27/:/opt/local/bin/
VERSION=`git describe`
ARCH=`uname -m`

if [ "`uname -s`" = "Darwin" ] ; then
	export VERSIONER_PYTHON_PREFER_32_BIT=yes
	PYTHON="arch -i386 python2.7"
	ICON="--icon images/context-icon.icns"
else
	PYTHON=python
	ICON="--icon images/context-icon.ico"
fi

function svg2icons() {
	rsvg -w 128 -h 128 images/$1.svg images/$1.png
	convert -background none images/$1.png \
			\( -clone 0 -resize 64x64 \) \
			\( -clone 0 -resize 48x48 \) \
			\( -clone 0 -resize 32x32 \) \
			\( -clone 0 -resize 16x16 \) \
			-delete 0 images/$1.ico
	if [ "`uname -s`" = "Darwin" ] ; then
		makeicns -512 images/$1.png -128 images/$1.png -64 images/$1.png
	fi
}

function build() {
	VER=$1
	echo "VERSION='$VER'" > ctx_ver.py
	echo "!define VERSION '${VER}'" > ctx_ver.nsh

	$PYTHON ../pyinstaller-1.5.1/pyinstaller.py --tk --onefile --windowed --upx $ICON context

	if [ "`uname -s`" = "Linux" ] ; then
		rm -rf context-$VER
		mkdir context-$VER
		cp -rv api context-$VER/
		cp -rv docs context-$VER/
		cp dist/* context-$VER/
		cp -rv images context-$VER/
		tar cvzf context-$VER-$ARCH.tgz --exclude "*.pyc" context-$VER
	fi
	if [ "`uname -s`" = "Darwin" ] ; then
		rm -rf context-$VER
		mkdir context-$VER
		cp -rv api context-$VER/
		cp -rv docs context-$VER/
		cp -rv dist/context.app context-$VER/
		CONTENTS=context-$VER/context.app/Contents/
		cp images/context-icon.icns $CONTENTS/Resources/App.icns
		cp -rv images $CONTENTS/MacOS/
		mv $CONTENTS/MacOS/context $CONTENTS/MacOS/context.bin
		echo '#!/bin/sh' > $CONTENTS/MacOS/context
		echo 'cd "`dirname \"$0\"`"' >> $CONTENTS/MacOS/context
		echo './context.bin' >> $CONTENTS/MacOS/context
		chmod +x $CONTENTS/MacOS/context
		sed -i "" "s#<string>App.icns</string>#<string>App</string>#" $CONTENTS/Info.plist
		sed -i "" "s#<string>1</string>#<string>0</string>#" $CONTENTS/Info.plist
		mv context-$VER/context.app context-$VER/Context\ Viewer.app
		hdiutil create context-$VER-$ARCH.dmg -srcfolder ./context-$VER/ -ov
		# auto-extract to desktop
		#hdiutil internet-enable -yes context-$VER-$ARCH.dmg
	fi
}

rsvg -w 256 images/context-name.svg images/context-name.png
convert -background white -bordercolor white -border 15x5 images/context-name.png images/context-name.gif
svg2icons tools-icon
svg2icons context-icon
build $VERSION
build $VERSION-demo
