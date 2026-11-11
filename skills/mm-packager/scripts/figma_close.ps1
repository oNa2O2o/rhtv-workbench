# 正常关闭 Figma 登录窗口（不强杀，保证登录 cookie 落盘），让 shot 能用同一配置目录
$edge = Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'msedge.exe' -and $_.CommandLine -like '*mmw-figma-profile*' -and $_.CommandLine -notlike '*--type=*' }
foreach ($e in $edge) { taskkill /PID $e.ProcessId | Out-Null }
Start-Sleep 6
$left = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*mmw-figma-profile*' -or $_.CommandLine -like '*figma_ref.py*login*' }
foreach ($p in $left) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
"closed_main=$($edge.Count) forced_left=$($left.Count)"
