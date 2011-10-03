#!/bin/bash

PATH=$PATH:/c/Python27/
VER=`git describe`
ARCH=`uname -m`

echo "VERSION='$VER'" > ctx_ver.py
echo "!define VERSION '${VER}'" > ctx_ver.nsh

../pyinstaller-1.5.1/pyinstaller.py --onefile --windowed --upx --icon images/boomtools.ico context

if [ "`uname -s`" = "Linux" ] ; then
	rm -rf context-$VER
	mkdir context-$VER
	cp -rv api context-$VER/
	cp -rv images context-$VER/
	cp -rv docs context-$VER/
	cp dist/* context-$VER/
	tar cvzf context-$VER-$ARCH.tgz --exclude "*.pyc" context-$VER
fi