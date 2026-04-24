#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日菜谱搜索脚本 - 通过下厨房/美食杰等搜索菜谱
支持按关键词、食材、口味、餐次搜索
"""

import sys
import json
import re
import requests
from urllib.parse import quote


def search_xiachufang(keyword, count=5):
    """从下厨房搜索菜谱"""
    results = []
    try:
        url = f"https://www.xiachufang.com/search/?keyword={quote(keyword)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = "utf-8"

        # 解析搜索结果列表
        pattern = r'<a[^>]*href="(/recipe/\d+/)"[^>]*>\s*<img[^>]*alt="([^"]*)"[^>]*>'
        matches = re.findall(pattern, resp.text)
        seen = set()
        for path, name in matches:
            name = name.strip()
            if name and name not in seen and len(seen) < count:
                seen.add(name)
                results.append({
                    "name": name,
                    "url": f"https://www.xiachufang.com{path}",
                    "source": "下厨房"
                })
    except Exception as e:
        results.append({"error": f"下厨房搜索失败: {str(e)}"})

    return results


def search_meishij(keyword, count=5):
    """从美食杰搜索菜谱"""
    results = []
    try:
        url = f"https://www.meishij.net/search/{quote(keyword)}/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = "utf-8"

        # 美食杰搜索结果
        pattern = r'<a[^>]*href="(https://www\.meishij\.net/zuofa/[^"]+)"[^>]*title="([^"]*)"'
        matches = re.findall(pattern, resp.text)
        seen = set()
        for url, name in matches:
            name = name.strip()
            if name and name not in seen and len(seen) < count:
                seen.add(name)
                results.append({
                    "name": name,
                    "url": url,
                    "source": "美食杰"
                })
    except Exception as e:
        results.append({"error": f"美食杰搜索失败: {str(e)}"})

    return results


def search_recipe(keyword, count=5):
    """综合搜索菜谱"""
    all_results = []

    # 并行搜索多个源
    r1 = search_xiachufang(keyword, count)
    r2 = search_meishij(keyword, count)

    # 去重合并
    seen_names = set()
    for r in r1 + r2:
        if "error" in r:
            all_results.append(r)
            continue
        if r["name"] not in seen_names:
            seen_names.add(r["name"])
            all_results.append(r)

    return all_results[:count * 2]


def get_recipe_detail_xiachufang(url):
    """获取下厨房菜谱详情"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = "utf-8"

        detail = {"url": url}

        # 提取食材
        ing_pattern = r'<tr[^>]*class="ingredient"[^>]*>.*?<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>'
        ingredients = re.findall(ing_pattern, resp.text, re.DOTALL)
        if ingredients:
            detail["ingredients"] = [
                f"{re.sub(r'<[^>]+>', '', name).strip()} {re.sub(r'<[^>]+>', '', amount).strip()}"
                for name, amount in ingredients
            ]

        # 提取步骤
        step_pattern = r'<div[^>]*class="text"[^>]*>\s*<p>(.*?)</p>'
        steps = re.findall(step_pattern, resp.text, re.DOTALL)
        if steps:
            detail["steps"] = [re.sub(r'<[^>]+>', '', s).strip() for s in steps if s.strip()]

        return detail
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python meal_search.py <关键词> [数量]")
        print("示例: python meal_search.py 清淡午餐 5")
        sys.exit(1)

    keyword = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    results = search_recipe(keyword, count)
    print(json.dumps(results, ensure_ascii=False, indent=2))
