# 打开目录；该目录已有资源管理器窗口时只激活，不重复打开
# 用法：powershell -NoProfile -ExecutionPolicy Bypass -File open_dir.ps1 "<目录>"
param([Parameter(Mandatory = $true)][string]$Path)
$p = (Resolve-Path -LiteralPath $Path).Path.TrimEnd('\')
$sh = New-Object -ComObject Shell.Application
foreach ($w in $sh.Windows()) {
  try {
    if ($w.Document.Folder.Self.Path.TrimEnd('\') -ieq $p) {
      Add-Type -Namespace W -Name U -MemberDefinition '[DllImport("user32.dll")] public static extern bool SetForegroundWindow(System.IntPtr h);'
      [W.U]::SetForegroundWindow([IntPtr]$w.HWND) | Out-Null
      Write-Output "already-open $p"; exit 0
    }
  } catch {}
}
Start-Process explorer.exe -ArgumentList "`"$p`""
Write-Output "opened $p"
