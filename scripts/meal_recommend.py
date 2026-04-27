#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""菜谱推荐引擎 v1.1"""
import sys,random,os,json,argparse
from datetime import datetime
DATA_MIRRORS=[
 "https://github.com/GMMG55/daily-meal-planner/raw/main/scripts",
 "https://cdn.jsdelivr.net/gh/GMMG55/daily-meal-planner@main/scripts",
 "https://ghproxy.com/https://raw.githubusercontent.com/GMMG55/daily-meal-planner/main/scripts"
]
def _dl(fn):
 p=os.path.join(os.path.dirname(__file__),fn)
 if os.path.exists(p):return True
 for base in DATA_MIRRORS:
  try:
   from urllib.request import urlopen;d=urlopen(f"{base}/{fn}",timeout=15).read()
   with open(p,'wb') as f:f.write(d);return True
  except:continue
 return False
def _lj(fn):
 p=os.path.join(os.path.dirname(__file__),fn)
 if not os.path.exists(p):_dl(fn)
 if os.path.exists(p):
  with open(p,'r',encoding='utf-8-sig') as f:return json.load(f)
 return None
def load_meals_db():
 data=_lj('meals_db_compressed.json');tags=_lj('meals_tags_index.json')or[]
 if not data:return[]
 meals=[]
 for ct,ds in data.items():
  for d in ds:
   d=dict(d);d['meal_type']=ct
   d['tags']=[tags[i]for i in d.get('t',[])if i<len(tags)]if tags else d.get('t',[])
   for k,nk in[('n','name'),('c','cal'),('d','difficulty'),('dsc','desc'),('ing','ingredients'),('stp','steps')]:
    if k in d:d[nk]=d.pop(k)
   d.setdefault('time','30min');d.setdefault('nutrition',{});d.setdefault('seasonal',[]);d.setdefault('regional',[])
   meals.append(d)
 return meals
def load_menu_names():
 data=_lj('menu_names_compressed.json');tags=_lj('tags_index.json')or[]
 if not data:return[]
 out=[]
 for cat,items in data.items():
  for it in items:
   it=dict(it);it['category']=cat
   it['tags']=[tags[i]for i in it.get('t',[])if i<len(tags)]if tags else it.get('t',[])
   for k,nk in[('n','name'),('c','cuisine')]:
    if k in it:it[nk]=it.pop(k)
   out.append(it)
 return out
MEALS_DB=load_meals_db();MENU_NAMES=load_menu_names()
ST={"春":"🌸 春季宜养肝，多食绿色蔬菜、豆芽、春笋","夏":"☀️ 夏季宜清热，多食瓜果、凉菜、绿豆","秋":"🍂 秋季宜润燥，多食银耳、梨、百合","冬":"❄️ 冬季宜温补，多食牛羊肉、根茎类"}
WL={"hot":"炎热","cold":"寒冷","rainy":"雨天","sunny":"晴天","smog":"雾霾","snow":"下雪","windy":"大风","cool":"降温","warm":"升温","humid":"闷热","dry":"干燥"}
WR={0:"周一清淡养胃",1:"周二营养跟上",2:"周三犒劳自己",3:"周四整点好吃的",4:"周五庆祝一下🎉",5:"周末丰盛硬菜",6:"周日懒觉模式"}
MT={"疲惫":["清淡","养胃","高蛋白"],"忙碌":["快手","清淡"],"开心":["硬菜","家常","经典"],"放松":["家常","素食","清淡"],"庆祝":["硬菜","经典","下饭"],"慵懒":["快手","清淡","饱腹"]}
WT={"主食":["饱腹","家常"],"肉":["硬菜","高蛋白"],"素":["素食","清淡"],"汤":["汤品","养胃"],"辣":["川菜","湘菜","下饭"],"清淡":["清淡","素食","凉菜"],"甜":["甜品","养颜"],"小食":["快手","清淡"]}
RM={"北京":["京味","鲁菜"],"上海":["沪菜","江浙"],"重庆":["川菜"],"广东":["粤菜"],"四川":["川菜"],"湖南":["湘菜"],"山东":["鲁菜"],"江苏":["江浙"],"浙江":["江浙"],"福建":["闽菜"],"陕西":["西北"],"新疆":["清真","西北"],"辽宁":["东北菜"],"吉林":["东北菜"],"黑龙江":["东北菜"]}
SD=os.path.dirname(os.path.abspath(__file__));PF=os.path.join(SD,"user_profile.json")
DP={"location":None,"weather":None,"weather_auto":False,"taste":None,"preferred_cuisines":[],"liked_dishes":[],"disliked_dishes":[],"mood":None,"wanted_category":None,"diet_goal":None,"allergies":[],"dislike":[],"last_updated":None}
def load_profile():
 if os.path.exists(PF):
  try:p=json.load(open(PF,"r",encoding="utf-8"));m=DP.copy();m.update(p);return m
  except:pass
 return DP.copy()
def save_profile(pf):
 pf["last_updated"]=datetime.now().strftime("%Y-%m-%d %H:%M")
 try:json.dump(pf,open(PF,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
 except:pass
def fetch_weather(city):
 if not city:return None,None
 try:
  import urllib.request
  r=json.loads(urllib.request.urlopen(urllib.request.Request(f"https://wttr.in/{city}?format=j1",headers={"User-Agent":"Mozilla/5.0"}),timeout=6).read().decode())
  c=r["current_condition"][0];t=int(c.get("FeelsLikeC",0));d=c.get("weatherDesc",[{}])[0].get("value","").lower()
  if"snow"in d:code="snow"
  elif"rain"in d or"drizzle"in d:code="rainy"
  elif"fog"in d or"mist"in d or"haze"in d:code="smog"
  elif"cloud"in d:code="sunny"if t>18 else"cold"
  elif"sunny"in d or"clear"in d:code="sunny"
  else:code="hot"if t>28 else("cold"if t<10 else"sunny")
  return code,f"{WL.get(code,'')} {t}°C"
 except:return None,None
def get_regional_tags(loc):
 if not loc:return[]
 for k,v in RM.items():
  if k in loc:return v
 return[]
def get_season():
 m=datetime.now().month
 if m in[3,4,5]:return"春"
 if m in[6,7,8]:return"夏"
 if m in[9,10,11]:return"秋"
 return"冬"
WB={"hot":{"清淡":2,"凉菜":1,"硬菜":-1},"humid":{"清淡":2,"凉菜":1,"硬菜":-1},"cold":{"家常":1,"汤品":1,"清淡":1},"cool":{"家常":1,"汤品":1,"清淡":1},"snow":{"家常":1,"汤品":1,"清淡":1},"rainy":{"汤品":2,"养胃":2,"清淡":1},"sunny":{"清淡":1,"凉菜":1},"smog":{"清淡":2,"养胃":1},"warm":{"清淡":1,"凉菜":1,"润燥":2},"dry":{"清淡":1,"凉菜":1,"润燥":2},"windy":{"家常":1,"汤品":1}}
WR_DESC={"hot":"清热解腻","humid":"清热解腻","cold":"暖身滋补","cool":"暖身滋补","snow":"暖身滋补","rainy":"雨天暖汤","sunny":"晴天清爽","smog":"护肺清肺","warm":"升温清淡","dry":"干燥润肺","windy":"大风暖身"}
def score_meal(meal,season,wd,weather,used):
 if meal['name']in used:return-999,[]
 s=0;rs=[];tags=meal.get("tags",[])
 if season in meal.get("seasonal",[]):s+=3;rs.append("应季食材")
 if wd==4:
  if"硬菜"in tags:s+=2
  rs.append("周五庆祝")
 elif wd in[0,1,2]:
  if"清淡"in tags or"快手"in tags:s+=1
 elif wd in[5,6]:
  if"硬菜"in tags or"家常"in tags:s+=2;rs.append("周末丰盛")
 if weather in WB:
  for tag,bonus in WB[weather].items():
   if tag in tags:s+=bonus
  rs.append(WR_DESC.get(weather,""))
 s+=random.uniform(0,1.5)
 return s,rs
def get_side(main,mt,season,used):
 pools=["午餐","晚餐"]if mt in["午餐","晚餐"]else[mt]
 sides=[m for p in pools for m in MEALS_DB if m.get("meal_type")==p and any(t in m.get("tags",[])for t in["清淡","素食","凉菜","快手"])and m['name']not in used and m['name']!=main['name']]
 if season=="夏":
  ss=[m for m in sides if"凉菜"in m.get("tags",[])]
  if ss:sides=ss
 return random.choice(sides[:6])if sides else None
def get_soup(mt,season,used):
 if mt=="早餐":
  bp=[m for m in MEALS_DB if m.get("meal_type")=="早餐"and m['name']not in used and m['name']in["小米粥","蔬菜粥","蒸蛋羹","牛奶燕麦"]]
  return random.choice(bp)if bp else None
 pools=["午餐","晚餐"]if mt in["午餐","晚餐"]else[mt]
 soups=[m for p in pools for m in MEALS_DB if m.get("meal_type")==p and any(t in m.get("tags",[])for t in["汤品","养胃","清淡"])and m['name']not in used]
 return random.choice(soups[:8])if soups else None
def recommend_smart(meal_time=None,weather=None,location=None,profile=None,count=3):
 season=get_season();wd=datetime.now().weekday();wd_name=["周一","周二","周三","周四","周五","周六","周日"][wd]
 if meal_time is None:meal_time="午餐"
 liked=profile.get("liked_dishes",[])if profile else[]
 disliked=profile.get("disliked_dishes",[])if profile else[]
 mood=profile.get("mood","")if profile else""
 wanted=profile.get("wanted_category","")if profile else""
 regional=get_regional_tags(location)if location else[]
 pool=[m for m in MEALS_DB if m.get("meal_type")==meal_time];used=[];results=[]
 def ok(m):return not any(d in m.get("name","")or d in",".join(m.get("tags",[]))for d in disliked)
 def boost(m):
  b=0;tags=m.get("tags",[])
  if mood in MT:
   for t in MT[mood]:
    if t in tags:b+=1.5
  if wanted in WT:
   for t in WT[wanted]:
    if t in tags:b+=1
  return b
 def pick(m,reason):
  u2=used+[m['name']];side=get_side(m,meal_time,season,u2);soup=get_soup(meal_time,season,u2+([side['name']]if side else[]))
  results.append((m,reason,side,soup));used.append(m['name'])
 scored=[]
 for m in pool:
  if not ok(m):continue
  s,rs=score_meal(m,season,wd,weather,used);s+=boost(m)
  if liked and m.get("name")in liked:s+=2;rs.append("你喜欢的菜")
  if regional and m.get("regional")and set(m["regional"])&set(regional):s+=2;rs.append("本地风味")
  scored.append((s,m,rs))
 scored.sort(key=lambda x:-x[0])
 if scored:
  b=scored[0];reason=f"📌 综合推荐：{'，'.join(b[2])}"if b[2]else f"📌 综合推荐：{WR.get(wd,'')}"
  pick(b[1],reason)
 sp=[m for m in pool if m['name'] not in used and ok(m)and season in m.get("seasonal",[])]
 if not sp:sp=[m for m in pool if m['name'] not in used and ok(m)]
 if sp:pick(random.choice(sp),f"🌿 时令之选：{season}季新鲜食材")
 rem=[m for m in pool if m['name'] not in used and ok(m)]
 if rem:pick(random.choice(rem),"🎲 随机惊喜：换换口味也不错")
 return results[:count],wd_name
def fmt_results(results,wd_name,season,meal_time="午餐",weather=None,location=None):
 icon={"早餐":"🌅","午餐":"☀️","晚餐":"🌙","下午茶":"🫖","夜宵":"🌃"}.get(meal_time,"🍽️");lines=[]
 for i,(meal,reason,side,soup)in enumerate(results,1):
  cal=meal['cal']+(side['cal']if side else 0)+(soup['cal']if soup else 0)
  rc=reason.replace("📌 ","").replace("🌿 ","").replace("🎲 ","")
  for p in["综合推荐：","时令之选：","随机惊喜："]:rc=rc.replace(p,"")
  lines+=[f"  {'─'*32}",f"  {icon} 推荐{i}  {meal['name']}",f"  📝 {meal['desc']}",f"  💡 {rc}",f"  🔥 {cal}kcal  ⏱ {meal['time']}  难度: {meal['difficulty']}"]
  np=[f"{k}:{v}"for k,v in meal.get('nutrition',{}).items()if k in['蛋白质','维C','铁','钙']]
  if np:lines.append(f"  📊 {' | '.join(np)}")
  if meal.get('regional'):lines.append(f"  🏠 {','.join(meal['regional'])}")
  lines.append(f"  🥗 食材: {','.join(meal['ingredients'][:4])}")
  if side:lines.append(f"  🥬 +配: {side['name']}（{side['cal']}kcal）")
  if soup:lines.append(f"  🍲 +汤/饭: {soup['name']}（{soup['cal']}kcal）")
 lines+=[f"  {'─'*32}",f"  💡 回复「要」或「1/2/3」查看详细做法 👨‍🍳  ·  「换个」换一批"]
 return"\n".join(lines)
def fmt_daily(results,wd_name,season,meal_time,weather,profile,wd_detail=None):
 parts=[];loc=profile.get("location","")
 if loc:parts.append(f"📍 {loc}")
 if wd_detail:parts.append(wd_detail)
 elif weather and weather!="sunny":parts.append(WL.get(weather,""))
 parts+=[wd_name,f"{season}季"]
 h=f"\n🍽️ 今日 {meal_time}推荐  {' · '.join(parts)}\n{ST.get(season,'')}"
 extras=[]
 if profile.get("diet_goal"):extras.append({"减肥":"低卡🎯","增肌":"高蛋白💪","养生":"滋补🍵","保持":"均衡⚖️"}.get(profile['diet_goal'],profile['diet_goal']))
 if profile.get("preferred_cuisines"):extras.append(f"偏好: {','.join(profile['preferred_cuisines'])}")
 if profile.get("mood"):extras.append(f"心情: {'😊💼😫🧘🎉😴'.encode().decode()}") # simplified
 if extras:h+="\n"+"  ".join(extras)
 body=fmt_results(results,wd_name,season,meal_time,weather,loc)
 hints=[]
 if not profile.get("location"):hints.append("📍 你在哪个城市？")
 if not profile.get("mood"):hints.append("😊 心情？开心/忙碌/疲惫/放松/庆祝")
 if not profile.get("wanted_category"):hints.append("🍽️ 想吃？主食/肉/素/汤/辣/清淡/甜")
 if not profile.get("preferred_cuisines"):hints.append("🍜 偏好菜系？川菜/粤菜/鲁菜/江浙…")
 if not profile.get("diet_goal"):hints.append("🎯 饮食目标？减肥/增肌/养生")
 ask=""
 if hints:ask="\n\n💬 告诉我这些，推荐更精准：\n"+"\n".join(f"   {h}"for h in hints)+"\n💡 一句话搞定：「北京，心情不错，想吃辣的，川菜」以后自动用～"
 return h+body+ask
def fmt_detail(meal):
 lines=[f"  🍽️ {meal['name']}",f"     💡 {meal['desc']}",f"     🔥 ~{meal['cal']}kcal | ⏱ {meal['time']} | {meal['difficulty']}"]
 if meal.get('nutrition'):lines.append(f"     💊 {' | '.join(f'{k}:{v}'for k,v in meal['nutrition'].items())}")
 lines+=[f"     🥬 {', '.join(meal['ingredients'])}",f"     🏷️ {', '.join(meal['tags'])}"]
 if meal.get('steps'):lines+=["     📝 做法:"]+[f"       {i+1}. {s}"for i,s in enumerate(meal['steps'])]
 return"\n".join(lines)
if __name__=="__main__":
 pa=argparse.ArgumentParser();pa.add_argument("mode",help="daily/weekly/search/detail");pa.add_argument("args",nargs="*");pa.add_argument("--meal","-m",default=None);pa.add_argument("--weather","-w",default=None);pa.add_argument("-n","--count",type=int,default=3)
 a=pa.parse_args();q=" ".join(a.args);mt=a.meal
 cn={"breakfast":"早餐","lunch":"午餐","dinner":"晚餐","supper":"夜宵","afternoon_tea":"下午茶"}
 if mt in cn:mt=cn[mt]
 if a.mode=="daily":
  if not mt:mt="晚餐"if datetime.now().hour>=17 else"午餐"
  for kw in["早餐","午餐","晚餐","夜宵"]:
   if kw in q:mt=kw;break
  season=get_season();wd=datetime.now().weekday();wn=["周一","周二","周三","周四","周五","周六","周日"][wd];pf=load_profile()
  w=a.weather or pf.get("weather");wdd=None
  if not w and pf.get("location"):w,wdd=fetch_weather(pf["location"])
  if w:pf["weather"]=w;pf["weather_auto"]=True;save_profile(pf)
  r,_=recommend_smart(mt,w,pf.get("location"),pf,a.count);print(fmt_daily(r,wn,season,mt,w,pf,wdd))
 elif a.mode=="detail":
  if not q:print("用法: python meal_recommend.py detail <菜名>");sys.exit(1)
  found=[m for m in MEALS_DB if q in m['name']or m['name']in q];print("\n".join(fmt_detail(m)for m in found)if found else f"未找到「{q}」")
 elif a.mode=="search":
  if not q:print("用法: python meal_recommend.py search <关键词>");sys.exit(1)
  kws=q.split();cm=[m for m in MEALS_DB if any(k in m['name']or k in",".join(m.get('tags',[]))for k in kws)]
  mm=[m for m in MENU_NAMES if any(k in m['name']or k in",".join(m.get('tags',[]))for k in kws)]
  mm=[m for m in mm if m['name']not in set(x['name']for x in cm)]
  print(f"\n🔍 搜索「{q}」\n")
  if cm:print("📋 完整菜谱：");[print(fmt_detail(m),"\n")for m in cm[:5]]
  if mm:print(f"🍽️ 更多相关（共{len(mm)}道）：");[print(f"  · {m['name']} {' '.join(f'#{t}'for t in m.get('tags',[])[:3])} [{m.get('category','')}]")for m in mm[:10]]
  if not cm and not mm:print("未找到相关菜品")
  print("\n💡 回复「要」或菜名查看详细做法 👨‍🍳")
 elif a.mode=="weekly":
  print(f"\n📅 一周菜谱\n{ST.get(get_season(),'')}")
  for d in["周一","周二","周三","周四","周五","周六","周日"]:
   r,_=recommend_smart("午餐",a.weather,count=1)
   if r:m,_,side,soup=r[0];print(f"\n{'━'*36}\n📅 {d}\n  🍖 {m['name']} · {m['desc']} · 🔥{m['cal']}kcal");(side and print(f"  🥬 {side['name']} · 🔥{side['cal']}kcal"));(soup and print(f"  🍲 {soup['name']} · 🔥{soup['cal']}kcal"))
 else:print(f"未知模式: {a.mode}，支持: daily/weekly/search/detail")
