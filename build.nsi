!include "file_assoc.nsh"
!include "version.nsh"

; !include "MUI2.nsh"
Name "Context ${VERSION}"
Outfile context-${VERSION}-i686.exe
Icon images\tools-icon.ico
LicenseData LICENSE.txt

InstallDir "$PROGRAMFILES32\Context"
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
	file "dist\context-viewer.exe"
	file "dist\context-compiler.exe"

	${registerExtension} "$INSTDIR\context-viewer.exe" ".ctxt" "Context Text"
	${registerExtension} "$INSTDIR\context-viewer.exe" ".cbin" "Context Binary"

	createShortCut "$SMPROGRAMS\Context.lnk" "$INSTDIR\context-viewer.exe"
	WriteRegStr HKCU "Software\Context" "" $INSTDIR
	writeUninstaller $INSTDIR\uninstaller.exe
sectionEnd

section "Uninstall"
	delete $INSTDIR\uninstaller.exe
	delete "$SMPROGRAMS\Context.lnk"

	${unregisterExtension} ".cbin" "Context Binary"
	${unregisterExtension} ".ctxt" "Context Text"

	delete $INSTDIR\context-compiler.exe
	delete $INSTDIR\context-viewer.exe
	rmdir /r $INSTDIR
sectionEnd
