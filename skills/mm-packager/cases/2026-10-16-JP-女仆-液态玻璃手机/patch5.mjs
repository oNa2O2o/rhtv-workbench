const U='http://localhost:4400/api/projects/'+encodeURIComponent('2026年10月16日MM-JP-女仆');
const r=await (await fetch(U)).json(); const p=r.project; const rev=r.revision??p.revision;
const near=(a,b)=>Math.abs(a-b)<0.05;
const SL=17.74, SHIFT=2.8, CJ=14.267;
// 1) title owns 0-2s: push everything else right by 2s
for(const c of p.clips){ if(c.module?.type==='title'){ c.start=0; c.duration=2.8; Object.assign(c.module.params||(c.module.params={}),{mediaId:'mmvgdkfz42j2u3',topTime:2.2,bottomTime:9.5,bottomShift:780,topShift:-60,tilt:7,split:'で',logo:true}); continue; }
  c.start=+(c.start+SHIFT).toFixed(4);
}
const bg=p.clips.find(c=>c.type==='audio'&&c.trackId==='A2'); if(bg){ bg.start=0; bg.in=0; bg.duration=+(Math.max(...p.clips.map(c=>c.start+c.duration))).toFixed(4); }
const kf=(a)=>a.map(([t,v])=>({t,v,ease:'linear'}));
for(const c of p.clips){
 const m=c.module; if(!m) continue; const P=m.params=m.params||{};
 for(const k of ['halo','crackAt','shakeAt','cracked']) delete P[k];
 if(m.type==='bubble'){
  const t=m.data.text;
  if(near(c.start,14.6)){ // close the gap under the freeze so the phone never blinks out
    const d=c.start-14.267; c.start=14.267; c.duration+=d; m.data.words=m.data.words.map(w=>({...w,start:+(w.start+d).toFixed(3),end:+(w.end+d).toFixed(3)}));
  }
  if(t.startsWith('私はあんた')||t==='キモい。'||t==='マジ最低。') P.tone='hot';
  if(t==='キモい。') P.slapAt=SL;
  if(t==='マジ最低。') P.shatterAt=0.85;
 }
 if(m.type==='choice'&&near(c.start,9.867)) P.selectAt=2.6;
 if(m.type==='choice'&&near(c.start,20.1)) Object.assign(P,{tone:'hot',timeout:true,phoneExit:false,timeoutText:'時間切れ',failText:'説得失敗',retryText:'リトライ'});
 if(m.type==='end'){ m.data.backdrop={mediaId:'mmvgdkfz42j2u3',time:12.87}; m.params={...(m.params||{}),rewind:true,rewindTo:2.2}; }
 if(m.type==='meter'){
  const L=SL-c.start; P.overflowAt=L; P.centerAt=+(CJ-c.start).toFixed(3); P.centerDur=1.3; P.grayAt=+(20.1+80/30-c.start).toFixed(3);
  m.data.keyframes=m.data.keyframes.map(k=>k.value===100?{...k,t:+(CJ-c.start+0.35).toFixed(3)}:k);
  P.fx=[
   {type:'flicker',at:CJ-c.start,life:14},
   {type:'flash',at:L,color:'255,255,255',alpha:0.55},
   {type:'shock',at:L,x:540,y:620,max:1000},
   {type:'edge',at:L,color:'255,40,70',life:200},
   {type:'vignette',at:L,color:'120,0,20',alpha:50,life:200},
   {type:'onomato',at:L,text:'パァン',x:560,y:560,size:210,rot:-9,color:'#ff3b5c',life:30}
  ];
 }
}
const v=p.clips.find(c=>c.type==='video'&&c.start>14&&c.start<15);
const l=SL-v.start;
v.keyframes={x:kf([[0,0],[l,0],[l+.04,-42],[l+.1,30],[l+.18,-16],[l+.3,6],[l+.45,0]]),
 rotation:kf([[0,0],[l,0],[l+.04,-2.6],[l+.1,1.6],[l+.2,-.6],[l+.4,0]]),
 scale:kf([[0,1],[l,1],[l+.04,1.09],[l+.5,1]])};
const fz=p.clips.find(c=>c.type==='freeze'&&near(c.start,14.267));
if(fz) fz.keyframes={x:kf([[0,0],[.03,-34],[.07,30],[.11,-24],[.15,20],[.2,-12],[.26,8],[.33,-10]]),y:kf([[0,0],[.05,14],[.09,-12],[.14,9],[.2,-6],[.33,4]]),scale:kf([[0,1],[.03,1.06],[.33,1.03]])};
v.keyframes.x=kf([[0,-10],[.05,8],[.1,-5],[.16,3],[.25,0],[l,0],[l+.04,-42],[l+.1,30],[l+.18,-16],[l+.3,6],[l+.45,0]]);
v.keyframes.scale=kf([[0,1.03],[.3,1],[l,1],[l+.04,1.09],[l+.5,1]]);
const a=p.clips.find(c=>c.type==='audio'&&c.trackId==='A1'&&Math.abs(c.start-SHIFT)<0.01);
a.keyframes={volume:kf([[0,0],[0.52,0],[0.58,1]])};
const put=await fetch(U,{method:'PUT',headers:{'content-type':'application/json'},body:JSON.stringify({project:p,revision:rev})});
console.log(put.status,(await put.text()).slice(0,200));
