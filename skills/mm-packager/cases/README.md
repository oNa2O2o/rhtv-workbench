# 案例索引

每个案例只记本片参数和修改记录：参考案例的每条修改标「已进规则（文件）」或「只属本片」；旧版案例标「旧版·不作参考」。数值、文案、路径不照搬（每片素材、脸的位置都不一样），规则以 `rules/` 为准。写法和目录命名见 SKILL.md；下面这些已有目录没有版式段，不改名，版式看本表和各 README 顶部。

## 参考案例
| 案例 | 版式 | 看什么 | 脚本 |
|---|---|---|---|
| [2026-11-12-JP-B-病娇女教师](2026-11-12-JP-B-病娇女教师/README.md) | B | 多版本时间映射（版本配置.json + timewarp）、三卡片尾板 endcard3、用户音效优先 + ElevenLabs 补缺、BGM 断档续接 | gen.py、audio_gen.py、audio_gen2.py、prep_version.py、make_config.py、endcard3.py 原样存档，不能直接运行；已通用化成 scripts/mmkit/timewarp.py、prep.py、align_subs.py、modules/endcard3 |
| [2026-11-05-JP-追放された女騎士](2026-11-05-JP-追放された女騎士/README.md) | B | 负向数值条、两首 BGM + 整句平滑闪避、划卡卡面取原始素材 | 本目录无脚本；原工程 mix_bgm.py 是整句平滑闪避的实现 |
| [2026-11-05-JP-上の階のスポーツ女子](2026-11-05-JP-上の階のスポーツ女子/README.md) | B | 数值条出镜后才出现、多版本（ver_cfg + build_ver） | 本目录无脚本；原工程 patch.mjs 不能运行 |
| [2026-11-02-JP-命令模式保镖](2026-11-02-JP-命令模式保镖/README.md) | B | 尺寸验收值、命令输入框、逐帧跟头 | 本目录无脚本；原工程 patch.mjs 不能运行 |
| [2026-11-04-JP-签售会POV-网感剪辑](2026-11-04-JP-签售会POV-网感剪辑/README.md) | C | 语气词钩子、快切口播大字、网感尾板 | render_v2 / render_end_v2 / make_ui_cfg 可复用（先改路径、补原工程依赖）；assemble_v3 的侧链混音已作废 |

## 旧版·不作参考
编辑器或旧模板时代的片子，做法可能已被推翻；里面的 `patch*.mjs` 往已停用的编辑器 API 写工程，都不能运行；本地合成 BGM/音效的脚本已作废。

| 案例 | 原版式 | 还能用的东西 |
|---|---|---|
| [2026-10-16-JP-女仆-液态玻璃手机](2026-10-16-JP-女仆-液态玻璃手机/README.md) | A 模板 + 编辑器 lgx | 无 |
| [2026-10-19-JP-偶像逆攻略男性向](2026-10-19-JP-偶像逆攻略男性向/README.md) | 无选项 | 无 |
| [2026-10-20-JP-伪人义妹敲门-监控HUD](2026-10-20-JP-伪人义妹敲门-监控HUD/README.md) | 编辑器时代 B | face_track.py（动漫人脸检测，路径写死） |
| [2026-10-21-JP-贞操逆转上门讨债-香槟简约](2026-10-21-JP-贞操逆转上门讨债-香槟简约/README.md) | 编辑器时代 B | analyze_ver.py（多版本分析：抽帧、跟脸、ASR、黑场、能量；路径写死） |
| [2026-10-26-JP-1年ぶりの彼-深夜琥珀](2026-10-26-JP-1年ぶりの彼-深夜琥珀/README.md) | 编辑器时代 B | music.py（ElevenLabs BGM） |
| [2026-10-26-JP-猫娘报恩-琥珀橘](2026-10-26-JP-猫娘报恩-琥珀橘/README.md) | 编辑器时代 B | matte.py（BiRefNet_lite CUDA fp16 蒙版）、face_track.py |
| [2026-11-05-JP-五音梗-毒舌講座-迭代](2026-11-05-JP-五音梗-毒舌講座-迭代/README.md) | 真人 POV 无选项 | to_timeline.mjs、batch.sh 已移到 `scripts/examples/`（多版本写法示例） |

## 案例里写的路径
`$WORK_ROOT`（工程根目录）、`$UPLOAD_IN`（投放目录）、`$USER_SFX`（用户音效库）等变量的含义和本机值见 `reference/环境.md`。案例脚本里的路径仍是原工程绝对路径，复用前改成 `$P`。
