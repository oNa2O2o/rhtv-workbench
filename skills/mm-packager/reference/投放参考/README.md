# 投放参考（转化承接 / 片尾）

## 样式索引（用户点名样式时先查这里，两个以上都对得上就按 rules/通用.md「沟通与改版」出候选静帧问一句）
| 用户说法 | 参考 | 模块 |
|---|---|---|
| 三卡片尾板 | 本目录 `三卡片尾板_参考.webp`（用户 2026-11-12 给的参考图：顶部 Logo、三张角色卡扇形、中间本片角色金边高亮、金橙渐变下载按钮） | `modules/endcard3`（JP 默认片尾） |
| 主卡长廊尾板（3D 卡片一镜到底，17.3 s） | — | `modules/jp-endcard`（用户点名才用） |

## 产品 UI：Figma 设计稿
- 文件：Miraimind - 1.0-4.0版本
- 链接：https://www.figma.com/design/5l7Y1FahFUy1IB1tS7WR2G/Miraimind---1.0-4.0%E7%89%88%E6%9C%AC?node-id=11459-43295&p=f&t=D3Y9BYqZq1ESUedY-0
- 抓取：`python $SK/scripts/figma_ref.py shot "<链接>" <输出.png>`（独立 Edge 配置 `FIGMA_PROFILE`，值见 `reference/环境.md`）
- 输出 `NOT_LOGGED_IN` / 登录过期 → `powershell -NoProfile -ExecutionPolicy Bypass -File $SK/scripts/figma_login.ps1`（先关旧窗口再弹登录窗口），让用户在弹窗里登录。
- 抓下来的截图存 `$RES/投放参考/Figma/`，文件名写清楚是哪个界面；做片尾对话时照它的版式、配色、字体、气泡、输入框做（气泡字号按 `rules/通用.md`，B 的输入框等尺寸按 `rules/B-剧情选择.md`「版面」）。

## 商店页风格
- 来源：Google Play（JP）https://play.google.com/store/apps/details?id=com.immomo.miraimind&hl=ja
- 抓取：`python $SK/scripts/store_ref.py "<商店链接>" <输出目录>`（整页截图 + 商店截图原图 1080×1920）
- 已抓：`$RES/投放参考/商店页_GP_JP/`（`商店截图_01..05.png`，`_拼图.jpg` 一览，2026-10-30）
- 风格要点：待与 Figma 一起分析、用户审核后再写入。
