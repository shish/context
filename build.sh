#!/bin/bash

export PATH=$PATH:/c/Python27/:/c/msysgit/bin/:/c/msysgit/libexec/git-core/:/c/local/:/c/Program\ Files\ \(x86\)/NSIS/
export PATH=$PATH:/opt/local/bin/
export VERSION=`git describe`
export ARCH=`uname -m`
export OS=`uname -s`

if [ "$OS" = "Darwin" ] ; then
	export VERSIONER_PYTHON_PREFER_32_BIT=yes
	PYTHON="arch -i386 python2.7"
	ICON="--icon images/context-icon.icns"
elif [ "$OS" = "MINGW32_NT-6.1" ] ; then
	PYTHON=python
	ICON="--icon images/context-icon.ico"
else
	PYTHON=python
	ICON=""
fi

function svg2icon() {
	rsvg-convert -a -w 128 -h 128 images/$1.svg -o images/$1.png
	if [ "$OS" = "MINGW32_NT-6.1" ] ; then
		convert -background none images/$1.png \
			\( -clone 0 -resize 64x64 \) \
			\( -clone 0 -resize 48x48 \) \
			\( -clone 0 -resize 32x32 \) \
			\( -clone 0 -resize 16x16 \) \
			-delete 0 images/$1.ico
	fi
	if [ "$OS" = "Darwin" ] ; then
		makeicns -512 images/$1.png -128 images/$1.png -64 images/$1.png
	fi
	# for linux, keep the .png
}

function build() {
	VER=$1
	echo "VERSION='$VER'" > context/viewer/ctx_ver.py
	echo "!define VERSION '${VER}'" > ctx_ver.nsh
	
	if [ ! -f ../pyinstaller-2.0/pyinstaller.py ] ; then
		git clone https://github.com/pyinstaller/pyinstaller.git ../pyinstaller-2.0
	fi
	$PYTHON ../pyinstaller-2.0/pyinstaller.py --onefile --log-level WARN --windowed $ICON --name context-viewer context/viewer/main.py
	$PYTHON ../pyinstaller-2.0/pyinstaller.py --onefile --log-level WARN --console $ICON --name context-compiler context/compiler/main.py

	if [ "$OS" = "Linux" ] ; then
		rm -rf context-$VER
		mkdir context-$VER
		cp -rv docs/* context-$VER/
		cp dist/* context-$VER/
		cp -rv images context-$VER/
		tar cvzf context-$VER-$ARCH.tgz --exclude "*.pyc" context-$VER
	fi
	if [ "$OS" = "Darwin" ] ; then
		rm -rf context-$VER
		mkdir context-$VER
		cp -rv docs/* context-$VER/
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
	if [ "$OS" = "MINGW32_NT-6.1" ] ; then
		makensis build.nsi
	fi
}

echo "Building static files"
rsvg-convert -a -w 256 images/context-name.svg -o images/context-name.png >> build.log
convert -background white -bordercolor white -border 15x5 images/context-name.png images/context-name.gif >> build.log
svg2icon tools-icon >> build.log
svg2icon context-icon >> build.log
echo "Built static files"

echo "Building demo"
build $VERSION-demo >> build.log
echo "Built demo"

echo "Building main"
build $VERSION
echo "Built main"
