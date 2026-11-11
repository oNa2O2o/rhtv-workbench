import json,re
A="F:/钟海明/2026/2026年10月16日MM-JP-女仆/工作区/audio/"
F="2026年10月16日MM-JP-女仆"
def split(text):
    toks=[];i=0
    while i<len(text):
        c=text[i]; j=i+1
        while j<len(text) and text[j] in 'ゃゅょっー〜。、？！っゃゅょ ' : j+=1
        toks.append(text[i:j]); i=j
    return toks
def words(text,a,b):
    toks=split(text); w=[0.6 if t[0] in '◯' else 1.0 for t in toks]
    tot=sum(w); t=a; out=[]
    for k,x in zip(toks,w):
        d=(b-a)*x/tot; out.append({"word":k,"start":round(t,3),"end":round(t+d,3)}); t+=d
    return out
L=[("◯◯◯もしたにゃ〜",0.07,1.11,0.0,1.5,0),
("お母さんって呼んでたくせに",1.56,2.91,1.5,3.3,0),
("他に彼女できたの",3.42,4.51,3.3,5.1,0),
("じゃあ 私はなんなのにゃ〜",5.32,6.95,5.1,7.06,0),
("私はあんたのお母さんってわけ",8.6,10.24,7.4,10.45,1),
("キモい",11.15,11.56,10.45,11.9,1),
("マジ最低",12.07,12.78,11.9,12.9,1)]
bub=[{"template":"bubble/lgx","start":s,"end":e,"text":t,"words":words(t,a,b),"role":"character","speaker":"メイド","avatar":"F:/钟海明/2026/2026年10月16日MM-JP-女仆/工作区/avatar.png"} for t,a,b,s,e,h in L]
spec={"folder":F,"app":"F:/钟海明/2026/2026年10月10日MM-编辑器重构/app",
"copyFile":"F:/钟海明/2026/2026年10月16日MM-JP-女仆/工作区/全量文案.md",
"approvedUiStrings":["パァン","メイド","120万","チャット","時間切れ","説得失敗","リトライ"],
"video":{"mediaId":"mmvgdkfz42j2u3","in":0,"end":12.9,"fit":"blur-pad","holds":[{"from":7.07,"to":7.4,"frame":7.04}]},
"title":{"template":"title/lgxsplit","text":"MiraiMindでメイドがブチギレ","duration":2.0},
"bubbles":bub,
"choices":[{"template":"choice/lgx","at":7.07,"duration":4.4,"question":"なんて返す","options":["① 言い訳する","② 告る","③ はぐらかす"],"pick":0},
{"template":"choice/lgx","at":12.9,"duration":8.0,"question":"キレちゃった どうする","options":["① 謝る","② 引き止める"],"pick":-1}],
"meter":{"template":"meter/lglass","start":0.4,"keyframes":[{"at":0.5,"value":0},{"at":1.2,"value":15},{"at":2.98,"value":30},{"at":4.58,"value":45},{"at":6.98,"value":60},{"at":9.0,"value":100}],"stages":[{},{},{},{}],"lockedStage":2,"params":{"label":"失望度"}},
"end":{"template":"end/lgx","duration":5.8,"title":"恋人のつもりが お母さん扱い","cta":"ダウンロードして続きを見る","characterName":"嫉妬メイドをなだめる","chatCount":"120万","chatLabel":"チャット","gallery":[12.2,5.6,2.2],"backdrop":2.2},
"bgm":{"file":"F:/钟海明/2026/2026年10月16日MM-JP-女仆/工作区/audio/bgm_maid_drama5.wav","volume":0.2,"fadeOut":1.0},
"sfx":[{"file":A+n,"outAt":t,"volume":v} for n,t,v in [("censor_pi.wav",0.07,1.0),("error_buzz.wav",11.467,0.85),("slap_combo2.wav",14.7,1.0),("shatter_real.wav",17.15,0.75)]]}
json.dump(spec,open('v5-spec5.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
