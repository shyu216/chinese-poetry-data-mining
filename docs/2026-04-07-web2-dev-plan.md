# 2026-04-07 Web 2.0 开发计划

## 技术决策

继续用 **Vue 3 SPA**，不加 Nuxt。理由：

- 纯静态后端，SSR 没意义
- 团队熟悉，改动小
- Service Worker 足以解决缓存和离线

## 目标

做一个**快、持久、可版本化**的前端。

---

## 一、数据层重构

### 当前状态

```
results/                      # 原始数据（构建产物）
├── hash-manifest.json        # 有版本号 + hash
├── author/
├── poem_index/
├── keyword_index/
└── wordcount_v2/

web/public/data -> ???        # 前端怎么访问？
```

### 目标结构

```
results/
├── hash-manifest.json        # 保留
├── data.json                 # 前端热数据打包（合并 manifest + 少量 chunk）
├── chunks/                   # 分块数据
│   ├── poems/
│   ├── authors/
│   └── wordcount/
└── index/                    # 检索索引
    ├── poem_index/
    ├── keyword_index/
    └── word_index/

web/public/data -> results/   # 软链接
```

### 版本化机制

每次 mining 脚本跑完，生成新 `hash-manifest.json`：

```json
{
  "version": "2026-04-07T10:00:00.000Z",
  "files": {
    "data.json": "abc123",
    "chunks/poems/0000.json": "def456",
    ...
  }
}
```

前端启动时：

1. 拉 `manifest.json`（5分钟缓存）
2. 对比本地存储的 version
3. 不一致 → 按需下载新 chunk
4. 一致 → 用本地缓存

---

## 二、前端架构

```
web/src/
├── api/
│   ├── manifest.ts           # 版本检查 + 增量更新
│   ├── poems.ts             # 诗词 API
│   ├── authors.ts           # 作者 API
│   └── search.ts            # 搜索 API
├── stores/
│   ├── cache.ts             # IndexedDB 缓存管理
│   └── sync.ts              # 版本同步
├── composables/
│   ├── useManifest.ts       # 拉 manifest，对比版本
│   ├── useChunk.ts          # 按需加载 chunk
│   └── useOffline.ts        # 离线支持
├── views/                   # 页面（保留现有，稍作整理）
└── App.vue
```

### 核心函数

| 模块 | 函数 | 说明 |
|------|------|------|
| api/manifest.ts | `fetchManifest()` | 拉远程 manifest |
| api/manifest.ts | `checkUpdate()` | 对比版本，返回需要更新的文件列表 |
| stores/cache.ts | `getCached(key)` | 从 IndexedDB 读 |
| stores/cache.ts | `setCached(key, data)` | 写到 IndexedDB |
| composables/useChunk.ts | `loadChunk(type, id)` | 智能加载：本地有 → 返回本地；没有 → 拉远程 → 存本地 |

### 数据流

```
App 启动
  ↓
useManifest() 拉 manifest.json
  ↓
checkUpdate() 对比 version
  ↓
有更新？ → useChunk() 按需下载 → setCached() 存 IndexedDB
  ↓
无更新 → getCached() 读本地
  ↓
页面渲染
```

---

## 三、Service Worker

做两层缓存：

| 资源 | 缓存策略 |
|------|----------|
| manifest.json | NetworkFirst（总是拉最新的） |
| data.json / chunks/* | CacheFirst（本地优先） |
| JS/CSS 图片 | CacheFirst |

### 关键函数

```typescript
// sw.ts
register(({
  url, strategy
}: {
  url: Request,
  strategy: 'CacheFirst' | 'NetworkFirst' | 'StaleWhileRevalidate'
}) => {
  if (url.pathname.includes('manifest')) {
    return 'NetworkFirst'
  }
  if (url.pathname.includes('data/')) {
    return 'CacheFirst'
  }
  return 'CacheFirst'
})
```

---

## 四、IndexedDB 设计

用 `idb` 库（已有），表结构：

```typescript
interface CacheDB {
  manifest: {
    version: string
    updatedAt: number
  }
  data: {
    key: string      // 如 "poems_0001"
    value: any
    updatedAt: number
  }
  history: {
    id: number
    type: 'view' | 'search'
    query: string
    timestamp: number
  }
}
```

### 核心函数

```typescript
// stores/cache.ts
import { openDB } from 'idb'

const db = await openDB('poetry-cache', 1, {
  upgrade(db) {
    db.createObjectStore('manifest')
    db.createObjectStore('data')
    db.createObjectStore('history')
  }
})

async function getChunk(key: string) {
  return db.get('data', key)
}

async function setChunk(key: string, value: any) {
  return db.put('data', { value, updatedAt: Date.now() }, key)
}

async function getVersion() {
  return db.get('manifest', 'version')
}

async function setVersion(version: string) {
  return db.put('manifest', { version, updatedAt: Date.now() }, 'version')
}
```

---

## 五、按需加载策略

### 热数据（首页必备）

```
data.json（约 1MB）包含：
- manifest 摘要
- 前 100 首热门诗词
- 前 20 个热门作者
- 词频 Top 500
```

### 冷数据（按需加载）

```
用户点击详情 → 加载对应 chunk
用户搜索 → 加载搜索索引分片
用户看词云 → 加载 wordcount chunk
```

### 预取策略

```typescript
// 用户在诗词列表页，准备点详情
const preload = () => {
  // 预取相邻的 3 个 chunk
  for (let i = -1; i <= 1; i++) {
    const nextId = currentId + i
    if (!cache.has(`poems_${nextId}`)) {
      loadChunk('poems', nextId)
    }
  }
}
```

---

## 六、代码量估算

```
api/
├── manifest.ts      # 80 行
├── poems.ts         # 60 行
├── authors.ts       # 60 行
└── search.ts        # 60 行

stores/
├── cache.ts         # 120 行
└── sync.ts          # 80 行

composables/
├── useManifest.ts   # 60 行
├── useChunk.ts      # 100 行
└── useOffline.ts    # 60 行

sw.ts                # 80 行
```

总计约 **760 行 TypeScript**

---

## 七、执行顺序

### 第一步：建软链接

```bash
# 把 data 目录软链到 web/public/
cd web/public
mklink /D data ..\..\results
```

### 第二步：写版本检查

```typescript
// api/manifest.ts
// 拉 manifest + 对比版本 + 返回更新列表
```

### 第三步：写缓存层

```typescript
// stores/cache.ts
// IndexedDB 封装：get/set/list
```

### 第四步：改造 composables

```typescript
// composables/useChunk.ts
// 改造现有 usePoemsV2 等，改用新缓存层
```

### 第五步：加 Service Worker

```typescript
// sw.ts
// 注册 + 缓存策略
```

### 第六步：优化首页

```typescript
// 产出 data.json 热数据打包
// 包含前 100 首热门诗词
```

---

## 八、预期效果

| 指标 | 目标 |
|------|------|
| 首屏加载 | < 500KB + 1s LCP |
| 第二次访问 | 几乎即时（本地缓存） |
| 离线可用 | 是 |
| 版本更新 | 自动增量同步 |

---

这个计划先把**基础打扎实**——版本化、缓存、离线。然后再谈功能。
