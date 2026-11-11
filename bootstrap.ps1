# RHTV 视频素材工作台 · Agent 一条命令安装
# 用法（Agent 在 PowerShell 里执行，可重复执行）：
#   powershell -NoProfile -ExecutionPolicy Bypass -Command "& ([scriptblock]::Create((irm https://raw.githubusercontent.com/oNa2O2o/rhtv-workbench/main/bootstrap.ps1)))"
# 公司内网也可以直接运行共享盘里的副本：
#   powershell -NoProfile -ExecutionPolicy Bypass -File "\\file.wemomo.com\share\创新事业部\AIGC项目视频组\Agent+RHTV自动化工作流依赖文件\bootstrap.ps1"
# 可选参数：-Designer 名字（默认读公司域账号）、-Root 目录（默认容量最大的盘\RHTV工作台）、-SkipLogin
param([string]$Designer, [string]$Root, [switch]$SkipLogin, [switch]$ForceLink)

$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
$REPO = 'oNa2O2o/rhtv-workbench'
$SHAREDEP = '\\file.wemomo.com\share\创新事业部\AIGC项目视频组\Agent+RHTV自动化工作流依赖文件'
if (-not (Test-Path $SHAREDEP) -and (Test-Path 'Z:\创新事业部\AIGC项目视频组\Agent+RHTV自动化工作流依赖文件')) { $SHAREDEP = 'Z:\创新事业部\AIGC项目视频组\Agent+RHTV自动化工作流依赖文件' }
$shareOk = Test-Path $SHAREDEP

function Test-Writable([string]$dir) {
    try { New-Item -ItemType Directory -Force $dir -ErrorAction Stop | Out-Null; $f = Join-Path $dir '.wbtest'; Set-Content $f 'x' -ErrorAction Stop; Remove-Item $f; return $true } catch { return $false }
}
# 安装位置：已有配置 → 容量最大的本地盘\RHTV工作台
if (-not $Root) {
    $cfgPath = Join-Path $env:USERPROFILE '.rhtv-workbench\config.json'
    if (Test-Path $cfgPath) { try { $c = Get-Content $cfgPath -Raw -Encoding UTF8 | ConvertFrom-Json; if ($c.root -and (Test-Writable $c.root)) { $Root = $c.root } } catch {} }
}
if (-not $Root) {
    foreach ($dk in (Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' -ErrorAction SilentlyContinue | Sort-Object Size, FreeSpace -Descending)) {
        $cand = Join-Path ($dk.DeviceID + '\') 'RHTV工作台'
        if (Test-Writable $cand) { $Root = $cand; break }
    }
    if (-not $Root) { $Root = Join-Path $env:USERPROFILE 'RHTV工作台' }
}
$PKGDIR = Join-Path $Root '_系统\安装包'
New-Item -ItemType Directory -Force $PKGDIR | Out-Null
Write-Host "安装位置：$Root"
Write-Host ("共享依赖：" + $(if ($shareOk) { $SHAREDEP } else { '连不上（改用 GitHub 下载）' }))

# 1. 安装包：共享盘和 GitHub 取版本新的；GitHub 连不上就用共享盘
function Ver([string]$s) { if ($s -match '(\d+\.\d+\.\d+)') { return [version]$Matches[1] } return [version]'0.0.0' }
$shareVer = if ($shareOk -and (Test-Path "$SHAREDEP\rhtv-workbench\VERSION.txt")) { Ver (Get-Content "$SHAREDEP\rhtv-workbench\VERSION.txt" -TotalCount 1) } else { [version]'0.0.0' }
$ghVer = [version]'0.0.0'
try { $ghVer = Ver ([string](Invoke-WebRequest "https://raw.githubusercontent.com/$REPO/main/VERSION.txt" -UseBasicParsing -TimeoutSec 20).Content) } catch {}
$got = $false
if ($shareOk -and $shareVer -ge $ghVer -and $shareVer -gt [version]'0.0.0') {
    $null = robocopy "$SHAREDEP\rhtv-workbench" $PKGDIR /MIR /XD vendor .git /NFL /NDL /NJH /NJS /NP
    $got = Test-Path (Join-Path $PKGDIR 'install.ps1')
    if ($got) { Write-Host "安装包：共享盘 $shareVer" }
}
if (-not $got) {
    $zip = Join-Path $env:TEMP "rhtv-workbench-src.zip"
    try {
        Invoke-WebRequest "https://codeload.github.com/$REPO/zip/refs/heads/main" -OutFile $zip -UseBasicParsing -TimeoutSec 600
        $tmp = Join-Path $env:TEMP "rhtv-workbench-src"
        Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
        Expand-Archive -LiteralPath $zip -DestinationPath $tmp -Force
        $src = (Get-ChildItem $tmp -Directory | Select-Object -First 1).FullName
        $null = robocopy $src $PKGDIR /MIR /XD vendor /NFL /NDL /NJH /NJS /NP
        $got = Test-Path (Join-Path $PKGDIR 'install.ps1')
        if ($got) { Write-Host "安装包：GitHub $ghVer" }
    } catch { Write-Host "GitHub 下载失败：$($_.Exception.Message)" -ForegroundColor Yellow }
}
if (-not $got) {
    Write-Host 'RESULT_JSON: {"code":2,"failed":["拿不到安装包：共享盘和 GitHub 都连不上。请连上公司网络/VPN 后再运行"]}'
    exit 2
}

# 2. 离线依赖：共享盘 vendor → 本地；连不上共享盘就下载 GitHub Release
$VEND = Join-Path $PKGDIR 'vendor'
New-Item -ItemType Directory -Force $VEND | Out-Null
if ($shareOk -and (Test-Path "$SHAREDEP\vendor")) {
    $null = robocopy "$SHAREDEP\vendor" $VEND /E /XO /NFL /NDL /NJH /NJS /NP
} elseif (-not (Get-ChildItem $VEND -Filter 'rhtv-canvas-clients-*.zip' -ErrorAction SilentlyContinue)) {
    $vz = Join-Path $env:TEMP 'rhtv-workbench-vendor.zip'
    try {
        Write-Host '正在从 GitHub 下载离线依赖（约 250 MB）…'
        Invoke-WebRequest "https://github.com/$REPO/releases/latest/download/rhtv-workbench-vendor.zip" -OutFile $vz -UseBasicParsing -TimeoutSec 3600
        Expand-Archive -LiteralPath $vz -DestinationPath $VEND -Force
        Get-ChildItem $VEND -Recurse -File | Where-Object { $_.DirectoryName -ne $VEND } | Move-Item -Destination $VEND -Force
    } catch { Write-Host "离线依赖下载失败（安装器会尽量在线补装）：$($_.Exception.Message)" -ForegroundColor Yellow }
}
Get-ChildItem $PKGDIR -Recurse -File -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue

# 3. 安装
$argsList = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$(Join-Path $PKGDIR 'install.ps1')`"", '-Agent', '-Root', "`"$Root`"")
if ($Designer) { $argsList += @('-Designer', "`"$Designer`"") }
if ($SkipLogin) { $argsList += '-SkipLogin' }
if ($ForceLink) { $argsList += '-ForceLink' }
$p = Start-Process powershell.exe -ArgumentList $argsList -NoNewWindow -PassThru
$null = $p.Handle
$p.WaitForExit()
exit $p.ExitCode
