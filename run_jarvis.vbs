Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

Dim scriptPath
scriptPath = fso.GetParentFolderName(WScript.ScriptFullName)
Dim psScript
psScript = scriptPath & "\jarvis_hotkey.ps1"

' Create PowerShell script for hotkey handling
Dim psContent
psContent = "$scriptPath = '" & Replace(scriptPath, "\", "\\") & "'" & vbCrLf & _
"$batFile = Join-Path $scriptPath 'run_jarvis.bat'" & vbCrLf & _
"$processId = 0" & vbCrLf & _
"" & vbCrLf & _
"Add-Type -TypeDefinition @'" & vbCrLf & _
"using System;" & vbCrLf & _
"using System.Runtime.InteropServices;" & vbCrLf & _
"using System.Diagnostics;" & vbCrLf & _
"public class HotkeyManager {" & vbCrLf & _
"    [DllImport(""user32.dll"")]" & vbCrLf & _
"    public static extern bool RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);" & vbCrLf & _
"    [DllImport(""user32.dll"")]" & vbCrLf & _
"    public static extern bool UnregisterHotKey(IntPtr hWnd, int id);" & vbCrLf & _
"    [DllImport(""user32.dll"")]" & vbCrLf & _
"    public static extern bool PeekMessage(out MSG lpMsg, IntPtr hWnd, uint wMsgFilterMin, uint wMsgFilterMax, uint wRemoveMsg);" & vbCrLf & _
"    [DllImport(""user32.dll"")]" & vbCrLf & _
"    public static extern bool TranslateMessage(ref MSG lpMsg);" & vbCrLf & _
"    [DllImport(""user32.dll"")]" & vbCrLf & _
"    public static extern IntPtr DispatchMessage(ref MSG lpMsg);" & vbCrLf & _
"    public const uint PM_REMOVE = 0x0001;" & vbCrLf & _
"    [StructLayout(LayoutKind.Sequential)]" & vbCrLf & _
"    public struct MSG {" & vbCrLf & _
"        public IntPtr hwnd;" & vbCrLf & _
"        public uint message;" & vbCrLf & _
"        public IntPtr wParam;" & vbCrLf & _
"        public IntPtr lParam;" & vbCrLf & _
"        public uint time;" & vbCrLf & _
"        public System.Drawing.Point pt;" & vbCrLf & _
"    }" & vbCrLf & _
"    public const uint WM_HOTKEY = 0x0312;" & vbCrLf & _
"}" & vbCrLf & _
"'@" & vbCrLf & _
"" & vbCrLf & _
"[HotkeyManager]::RegisterHotKey([IntPtr]::Zero, 1, 0, 0x72) | Out-Null  # F3" & vbCrLf & _
"[HotkeyManager]::RegisterHotKey([IntPtr]::Zero, 2, 0, 0x73) | Out-Null  # F4" & vbCrLf & _
"" & vbCrLf & _
"Write-Host 'JARVIS Hotkey Handler Active' -ForegroundColor Cyan" & vbCrLf & _
"Write-Host 'F3: Start/Restart JARVIS' -ForegroundColor Green" & vbCrLf & _
"Write-Host 'F4: Stop JARVIS' -ForegroundColor Red" & vbCrLf & _
"Write-Host 'Close this window to exit' -ForegroundColor Yellow" & vbCrLf & _
"" & vbCrLf & _
"# Cleanup function" & vbCrLf & _
"function Cleanup {" & vbCrLf & _
"    if ($processId -ne 0) {" & vbCrLf & _
"        try {" & vbCrLf & _
"            $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue" & vbCrLf & _
"            if ($proc) {" & vbCrLf & _
"                $children = Get-WmiObject Win32_Process | Where-Object { $_.ParentProcessId -eq $processId }" & vbCrLf & _
"                foreach ($child in $children) { Stop-Process -Id $child.ProcessId -Force -ErrorAction SilentlyContinue }" & vbCrLf & _
"                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue" & vbCrLf & _
"            }" & vbCrLf & _
"        } catch {}" & vbCrLf & _
"    }" & vbCrLf & _
"    [HotkeyManager]::UnregisterHotKey([IntPtr]::Zero, 1) | Out-Null" & vbCrLf & _
"    [HotkeyManager]::UnregisterHotKey([IntPtr]::Zero, 2) | Out-Null" & vbCrLf & _
"}" & vbCrLf & _
"" & vbCrLf & _
"# Register cleanup on exit" & vbCrLf & _
"Register-EngineEvent PowerShell.Exiting -Action { Cleanup } | Out-Null" & vbCrLf & _
"" & vbCrLf & _
"$msg = New-Object HotkeyManager+MSG" & vbCrLf & _
"try {" & vbCrLf & _
"    while ($true) {" & vbCrLf & _
"        if ([HotkeyManager]::PeekMessage([ref]$msg, [IntPtr]::Zero, 0, 0, [HotkeyManager]::PM_REMOVE)) {" & vbCrLf & _
"            if ($msg.message -eq [HotkeyManager]::WM_HOTKEY) {" & vbCrLf & _
"            if ($msg.wParam.ToInt32() -eq 1) {" & vbCrLf & _
"                # F3 pressed - Start/Restart" & vbCrLf & _
"                if ($processId -ne 0) {" & vbCrLf & _
"                    try {" & vbCrLf & _
"                        $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue" & vbCrLf & _
"                        if ($proc) {" & vbCrLf & _
"                            Get-Process -Id $processId | Stop-Process -Force -ErrorAction SilentlyContinue" & vbCrLf & _
"                            $children = Get-WmiObject Win32_Process | Where-Object { $_.ParentProcessId -eq $processId }" & vbCrLf & _
"                            foreach ($child in $children) { Stop-Process -Id $child.ProcessId -Force -ErrorAction SilentlyContinue }" & vbCrLf & _
"                        }" & vbCrLf & _
"                    } catch {}" & vbCrLf & _
"                    Start-Sleep -Milliseconds 300" & vbCrLf & _
"                }" & vbCrLf & _
"                $p = Start-Process -FilePath $batFile -PassThru -WindowStyle Hidden" & vbCrLf & _
"                $processId = $p.Id" & vbCrLf & _
"                Write-Host '[F3] JARVIS Started (PID: $processId)' -ForegroundColor Green" & vbCrLf & _
"            }" & vbCrLf & _
"            elseif ($msg.wParam.ToInt32() -eq 2) {" & vbCrLf & _
"                # F4 pressed - Stop" & vbCrLf & _
"                if ($processId -ne 0) {" & vbCrLf & _
"                    try {" & vbCrLf & _
"                        $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue" & vbCrLf & _
"                        if ($proc) {" & vbCrLf & _
"                            $children = Get-WmiObject Win32_Process | Where-Object { $_.ParentProcessId -eq $processId }" & vbCrLf & _
"                            foreach ($child in $children) { Stop-Process -Id $child.ProcessId -Force -ErrorAction SilentlyContinue }" & vbCrLf & _
"                            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue" & vbCrLf & _
"                            Write-Host '[F4] JARVIS Stopped' -ForegroundColor Red" & vbCrLf & _
"                        }" & vbCrLf & _
"                        $processId = 0" & vbCrLf & _
"                    } catch {" & vbCrLf & _
"                        Write-Host '[F4] Error stopping JARVIS' -ForegroundColor Yellow" & vbCrLf & _
"                        $processId = 0" & vbCrLf & _
"                    }" & vbCrLf & _
"                } else {" & vbCrLf & _
"                    Write-Host '[F4] JARVIS is not running' -ForegroundColor Yellow" & vbCrLf & _
"                }" & vbCrLf & _
"            }" & vbCrLf & _
"            [HotkeyManager]::TranslateMessage([ref]$msg) | Out-Null" & vbCrLf & _
"            [HotkeyManager]::DispatchMessage([ref]$msg) | Out-Null" & vbCrLf & _
"        }" & vbCrLf & _
"        Start-Sleep -Milliseconds 50" & vbCrLf & _
"    }" & vbCrLf & _
"} finally {" & vbCrLf & _
"    Cleanup" & vbCrLf & _
"}"

' Write PowerShell script to file
Dim file
Set file = fso.CreateTextFile(psScript, True)
file.Write psContent
file.Close

' Run PowerShell script
WshShell.Run "powershell.exe -ExecutionPolicy Bypass -File """ & psScript & """", 1, False

Set WshShell = Nothing
Set fso = Nothing
