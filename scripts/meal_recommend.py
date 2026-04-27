#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
菜谱推荐引擎 v1.1
- 默认推荐3道：①综合智能推荐 ②时令菜 ③随机推荐
- 每道包含：主菜 + 配菜 + 汤/主食
- 支持按季节/周几/天气/地点智能加权
- 支持 daily / weekly / search / detail 模式
"""

import sys
import random
import argparse
import os
import json
from datetime import datetime


# ============ 数据加载（压缩格式支持）============
def _load_json(filename):
    path = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    return None

def load_meals_db():
    """加载 meals_db_compressed.json + meals_tags_index.json，解析数字索引→标签字符串"""
    data = _load_json('meals_db_compressed.json')
    tags_idx = _load_json('meals_tags_index.json') or []
    if not data:
        data = _load_json('meals_db.json')
        if data:
            meals = []
            for cn_type, dishes in data.items():
                for d in dishes:
                    d = dict(d)
                    d['meal_type'] = cn_type
                    meals.append(d)
            return meals
        return []
    # 解析压缩格式：t字段是数字索引→转回标签字符串
    meals = []
    for cn_type, dishes in data.items():
        for d in dishes:
            d = dict(d)
            d['meal_type'] = cn_type
            raw_tags = d.get('t', [])
            d['tags'] = [tags_idx[i] for i in raw_tags if i < len(tags_idx)] if tags_idx else raw_tags
            d['name'] = d.pop('n', d.get('name', ''))
            d['cal'] = d.pop('c', d.get('cal', 0))
            d['difficulty'] = d.pop('d', d.get('difficulty', '中'))
            d['desc'] = d.pop('dsc', d.get('desc', ''))
            d['ingredients'] = d.pop('ing', d.get('ingredients', []))
            d['steps'] = d.pop('stp', d.get('steps', []))
            meals.append(d)
    return meals

def load_menu_names():
    """加载 menu_names_compressed.json + tags_index.json，解析数字索引→标签字符串"""
    data = _load_json('menu_names_compressed.json')
    tags_idx = _load_json('tags_index.json') or []
    if not data:
        data = _load_json('menu_names.json')
        if data:
            menu_list = []
            for category, items in data.items():
                for item in items:
                    item = dict(item)
                    item['category'] = category
                    menu_list.append(item)
            return menu_list
        return []
    menu_list = []
    for category, items in data.items():
        for item in items:
            item = dict(item)
            item['category'] = category
            raw_tags = item.get('t', [])
            item['tags'] = [tags_idx[i] for i in raw_tags if i < len(tags_idx)] if tags_idx else raw_tags
            item['name'] = item.pop('n', item.get('name', ''))
            item['cuisine'] = item.pop('c', item.get('cuisine', ''))
            menu_list.append(item)
    return menu_list

MEALS_DB = load_meals_db()
MENU_NAMES = load_menu_names()

# ============ 季节/周几/天气配置 ============
SEASON_TIPS = {
    "春": "🌸 春季宜养肝，多食绿色蔬菜、豆芽、春笋，少酸多甘",
    "夏": "☀️ 夏季宜清热，多食瓜果、凉菜、绿豆，少油腻辛辣",
    "秋": "🍂 秋季宜润燥，多食银耳、梨、百合，少辛辣煎炸",
    "冬": "❄️ 冬季宜温补，多食牛羊肉、根茎类，适当进补",
}

# ============ 用户画像持久化 ============
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_FILE = os.path.join(SKILL_DIR, "user_profile.json")

DEFAULT_PROFILE = {
    "location": None,         # 地点（城市）
    "weather": None,          # 天气关键词（hot/cold/rainy/sunny/smog/snow/windy/cool/warm/humid/dry）
    "weather_auto": False,    # 天气是否自动查询
    "taste": None,            # 口味偏好（清淡/辣/下饭/快手/营养/养胃/素食）
    "preferred_cuisines": [],  # 偏好菜系（川菜/粤菜/鲁菜/京味/江浙/东北/西北/闽菜/湘菜）
    "liked_dishes": [],        # 喜欢的菜（菜品名称）
    "disliked_dishes": [],     # 不喜欢的菜（菜品名称）
    "mood": None,             # 心情（开心/忙碌/疲惫/放松/庆祝/慵懒）
    "wanted_category": None,  # 想吃哪类（主食/肉/素/汤/辣/清淡/甜/小食）
    "diet_goal": None,       # 饮食目标（减肥/增肌/保持/养生）
    "allergies": [],          # 过敏食材
    "dislike": [],            # 不喜欢的食材
    "last_updated": None,
}


def load_profile():
    """加载本地用户画像"""
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                profile = json.load(f)
            # 合并默认值，防止新增字段
            merged = DEFAULT_PROFILE.copy()
            merged.update(profile)
            return merged
        except Exception:
            return DEFAULT_PROFILE.copy()
    return DEFAULT_PROFILE.copy()


def save_profile(profile):
    """保存用户画像到本地"""
    profile["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    try:
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[警告] 无法保存用户画像: {e}")


def build_ask_prompt(existing_profile):
    """生成缺失信息的询问提示（v2.2：问心情+想吃类别）"""
    missing = []
    hints = []

    if not existing_profile.get("location"):
        missing.append("所在地")
        hints.append("📍 你在哪个城市？（告诉我后自动查天气）")

    if not existing_profile.get("mood"):
        missing.append("心情")
        hints.append("😊 今天心情怎么样？开心/忙碌/疲惫/放松/想庆祝？")

    if not existing_profile.get("wanted_category"):
        missing.append("想吃的类型")
        hints.append("🍽️ 想吃什么类的？主食/肉菜/素菜/汤/辣/清淡/甜/小食？")

    if not existing_profile.get("preferred_cuisines"):
        missing.append("偏好菜系")
        hints.append("🍜 有偏好的菜系吗？川菜/粤菜/鲁菜/京味/江浙/东北…？")

    if not existing_profile.get("diet_goal"):
        missing.append("饮食目标")
        hints.append("🎯 最近在减肥/增肌/养生吗？")

    if not missing:
        return None

    lines = [""]
    lines.append("💬 告诉我这些，推荐更精准：")
    for h in hints:
        lines.append(f"   {h}")
    lines.append("")
    lines.append("💡 直接回复一句话搞定，比如：")
    lines.append("   「北京，今天心情不错，想吃辣的，来个川菜」")
    lines.append("   以后每次都直接用，不用重复说啦～")
    return "\n".join(lines)


# ============ 自动天气查询（wttr.in 免费接口）============
def fetch_auto_weather(city):
    """通过 wttr.in 自动查询天气，返回天气代码（如 'sunny'/'rainy'/'hot' 等）"""
    if not city:
        return None, None
    try:
        import urllib.request
        url = f"https://wttr.in/{city}?format=j1"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read().decode())
        curr = data.get("current_condition", [{}])[0]
        temp = int(curr.get("FeelsLikeC", 0))
        desc_list = [d.get("value", "") for d in curr.get("weatherDesc", [])]
        desc = desc_list[0].lower() if desc_list else ""
        humidity = int(curr.get("humidity", 0))
        precip = float(curr.get("precipMM", 0))
        wind = float(curr.get("windspeedKmph", 0))

        # 天气代码映射
        if "snow" in desc or "blizzard" in desc:
            code = "snow"
        elif "rain" in desc or "drizzle" in desc or "shower" in desc:
            code = "rainy"
        elif "fog" in desc or "mist" in desc or "haze" in desc:
            code = "smog"
        elif "cloud" in desc:
            code = "sunny" if temp > 18 else "cold"
        elif "sunny" in desc or "clear" in desc:
            code = "sunny"
        elif precip > 5:
            code = "rainy"
        else:
            code = "hot" if temp > 28 else ("cold" if temp < 10 else "sunny")

        # 中文描述
        label = WEATHER_LABELS.get(code, "")
        detail = f"{label} {temp}°C" if label else f"{temp}°C"
        return code, detail
    except Exception:
        return None, None


# ============ 地域特色推荐 ============
def get_regional_tags(location):
    """根据城市返回地域风味标签"""
    if not location:
        return []
    region_map = {
        "北京": ["京味","鲁菜","京菜"],
        "天津": ["津菜","鲁菜","京菜"],
        "河北": ["冀菜","鲁菜"],
        "山西": ["晋菜","西北"],
        "内蒙古": ["蒙餐","西北"],
        "上海": ["沪菜","江浙","本帮菜"],
        "江苏": ["苏菜","江浙","淮扬菜"],
        "浙江": ["浙菜","江浙"],
        "安徽": ["徽菜","江浙"],
        "福建": ["闽菜"],
        "江西": ["赣菜","湘菜"],
        "山东": ["鲁菜","京味"],
        "河南": ["豫菜","中菜"],
        "湖北": ["鄂菜","湘菜"],
        "湖南": ["湘菜"],
        "广东": ["粤菜"],
        "广西": ["桂菜","粤菜"],
        "海南": ["海南菜","粤菜"],
        "重庆": ["川菜","渝菜"],
        "四川": ["川菜"],
        "贵州": ["黔菜","川菜"],
        "云南": ["滇菜","川菜"],
        "西藏": ["藏菜","西北"],
        "陕西": ["陕菜","西北","清真"],
        "甘肃": ["陇菜","西北"],
        "青海": ["青菜","西北"],
        "宁夏": ["清真","西北"],
        "新疆": ["新疆菜","清真","西北"],
        "东北": ["东北菜"],
        "辽宁": ["辽菜","东北菜"],
        "吉林": ["吉菜","东北菜"],
        "黑龙江": ["龙江菜","东北菜"],
        "全国": ["家常","下饭"],
    }
    for key, tags in region_map.items():
        if key in location:
            return tags
    return []


# ============ 天气标签映射 ============
WEATHER_LABELS = {
    "hot":       "炎热",
    "cold":      "寒冷",
    "rainy":     "雨天",
    "sunny":     "晴天",
    "smog":      "雾霾",
    "snow":      "下雪",
    "windy":     "大风",
    "cool":      "降温",
    "warm":      "升温",
    "humid":     "闷热",
    "dry":       "干燥",
}

# ============ 周几推荐理由 ============
WEEK_REASONS = {
    0: "周一开工，来点清淡养胃的，舒服开启新一周",
    1: "周二工作日，能量满满，营养要跟上",
    2: "周三过半，犒劳一下自己",
    3: "周四快熬到头了，整点好吃的",
    4: "周五啦！辛苦一周，吃点好的庆祝一下 🎉",
    5: "周六休闲时光，可以做点丰盛的硬菜",
    6: "周日在享受懒觉，早餐吃好不将就",
}


# ============ 核心推荐函数 ============

def get_season():
    month = datetime.now().month
    if month in [3,4,5]:   return "春"
    elif month in [6,7,8]: return "夏"
    elif month in [9,10,11]: return "秋"
    else: return "冬"


def score_meal(meal, season, weekday, weather, used_names):
    """综合评分函数"""
    if meal['name'] in used_names:
        return -999, []

    score = 0
    reasons = []

    # 季节匹配 +3
    if season in meal.get("seasonal", []):
        score += 3
        reasons.append("应季食材")

    # 周几权重
    if weekday == 4:  # 周五
        if "硬菜" in meal.get("tags", []): score += 2
        if "经典" in meal.get("tags", []): score += 1
        reasons.append("周五庆祝")
    elif weekday in [0, 1, 2]:  # 周一到周三
        if "清淡" in meal.get("tags", []) or "快手" in meal.get("tags", []):
            score += 1
        reasons.append("工作日轻食")
    elif weekday in [5, 6]:  # 周末
        if "硬菜" in meal.get("tags", []) or "家常" in meal.get("tags", []):
            score += 2
        reasons.append("周末丰盛")

    # 天气权重
    if weather in ["hot", "humid"]:
        if "清淡" in meal.get("tags", []): score += 2
        if "凉菜" in meal.get("tags", []): score += 1
        if "硬菜" in meal.get("tags", []): score -= 1
        if weather == "hot":  reasons.append("天热清热")
        else:                   reasons.append("闷热解腻")
    elif weather in ["cold", "cool", "snow"]:
        if "家常" in meal.get("tags", []) or "汤品" in meal.get("tags", []): score += 1
        if "清淡" in meal.get("tags", []) and "凉菜" not in meal.get("tags", []): score += 1
        if weather == "cold":  reasons.append("天冷暖身")
        elif weather == "cool": reasons.append("降温滋补")
        else:                   reasons.append("雪天热汤")
    elif weather in ["rainy", "humid"]:
        if "汤品" in meal.get("tags", []) or "养胃" in meal.get("tags", []): score += 2
        if "清淡" in meal.get("tags", []): score += 1
        if weather == "rainy": reasons.append("雨天暖汤")
        else:                  reasons.append("祛湿暖胃")
    elif weather == "sunny":
        if "清淡" in meal.get("tags", []): score += 1
        if "凉菜" in meal.get("tags", []): score += 1
        reasons.append("晴天清爽")
    elif weather == "smog":
        if "清淡" in meal.get("tags", []) and "凉菜" not in meal.get("tags", []): score += 2
        if "养胃" in meal.get("tags", []): score += 1
        reasons.append("雾霾护肺")
    elif weather in ["warm", "dry"]:
        if "清淡" in meal.get("tags", []) or "凉菜" in meal.get("tags", []): score += 1
        if "润燥" in meal.get("tags", []): score += 2
        if weather == "warm":  reasons.append("升温清淡")
        else:                    reasons.append("干燥润肺")
    elif weather == "windy":
        if "家常" in meal.get("tags", []) or "汤品" in meal.get("tags", []): score += 1
        reasons.append("大风暖身")

    # 随机微调
    score += random.uniform(0, 1.5)

    return score, reasons


def score_regional_preference(meal, preferred_cuisines):
    """地域风味偏好评分（v2.2 新增）"""
    score = 0
    reasons = []
    if not preferred_cuisines or not meal.get("regional"):
        return score, reasons
    meal_regions = set(meal.get("regional", []))
    matched = meal_regions & set(preferred_cuisines)
    if matched:
        score += 3
        reasons.append(f"家乡味道({'/'.join(list(matched)[:2])})")
    return score, reasons


def get_side_dish(main_meal, meal_time, season, used_names):
    """为套餐配一个清爽配菜（同餐次内选择清淡/素菜/凉菜）"""
    # 优先从同餐次选，午餐/晚餐互用，早餐单独处理
    pool_sources = [meal_time]
    if meal_time in ["午餐", "晚餐"]:
        pool_sources = ["午餐", "晚餐"]

    side_pool = []
    for src in pool_sources:
        for m in [x for x in MEALS_DB if x.get("meal_type") == src]:
            tags = m.get("tags", [])
            if ("清淡" in tags or "素食" in tags or "凉菜" in tags or "快手" in tags) \
               and m['name'] not in used_names and m['name'] != main_meal['name']:
                side_pool.append(m)

    # 夏季优先凉菜
    if season == "夏":
        summer_sides = [m for m in side_pool if "凉菜" in m.get("tags", [])]
        if summer_sides:
            side_pool = summer_sides

    if side_pool:
        return random.choice(side_pool[:6])
    return None


def get_soup_or_staple(meal_time, season, used_names):
    """为套餐配一个汤/主食（同餐次优先）"""
    pool_sources = [meal_time]
    if meal_time in ["午餐", "晚餐"]:
        pool_sources = ["午餐", "晚餐"]

    soup_pool = []
    for src in pool_sources:
        for m in [x for x in MEALS_DB if x.get("meal_type") == src]:
            tags = m.get("tags", [])
            if ("汤品" in tags or "养胃" in tags or "清淡" in tags) \
               and m['name'] not in used_names:
                soup_pool.append(m)

    # 早餐默认推荐粥/饮品（仅从早餐池选）
    if meal_time == "早餐":
        breakfast_pool = [m for m in MEALS_DB if m.get("meal_type") == "早餐"
                          if m['name'] not in used_names
                          and m['name'] in ["小米粥","蔬菜粥","蒸蛋羹","牛奶燕麦"]]
        soup_pool = breakfast_pool

    if soup_pool:
        return random.choice(soup_pool[:8])
    return None


def recommend_smart(meal_time=None, weather=None, location=None, profile=None, count=3):
    """智能三菜推荐，返回: [(meal, reason, side, soup), ...]
    v2.2: 支持地域偏好评分、心情/想吃类别过滤、排除不喜欢的菜"""
    now = datetime.now()
    season = get_season()
    weekday = now.weekday()
    weekday_names = ["周一","周二","周三","周四","周五","周六","周日"]
    weekday_name = weekday_names[weekday]

    if meal_time is None:
        meal_time = "午餐"

    # v2.2: 获取用户偏好
    liked_dishes = profile.get("liked_dishes", []) if profile else []
    disliked_dishes = profile.get("disliked_dishes", []) if profile else []
    preferred_cuisines = profile.get("preferred_cuisines", []) if profile else []
    mood = profile.get("mood", "") if profile else ""
    wanted = profile.get("wanted_category", "") if profile else ""
    regional_tags = get_regional_tags(location) if location else []

    # 心情→标签映射
    mood_tag_map = {
        "疲惫": ["清淡","养胃","高蛋白"],
        "忙碌": ["快手","清淡"],
        "开心": ["硬菜","家常","经典"],
        "放松": ["家常","素食","清淡"],
        "庆祝": ["硬菜","经典","下饭"],
        "慵懒": ["快手","清淡","饱腹"],
    }
    # 想吃类别→标签映射
    wanted_tag_map = {
        "主食": ["饱腹","家常"],
        "肉": ["硬菜","高蛋白"],
        "素": ["素食","清淡"],
        "汤": ["汤品","养胃"],
        "辣": ["川菜","湘菜","下饭"],
        "清淡": ["清淡","素食","凉菜"],
        "甜": ["甜品","养颜"],
        "小食": ["快手","清淡"],
    }

    # MEALS_DB 是 list，按 meal_type 过滤
    pool = [m for m in MEALS_DB if m.get("meal_type") == meal_time]
    all_used = []
    results = []

    # --- 预处理：排除不喜欢的菜 ---
    def is_acceptable(meal):
        name = meal.get("name", "")
        tags = meal.get("tags", [])
        for d in disliked_dishes:
            if d in name or d in ",".join(tags):
                return False
        return True

    def boost_score(meal):
        """心情/类别加权"""
        bonus = 0
        tags = meal.get("tags", [])
        if mood and mood in mood_tag_map:
            for tag in mood_tag_map[mood]:
                if tag in tags:
                    bonus += 1.5
        if wanted and wanted in wanted_tag_map:
            for tag in wanted_tag_map[wanted]:
                if tag in tags:
                    bonus += 1
        return bonus

    # --- ① 综合智能推荐 ---
    scored = []
    for m in pool:
        if not is_acceptable(m):
            continue
        s, reasons = score_meal(m, season, weekday, weather, all_used)
        s += boost_score(m)
        # 喜欢吃的菜加权
        if liked_dishes and m.get("name") in liked_dishes:
            s += 2
            reasons.append("你喜欢的菜")
        # 地域风味加权
        if regional_tags and m.get("regional"):
            match = set(m["regional"]) & set(regional_tags)
            if match:
                s += 2
                reasons.append(f"本地风味")
        scored.append((s, m, reasons))

    scored.sort(key=lambda x: -x[0])
    if scored:
        best_meal = scored[0][1]
        best_reasons = scored[0][2]
        if best_reasons:
            reason_text = f"📌 综合推荐：{'，'.join(best_reasons)}"
        else:
            reason_text = f"📌 综合推荐：{WEEK_REASONS.get(weekday, '今天吃点好的')}"
        side = get_side_dish(best_meal, meal_time, season, all_used + [best_meal['name']])
        soup = get_soup_or_staple(meal_time, season, all_used + [best_meal['name'], (side['name'] if side else '')])
        results.append((best_meal, reason_text, side, soup))
        all_used.append(best_meal['name'])

    # --- ② 时令菜推荐 ---
    seasonal_pool = [m for m in pool if m not in all_used and is_acceptable(m) and season in m.get("seasonal", [])]
    if not seasonal_pool:
        seasonal_pool = [m for m in pool if m not in all_used and is_acceptable(m)]
    if seasonal_pool:
        pick = random.choice(seasonal_pool)
        reason_text = f"🌿 时令之选：{season}季新鲜食材"
        side = get_side_dish(pick, meal_time, season, all_used + [pick['name']])
        soup = get_soup_or_staple(meal_time, season, all_used + [pick['name'], (side['name'] if side else '')])
        results.append((pick, reason_text, side, soup))
        all_used.append(pick['name'])

    # --- ③ 随机推荐 ---
    remaining = [m for m in pool if m not in all_used and is_acceptable(m)]
    if remaining:
        pick = random.choice(remaining)
        reason_text = f"🎲 随机惊喜：换换口味也不错"
        side = get_side_dish(pick, meal_time, season, all_used + [pick['name']])
        soup = get_soup_or_staple(meal_time, season, all_used + [pick['name'], (side['name'] if side else '')])
        results.append((pick, reason_text, side, soup))

    return results[:count], weekday_name


def safe_nutrition(nutrition_dict, keys):
    """安全获取营养值"""
    parts = []
    for k in keys:
        v = nutrition_dict.get(k, '—')
        parts.append(f"{k}:{v}")
    return " | ".join(parts)


def format_smart_recommendations(results, weekday_name, season, meal_time="午餐", weather=None, location=None):
    """格式化智能推荐输出 v2.2（清爽卡片格式）
    每道推荐含：套餐组合（主菜+配菜+汤）+ 热量 + 标签 + 原因
    """
    lines = []
    meal_type_icon = {"早餐":"🌅","午餐":"☀️","晚餐":"🌙","下午茶":"🫖","夜宵":"🌃","饮品":"🥤","零食":"🍿"}.get(meal_time,"🍽️")

    for i, (meal, reason, side, soup) in enumerate(results, 1):
        cal_total = meal['cal'] + (side['cal'] if side else 0) + (soup['cal'] if soup else 0)

        # 提取推荐原因（去掉前缀emoji）
        reason_clean = reason.replace("📌 ","").replace("🌿 ","").replace("🎲 ","")
        for prefix in ["综合推荐：","时令之选：","随机惊喜："]:
            reason_clean = reason_clean.replace(prefix,"")

        # 提取标签
        tags = meal.get("tags", [])
        regional = meal.get("regional", [])
        tag_str = " ".join(f"#{t}" for t in (tags[:3]))

        lines.append("")
        lines.append(f"  {'─'*32}")
        lines.append(f"  {meal_type_icon} 推荐{i}  {meal['name']}")
        lines.append(f"  📝 {meal['desc']}")
        lines.append(f"  💡 {reason_clean}")
        lines.append(f"  🔥 {cal_total}kcal  ⏱ {meal['time']}  难度: {meal['difficulty']}")

        # 营养亮点
        if 'nutrition' in meal:
            n = meal['nutrition']
            parts = []
            for k in ['蛋白质','维C','铁','钙']:
                if k in n: parts.append(f"{k}:{n[k]}")
            if parts: lines.append(f"  📊 {' | '.join(parts)}")

        # 地域标签
        if regional:
            lines.append(f"  🏠 {','.join(regional)}")

        lines.append(f"  🥗 食材: {','.join(meal['ingredients'][:4])}")

        # 套餐组合
        if side:
            lines.append(f"  🥬 +配: {side['name']}（{side['cal']}kcal）")
        if soup:
            lines.append(f"  🍲 +汤/饭: {soup['name']}（{soup['cal']}kcal）")

    lines.append(f"  {'─'*32}")
    lines.append("")
    lines.append(f"  💡 回复「要」或「1/2/3」查看详细做法 👨‍🍳  ·  「换个」换一批")
    return "\n".join(lines)


def format_daily_with_profile(results, weekday_name, season, meal_time, weather, profile, weather_detail=None):
    """整合用户画像的完整输出 v2.2
    标题: [位置] [天气] [周几] · [季节]
    末尾: 心情/类型询问
    """
    # 组装标题
    parts = []
    location = profile.get("location","")
    if location:
        parts.append(f"📍 {location}")
    if weather_detail:
        parts.append(weather_detail)
    elif weather and weather != "sunny":
        parts.append(WEATHER_LABELS.get(weather,""))
    parts.append(f"{weekday_name}")
    parts.append(f"{season}季")
    title_str = " · ".join(parts)

    header = f"\n🍽️ 今日{' '+meal_time if meal_time else ''}推荐  {title_str}"
    header += f"\n{SEASON_TIPS.get(season,'')}"

    # 目标行
    extras = []
    if profile.get("diet_goal"):
        gm = {"减肥":"低卡模式 🎯","增肌":"高蛋白模式 💪","养生":"滋补模式 🍵","保持":"均衡模式 ⚖️"}
        extras.append(gm.get(profile['diet_goal'], profile['diet_goal']))
    if profile.get("preferred_cuisines"):
        extras.append(f"偏好菜系: {','.join(profile['preferred_cuisines'])}")
    if profile.get("mood"):
        mood_emoji = {"开心":"😊","忙碌":"💼","疲惫":"😫","放松":"🧘","庆祝":"🎉","慵懒":"😴"}
        extras.append(f"心情: {mood_emoji.get(profile['mood'], profile['mood'])}")
    if extras:
        header += "\n" + "  ".join(extras)

    body = format_smart_recommendations(results, weekday_name, season, meal_time, weather, location)

    # 末尾询问（新版：问心情+想吃类型）
    ask = build_ask_prompt(profile)
    footer = f"\n{ask}" if ask else ""

    return header + body + footer


def format_meal_detail(meal, detail=False):
    """格式化单个菜品"""
    lines = [
        f"  🍽️ {meal['name']}",
        f"     💡 {meal['desc']}",
        f"     🔥 热量: ~{meal['cal']}kcal | ⏱ {meal['time']} | 难度: {meal['difficulty']}",
    ]
    if 'nutrition' in meal:
        nutrition_parts = [f"{k}: {v}" for k, v in meal['nutrition'].items()]
        lines.append(f"     💊 营养: {' | '.join(nutrition_parts)}")
    lines.append(f"     🥬 食材: {', '.join(meal['ingredients'])}")
    lines.append(f"     🏷️ 标签: {', '.join(meal['tags'])}")
    if detail and 'steps' in meal:
        lines.append("     📝 做法:")
        for idx, step in enumerate(meal['steps'], 1):
            lines.append(f"       {idx}. {step}")
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="菜谱推荐引擎 v2.2")
    parser.add_argument("mode", help="模式: daily / weekly / search / detail")
    parser.add_argument("args", nargs="*", help="餐次/口味/菜名")
    parser.add_argument("--meal", "-m", default=None, help="指定餐次: 早餐/午餐/晚餐/下午茶/夜宵/饮品/零食")
    parser.add_argument("--weather", "-w", default=None, help="天气(可省，自动查询): hot / cold / rainy / sunny / smog")
    parser.add_argument("-n", "--count", type=int, default=3, help="推荐数量")

    args = parser.parse_args()
    mode = args.mode
    raw_args = " ".join(args.args)
    meal_time = args.meal
    weather = args.weather

    # 英文餐次 → 中文
    meal_cn_map = {"breakfast": "早餐", "lunch": "午餐", "dinner": "晚餐", "supper": "夜宵", "afternoon_tea": "下午茶"}
    if meal_time and meal_time in meal_cn_map:
        meal_time = meal_cn_map[meal_time]

    # 默认午餐
    if mode == "daily" and not meal_time:
        meal_time = "晚餐" if datetime.now().hour >= 17 else "午餐"

    # 从raw_args推断餐次
    if not meal_time:
        for kw in ["早餐","午餐","晚餐","夜宵"]:
            if kw in raw_args:
                meal_time = kw
                break

    if mode == "daily":
        season = get_season()
        weekday_names = ["周一","周二","周三","周四","周五","周六","周日"]
        wd = datetime.now().weekday()
        weekday_name = weekday_names[wd]
        profile = load_profile()

        # 自动查天气（优先：CLI参数 > 本地保存 > 自动查询）
        effective_weather = weather or profile.get("weather")
        weather_detail = None
        if not effective_weather and profile.get("location"):
            effective_weather, weather_detail = fetch_auto_weather(profile["location"])
            if effective_weather:
                profile["weather"] = effective_weather
                profile["weather_auto"] = True
                save_profile(profile)

        # 传入完整画像给推荐引擎
        results, _ = recommend_smart(
            meal_time=meal_time,
            weather=effective_weather,
            location=profile.get("location"),
            profile=profile,
            count=args.count
        )
        print(format_daily_with_profile(results, weekday_name, season, meal_time, effective_weather, profile, weather_detail))

    elif mode == "detail":
        query = raw_args or ""
        if not query:
            print("用法: python meal_recommend.py detail <菜名>")
            sys.exit(1)
        all_meals = []
        for _ in [1]:
            all_meals = MEALS_DB
        found = [m for m in all_meals if query in m['name'] or m['name'] in query]
        if found:
            print()
            for m in found:
                print(format_meal_detail(m, detail=True))
        else:
            print(f"未找到「{query}」，试试其他菜名")

    elif mode == "search":
        query = raw_args or ""
        if not query:
            print("用法: python meal_recommend.py search <关键词>")
            sys.exit(1)
        
        # 1. 先从完整菜谱库搜索
        all_meals = MEALS_DB
        keywords = query.split()
        
        # 从完整菜谱匹配
        complete_matches = [m for m in all_meals
                          if any(kw in m['name'] or kw in ",".join(m.get('tags',[])) for kw in keywords)]
        
        # 2. 从菜单名索引搜索
        menu_matches = [m for m in MENU_NAMES
                       if any(kw in m['name'] or kw in ",".join(m.get('tags',[])) for kw in keywords)]
        
        # 去重（菜单名索引中的菜名可能与完整菜谱重复）
        complete_names = set(m['name'] for m in complete_matches)
        menu_matches_unique = [m for m in menu_matches if m['name'] not in complete_names]
        
        print(f"\n🔍 搜索「{query}」\n")
        
        # 输出完整菜谱
        if complete_matches:
            print("📋 完整菜谱：")
            for m in complete_matches[:5]:
                print(format_meal_detail(m))
                print()
        
        # 输出菜单名索引
        if menu_matches_unique:
            print(f"🍽️ 更多相关菜品（共{len(menu_matches_unique)}道）：")
            for m in menu_matches_unique[:10]:
                tags_str = " ".join(f"#{t}" for t in m.get('tags', [])[:3])
                category = m.get('category', '')
                print(f"  · {m['name']} {tags_str} [{category}]")
        
        if not complete_matches and not menu_matches_unique:
            print("未找到相关菜品，试试其他关键词")
        
        print("\n💡 回复「要」或菜名查看详细做法 👨‍🍳")

    elif mode == "weekly":
        print(f"\n📅 一周菜谱计划")
        print(SEASON_TIPS.get(get_season(), ""))
        days = ["周一","周二","周三","周四","周五","周六","周日"]
        for day in days:
            print(f"\n{'━'*36}")
            print(f"📅 {day}")
            results, _ = recommend_smart(meal_time="午餐", weather=weather, count=1)
            if results:
                meal, reason, side, soup = results[0]
                print(f"  🍖 {meal['name']} · {meal['desc']} · 🔥{meal['cal']}kcal")
                if side: print(f"  🥬 {side['name']} · 🔥{side['cal']}kcal")
                if soup: print(f"  🍲 {soup['name']} · 🔥{soup['cal']}kcal")
    else:
        print(f"未知模式: {mode}，支持: daily / weekly / search / detail")
