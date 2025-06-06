; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "GOST Encryptor"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "LuTi_Flek$$er, iliacym"
#define MyAppURL "https://github.com/LuTiFlekSSer/Encryption_app"
#define MyAppExeName "GOST Encryptor.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{B5D1F72B-8D58-4EAA-8D9F-51E179EEB098}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
; "ArchitecturesAllowed=x64compatible" specifies that Setup cannot run
; on anything but x64 and Windows 11 on Arm.
ArchitecturesAllowed=x64compatible
; "ArchitecturesInstallIn64BitMode=x64compatible" requests that the
; install be done in "64-bit mode" on x64 or Windows 11 on Arm,
; meaning it should use the native 64-bit Program Files directory and
; the 64-bit view of the registry.
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
; Remove the following line to run in administrative install mode (install for all users).
PrivilegesRequired=admin
OutputBaseFilename=GOST Encryptor {#MyAppVersion} Setup
SetupIconFile=.\res\favicon.ico
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: ".\build\main.dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: ".\build\main.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

Source: ".\encryption_algs\libs\release\libkyznechik-base.dll"; DestDir: "{app}\libs"; Flags: ignoreversion
Source: ".\encryption_algs\libs\release\libkyznechik-cbc.dll"; DestDir: "{app}\libs"; Flags: ignoreversion
Source: ".\encryption_algs\libs\release\libkyznechik-ctr.dll"; DestDir: "{app}\libs"; Flags: ignoreversion
Source: ".\encryption_algs\libs\release\libkyznechik-ecb.dll"; DestDir: "{app}\libs"; Flags: ignoreversion
Source: ".\encryption_algs\libs\release\libmagma-base.dll"; DestDir: "{app}\libs"; Flags: ignoreversion
Source: ".\encryption_algs\libs\release\libmagma-cbc.dll"; DestDir: "{app}\libs"; Flags: ignoreversion
Source: ".\encryption_algs\libs\release\libmagma-ctr.dll"; DestDir: "{app}\libs"; Flags: ignoreversion
Source: ".\encryption_algs\libs\release\libmagma-ecb.dll"; DestDir: "{app}\libs"; Flags: ignoreversion
Source: ".\encryption_algs\libs\release\libutils.dll"; DestDir: "{app}\libs"; Flags: ignoreversion

; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKCR; Subkey: "*\shell\GOST_Encryptor"; ValueType: string; ValueName: "MUIVerb"; ValueData: "{code:GetMainLabel}"; Flags: uninsdeletekey
Root: HKCR; Subkey: "*\shell\GOST_Encryptor"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\{#MyAppExeName}"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "*\shell\GOST_Encryptor"; ValueType: string; ValueName: "SubCommands"; ValueData: ""; Flags: uninsdeletevalue

Root: HKCR; Subkey: "*\shell\GOST_Encryptor\shell\encrypt"; ValueType: string; ValueName: "MUIVerb"; ValueData: "{code:GetEncryptLabel}"; Flags: uninsdeletekey
Root: HKCR; Subkey: "*\shell\GOST_Encryptor\shell\encrypt"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\{#MyAppExeName}"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "*\shell\GOST_Encryptor\shell\encrypt\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" encrypt ""%1"""; Flags: uninsdeletekey

Root: HKCR; Subkey: "*\shell\GOST_Encryptor\shell\decrypt"; ValueType: string; ValueName: "MUIVerb"; ValueData: "{code:GetDecryptLabel}"; Flags: uninsdeletekey
Root: HKCR; Subkey: "*\shell\GOST_Encryptor\shell\decrypt"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\{#MyAppExeName}"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "*\shell\GOST_Encryptor\shell\decrypt\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" decrypt ""%1"""; Flags: uninsdeletekey

Root: HKCR; Subkey: ".gost"; ValueType: string; ValueName: ""; ValueData: "GOSTEncryptorFile"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "GOSTEncryptorFile"; ValueType: string; ValueName: ""; ValueData: "GOST Encrypted File"; Flags: uninsdeletekey
Root: HKCR; Subkey: "GOSTEncryptorFile\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "GOSTEncryptorFile\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Flags: uninsdeletevalue

[Code]
function GetMainLabel(Value: string): string;
begin
    Result := 'GOST Encryptor';
end;

function GetEncryptLabel(Value: string): string;
begin
  if ActiveLanguage() = 'russian' then
    Result := 'Зашифровать файл'
  else
    Result := 'Encrypt the file';
end;

function GetDecryptLabel(Value: string): string;
begin
  if ActiveLanguage() = 'russian' then
    Result := 'Расшифровать файл'
  else
    Result := 'Decrypt the file';
end;

