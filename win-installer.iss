; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "Novatool"
#define MyAppVersion "1.0"
#define MyAppPublisher "Webos Internals"
#define MyAppURL "http://www.webos-internals.org"
#define MyAppExeName "novatool.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{75D09084-3FB6-46C6-9DEC-15991E11C4B7}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputBaseFilename=NovatoolSetup
Compression=lzma
SolidCompression=yes
OutputDir="dist\windows"

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 0,6.1

[Files]
Source: "build\exe.win32-2.6\novatool.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\exe.win32-2.6\_ctypes.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\exe.win32-2.6\_hashlib.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\exe.win32-2.6\_socket.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\exe.win32-2.6\_ssl.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\exe.win32-2.6\bz2.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\exe.win32-2.6\library.zip"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\exe.win32-2.6\novatool.zip"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\exe.win32-2.6\PySide.QtCore.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\exe.win32-2.6\PySide.QtGui.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\exe.win32-2.6\pywintypes26.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\exe.win32-2.6\python26.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\exe.win32-2.6\pyside-python2.6.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\exe.win32-2.6\QtCore4.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\exe.win32-2.6\QtGui4.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\exe.win32-2.6\select.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\exe.win32-2.6\shiboken-python2.6.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\exe.win32-2.6\twisted.python._initgroups.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\exe.win32-2.6\unicodedata.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\exe.win32-2.6\win32api.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\exe.win32-2.6\win32event.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\exe.win32-2.6\win32file.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\exe.win32-2.6\win32pipe.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\exe.win32-2.6\win32process.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\exe.win32-2.6\win32security.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\exe.win32-2.6\zope.interface._zope_interface_coptimizations.pyd"; DestDir: "{app}"; Flags: ignoreversion
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, "&", "&&")}}"; Flags: nowait postinstall skipifsilent

