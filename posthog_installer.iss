#define MyAppName "PostHog"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "PostHog Offline"
#define MyAppURL "https://posthog.com"
#define MyAppExeName "posthog.exe"

[Setup]
AppId={{27A53A24-A55C-4B37-9B72-E4F799F7268F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=LICENSE.txt
OutputDir=output
OutputBaseFilename=posthog-windows-setup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main application files
Source: "dist\posthog\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Bundled Node.js runtime
Source: "embedded\node\*"; DestDir: "{app}\node"; Flags: ignoreversion recursesubdirs createallsubdirs

; Bundled Python runtime
Source: "embedded\python\*"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs createallsubdirs

; Firewall exception script
Source: "scripts\firewall.ps1"; DestDir: "{app}\scripts"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\posthog.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\posthog.ico"; Tasks: desktopicon

[Run]
; Run the application after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

; Create firewall exception
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\scripts\firewall.ps1"""; Flags: runhidden

[UninstallRun]
; Remove firewall exception on uninstall
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -Command ""Remove-NetFirewallRule -DisplayName 'PostHog' -ErrorAction SilentlyContinue"""; Flags: runhidden

[Code]
// Check if ports 8000 are available
function CheckPorts: Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  if Exec('powershell.exe', '-ExecutionPolicy Bypass -Command "if (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue) { exit 1 } else { exit 0 }"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    if ResultCode <> 0 then
    begin
      Result := False;
    end;
  end;
end;

// Initialize setup
function InitializeSetup(): Boolean;
begin
  Result := True;
  
  // Check ports
  if not CheckPorts then
  begin
    MsgBox('Port 8000 is currently in use by another application.' + #13#10 +
           'Please close any applications that might be using this port and try again.', mbError, MB_OK);
    Result := False;
  end;
end; 