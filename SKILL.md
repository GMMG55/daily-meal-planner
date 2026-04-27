---
name: daily-meal-planner
version: "1.0.5"
description: "每日智能菜谱推荐。触发词：今天吃什么/中午吃什么/晚餐推荐/下午茶/夜宵/一周菜单/清淡/辣的/快手菜/减肥。支持按餐次、口味、心情、季节、天气、地域智能推荐，带详细做法和营养数据。"
---

# Daily Meal Planner

智能推荐菜谱，支持用户画像记忆和偏好学习。每餐推荐3套完整套餐（主菜+配菜+汤/主食）。

## 智能三菜推荐

1. **📌 综合智能推荐** — 季节+周几+天气+用户画像加权
2. **🌿 时令之选** — 按当季食材筛选
3. **🎲 随机惊喜** — 换换口味

## 用户画像

自动保存到本地 `user_profile.json`：地点、心情、想吃类别、偏好菜系、喜欢的菜、不喜欢的菜、饮食目标、过敏食材。

## 天气适配

11种天气类型自动适配（炎热→清热、雨天→暖汤、雾霾→护肺等）。天气来源：CLI参数 > 本地保存 > wttr.in自动查询。

## 使用方法

```bash
python scripts/meal_recommend.py daily                    # 今日推荐
python scripts/meal_recommend.py daily -m 晚餐            # 指定餐次
python scripts/meal_recommend.py daily -w rainy           # 指定天气
python scripts/meal_recommend.py search 辣                # 搜索
python scripts/meal_recommend.py detail 西红柿牛腩         # 详细做法
python scripts/meal_recommend.py weekly                   # 一周菜单
```

## 触发场景

- 餐次：「今天吃什么」「晚餐推荐」「下午茶」「夜宵」「一周菜单」
- 口味：「清淡的」「辣的」「快手菜」「硬菜」
- 营养：「低卡」「减肥」「高蛋白」「养生」「滋补」

## 输出格式

```
  ────────────────────────────────
  ☀️ 推荐1  西红柿牛腩
  📝 酸甜浓郁肉烂汤鲜
  💡 应季食材，周五庆祝，晴天清爽
  🔥 650kcal  ⏱ 30min  难度: 中等
  📊 蛋白质:28g | 铁:4mg
  🏠 南方,江浙,粤菜
  🥗 食材: 牛腩400g,番茄3个,土豆1个,洋葱半个
  🥬 +配: 清炒时蔬（120kcal）
  🍲 +汤/饭: 白灼虾（150kcal）
  ────────────────────────────────
  💡 回复「要」或「1/2/3」查看详细做法 👨‍🍳  ·  「换个」换一批
```

## 心情→菜品

疲惫→清淡养胃、忙碌→快手清淡、开心→硬菜家常、放松→素食清淡、庆祝→硬菜经典、慵懒→快手饱腹

## 数据文件

| 文件 | 用途 |
|---|---|
| `meals_db_compressed.json` + `meals_tags_index.json` | 42道完整菜谱（含做法、营养） |
| `menu_names_compressed.json` + `tags_index.json` | 595道菜单名索引 |
| `user_profile.json` | 用户画像（自动生成） |

> 数据文件首次运行时自动从 GitHub 下载。

## 脚本

- `scripts/meal_recommend.py` — 推荐引擎
- `scripts/meal_search.py` — 在线搜索（下厨房/美食杰）
- `scripts/requirements.txt` — 依赖
