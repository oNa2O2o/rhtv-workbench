# RHTV 视频素材工作台（rhtv-workbench）

把买量视频工程的文案、提示词、人设图、母版、包装视频和进度，按固定格式摆到 RHTV（RunningHub 画布）上，任何 Agent（Claude Code、Codex、Gemini CLI、Cursor、pi、OpenCode）加载 Skill 即可使用。

## 下载安装（Windows）

1. 下载完整安装包：**[rhtv-workbench-installer.zip](https://github.com/oNa2O2o/rhtv-workbench/releases/latest/download/rhtv-workbench-installer.zip)**（约 144 MB，含离线依赖）
2. 解压整个压缩包。
3. 双击 `双击安装.bat`，输入你的名字，在浏览器里登录 rhTV / ElevenLabs 并点「批准」。其余全部自动完成。
4. 装完关掉已打开的 Agent 再重新打开，说「新建工程 261110-JP-名称」开始。

> 直接 clone 本仓库缺少 `vendor/` 里的离线依赖，请用上面的 Release 安装包。

## 出问题

- 重新双击安装即可，已完成的会跳过，坏的会修。
- 在 Agent 里说「导出工作台日志」，把桌面上生成的 zip 发给维护者。日志在 `%USERPROFILE%\.rhtv-workbench\logs\`。

## 内容

- `install.ps1` / `双击安装.bat`：一键安装器（日志、自动修复、各 Agent 平台链接）
- `skills/`：rhtv-workbench、mm-packager、2.5prompt、shortdrama-copy、xmp-upload
- Release 附件额外包含 `vendor/`：rhTV 客户端 0.7.1、ffmpeg/ffprobe、ElevenLabs CLI、Python 3.11.9、Node 24.22.1 安装文件
