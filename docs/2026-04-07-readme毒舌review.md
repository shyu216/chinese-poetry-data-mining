# 2026-04-07 千万用户重构计划

上个月只有5个人访问。老板要1000万。我是第一天接手的新人。

## 一、人群画像与痛点

### 10类广泛人群

1. **学生** 写作业找素材，考试复习背诗
2. **诗词爱好者** 想深入阅读，但现有体验太单调
3. **创作者** 写歌词、文案、PPT需要灵感
4. **老师** 找教学素材，课堂演示
5. **家长** 给孩子早教，背诗打卡
6. **网红/KOL** 发小红书/抖音装文化人
7. **程序员** 学前端练手，做项目展示
8. **投资人** 看AI项目潜力
9. **外国人** 学中文，对中国文化好奇
10. **老年人** 怀旧，回忆年轻时学的诗

### 他们的痛点

| 人群 | 痛点 |
|------|------|
| 学生 | 搜索结果太乱，没有考试重点标记 |
| 爱好者 | 只能看字，没有朗读、没有赏析 |
| 创作者 | 没有金句摘抄，没有灵感触发 |
| 老师 | 没有教案配套，没有分级难度 |
| 家长 | 不知道孩子该背哪首，没有打卡 |
| 网红 | 分享出去没人点赞，没有社交货币 |
| 程序员 | 代码没有GitHub star，不能展示 |
| 投资人 | 不知道这个项目有什么数据资产 |
| 外国人 | 界面全是中文，看不懂 |
| 老年人 | 字号太小，操作太复杂 |

### 他们追求什么

- **快**：3秒内看到结果
- **有用**：能解决具体问题（背诗/找素材/教学）
- **能装逼**：分享出去有人点赞
- **有文化**：感觉自己有文化
- **简单**：别让我学就会

## 二、Mining 重构计划

### 目标

产出**可直接被前端消费**的数据，拒绝半成品。

### 当前问题

- 产物分散，v1/v2/v3 不知道用哪个
- 没有版本追踪
- 脚本运行顺序靠猜

### 新架构

```
scripts/
├── pipeline/
│   ├── 01_preprocess.py        # 统一入口，按顺序执行所有前置处理
│   ├── 02_build_poem_index.py  # 诗词检索索引
│   ├── 03_build_author.py      # 作者数据 + 相似度 + 聚类
│   ├── 04_build_wordcount.py   # 词频统计
│   ├── 05_build_word_sim.py    # 词向量 + 相似词
│   ├── 06_build_keyword.py     # 关键词索引
│   └── 07_build_frontend_data.py  # 打包前端需要的精简数据
├── lib/
│   ├── config.py                # 统一配置，版本号在这里改
│   ├── io.py                   # 读写文件封装
│   └── utils.py                # 工具函数
└── requirements.txt
```

### 关键脚本与函数

| 脚本 | 核心函数 | 输出 |
|------|----------|------|
| 01_preprocess.py | `clean_poem()`, `simplify_text()`, `normalize_dynasty()` | poems_clean.csv |
| 02_build_poem_index.py | `build_inverted_index()`, `build_manifest()` | poem_index/*.json |
| 03_build_author.py | `calc_similarity()`, `clustering()`, `export_frontend_author_data()` | author_data.json |
| 04_build_wordcount.py | `count_words()`, `export_chunked()` | wordcount_v2/chunk_*.json |
| 05_build_word_sim.py | `train_fasttext()`, `export_onnx()`, `build_word_sim_index()` | word_similarity.fb |
| 06_build_keyword.py | `extract_keywords()`, `build_manifest()` | keyword_index/*.json |
| 07_build_frontend_data.py | `bundle_hot_data()`, `generate_manifest()` | frontend_manifest.json |

### 数据量预估

| 产物 | 大小 | 说明 |
|------|------|------|
| poems_clean.csv | ~30MB | 约30万首诗词 |
| poem_index/ | ~50MB | 倒排索引 + manifest |
| author_data.json | ~5MB | 作者 + 相似度 + 聚类 |
| wordcount_v2/ | ~20MB | 分块词频 |
| word_similarity.fb | ~100MB | FlatBuffers 词向量 |
| keyword_index/ | ~30MB | 关键词索引 |
| frontend_manifest.json | ~1MB | 前端热数据打包 |

### 代码量

```
scripts/
├── pipeline/     # 7个主脚本，约 2000 行
├── lib/          # 3个工具模块，约 500 行
└── tests/        # 单元测试，约 300 行
```

总计约 **2800 行 Python**

## 三、Web 重构计划

### 目标

1000万用户 = **必须能扛流量 + 必须能传播**

### 当前问题

- 全量加载，首屏慢
- 没有个性化
- 没有分享动机
- 没有用户系统
- 外国人和老年人体验差

### 新架构

```
web/src/
├── api/                    # 统一 API 层
│   ├── index.ts           # 入口
│   ├── poem.ts            # 诗词 API
│   ├── author.ts          # 作者 API
│   └── user.ts            # 用户 API（新增）
├── stores/                # Pinia 状态管理
│   ├── user.ts            # 用户偏好、登录态
│   ├── history.ts         # 浏览/搜索历史
│   └── settings.ts        # 主题、字号、语言
├── composables/            # 保留，简化
│   └── useApi.ts          # 统一调用 api/
├── views/
│   ├── HomeView.vue       # 重新设计首页
│   ├── PoemView.vue       # 合并 poems/detail
│   ├── AuthorView.vue     # 合并 authors 相关
│   ├── WordView.vue       # 词云/词频
│   ├── TeachView.vue      # 【新增】教学专区
│   ├── CreateView.vue     # 【新增】创作灵感
│   ├── ShareView.vue      # 【新增】分享落地页
│   ├── SocialView.vue     # 【新增】社区/打卡
│   └── SettingsView.vue  # 【新增】个性化设置
└── i18n/                  # 【新增】国际化
    ├── en.json
    ├── zh.json
    └── ja.json
```

### 关键技术选型

| 需求 | 技术 | 理由 |
|------|------|------|
| 状态管理 | Pinia | 比 Vuex 轻，TypeScript 友好 |
| 国际化 | vue-i18n | 官方推荐 |
| 用户系统 | Supabase / Firebase | 快速上线，扛并发 |
| 分析 | Google Analytics 4 / Plausible | 不影响性能 |
| CDN | Cloudflare | 免费，边缘计算 |
| 部署 | Vercel / Cloudflare Pages | 免费，CDN 加速 |
| SSR | Nuxt 3 | SEO 必须 |

### 关键函数

| 模块 | 函数 | 说明 |
|------|------|------|
| api/poem.ts | `searchPoems(query, filters)` | 统一搜索入口 |
| api/poem.ts | `getPoemDetail(id)` | 详情页数据 |
| api/user.ts | `getRecommendations()` | 个性化推荐 |
| stores/user.ts | `loadPreferences()` | 加载用户设置 |
| composables/useApi.ts | `useRequest()` | 请求封装，带缓存 |

### 首屏加载优化

```
首屏目标：< 500KB JS，< 1s LCP

策略：
1. 关键数据预加载（manifest.json）
2. 骨架屏 + 渐进加载
3. 图片懒加载
4. Service Worker 缓存
5. CDN 边缘缓存
```

### 代码量

```
web/src/
├── api/          # 约 300 行
├── stores/       # 约 400 行
├── composables/ # 精简到约 500 行
├── views/        # 约 10 个页面，约 3000 行
└── i18n/         # 约 500 行
```

总计约 **4700 行 TypeScript/Vue**

## 四、系统架构图

```
用户 → CDN → 静态资源 (JS/CSS/图片)
     ↓
  Vercel/Cloudflare Pages (边缘节点)
     ↓
  前端 (Vue SPA)
     ↓
  数据请求
     ↓
  静态 JSON/CSV (Cloudflare 缓存)
     ↓
  Supabase (用户数据/分析)

API 调用全部走 CDN 缓存，只有用户数据走后端
```

## 五、传播机制设计

### 分享场景

| 场景 | 触发 | 分享内容 |
|------|------|----------|
| 诗词详情页 | 点击分享按钮 | 带诗句卡片的海报 |
| 词云 | 点击分享 | 个人词云图片 |
| 学习打卡 | 完成背诗 | 成就海报 |
| 创作灵感 | 获得金句 | 金句卡片 |

### 增长飞轮

```
优质内容 → 分享 → 新用户 → 数据积累 → 更好推荐 → 更多分享
    ↑                                              ↓
    └──────────────────────────────────────────────┘
```

### 关键指标

| 指标 | 目标 |
|------|------|
| 日活 | 10万 |
| 分享率 | 20% |
| 次日留存 | 30% |
| 首屏加载 | < 1s |

## 六、执行优先级

### 第一阶段：止血 (1周)

1. 修复现有 bug
2. 完善 README（回答之前提的5个问题）
3. 添加基础分析（看看谁在访问）

### 第二阶段：MVP (2周)

1. 国际化（英文/日文）
2. 简化首页，提升首屏速度
3. 添加分享功能
4. 部署到 Cloudflare Pages

### 第三阶段：增长 (1个月)

1. 用户系统（匿名 + 登录）
2. 个性化推荐
3. 教学专区
4. 创作灵感页
5. 社交打卡

### 第四阶段：规模化 (3个月)

1. 多语言支持
2. 社区功能
3. API 开放
4. 品牌合作

---

这个计划很激进。但上个月5个人访问，不激进就是等死。
