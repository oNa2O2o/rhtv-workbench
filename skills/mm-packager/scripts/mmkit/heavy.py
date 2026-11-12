"""重任务锁：放大、ASR、全片渲染这类吃内存的步骤自动排队，可用内存不够就等；其余步骤可放心并行。

    from mmkit.heavy import heavy_lock
    with heavy_lock("asr"):                 # 同名的任务一次只跑一个（跨进程），拿到锁后可用内存 < 2 GB 就等
        ...
    with heavy_lock("elevenlabs", min_free_gb=0):   # 只串行，不看内存

- 锁是按 name 的文件锁（~/.mm-packager/locks/<name>.lock），进程退出（包括崩溃）自动释放，不会留死锁。
- 同一进程里嵌套拿同名锁直接通过（不自锁）。
- 可用内存：Windows 取 min(可用物理内存, 提交余量)（本机提交内存常年 28/34 GB，提交满了照样分配失败）；其他系统取 MemAvailable。读不到就不等。
- 等的时候往 stderr 打印在等什么（约每分钟一次）。
"""
import contextlib, os, sys, time

LOCK_DIR = os.path.join(os.path.expanduser("~"), ".mm-packager", "locks")
_held = {}


def _log(msg):
    print(f"[heavy] {msg}", file=sys.stderr, flush=True)


def free_gb():
    """返回 (可用 GB, 说明)；读不到返回 (None, 原因)。"""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class MS(ctypes.Structure):
            _fields_ = [("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        ms = MS(); ms.dwLength = ctypes.sizeof(MS)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms)):
            return None, "GlobalMemoryStatusEx 失败"
        g = 1024 ** 3
        phys, commit = ms.ullAvailPhys / g, ms.ullAvailPageFile / g
        used = (ms.ullTotalPageFile - ms.ullAvailPageFile) / g
        return min(phys, commit), f"可用物理 {phys:.1f} GB，提交 {used:.1f}/{ms.ullTotalPageFile / g:.1f} GB（余 {commit:.1f} GB）"
    try:
        with open("/proc/meminfo") as f:
            kv = {l.split(":")[0]: l.split()[1] for l in f}
        v = int(kv["MemAvailable"]) / 1024 ** 2
        return v, f"MemAvailable {v:.1f} GB"
    except Exception:
        pass
    try:
        import psutil
        v = psutil.virtual_memory().available / 1024 ** 3
        return v, f"可用 {v:.1f} GB"
    except Exception as e:
        return None, f"读不到可用内存（{e.__class__.__name__}）"


def _try_lock(f):
    try:
        if os.name == "nt":
            import msvcrt
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def _unlock(f):
    try:
        if os.name == "nt":
            import msvcrt
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass


def _owner(name):
    try:
        with open(os.path.join(LOCK_DIR, f"{name}.owner"), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return "持有者不明"


@contextlib.contextmanager
def heavy_lock(name="heavy", min_free_gb=2.0, poll=5):   # 用户定 2GB：本机可用内存常年 2.5–2.9 GB，3GB 会一直排队
    if _held.get(name):
        _held[name] += 1
        try: yield
        finally: _held[name] -= 1
        return
    os.makedirs(LOCK_DIR, exist_ok=True)
    f = open(os.path.join(LOCK_DIR, f"{name}.lock"), "a+b")
    try:
        t0, said = time.time(), -1e9
        while not _try_lock(f):
            if time.time() - said >= 60:
                _log(f"等「{name}」锁：另一个 {name} 任务在跑（{_owner(name)}），已等 {time.time() - t0:.0f} s")
                said = time.time()
            time.sleep(poll)
        try:
            with open(os.path.join(LOCK_DIR, f"{name}.owner"), "w", encoding="utf-8") as o:
                o.write(f"pid {os.getpid()}，{time.strftime('%H:%M:%S')} 起，{' '.join(os.path.basename(a) for a in sys.argv[:2])}")
        except OSError:
            pass
        if min_free_gb and min_free_gb > 0:
            t1, said = time.time(), -1e9
            while True:
                v, info = free_gb()
                if v is None or v >= min_free_gb: break
                if time.time() - said >= 60:
                    _log(f"「{name}」要 ≥ {min_free_gb:g} GB 可用内存，现在 {info}；等别的任务释放内存（已等 {time.time() - t1:.0f} s）")
                    said = time.time()
                time.sleep(poll)
        _held[name] = 1
        try:
            yield
        finally:
            _held.pop(name, None)
            _unlock(f)
    finally:
        f.close()
