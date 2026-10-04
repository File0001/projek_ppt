; =====================================================================
;  Inno Setup script untuk PDF Multi Slide Pro
;  Dibuat otomatis oleh build.ps1. Jangan ubah ManualAppVersion di sini
;  bila build lewat script (akan ditimpa oleh /DMyAppVersion).
; =====================================================================

#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif

#define MyAppName        "PDF Multi Slide Pro"
#define MyAppPublisher   "PDF Multi Slide Pro"
#define MyAppExeName     "PDFMultiSlidePro.exe"
#define MyAppURL         ""
#define ProjectRoot      SourcePath + "\.."
#define OnedirDist       ProjectRoot + "\dist\PDFMultiSlidePro"

[Setup]
AppId={{8F3A7C41-2B9E-4D6A-9C15-7E4B0A9D1F22}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir={#ProjectRoot}\dist\installer
OutputBaseFilename=PDFMultiSlidePro-Setup-{#MyAppVersion}
SetupIconFile={#SourcePath}\app.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Windows 10 ke atas.
MinVersion=10.0
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "assocpdf"; Description: "Kaitkan dengan file .pdf (buka via aplikasi ini)"; GroupDescription: "Asosiasi file:"; Flags: unchecked

[Files]
; Seluruh isi folder onedir (exe + semua DLL/lib).
Source: "{#OnedirDist}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; README (jika ada) — tidak fatal bila tidak ada.
Source: "{#ProjectRoot}\README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme skipifsourcedoesntexist

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Bersihkan sisa build bila ada di folder install (tidak menyentuh file user).
Type: filesandordirs; Name: "{app}\build"
Type: filesandordirs; Name: "{app}\__pycache__"
