#define MyAppName "Footprint Cleaner"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Local Privacy Tools"
#define MyAppExeName "FootprintCleaner.exe"

[Setup]
AppId={{6B70C2C7-9F16-49A2-93C9-BE13D7F14752}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Footprint Cleaner
DefaultGroupName={#MyAppName}
OutputDir=installer-output
OutputBaseFilename=FootprintCleaner-Setup-0.1.0
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
WizardStyle=modern

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
