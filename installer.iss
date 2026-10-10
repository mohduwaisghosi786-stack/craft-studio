; Inno Setup Script for UWAIS INternet CAfe Studio
; build by UWAIS GHosi

#define MyAppName "UWAIS INternet CAfe Studio"
#define MyAppVersion "1.4.5"
#define MyAppPublisher "UWAIS GHosi"
#define MyAppExeName "UWAIS-Internet-Cafe-Studio.exe"

[Setup]
AppId={{C8E9D01F-43B2-4EA8-9712-42CD899E5578}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\UwaisCafeStudio
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputBaseFilename=UWAIS-Internet-Cafe-Studio-x64-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\UWAIS-Internet-Cafe-Studio-x64-Portable.exe"; DestDir: "{app}"; DestName: "{#MyAppExeName}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
