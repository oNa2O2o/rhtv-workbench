"""mm-packager 脚本公共库（工程 gen.py、模块脚本共用）。

用法：工程脚本里先 `sys.path.insert(0, f"{SK}/scripts")`，再按需导入子模块（本文件不预先导入任何子模块，缺依赖的子模块不影响别的）：
- mmkit.timewarp：多版本时间映射 TimeWarp(cfg, canon) → .TW(t) / .vsrc(t) / .warp(clips, audio, end, src_video)
- mmkit.heavy：重任务锁 heavy_lock(name, min_free_gb, poll)（放大、ASR、全片渲染排队，可用内存不够就等）
- mmkit.audio：音频工具（duck_points 等）
- mmkit.layers：图层公共函数（add_img / kf / snap / add_audio / us / pointer_path 等）
"""
