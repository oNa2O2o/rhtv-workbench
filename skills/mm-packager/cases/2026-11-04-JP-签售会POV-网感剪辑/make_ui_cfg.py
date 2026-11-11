# -*- coding: utf-8 -*-
"""生成划卡/聊天 config。用法: python -I make_ui_cfg.py HERO CARD1 CARD2 outdir"""
import sys, json
P = "F:/钟海明/2026/2026年11月4日MM-JP-女性向-签售会POV"
CH = json.load(open(f"{P}/工作/specs/chars.json", encoding="utf-8"))
img = lambda k: f"{P}/工作/up/{k}.jpg"
hero, c1, c2, out = sys.argv[1:5]

def card(k):
    c = CH[k]
    return {"image": img(c["frame"]), "focusY": c["focusY"], "name": c["name"], "tags": c["tags"], "intro": c["intro"]}

h = CH[hero]
swipe = {"template": "swipe", "cards": [card(c1), card(c2)],
         "hero": {**card(hero), "story": h["story"], "gallery": [img(x) for x in h["gallery"]]},
         "times": {"swipes": [2.15, 2.85], "swipeDur": 0.6, "tapAt": 3.75, "scrollAt": 4.6, "scrollDur": 1.4, "chatTapAt": 6.7, "end": 7.25}}
chat = {"template": "chat", "bg": {"image": img(h["frame"]), "focusY": 0.3, "blur": 0, "dim": 0.1},
        "name": h["name"], "status": "オンライン", "placeholder": "メッセージを入力",
        "messages": h.get("chat") or [
            {"from": "char", "t": 0.45, "typing": 0.3, "text": "来てくれてありがとう。"},
            {"from": "user", "t": 1.45, "typeDur": 0.6, "text": "会えて幸せ…！"},
            {"from": "char", "t": 2.25, "typing": 0.35, "text": "次は二人きりで、ね？"}],
        "duration": 3.1}
json.dump(swipe, open(f"{out}/swipe_{hero}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(chat, open(f"{out}/chat_{hero}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok")
