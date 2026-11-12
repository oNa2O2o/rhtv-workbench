# scripts/examples：多版本出片示例

来自 `cases/2026-11-05-JP-五音梗-毒舌講座-迭代/`（旧版案例，设计不作参考）。只学「一个版本一键出片」的结构，参数按本片重写。目录和命名已按 `rules/工程交付.md` 改好。各版本时间怎么迁移不照这里，按 `rules/工程交付.md`「多版本」（版本配置.json + `scripts/mmkit/timewarp.py`），实例见 `cases/2026-11-12-JP-B-病娇女教师/gen.py`。

## 文件
| 文件 | 作用 |
|---|---|
| `to_timeline.mjs` | 读 `$P/包装素材_版本N/layers.json`（gen.py 输出）和环境变量 `VER=版本N`，写 `$P/timeline_版本N.json`：正片视频 + 同源原声、产品 UI mp4（`产品UI-划卡_版本N.mp4` / `产品UI-聊天_版本N.mp4`）、图层、BGM 分段闪避、口播、音效（自动分车道）。不写 `out`，出片路径由 batch.sh 给。timeline 格式见 `scripts/render.py` 文件头 |
| `batch.sh` | 一个版本一键出片：`素材/视频_N.mp4` 放大到 1080 → 抽帧到 `工程素材/抽帧_版本N/` → 产品 UI 配置（没有本版的就从 `swipe_版本1.json` / `chat_版本1.json` 复制并换抽帧路径）并渲染 → `gen.py` → `to_timeline.mjs` → `render.py`（draft 出预览，final 出成品） |

## 用法
1. 把两个文件复制到 `$P/脚本/`（和本片 `gen.py` 放一起）。工程里要有 `素材/视频_N.mp4`，`包装素材_产品UI/` 里至少有 `swipe_版本1.json`、`chat_版本1.json`。
2. 运行：
   ```bash
   P="$WORK_ROOT/<工程目录>" SK="$SK" ROLE=<角色名> bash "$P/脚本/batch.sh" 版本2 draft   # 预览 导出/<工程名>_预览vN_<角色名>.mp4
   P="$WORK_ROOT/<工程目录>" SK="$SK" ROLE=<角色名> bash "$P/脚本/batch.sh" 版本2 final   # 成品 成品/<工程名>_<角色名>.mp4
   ```
   复制到工程后脚本位置变了，`SK` 要显式传。
3. `gen.py` 只按版本1 的规范时间写，不存各版本时间表；各版本差异放 `工程素材/抽帧_版本N/版本配置.json`，build() 最后用 `scripts/mmkit/timewarp.py` 映射到本版本（见 `rules/工程交付.md`「多版本」）；按环境变量 `VER` 切换，图层写到 `$P/包装素材_版本N/`。用本目录的 to_timeline.mjs 时，`layers.json` 需要的字段：`tracks`、`layers[{file, ext, track, name, start, dur, ax, ay, k}]`、`shake`、`push0/end0/end1`、`sw0/swd`、`ch0/chd`、`ec0`、`vos`、`sfx`。原案例的 gen.py 仍是旧目录（`包装素材v1`、`VER=_2`），照抄时按上面改。

## 复用前要改
- BGM 闪避：`lvl()` 里固定的 .11/.28 和 0.06 s 淡变是该片旧写法。现行做法见 `rules/通用.md`（整句平滑压低，不写死音量），重写这一段。
- `SPEECH` 区间、`VOF` 口播时长、`bgm_beat5.mp3` 文件名、推近手机的缩放/位移都是该片的值。
- 多版本要重做哪些、沿用哪些，见 `rules/工程交付.md`。
