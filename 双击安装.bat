@echo off
chcp 65001 >nul
title RHTV 视频素材工作台 一键安装
if not exist "%~dp0install.ps1" (
  echo 请先把整个压缩包解压到一个文件夹，再双击里面的「双击安装.bat」。
  pause
  exit /b 1
)
if not exist "%~dp0vendor" (
  echo 安装包不完整（缺 vendor 文件夹），请重新解压整个压缩包。
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
if errorlevel 1 pause
