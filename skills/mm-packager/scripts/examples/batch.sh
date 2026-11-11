# 多版本一键出片示例（来自五音梗·毒舌講座迭代，旧版案例；只当写法参考，说明见同目录 README.md）
# 目录和命名按 rules/工程交付.md。本脚本和 gen.py、to_timeline.mjs 一起放在 $P/脚本/。
# 用法：P=<工程目录> SK=<Skill 目录> ROLE=<角色名> bash batch.sh 版本N [draft|final]
# 可选：NAME=<工程名>（默认 = 工程目录名去掉日期前缀）；ROLE 默认用版本号；SK 默认由本脚本位置推出（只在 scripts/examples 里直接运行时有效）。
VER="$1"; KIND="${2:-draft}"
case "$VER" in 版本[0-9]*) ;; *) echo "用法：bash batch.sh 版本N [draft|final]"; exit 1 ;; esac
N="${VER#版本}"
D="${P:?先设置 P=<工程目录>}"; ROLE="${ROLE:-$VER}"
NAME="${NAME:-$(basename "$D" | sed -E 's/^[0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日//')}"
SK="${SK:-$(cd "$(dirname "$0")/../.." && pwd)}"; M="$SK/modules/app-ui/appui.py"
cd "$D" || exit 1
# 源视频 素材/视频_N.mp4 → 放大到 1080
[ -f "素材/视频_${N}_1080.mp4" ] || ffmpeg -nostdin -y -v error -i "素材/视频_${N}.mp4" -vf "scale=1080:1920:flags=lanczos,unsharp=5:5:0.6" -c:v libx264 -crf 16 -preset slow -c:a aac -b:a 192k "素材/视频_${N}_1080.mp4"
# 每个版本独立抽帧
FR="工程素材/抽帧_${VER}"; mkdir -p "$FR"
ls "$FR"/*.jpg >/dev/null 2>&1 || ffmpeg -nostdin -y -v error -i "素材/视频_${N}_1080.mp4" -vf fps=24 -q:v 2 "$FR/%04d.jpg"
# 产品 UI 配置按版本隔离：没有本版配置时，从 版本1 复制一份，抽帧路径换成本版
cd 包装素材_产品UI || exit 1
VER="$VER" python - <<'PY'
import os, re
V = os.environ['VER']
for n in ('swipe', 'chat'):
    dst, src = f'{n}_{V}.json', f'{n}_版本1.json'
    if os.path.exists(dst) or not os.path.exists(src): continue
    s = open(src, encoding='utf-8').read()
    open(dst, 'w', encoding='utf-8').write(re.sub(r'工程素材/抽帧_版本\d+/', f'工程素材/抽帧_{V}/', s))
PY
python "$M" render --config "swipe_${VER}.json" --out "产品UI-划卡_${VER}.mp4" >/dev/null 2>&1
python "$M" render --config "chat_${VER}.json" --out "产品UI-聊天_${VER}.mp4" >/dev/null 2>&1
# 图层（写到 包装素材_版本N/）→ timeline_版本N.json → 出片
cd "$D/脚本" && VER="$VER" P="$D" PYTHONIOENCODING=utf-8 python gen.py 2>&1 | tail -1 && VER="$VER" P="$D" node to_timeline.mjs 2>&1 | tail -1 || exit 1
TL="$D/timeline_${VER}.json"; mkdir -p "$D/导出"
if [ "$KIND" = final ]; then
  mkdir -p "$D/成品"; python "$SK/scripts/render.py" "$TL" --out "$D/成品/${NAME}_${ROLE}.mp4" && echo "FINAL 成品/${NAME}_${ROLE}.mp4"
else
  V=1; while [ -f "$D/导出/${NAME}_预览v${V}_${ROLE}.mp4" ]; do V=$((V+1)); done
  python "$SK/scripts/render.py" "$TL" --draft --out "$D/导出/${NAME}_预览v${V}_${ROLE}.mp4" && echo "OUT 预览v$V"
fi
