# 重新打开 Figma 登录窗口：先关掉旧的自动化窗口/进程（配置目录被占用会打不开），再启动 login
$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*figma_ref*' -or $_.CommandLine -like '*mmw-figma-profile*' }
foreach ($p in $procs) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep 2
Start-Process python -ArgumentList 'figma_ref.py','login' -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
Start-Sleep 8
$n = (Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*mmw-figma-profile*' }).Count
"killed=$($procs.Count) edge_now=$n"
