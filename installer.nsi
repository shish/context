!define VERSION "0.9.0"

; !include "MUI2.nsh"
Name "Context ${VERSION}"
Outfile context-installer-${VERSION}.exe

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
	setOutPath $INSTDIR

	file /r "dist\*.*"

	createShortCut "$SMPROGRAMS\Context.lnk" "$INSTDIR\context.exe"
	WriteRegStr HKCU "Software\Context" "" $INSTDIR
	writeUninstaller $INSTDIR\uninstaller.exe
sectionEnd

section "Uninstall"
	delete $INSTDIR\uninstaller.exe
	delete "$SMPROGRAMS\Context.lnk"

	delete $INSTDIR\context.exe
	delete $INSTDIR\tk85.dll
	delete $INSTDIR\tcl85.dll
	rmdir /r $INSTDIR\tcl
	rmdir /r $INSTDIR\images
	rmdir /r $INSTDIR\api
	rmdir $INSTDIR

sectionEnd