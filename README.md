# 🍽️ Daily Meal Planner - 每日智能菜谱推荐

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

> 智能推荐每日菜谱，支持按餐次、口味、心情、季节、天气、地域智能推荐，带详细做法和营养数据。

> 💡 **本项目是 [OpenClaw](https://github.com/openclaw) 的 Skill 插件**，通过 ClawHub 安装：
>
> ```bash
> clawhub install daily-meal-planner
> ```
>
> 安装后即可在 OpenClaw 中直接使用，无需手动克隆。

---

## ✨ 核心功能

### 🍽️ 智能三菜推荐

每餐推荐 **3 套完整套餐**（主菜+配菜+汤/主食）：

1. **📌 综合智能推荐** — 结合季节、周几、天气、用户画像加权评分
2. **🌿 时令之选** — 纯按当季食材筛选
3. **🎲 随机惊喜** — 换换口味也不错

### 👤 用户画像系统

自动收集并保存到本地（`user_profile.json`）：

| 维度 | 示例 | 作用 |
|---|---|---|
| 地点 | 北京、上海、成都 | 自动查天气、优先推荐本地风味 |
| 心情 | 开心/忙碌/疲惫/放松/庆祝 | 心情→菜品匹配 |
| 想吃类别 | 主食/肉/素/汤/辣/清淡/甜 | 类别→标签匹配 |
| 偏好菜系 | 川菜/粤菜/鲁菜/京味/江浙 | 家乡味道加权 |
| 饮食目标 | 减肥/增肌/保持/养生 | 低卡/高蛋白/滋补模式 |
| 过敏食材 | 花生、海鲜 | 安全过滤 |

### 🌤️ 自动天气适配

支持 **11 种天气类型**智能推荐：炎热、寒冷、雨天、晴天、雾霾、下雪、大风、降温、升温、闷热、干燥。

### 🗓️ 一周菜单规划

- **周一**：清淡养胃，开启新一周
- **周三**：过半犒劳，吃点好的
- **周五**：辛苦一周，庆祝一下 🎉
- **周末**：休闲时光，丰盛硬菜

### 🍃 四季养生提示

| 季节 | 月份 | 养生建议 |
|---|---|---|
| 🌸 春 | 3-5月 | 宜养肝，多食绿色蔬菜 |
| ☀️ 夏 | 6-8月 | 宜清热，多食瓜果凉菜 |
| 🍂 秋 | 9-11月 | 宜润燥，多食银耳、梨 |
| ❄️ 冬 | 12-2月 | 宜温补，多食牛羊肉 |

---

## 🚀 快速开始

### 作为 OpenClaw Skill 安装（推荐）

```bash
clawhub install daily-meal-planner
```

安装后直接在 OpenClaw / QClaw 对话中使用即可，无需额外配置。

### 作为独立项目使用

```bash
# 克隆项目
git clone https://github.com/GMMG55/daily-meal-planner.git
cd daily-meal-planner

# 无需安装依赖，Python 标准库即可运行
python scripts/meal_recommend.py daily
```

### 使用

```bash
# 今日推荐（自动判断餐次）
python scripts/meal_recommend.py daily

# 指定餐次
python scripts/meal_recommend.py daily --meal 午餐
python scripts/meal_recommend.py daily --meal 晚餐
python scripts/meal_recommend.py daily -m 下午茶

# 指定天气
python scripts/meal_recommend.py daily --weather rainy

# 一周菜单
python scripts/meal_recommend.py weekly

# 搜索菜品
python scripts/meal_recommend.py search 番茄

# 查看详细做法
python scripts/meal_recommend.py detail 番茄牛腩
```

---

## 📊 菜品数据库

内置 **32 道经典家常菜**，覆盖 4 个餐次：

- **早餐**：粥品、面点、蛋类、豆浆油条等
- **午餐**：米饭套餐、面条、炒菜等
- **晚餐**：正餐套餐、粥品等
- **下午茶/夜宵**：简餐、甜品、轻食等

每道菜包含：
- 热量数据（kcal）
- 营养标签（低卡/高蛋白/养生等）
- 详细做法步骤
- 食材清单
- 季节标签（春夏秋冬）
- 地域标签（川/粤/鲁/京/江浙等）

---

## 📁 项目结构

```
daily-meal-planner/
├── SKILL.md              # OpenClaw Skill 定义文件
├── README.md             # 项目说明（本文件）
├── LICENSE               # MIT 开源协议
├── .gitignore            # Git 忽略文件
├── scripts/
│   ├── meal_recommend.py # 核心推荐脚本
│   ├── meal_search.py    # 搜索脚本
│   └── meals_db.json     # 菜品数据库
├── assets/               # 资源文件
└── references/           # 参考资料
```

---

## 🔧 技术细节

- **Python 3.8+** — 仅使用标准库，无第三方依赖
- **wttr.in API** — 免费天气查询
- **JSON 数据存储** — 用户画像本地保存

---

## 📜 开源协议

本项目基于 **MIT 协议** 开源，欢迎自由使用、修改和分发。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 🙏 致谢

- 天气数据：[wttr.in](https://wttr.in)
- 食材数据：基于家常菜谱整理

---


