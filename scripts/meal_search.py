#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""菜谱在线搜索（下厨房/美食杰）"""
import sys,json,re,requests
from urllib.parse import quote
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36","Accept-Language":"zh-CN,zh;q=0.9"}
def search_xiachufang(kw,n=5):
 r=[];seen=set()
 try:
  resp=requests.get(f"https://www.xiachufang.com/search/?keyword={quote(kw)}",headers=UA,timeout=10);resp.encoding="utf-8"
  for path,name in re.findall(r'<a[^>]*href="(/recipe/\d+/)"[^>]*>\s*<img[^>]*alt="([^"]*)"',resp.text):
   name=name.strip()
   if name and name not in seen and len(seen)<n:seen.add(name);r.append({"name":name,"url":f"https://www.xiachufang.com{path}","source":"下厨房"})
 except:r.append({"error":f"下厨房搜索失败"})
 return r
def search_meishij(kw,n=5):
 r=[];seen=set()
 try:
  resp=requests.get(f"https://www.meishij.net/search/{quote(kw)}/",headers=UA,timeout=10);resp.encoding="utf-8"
  for url,name in re.findall(r'<a[^>]*href="(https://www\.meishij\.net/zuofa/[^"]+)"[^>]*title="([^"]*)"',resp.text):
   name=name.strip()
   if name and name not in seen and len(seen)<n:seen.add(name);r.append({"name":name,"url":url,"source":"美食杰"})
 except:r.append({"error":f"美食杰搜索失败"})
 return r
def search_recipe(kw,n=5):
 r1=search_xiachufang(kw,n);r2=search_meishij(kw,n);seen=set();out=[]
 for r in r1+r2:
  if"error"in r:out.append(r);continue
  if r["name"]not in seen:seen.add(r["name"]);out.append(r)
 return out[:n*2]
def get_detail(url):
 try:
  resp=requests.get(url,headers=UA,timeout=10);resp.encoding="utf-8";d={"url":url}
  ing=re.findall(r'<tr[^>]*class="ingredient"[^>]*>.*?<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>',resp.text,re.DOTALL)
  if ing:d["ingredients"]=[f"{re.sub(r'<[^>]+>','',n).strip()} {re.sub(r'<[^>]+>','',a).strip()}"for n,a in ing]
  st=re.findall(r'<div[^>]*class="text"[^>]*>\s*<p>(.*?)</p>',resp.text,re.DOTALL)
  if st:d["steps"]=[re.sub(r'<[^>]+>','',s).strip()for s in st if s.strip()]
  return d
 except:return{"error":"获取详情失败"}
if __name__=="__main__":
 if len(sys.argv)<2:print("用法: python meal_search.py <关键词> [数量]");sys.exit(1)
 kw=sys.argv[1];n=int(sys.argv[2])if len(sys.argv)>2 else 5
 print(json.dumps(search_recipe(kw,n),ensure_ascii=False,indent=2))
