# Instalation script for photoplace on Windows platforms
# Copyright 2011 Jose Riguera Lopez <jriguera@gmail.com>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

; HM NIS Edit Wizard helper defines
!define PRODUCT_NAME "PhotoPlace"
!define PRODUCT_EXEC "photoplace.exe"
!define PRODUCT_VERSION "0.5.0"
!define PRODUCT_PUBLISHER "Jose Riguera"
!define PRODUCT_AUTHOR "Jose Riguera"
!define PRODUCT_WEB_SITE "http://code.google.com/p/photoplace/"
!define PRODUCT_DONATIONS "https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=N6XRW9DLPFSRN"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\photoplace.exe"
!define PRODUCT_CFG_REGKEY "Software\PhotoPlace"
!define PRODUCT_CFG_FILE "share\photoplace\conf\photoplace.cfg"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"
!define PRODUCT_STARTMENU_REGVAL "NSIS:StartMenuDir"
!define MSVC2008 "http://download.microsoft.com/download/1/1/1/1116b75a-9ec3-481a-a3c8-1777b5381140/vcredist_x86.exe"
!define INPUT_DIR "bdist\photoplace-0.5.0"
!define OUTPUT_FILE "bdist\photoplace-0.5.0.exe"

; MUI 1.67 compatible ------
!include "MUI.nsh"

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "logos\photoplace.ico"
;!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; Language Selection Dialog Settings
!define MUI_LANGDLL_ALWAYSSHOW
!define MUI_LANGDLL_REGISTRY_ROOT "${PRODUCT_UNINST_ROOT_KEY}"
!define MUI_LANGDLL_REGISTRY_KEY "${PRODUCT_UNINST_KEY}"
!define MUI_LANGDLL_REGISTRY_VALUENAME "NSIS:Language"
var CURRENT_LANG

; Welcome page
!insertmacro MUI_PAGE_WELCOME
; License page
!insertmacro MUI_PAGE_LICENSE "${INPUT_DIR}\LICENSE.txt"
; Directory page
!insertmacro MUI_PAGE_DIRECTORY
; Start menu page
var ICONS_GROUP
!define MUI_STARTMENUPAGE_NODISABLE
!define MUI_STARTMENUPAGE_DEFAULTFOLDER "PhotoPlace"
!define MUI_STARTMENUPAGE_REGISTRY_ROOT "${PRODUCT_UNINST_ROOT_KEY}"
!define MUI_STARTMENUPAGE_REGISTRY_KEY "${PRODUCT_UNINST_KEY}"
!define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "${PRODUCT_STARTMENU_REGVAL}"
!insertmacro MUI_PAGE_STARTMENU Application $ICONS_GROUP
; Instfiles page
!insertmacro MUI_PAGE_INSTFILES
; Finish page
!define MUI_FINISHPAGE_RUN "$INSTDIR\photoplace.exe"
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.txt"
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_INSTFILES

; Language files
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "Spanish"
; MUI end ------

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "${OUTPUT_FILE}"
InstallDir "$PROGRAMFILES\${PRODUCT_NAME}"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

; Request application privileges for Windows Vista
RequestExecutionLevel admin

;--------------------------------
;Version Information
VIProductVersion "${PRODUCT_VERSION}.0"
VIAddVersionKey "ProductName" "${PRODUCT_NAME}"
VIAddVersionKey "Comments" "It is a multiplatform program developed in python to easily geotag your photos. It is tested on Linux and Windows platforms with python >= 2.6 series. Also, with a track log from a GPS device, it can generate a Google Earth/Maps layer with your photos. Moreover, the program can be easily adapted by editing templates and its functionality can be complemented with addons, for example there is one to generate a music tour that can be used to present your photo collection."
VIAddVersionKey "LegalCopyright" "${PRODUCT_WEB_SITE}"
VIAddVersionKey "FileDescription" "A tool for geotagging your photos and ... much more!"
VIAddVersionKey "FileVersion" "${PRODUCT_VERSION}"


Function .onInit
  StrCpy $CURRENT_LANG "en"
  !insertmacro MUI_LANGDLL_DISPLAY
  ${If} $LANGUAGE == 1034
    StrCpy $CURRENT_LANG "es"
  ${ElseIf} $LANGUAGE == 1036
    StrCpy $CURRENT_LANG "fr"
  ${EndIf}
FunctionEnd

Section "${PRODUCT_NAME}" SEC01
  ; Set output path to the installation directory.
  SetOutPath $INSTDIR
  ; Put files here
  File /r "${INPUT_DIR}\*.*"
  ; Shortcuts
  SetShellVarContext all
  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
  CreateDirectory "$SMPROGRAMS\$ICONS_GROUP"
  CreateShortCut "$SMPROGRAMS\$ICONS_GROUP\${PRODUCT_NAME}.lnk" "$INSTDIR\${PRODUCT_EXEC}"
  CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\${PRODUCT_EXEC}"
  !insertmacro MUI_STARTMENU_WRITE_END
SectionEnd

; -----------------------------------------------------------------------
; MSVC Redistributable - required if the user does not already have it
; Note: if your NSIS generates an error here it means you need to download the latest
; visual studio redist package from microsoft.  Any redist 2008/SP1 or newer will do.
;
; IMPORTANT: Online references for how to detect the presence of the VS2008 redists LIE.
; None of the methods are reliable, because the registry keys placed by the MSI installer
; vary depending on operating system *and* MSI installer version (youch).
;
Section -VC++2008Runtime SEC02
  SetOutPath $INSTDIR
  ; Check if VC++ 2008 runtimes are already installed:
  ReadRegStr $0 HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{FF66E9F6-83E7-3A3E-AF14-8DE9A809A6A4}" "DisplayName"
  ; If VC++ 2008 runtimes are not installed execute in Quiet mode
  StrCmp $0 "Microsoft Visual C++ 2008 Redistributable - x86 9.0.21022" done
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "You don't have the 'Microsoft Visual C++ 2008 Redistributable' library installed and it is necessary to run this program.$\n$\nDo you want to download it now?" IDNO end
  DetailPrint "Downloading Visual C++ 2008 Redistributable Setup..."
  NSISdl::download /TIMEOUT=15000 "${MSVC2008}" "vcredist_x86.exe"
  Pop $R0 ;Get the return value
  StrCmp $R0 "success" install
  MessageBox MB_OK "Could not download Visual Studio 2008 Redist; none of the mirrors appear to be functional."
  Goto end
  install:
    DetailPrint "Running Visual C++ 2008 Redistributable Setup..."
    ExecWait '"$INSTDIR\vcredist_x86.exe /qb'
    DetailPrint "Finished Visual C++ 2008 Redistributable Setup"
    Delete "$INSTDIR\vcredist_x86.exe"
  done:
    DetailPrint "Runtime MSVC++ 2008 OK."
  end:
SectionEnd

Section -AdditionalIcons
  SetOutPath $INSTDIR
  SetShellVarContext all
  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
  WriteIniStr "$INSTDIR\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  WriteIniStr "$SMPROGRAMS\$ICONS_GROUP\Website.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  WriteIniStr "$SMPROGRAMS\$ICONS_GROUP\Donate.url" "InternetShortcut" "URL" "${PRODUCT_DONATIONS}"
  CreateShortCut "$SMPROGRAMS\$ICONS_GROUP\Uninstall.lnk" "$INSTDIR\uninst.exe" "" "" ""
  !insertmacro MUI_STARTMENU_WRITE_END
SectionEnd

Section -Localization
  CopyFiles "$INSTDIR\share\photoplace\templates\$CURRENT_LANG\*.*" "$INSTDIR\share\photoplace\templates"
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\uninst.exe"
  SetShellVarContext all
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\${PRODUCT_EXEC}"
  WriteRegStr HKLM "${PRODUCT_CFG_REGKEY}" "cfgfile" "$INSTDIR\${PRODUCT_CFG_FILE}"
  WriteRegStr HKLM "${PRODUCT_CFG_REGKEY}" "author" "${PRODUCT_AUTHOR}"
  WriteRegStr HKLM "${PRODUCT_CFG_REGKEY}" "version" "${PRODUCT_VERSION}"  
  WriteRegStr HKLM "${PRODUCT_CFG_REGKEY}" "url" "${PRODUCT_WEB_SITE}"    
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\${PRODUCT_EXEC}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
SectionEnd

Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) was uninstalled."
FunctionEnd

Function un.onInit
  !insertmacro MUI_UNGETLANGUAGE
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Are you sure you want to uninstall $(^Name)?" IDYES +2
  Abort
FunctionEnd

Section Uninstall
  !insertmacro MUI_STARTMENU_GETFOLDER "Application" $ICONS_GROUP
  RMDir /r "$INSTDIR" 
  SetShellVarContext all
  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
  RMDir /r "$SMPROGRAMS\$ICONS_GROUP"
  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  SetAutoClose true
SectionEnd
