!include "file_assoc.nsh"
!include "ctx_ver.nsh"

; !include "MUI2.nsh"
Name "Context ${VERSION}"
Outfile context-${VERSION}-i686.exe
Icon images\tools-icon.ico
LicenseData docs\LICENSE.txt

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
	setOutPath $INSTDIR\images
	file "images\"
	setOutPath $INSTDIR\docs
	file "docs\"
	setOutPath $INSTDIR
	file "dist\context.exe"

	${registerExtension} "$INSTDIR\context.exe" ".ctxt" "Context Text"
	${registerExtension} "$INSTDIR\context.exe" ".cbin" "Context Binary"

	createShortCut "$SMPROGRAMS\Context.lnk" "$INSTDIR\context.exe"
	WriteRegStr HKCU "Software\Context" "" $INSTDIR
	writeUninstaller $INSTDIR\uninstaller.exe
sectionEnd

section "Uninstall"
	delete $INSTDIR\uninstaller.exe
	delete "$SMPROGRAMS\Context.lnk"

	${unregisterExtension} ".cbin" "Context Binary"
	${unregisterExtension} ".ctxt" "Context Text"

	delete $INSTDIR\context.exe
	rmdir /r $INSTDIR\docs
	rmdir /r $INSTDIR\images

	rmdir $INSTDIR
sectionEnd
