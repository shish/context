#!/bin/bash

VER=0.9

../pyinstaller-1.5.1/pyinstaller.py --onefile context

rm -rf context-$VER
mkdir context-$VER
cp -rv api context-$VER/
cp -rv images context-$VER/
cp -rv docs context-$VER/
cp dist/* context-$VER/
tar cvzf context-$VER-`uname -i`.tgz --exclude "*.pyc" context-$VER
