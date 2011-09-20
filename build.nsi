!define VERSION "0.9.0"
!system 'C:\Python27\python.exe pyinstaller-1.5.1\pyinstaller.py --onefile --windowed --upx --icon images/boomtools.ico context'

; !include "MUI2.nsh"
Name "Context ${VERSION}"
Outfile context-installer-${VERSION}.exe
Icon images\boomtools.ico

InstallDir $PROGRAMFILES32\Context
InstallDirRegKey HKCU "Software\Context" ""

Page license
Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

XPStyle on
SetCompressor /SOLID lzma

# RequestExecutionLevel user
# TargetMinimalOS 5.0

section
	setOutPath $INSTDIR\api
	file "api\"
	setOutPath $INSTDIR\images
	file "images\"
	setOutPath $INSTDIR
	file "dist\context.exe"

	createShortCut "$SMPROGRAMS\Context.lnk" "$INSTDIR\context.exe"
	WriteRegStr HKCU "Software\Context" "" $INSTDIR
	writeUninstaller $INSTDIR\uninstaller.exe
sectionEnd

section "Uninstall"
	delete $INSTDIR\uninstaller.exe
	delete "$SMPROGRAMS\Context.lnk"

	delete $INSTDIR\context.exe
	rmdir /r $INSTDIR\images
	rmdir /r $INSTDIR\api

	rmdir $INSTDIR
sectionEnd
