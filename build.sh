#!/bin/bash

PATH=$PATH:/c/Python27/
VER=`git describe`
ARCH=`uname -m`

if [ "`uname -s`" = "Darwin" ] ; then
	export VERSIONER_PYTHON_PREFER_32_BIT=yes
	PYTHON="arch -i386 python2.7"
else
	PYTHON=python
fi

echo "VERSION='$VER'" > ctx_ver.py
echo "!define VERSION '${VER}'" > ctx_ver.nsh

$PYTHON ../pyinstaller-1.5.1/pyinstaller.py --tk --onefile --windowed --upx --icon images/boomtools.ico context

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
