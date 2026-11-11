# RHTV 视频素材工作台 · 一键安装（Windows）
# 双击「双击安装.bat」运行。可重复运行：已装好的会跳过，坏的会修。
# 用户只需要做两件事：填设计师名字、在浏览器里登录并点「批准」。其余全部自动完成。
param(
    [string]$Designer,
    [string]$Root,
    [switch]$SkipLogin,      # 测试用：跳过 rhTV / ElevenLabs 登录
    [switch]$ForceLink,      # 各平台已有同名 Skill 时也强制换成安装包里的版本
    [switch]$NoPause,
    [switch]$Sandbox         # 测试用：环境变量只在本次进程生效，不写入系统
)

$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$OutputEncoding = [Text.Encoding]::UTF8
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$PKG = $PSScriptRoot
$H = $env:USERPROFILE
$WB = Join-Path $H '.rhtv-workbench'
$LOGDIR = Join-Path $WB 'logs'
$BIN = Join-Path $WB 'bin'
$TS = Get-Date -Format 'yyyyMMdd-HHmmss'
$PKGVER = [string](Get-Content (Join-Path $PKG 'VERSION.txt') -TotalCount 1 -ErrorAction SilentlyContinue)

# ---------------------------------------------------------------- 0. 不能用“以管理员身份运行”（rhTV 安装器会拒绝）
$me = [Security.Principal.WindowsIdentity]::GetCurrent()
if (([Security.Principal.WindowsPrincipal]$me).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator) -and
    $me.Owner.Value -ne $me.User.Value) {
    Write-Host '请不要用“以管理员身份运行”。关掉这个窗口，直接双击「双击安装.bat」。' -ForegroundColor Red
    if (-not $NoPause) { Read-Host '按回车关闭' | Out-Null }
    exit 1
}

# 关掉控制台“快速编辑”：用户点一下窗口不会把安装卡住
try {
    Add-Type -Namespace W -Name Con -MemberDefinition '[DllImport("kernel32.dll")] public static extern IntPtr GetStdHandle(int h);
[DllImport("kernel32.dll")] public static extern bool GetConsoleMode(IntPtr h, out uint m);
[DllImport("kernel32.dll")] public static extern bool SetConsoleMode(IntPtr h, uint m);' -ErrorAction Stop
    $hIn = [W.Con]::GetStdHandle(-10); $m = 0
    if ([W.Con]::GetConsoleMode($hIn, [ref]$m)) { [void][W.Con]::SetConsoleMode($hIn, ($m -band (-bnot 0x40)) -bor 0x80) }
} catch {}

New-Item -ItemType Directory -Force $LOGDIR, $BIN | Out-Null
# 从这次安装开始重新记录：旧日志归档
$old = Get-ChildItem $LOGDIR -File -ErrorAction SilentlyContinue
if ($old) {
    $arc = Join-Path $LOGDIR "归档-$TS"
    New-Item -ItemType Directory -Force $arc | Out-Null
    $old | Move-Item -Destination $arc -Force
}
$LOGTXT = Join-Path $LOGDIR "安装-$TS.log"
$LOGJ = Join-Path $LOGDIR '安装日志.jsonl'
$RESULTS = New-Object System.Collections.ArrayList

function Log([string]$step, [string]$status, [string]$msg, $detail = $null) {
    # status: ok / fixed / skip / warn / fail / info
    $color = @{ ok = 'Green'; fixed = 'Cyan'; skip = 'DarkGray'; warn = 'Yellow'; fail = 'Red'; info = 'White' }[$status]
    if (-not $color) { $color = 'White' }
    $tag = @{ ok = '[完成]'; fixed = '[已修复]'; skip = '[跳过]'; warn = '[注意]'; fail = '[失败]'; info = '[....]' }[$status]
    Write-Host ("{0} {1}：{2}" -f $tag, $step, $msg) -ForegroundColor $color
    $d = $null
    if ($detail) { $d = [string](($detail | Out-String).Trim()); if ($d.Length -gt 8000) { $d = $d.Substring(0, 8000) + '…' } }
    $line = "{0} {1} {2}：{3}" -f (Get-Date -Format 'HH:mm:ss'), $tag, $step, $msg
    if ($d) { $line += "`n    " + ($d -replace "`n", "`n    ") }
    Add-Content -Path $LOGTXT -Value $line -Encoding UTF8
    $rec = [ordered]@{ time = [string](Get-Date -Format 's'); host = [string]$env:COMPUTERNAME; user = [string]$env:USERNAME; ver = $PKGVER
        cmd = 'install'; kind = $status; ok = ($status -in @('ok', 'fixed', 'skip', 'info')); step = $step; msg = $msg }
    if ($d) { $rec.detail = $d }
    Add-Content -Path $LOGJ -Value ($rec | ConvertTo-Json -Compress -Depth 3) -Encoding UTF8
    if ($status -ne 'info') { [void]$RESULTS.Add([pscustomobject]@{ 步骤 = $step; 结果 = $tag; 说明 = $msg }) }
}
function Say([string]$msg) { Write-Host "  … $msg" -ForegroundColor DarkCyan }

function Set-UserEnv([string]$k, [string]$v) {
    if (-not $Sandbox) { [Environment]::SetEnvironmentVariable($k, $v, 'User') }
    Set-Item -Path "Env:$k" -Value $v
}
$script:EXTRA_PATH = @()
function Refresh-Path {
    $env:Path = "$BIN;" + [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + [Environment]::GetEnvironmentVariable('Path', 'Machine')
    if ($script:EXTRA_PATH) { $env:Path = ($script:EXTRA_PATH -join ';') + ';' + $env:Path }
}
function Add-UserPath([string]$dir, [switch]$Front) {
    $cur = [string][Environment]::GetEnvironmentVariable('Path', 'User')
    $parts = @($cur -split ';' | Where-Object { $_ -and $_.TrimEnd('\') -ne $dir.TrimEnd('\') })
    $new = if ($Front) { @($dir) + $parts } else { $parts + @($dir) }
    if (-not $Sandbox) { [Environment]::SetEnvironmentVariable('Path', ($new -join ';'), 'User') }
    else { $script:EXTRA_PATH = @($dir) + $script:EXTRA_PATH }
    Refresh-Path
}

function Run([string]$exe, [string[]]$argv, [int]$timeoutSec = 900) {
    # 运行外部程序，返回 @{code; out(stdout); err(stderr); all}
    $o = Join-Path $env:TEMP ("wb_" + [guid]::NewGuid().ToString('N') + '.txt')
    $e = $o + '.err'
    try {
        $sp = @{ FilePath = $exe; NoNewWindow = $true; PassThru = $true; RedirectStandardOutput = $o; RedirectStandardError = $e }
        if ($argv -and $argv.Count) { $sp.ArgumentList = $argv }
        $p = Start-Process @sp
        $null = $p.Handle   # PS 5.1：不先取句柄，退出码会是空值
        if (-not $p.WaitForExit($timeoutSec * 1000)) { try { $p.Kill() } catch {}; return @{ code = -1; out = ''; err = "超时 $timeoutSec 秒"; all = "超时 $timeoutSec 秒" } }
        $p.WaitForExit()
        $so = ''; $se = ''
        if (Test-Path $o) { $so = [IO.File]::ReadAllText($o, [Text.Encoding]::UTF8) }
        if (Test-Path $e) { $se = [IO.File]::ReadAllText($e, [Text.Encoding]::UTF8) }
        return @{ code = $p.ExitCode; out = $so.Trim(); err = $se.Trim(); all = ($so + "`n" + $se).Trim() }
    } catch {
        return @{ code = -2; out = ''; err = $_.Exception.Message; all = $_.Exception.Message }
    } finally { Remove-Item $o, $e -ErrorAction SilentlyContinue }
}
function Quote([string]$s) { if ($s -match '[\s"]') { '"' + ($s -replace '"', '\"') + '"' } else { $s } }

Write-Host ''
Write-Host "=== RHTV 视频素材工作台 一键安装 $PKGVER ===" -ForegroundColor Magenta
Write-Host "安装日志：$LOGTXT"
Write-Host '安装期间不要点击这个窗口里的文字；需要你操作时会用青色字提示。'
Write-Host ''
Log '开始' 'info' "电脑 $env:COMPUTERNAME，用户 $env:USERNAME，系统 $([Environment]::OSVersion.VersionString)，安装包 $PKG"
Get-ChildItem $PKG -Recurse -File -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue

# ---------------------------------------------------------------- 1. 脚本执行策略（rhTV 保存登录凭据要运行本地脚本）
$gpo = @((Get-ExecutionPolicy -Scope MachinePolicy), (Get-ExecutionPolicy -Scope UserPolicy)) | Where-Object { "$_" -ne 'Undefined' } | Select-Object -First 1
$cu = Get-ExecutionPolicy -Scope CurrentUser
$lm = Get-ExecutionPolicy -Scope LocalMachine
$persist = if ($gpo) { $gpo } elseif ("$cu" -ne 'Undefined') { $cu } elseif ("$lm" -ne 'Undefined') { $lm } else { 'Restricted' }
$goodPol = @('RemoteSigned', 'Unrestricted', 'Bypass')
if ($gpo -and "$gpo" -notin $goodPol) {
    Log '脚本执行策略' 'fail' "被公司组策略锁成 $gpo：rhTV 登录凭据脚本会被拦，请 IT 把本机执行策略放开为 RemoteSigned"
} elseif ("$persist" -notin $goodPol) {
    try { Set-ExecutionPolicy -Scope CurrentUser RemoteSigned -Force -ErrorAction Stop } catch {}   # “被更具体的作用域覆盖”报错可忽略，值已写入
    if ("$(Get-ExecutionPolicy -Scope CurrentUser)" -eq 'RemoteSigned') { Log '脚本执行策略' 'fixed' "原来是 $persist，已改为 RemoteSigned（只对当前用户）" }
    else { Log '脚本执行策略' 'fail' "改不了（当前 $persist）" }
} else { Log '脚本执行策略' 'ok' "$persist" }

# ---------------------------------------------------------------- 2. Python（64 位、3.9–3.12）
function Test-Py([string]$exe, [string[]]$pre = @()) {
    if (-not $exe -or $exe -like '*WindowsApps*') { return $false }   # 商店占位，不是真 Python
    $r = Run $exe ($pre + @('-c', '"import sys,struct;print((3,9)<=sys.version_info[:2]<=(3,12) and struct.calcsize(''P'')==8)"')) 60
    return ($r.code -eq 0 -and $r.out -match 'True')
}
function Find-Py {
    $cands = @()
    $cands += Get-Command python -All -ErrorAction SilentlyContinue | Where-Object { $_.Source -notlike '*WindowsApps*' } | Select-Object -ExpandProperty Source
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        foreach ($v in @('-3.11', '-3.12', '-3.10', '-3')) {
            $r = Run $py.Source @($v, '-c', '"import sys;print(sys.executable)"') 60
            if ($r.code -eq 0 -and $r.out) { $cands += $r.out.Trim() }
        }
    }
    $cands += Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe", "C:\Program Files\Python3*\python.exe", "C:\Python3*\python.exe" -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -ExpandProperty FullName
    foreach ($x in $cands) { if ($x -and (Test-Py $x)) { return $x } }
    return $null
}
$PY = Find-Py
if (-not $PY) {
    Say '没找到可用的 Python（需要 64 位 3.9–3.12），正在安装 Python 3.11（约 1–3 分钟）'
    $inst = Get-ChildItem (Join-Path $PKG 'vendor') -Filter 'python-3*.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $inst) {
        $dst = Join-Path $env:TEMP 'python-3.11.9-amd64.exe'
        foreach ($u in @('https://registry.npmmirror.com/-/binary/python/3.11.9/python-3.11.9-amd64.exe', 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe')) {
            try { Invoke-WebRequest $u -OutFile $dst -UseBasicParsing -TimeoutSec 600; $inst = Get-Item $dst; break } catch {}
        }
    }
    $r = @{ code = $null; all = '安装包里没有 Python 安装程序，网上也下载不到' }
    if ($inst) {
        $r = Run $inst.FullName @('/quiet', 'InstallAllUsers=0', 'InstallLauncherAllUsers=0', 'Include_launcher=1', 'PrependPath=1',
            'Include_test=0', 'Shortcuts=0', '/log', (Quote (Join-Path $LOGDIR 'python-install.log'))) 1200
        Refresh-Path
        $PY = Find-Py
    }
    if ($PY) { Log 'Python' 'fixed' "已安装：$PY" }
    else { Log 'Python' 'fail' 'Python 安装失败，后面的 Python 依赖和工作台脚本都用不了' ("安装程序：$($inst.FullName)`n退出码：$($r.code)`n$($r.all)`n详细：$LOGDIR\python-install.log") }
} else { Log 'Python' 'ok' $PY }
if ($PY) {
    # 让 Agent 里敲 python 也是这个 Python（排在商店占位前面）
    $pyDir = Split-Path $PY
    Add-UserPath (Join-Path $pyDir 'Scripts') -Front
    Add-UserPath $pyDir -Front
}

# ---------------------------------------------------------------- 3. Python 依赖（国内镜像优先）
function Py-Has([string]$mod) { return ((Run $PY @('-c', "`"import $mod`"") 120).code -eq 0) }
function Pip-Install([string]$pkg, [string]$mod) {
    if (Py-Has $mod) { return 'ok' }
    $last = $null
    $mirrors = @(@('https://pypi.tuna.tsinghua.edu.cn/simple', 'pypi.tuna.tsinghua.edu.cn'), @('https://mirrors.aliyun.com/pypi/simple', 'mirrors.aliyun.com'), @($null, $null))
    foreach ($m in $mirrors) {
        foreach ($user in @($false, $true)) {
            $a = @('-m', 'pip', 'install', '-q', '--disable-pip-version-check', '--timeout', '30', '--retries', '2') + ($pkg -split ' ')
            if ($user) { $a += '--user' }
            if ($m[0]) { $a += @('-i', $m[0], '--trusted-host', $m[1]) }
            $last = Run $PY $a 1800
            if (Py-Has $mod) { return 'fixed' }
        }
    }
    return 'fail:' + $last.all
}
if ($PY) {
    $need = @(
        @{ p = 'pillow'; m = 'PIL'; must = $true; t = '' }, @{ p = 'numpy'; m = 'numpy'; must = $true; t = '' },
        @{ p = 'fonttools'; m = 'fontTools'; must = $true; t = '' }, @{ p = 'playwright'; m = 'playwright'; must = $true; t = '（约 1–3 分钟）' },
        @{ p = 'faster-whisper'; m = 'faster_whisper'; must = $true; t = '（约 3–10 分钟）' }, @{ p = 'soundfile'; m = 'soundfile'; must = $false; t = '' }
    )
    foreach ($n in $need) {
        if (-not (Py-Has $n.m)) { Say "正在安装 Python 包 $($n.p)$($n.t)，请勿关闭窗口" }
        $s = Pip-Install $n.p $n.m
        if ($s -eq 'ok') { Log "Python 包 $($n.p)" 'ok' '已装' }
        elseif ($s -eq 'fixed') { Log "Python 包 $($n.p)" 'fixed' '已安装' }
        elseif ($n.must) { Log "Python 包 $($n.p)" 'fail' '装不上（检查网络或公司代理）' $s }
        else { Log "Python 包 $($n.p)" 'warn' '可选包没装上，不影响主流程' $s }
    }
}

# ---------------------------------------------------------------- 4. ffmpeg / ffprobe / ElevenLabs CLI（只认 .exe，Python 和 Agent 都能调用）
Add-UserPath $BIN -Front
foreach ($tool in @('ffmpeg', 'ffprobe', 'elevenlabs')) {
    $c = Get-Command $tool -CommandType Application -ErrorAction SilentlyContinue | Where-Object { $_.Extension -eq '.exe' } | Select-Object -First 1
    if ($c) { Log $tool 'ok' $c.Source; continue }
    $src = Join-Path $PKG "vendor\$tool.exe"
    if (Test-Path $src) {
        Copy-Item $src (Join-Path $BIN "$tool.exe") -Force
        Refresh-Path
        if (Get-Command "$tool.exe" -ErrorAction SilentlyContinue) { Log $tool 'fixed' "已装到 $BIN 并加入 PATH" }
        else { Log $tool 'fail' "复制到 $BIN 后仍找不到" }
    } else { Log $tool 'fail' "安装包 vendor 里缺 $tool.exe" }
}
$ELEXE = (Get-Command elevenlabs -CommandType Application -ErrorAction SilentlyContinue | Where-Object { $_.Extension -eq '.exe' } | Select-Object -First 1).Source

# ---------------------------------------------------------------- 5. 浏览器（app-ui / 尾板渲染、xmp-upload 用）
$chrome = @("$env:ProgramFiles\Google\Chrome\Application\chrome.exe", "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
$cenv = [Environment]::GetEnvironmentVariable('CHROME', 'User')
if ($chrome) {
    if ($chrome -ne "$env:ProgramFiles\Google\Chrome\Application\chrome.exe") { Set-UserEnv 'CHROME' $chrome }
    Log 'Chrome' 'ok' $chrome
} elseif ($cenv -and (Test-Path $cenv)) {
    Log 'Chrome' 'ok' "用环境变量 CHROME：$cenv"
} else {
    $edge = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe", "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($edge) { Set-UserEnv 'CHROME' $edge; Log 'Chrome' 'fixed' "没装 Chrome，已改用 Edge（同内核）：CHROME=$edge" }
    else { Log 'Chrome' 'fail' '没有 Chrome 也没有 Edge，渲染包装会失败，请安装 Chrome' }
}

# ---------------------------------------------------------------- 6. 共享资源盘（mm-packager 字体、模型、卡面库）
$SHARE = '\\file.wemomo.com\share'
$RESREL = '创新事业部\AIGC项目视频组\mm-packager资源'
$resZ = "Z:\$RESREL"
$resUNC = "$SHARE\$RESREL"
if (Test-Path $resZ) {
    Log '共享资源盘' 'ok' $resZ
} elseif (Test-Path $resUNC) {
    # 网络路径不用密码就能访问时才映射（否则 net use 会在后台等密码）
    if (-not (Test-Path 'Z:\')) { Run 'net.exe' @('use', 'Z:', $SHARE, '/persistent:yes') 60 | Out-Null }
    if (Test-Path $resZ) { Log '共享资源盘' 'fixed' "已映射 Z: → $SHARE" }
    else { Set-UserEnv 'MM_RES' $resUNC; Log '共享资源盘' 'fixed' "Z: 被占用或映射失败，已设 MM_RES=$resUNC" }
} else {
    Log '共享资源盘' 'warn' "连不上 $SHARE（不在公司网络/VPN，或要先在资源管理器里打开一次并登录）。连上后重新双击安装即可"
}

# ---------------------------------------------------------------- 7. rhTV 客户端（rhtvcli）
$RHHOME = Join-Path $H '.runninghub-canvas'
$RHCLI = Join-Path $RHHOME 'bin\rhtvcli.cmd'
$rhzip = Get-ChildItem (Join-Path $PKG 'vendor') -Filter 'rhtv-canvas-clients-*.zip' -ErrorAction SilentlyContinue | Select-Object -First 1
$wantVer = $null
if ($rhzip -and $rhzip.Name -match 'clients-(\d+\.\d+\.\d+)') { $wantVer = $Matches[1] }
function RH-Ver { if (Test-Path $RHCLI) { $r = Run $RHCLI @('--version') 60; if ($r.all -match '(\d+\.\d+\.\d+)') { return $Matches[1] } }; return $null }
$haveVer = RH-Ver
if ($haveVer -and (-not $wantVer -or [version]$haveVer -ge [version]$wantVer)) {
    Log 'rhTV 客户端' 'ok' "rhtvcli $haveVer"
} elseif ($Sandbox) {
    Log 'rhTV 客户端' 'skip' '沙盒模式：官方安装脚本要求真实用户目录，跳过'
} elseif (-not $rhzip) {
    Log 'rhTV 客户端' 'fail' '安装包 vendor 里缺 rhtv-canvas-clients-*.zip'
} else {
    Say '正在安装 rhTV 客户端（约 1–3 分钟）'
    # 先准备好 Node（离线包），避免官方脚本去 nodejs.org 下载超时
    $nodeZip = Get-ChildItem (Join-Path $PKG 'vendor') -Filter 'node-v*-win-x64.zip' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($nodeZip) {
        $nodeDir = Join-Path $WB 'node'
        if (-not (Test-Path (Join-Path $nodeDir 'node.exe'))) {
            $tmp = Join-Path $env:TEMP "wbnode_$TS"
            Expand-Archive -LiteralPath $nodeZip.FullName -DestinationPath $tmp -Force
            New-Item -ItemType Directory -Force $nodeDir | Out-Null
            Copy-Item (Get-ChildItem $tmp -Recurse -Filter node.exe | Select-Object -First 1).FullName $nodeDir -Force
            Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
        }
        $env:Path = "$nodeDir;$env:Path"
    }
    $rel = Join-Path $H ("rhtv-release\" + [IO.Path]::GetFileNameWithoutExtension($rhzip.Name).Replace('rhtv-canvas-clients-', ''))
    try {
        New-Item -ItemType Directory -Force $rel | Out-Null
        Expand-Archive -LiteralPath $rhzip.FullName -DestinationPath $rel -Force
        Get-ChildItem $rel -Filter '*.zip' | ForEach-Object { Expand-Archive -LiteralPath $_.FullName -DestinationPath $rel -Force }
        Get-ChildItem $rel -Recurse -File | Unblock-File -ErrorAction SilentlyContinue
        $bootDir = (Get-ChildItem $rel -Directory -Filter 'rhtv-bootstrap-*' | Select-Object -First 1).FullName
        $mcpDir = (Get-ChildItem $rel -Directory -Filter 'rhtv-mcp-*' | Select-Object -First 1).FullName
        $cliDir = (Get-ChildItem $rel -Directory -Filter 'rhtvcli-*' | Select-Object -First 1).FullName
        $out = ''
        foreach ($pkgDir in @($mcpDir, $cliDir)) {
            if (-not $pkgDir) { continue }
            # upgrade 在没装过时等同安装，装过旧版时直接升级
            $r = Run 'powershell.exe' @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Quote (Join-Path $bootDir 'install.ps1')), (Quote $pkgDir), 'upgrade') 1200
            if ($r.code -ne 0) { $r = Run 'powershell.exe' @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Quote (Join-Path $bootDir 'install.ps1')), (Quote $pkgDir), 'install') 1200 }
            $out += "`n--- $(Split-Path $pkgDir -Leaf) ---`n" + $r.all
        }
        $haveVer = RH-Ver
        if ($haveVer -and (-not $wantVer -or [version]$haveVer -ge [version]$wantVer)) { Log 'rhTV 客户端' 'fixed' "已安装 rhtvcli $haveVer" $out }
        else { Log 'rhTV 客户端' 'fail' "官方安装脚本没装成功（现在版本：$haveVer）" $out }
    } catch { Log 'rhTV 客户端' 'fail' $_.Exception.Message }
}
if (Test-Path (Join-Path $RHHOME 'bin')) { Add-UserPath (Join-Path $RHHOME 'bin') }

# ---------------------------------------------------------------- 8. Skill：复制到 ~/.rhtv-workbench/skills，再链接到每个 Agent 平台
function Get-SkillVer([string]$dir) {
    $f = Join-Path $dir 'SKILL.md'
    if (-not (Test-Path $f)) { return $null }
    $m = Select-String -Path $f -Pattern '^version:\s*([\d\.]+)' -List -ErrorAction SilentlyContinue
    if ($m) { try { return [version]$m.Matches[0].Groups[1].Value } catch {} }
    return [version]'0.0.0'
}
$SKSRC = Join-Path $PKG 'skills'
$SKDST = Join-Path $WB 'skills'
$BAK = Join-Path $WB "backup\$TS"
$skills = @(Get-ChildItem $SKSRC -Directory -ErrorAction SilentlyContinue)
New-Item -ItemType Directory -Force $SKDST | Out-Null
$copyFail = @()
foreach ($s in $skills) {
    $d = Join-Path $SKDST $s.Name
    $r = Run 'robocopy.exe' @((Quote $s.FullName), (Quote $d), '/E', '/NFL', '/NDL', '/NJH', '/NJS', '/NP', '/XF', 'config.json', '/XD', '__pycache__', '.git') 600
    if ($r.code -ge 8) { $copyFail += $s.Name; Log "Skill 文件 $($s.Name)" 'fail' '复制失败' $r.all }
}
if (-not $copyFail) { Log 'Skill 文件' 'ok' ("已放到 $SKDST：" + (($skills | Select-Object -ExpandProperty Name) -join '、')) }

$platforms = @(
    @{ n = 'Claude Code'; d = "$H\.claude\skills"; always = $true },
    @{ n = '通用 .agents（Codex/Gemini/OpenCode 等共用）'; d = "$H\.agents\skills"; always = $true },
    @{ n = 'Codex'; d = "$H\.codex\skills"; home = "$H\.codex"; cmd = 'codex' },
    @{ n = 'Gemini CLI'; d = "$H\.gemini\skills"; home = "$H\.gemini"; cmd = 'gemini' },
    @{ n = 'Cursor'; d = "$H\.cursor\skills"; home = "$H\.cursor"; cmd = 'cursor-agent' },
    @{ n = 'pi'; d = "$H\.pi\agent\skills"; home = "$H\.pi"; cmd = 'pi' },
    @{ n = 'OpenCode'; d = "$H\.config\opencode\skills"; home = "$H\.config\opencode"; cmd = 'opencode' }
)
$linked = @()
foreach ($pf in $platforms) {
    $present = $pf.always -or (Test-Path $pf.home) -or ($pf.cmd -and (Get-Command $pf.cmd -ErrorAction SilentlyContinue))
    if (-not $present) { Log "平台 $($pf.n)" 'skip' '本机没装，跳过'; continue }
    New-Item -ItemType Directory -Force $pf.d | Out-Null
    $notes = @()
    foreach ($s in $skills) {
        $mine = Join-Path $SKDST $s.Name
        $link = Join-Path $pf.d $s.Name
        $item = Get-Item $link -Force -ErrorAction SilentlyContinue
        if ($item) {
            $target = $item.Target
            if ($target -is [array]) { $target = $target[0] }
            $ok = Test-Path (Join-Path $link 'SKILL.md')
            if ($ok -and $target -and ((Resolve-Path $target -ErrorAction SilentlyContinue).Path -eq (Resolve-Path $mine).Path)) { continue }
            $their = if ($ok) { Get-SkillVer $link } else { $null }
            $ours = Get-SkillVer $mine
            if ($ok -and -not $ForceLink -and $their -and $ours -and $their -ge $ours) {
                $notes += "$($s.Name) 保留已有版本（$link → $target）"
                continue
            }
            # 坏链接或旧版本：移到备份目录（不能留在 skills 目录里，否则 Agent 会加载两份）
            if ($item.LinkType) { cmd /c rmdir (Quote $link) | Out-Null; $notes += "$($s.Name) 原来的链接（$target）已替换" }
            else {
                New-Item -ItemType Directory -Force $BAK | Out-Null
                $bk = Join-Path $BAK (($pf.n -replace '[^\w]', '_') + '-' + $s.Name)
                Move-Item $link $bk -Force
                $notes += "$($s.Name) 原来的目录已备份到 $bk"
            }
        }
        New-Item -ItemType Junction -Path $link -Target $mine -ErrorAction SilentlyContinue | Out-Null
    }
    # 清掉 skills 目录里的 .bak-* 备份（旧版安装器的遗留）
    Get-ChildItem $pf.d -Directory -Filter '*.bak-*' -ErrorAction SilentlyContinue | ForEach-Object {
        New-Item -ItemType Directory -Force $BAK | Out-Null; Move-Item $_.FullName (Join-Path $BAK $_.Name) -Force }
    # 最终逐个核对：每个 Skill 都能读到 SKILL.md
    $miss = @($skills | Where-Object { -not (Test-Path (Join-Path (Join-Path $pf.d $_.Name) 'SKILL.md')) } | Select-Object -ExpandProperty Name)
    if ($miss.Count -eq 0) {
        Log "平台 $($pf.n)" 'ok' ("全部 $($skills.Count) 个 Skill 已链接：$($pf.d)") ($notes -join "`n")
        $linked += $pf.n
    } else { Log "平台 $($pf.n)" 'fail' ("这些 Skill 链接失败：" + ($miss -join '、')) ($notes -join "`n") }
}

# ---------------------------------------------------------------- 9. 登录（唯一需要用户动手的地方）
function RH-Account {
    if (-not (Test-Path $RHCLI)) { return @() }
    $r = Run $RHCLI @('account', '--json') 60
    try { $j = $r.out | ConvertFrom-Json; return @($j.data.allowedActions) } catch { return @() }
}
if (Test-Path $RHCLI) {
    $acts = RH-Account
    if ($acts -contains 'canvas:edit' -and $acts -contains 'canvas:run' -and $acts -contains 'canvas:create') {
        Log 'rhTV 登录' 'ok' ('已登录，权限：' + ($acts -join ', '))
    } elseif ($SkipLogin) {
        Log 'rhTV 登录' 'skip' '按参数跳过登录'
    } else {
        $done = $false
        for ($try = 1; $try -le 3 -and -not $done; $try++) {
            Write-Host ''
            Write-Host '>>> 浏览器会打开 rhTV 授权页：登录你的 RunningHub 账号，然后点「批准」。批准前不要关这个窗口（最多等 15 分钟）。' -ForegroundColor Cyan
            $o = Join-Path $env:TEMP ("rhlogin_{0}_{1}.txt" -f $TS, $try)
            $p = Start-Process -FilePath $RHCLI -ArgumentList '--json', 'login' -NoNewWindow -PassThru -RedirectStandardOutput $o -RedirectStandardError "$o.err"
            $null = $p.Handle
            $shown = $false
            while (-not $p.HasExited) {
                Start-Sleep -Seconds 2
                $txt = (Get-Content $o, "$o.err" -Raw -Encoding UTF8 -ErrorAction SilentlyContinue) -join "`n"
                if (-not $shown -and $txt -match '"verification(Uri|Url)(Complete)?"\s*:\s*"(https://[^"]+)"') {
                    Write-Host "    如果浏览器没有自动打开，请手动打开：$($Matches[3])" -ForegroundColor Yellow
                    $shown = $true
                }
                if ((Get-Date) - $p.StartTime -gt [TimeSpan]::FromMinutes(15)) { try { $p.Kill() } catch {}; break }
            }
            $txt = (Get-Content $o, "$o.err" -Raw -Encoding UTF8 -ErrorAction SilentlyContinue) -join "`n"
            Remove-Item $o, "$o.err" -ErrorAction SilentlyContinue
            $acts = RH-Account
            if ($acts -contains 'canvas:edit') { Log 'rhTV 登录' 'fixed' ('登录成功，权限：' + ($acts -join ', ')); $done = $true; break }
            if ($txt -match 'LOGOUT_REQUIRED') {
                Run $RHCLI @('logout') 60 | Out-Null
                Log 'rhTV 登录' 'info' '本机有过期或旧格式的登录记录，已退出旧登录后重试'
                continue
            }
            if ($txt -match 'ExecutionPolicy|执行策略|DPAPI|CREDENTIALS_UNAVAILABLE') {
                try { Set-ExecutionPolicy -Scope CurrentUser RemoteSigned -Force -ErrorAction Stop } catch {}
                Log 'rhTV 登录' 'info' '保存凭据的脚本被执行策略拦住，已放开后重试（需要再批准一次）'
                continue
            }
            Log 'rhTV 登录' 'fail' '没有完成授权（超时或拒绝）。重新双击安装即可再登录' $txt
            break
        }
    }
} else { Log 'rhTV 登录' 'fail' 'rhTV 客户端没装好，无法登录（见上面 rhTV 客户端一项）' }

# ElevenLabs（口播 / BGM / 音效）
function EL-LoggedIn {
    if ($env:ELEVENLABS_API_KEY) { return $true }
    if (-not $ELEXE) { return $false }
    $s = Run $ELEXE @('auth', 'status', '--format', 'json') 60
    try { return (@((($s.out | ConvertFrom-Json).schemes) | Where-Object { $_.logged_in -eq $true }).Count -gt 0) } catch { return $false }
}
if ($ELEXE) {
    if (EL-LoggedIn) { Log 'ElevenLabs 登录' 'ok' '已登录' }
    elseif ($SkipLogin) { Log 'ElevenLabs 登录' 'skip' '按参数跳过登录' }
    else {
        Write-Host ''
        Write-Host '>>> 接下来登录 ElevenLabs（口播、BGM、音效要用）：浏览器会打开授权页，登录后确认即可（最多等 15 分钟）。' -ForegroundColor Cyan
        $p = Start-Process -FilePath $ELEXE -ArgumentList 'auth', 'login' -NoNewWindow -PassThru
        $null = $p.Handle
        while (-not $p.HasExited) {
            Start-Sleep -Seconds 2
            if ((Get-Date) - $p.StartTime -gt [TimeSpan]::FromMinutes(15)) { try { $p.Kill() } catch {}; break }
        }
        if (EL-LoggedIn) { Log 'ElevenLabs 登录' 'fixed' '登录完成' }
        else { Log 'ElevenLabs 登录' 'fail' '没登录成功，重新双击安装可再试' (Run $ELEXE @('auth', 'status') 60).all }
    }
} else { Log 'ElevenLabs 登录' 'fail' 'ElevenLabs CLI 没装好（见上面 elevenlabs 一项）' }

# ---------------------------------------------------------------- 10. 工作台配置
$WBPY = Join-Path $H '.claude\skills\rhtv-workbench\scripts\wb.py'
if (-not (Test-Path $WBPY)) { $WBPY = Join-Path $SKDST 'rhtv-workbench\scripts\wb.py' }
$cfgPath = Join-Path $WB 'config.json'
$cfg = $null
if (Test-Path $cfgPath) { try { $cfg = Get-Content $cfgPath -Raw -Encoding UTF8 | ConvertFrom-Json } catch {} }
if (-not $Designer -and $cfg -and $cfg.designer) { $Designer = $cfg.designer }
while (-not $Designer) {
    Write-Host ''
    $Designer = ([string](Read-Host '请输入你的名字（RHTV 里会建同名文件夹，例如 钟海明），输完按回车')).Trim()
}
function Test-Writable([string]$dir) {
    try { New-Item -ItemType Directory -Force $dir -ErrorAction Stop | Out-Null; $f = Join-Path $dir '.wbtest'; Set-Content $f 'x' -ErrorAction Stop; Remove-Item $f; return $true } catch { return $false }
}
if (-not $Root) {
    if ($cfg -and $cfg.root -and (Test-Writable $cfg.root)) { $Root = $cfg.root }
    elseif ((Test-Path 'D:\') -and (Test-Writable 'D:\RHTV工作台')) { $Root = 'D:\RHTV工作台' }
    else { $Root = Join-Path $H 'RHTV工作台' }
}
New-Item -ItemType Directory -Force $Root | Out-Null
# mm-packager 的工作目录变量：没设且默认路径不存在时，放到本地工作目录下
foreach ($v in @(
        @{ k = 'MM_WORK_ROOT'; def = 'F:\钟海明\2026'; sub = '工程' },
        @{ k = 'MM_UPLOAD_IN'; def = 'F:\钟海明\素材命名上传\输入'; sub = '投放上传\输入' },
        @{ k = 'MM_USER_SFX'; def = 'F:\钟海明\音效收集'; sub = '音效收集' })) {
    $cur = [Environment]::GetEnvironmentVariable($v.k, 'User')
    if ($cur -and (Test-Path $cur)) { continue }
    if (-not $cur -and (Test-Path $v.def)) { continue }
    $dir = Join-Path $Root $v.sub
    New-Item -ItemType Directory -Force $dir | Out-Null
    Set-UserEnv $v.k $dir
    Log "目录变量 $($v.k)" 'fixed' $dir
}
if ($PY -and (Test-Path $WBPY) -and (Test-Path $RHCLI)) {
    $acts = RH-Account
    if ($acts -contains 'canvas:edit') {
        $r = Run $PY @('-I', (Quote $WBPY), 'setup', '--designer', (Quote $Designer), '--root', (Quote $Root)) 300
        if ($r.code -eq 0) { Log '工作台配置' 'ok' "设计师 $Designer，本地目录 $Root" }
        else { Log '工作台配置' 'fail' 'wb setup 失败' $r.all }
    } else {
        Log '工作台配置' 'warn' "rhTV 还没登录，先记下设计师 $Designer、目录 $Root；登录后重新双击安装会自动完成"
    }
    $r = Run $PY @('-I', (Quote $WBPY), 'check') 120
    if ($r.code -eq 0) { Log '工作台自检' 'ok' 'wb check 通过' $r.out } else { Log '工作台自检' 'fail' 'wb check 没通过' $r.all }
} else {
    $miss = @(); if (-not $PY) { $miss += 'Python' }; if (-not (Test-Path $WBPY)) { $miss += "wb.py（$WBPY）" }; if (-not (Test-Path $RHCLI)) { $miss += 'rhTV 客户端' }
    Log '工作台配置' 'fail' ('缺 ' + ($miss -join '、') + '，见上面的失败项')
}

# mm-packager 环境自检（字体/模型/浏览器/ElevenLabs）——不加 -I，用户目录下的包也算
$mmchk = Join-Path $SKDST 'mm-packager\scripts\check_env.py'
if ($PY -and (Test-Path $mmchk)) {
    $r = Run $PY @((Quote $mmchk)) 300
    if ($r.code -eq 0) { Log '包装环境自检' 'ok' 'mm-packager check_env 全部必需项通过' $r.out }
    else { Log '包装环境自检' 'warn' ('还缺：' + ((($r.out -split "`n") | Where-Object { $_ -like 'MISS*' }) -join '；')) $r.all }
}

# ---------------------------------------------------------------- 11. 汇总
$fails = @($RESULTS | Where-Object { $_.结果 -eq '[失败]' })
$warns = @($RESULTS | Where-Object { $_.结果 -eq '[注意]' })
Write-Host ''
Write-Host '=== 安装结果 ===' -ForegroundColor Magenta
$RESULTS | Format-Table -AutoSize | Out-String -Width 200 | Write-Host
$desk = if ($Sandbox) { $H } else { [Environment]::GetFolderPath('Desktop') }
$report = Join-Path $desk 'RHTV工作台-安装报告.txt'
@("RHTV 视频素材工作台 安装报告  $(Get-Date)", "电脑：$env:COMPUTERNAME  用户：$env:USERNAME  安装包：$PKGVER", '',
    ($RESULTS | Format-Table -AutoSize | Out-String -Width 200), '',
    "已链接的 Agent 平台：$($linked -join '、')", "详细日志：$LOGTXT",
    '有问题时：在 Agent 里说「导出工作台日志」，或运行  python "' + $WBPY + '" report ，把桌面上的 zip 发给维护者。') |
    Set-Content -Path $report -Encoding UTF8
if ($fails.Count -eq 0) {
    Write-Host '全部完成。' -ForegroundColor Green
    Write-Host '请先关掉所有已经打开的 Agent / 终端（Claude Code、Codex、VS Code、Cursor 等）再重新打开，新设置才会生效。' -ForegroundColor Cyan
    Write-Host "然后在任意 Agent（$($linked -join '、')）里说「新建工程 261110-JP-名称」即可开始。" -ForegroundColor Green
    if ($warns.Count) { Write-Host "有 $($warns.Count) 项注意，见上表（不影响主流程）。" -ForegroundColor Yellow }
} else {
    Write-Host "有 $($fails.Count) 项失败，见上表。按提示处理后重新双击安装即可（会自动跳过已完成的）。" -ForegroundColor Red
}
Write-Host "安装报告：$report"
Log '结束' 'info' "失败 $($fails.Count) 项，注意 $($warns.Count) 项"
if (-not $NoPause) { Read-Host '按回车关闭' | Out-Null }
if ($fails.Count) { exit 2 }
