# RHTV 视频素材工作台（rhtv-workbench）

把买量视频工程的文案、提示词、人设图、母版、包装视频和进度，按固定格式摆到 RHTV（RunningHub 画布）上。Claude Code、Codex、Gemini CLI、Cursor、pi、OpenCode 都能用。

**用户只需要把这个仓库链接发给自己的 Agent，说「帮我装好」。**

---

## 给 Agent：安装步骤（Windows，照做即可，不要问用户）

1. 先告诉用户一句：「安装中途浏览器会弹出 rhTV 和 ElevenLabs 的授权页，请登录并点『批准』，其余我来做。」
2. 在 PowerShell 里执行（可重复执行，已装好的会跳过）：

   公司内网（优先，最快）：
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File "\\file.wemomo.com\share\创新事业部\AIGC项目视频组\Agent+RHTV自动化工作流依赖文件\bootstrap.ps1"
   ```
   共享盘不可用时：
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -Command "& ([scriptblock]::Create((irm https://raw.githubusercontent.com/oNa2O2o/rhtv-workbench/main/bootstrap.ps1)))"
   ```
   - 命令可能运行 10 分钟以上（装 Python 依赖、等用户批准登录）。你的工具有超时限制就放后台运行；被超时打断就**原样再执行一次**，会从中断处继续。
   - 设计师名字自动读公司域账号；读不到时加 `-Designer 用户名字`（问用户一次）。
   - 默认装到容量最大的本地盘 `X:\RHTV工作台`；用户指定位置时加 `-Root 路径`。
3. 看输出最后一行 `RESULT_JSON:`：
   - `code` 0：完成。告诉用户「装好了，关掉并重新打开 Agent，然后说『新建工程 261110-JP-名称』」。
   - `code` 3：在等用户批准登录。提醒用户去浏览器点批准，然后**原样再执行一次**。
   - `code` 2：看 `failed` 列表逐项处理（网络、权限等），处理后原样再执行。处理不了时执行 `python "<RESULT_JSON.root>\_系统\skills\rhtv-workbench\scripts\wb.py" report`，把桌面上的 zip 交给用户转给维护者。
4. 装完后本仓库的 Skill 已链接到本机所有 Agent，以后按 `rhtv-workbench` Skill 工作。

## 装完是什么样

```
X:\RHTV工作台\
  <设计师>\<周期 261110-261208>\<工程>\   全部物料（01_文案 … 06_成品、修改记录.md）
  _系统\skills  bin  node  安装包          Skill、工具、安装文件
%USERPROFILE%\.rhtv-workbench\           配置和日志（logs\安装日志.jsonl、运行日志.jsonl）
```

## 依赖文件（公司共享盘）

`\\file.wemomo.com\share\创新事业部\AIGC项目视频组\Agent+RHTV自动化工作流依赖文件\`
- `bootstrap.ps1`、`rhtv-workbench\`：最新安装包
- `vendor\`：rhTV 客户端、ffmpeg/ffprobe、ElevenLabs CLI、Python 3.11.9、Node 24.22.1
- `wheels-cp311-win_amd64\`：Python 依赖离线包

共享盘连不上时，`bootstrap.ps1` 会从本仓库 Release 下载 `rhtv-workbench-vendor.zip`。
