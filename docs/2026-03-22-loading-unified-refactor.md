# Loading 系统统一重构方案

## 设计目标

将 `GlobalLoading.vue` 和 `SearchProgressFloat.vue` 合并成一个统一的 Loading 系统，支持两种模式：
- **Blocking Loading**: 全屏遮罩，阻塞用户交互，用于初始化、页面跳转等关键操作
- **Non-blocking Loading**: 浮动提示，不阻塞交互，用于后台搜索、数据加载等

全局只允许有一个 Loading 实例，每个 View 必须调用。

## 核心设计原则

1. **单一实例**: 全局只有一个 Loading 管理器
2. **状态驱动**: 所有状态变化通过 `useLoading` 统一管理
3. **UX 优化**: 诗意文案、进度可视化、平滑动画
4. **严格步骤**: 每个 View 的主函数必须每一步都更新 Loading 状态

## 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     UnifiedLoading System                    │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐      ┌──────────────┐                     │
│  │   Blocking   │      │ Non-blocking │                     │
│  │   (全屏)     │      │  (浮动提示)  │                     │
│  └──────┬───────┘      └──────┬───────┘                     │
│         │                     │                             │
│         └──────────┬──────────┘                             │
│                    │                                        │
│              ┌─────┴─────┐                                  │
│              │ useLoading │  ← 单一实例                      │
│              └─────┬─────┘                                  │
│                    │                                        │
│    ┌───────────────┼───────────────┐                        │
│    │               │               │                        │
│ ┌──┴──┐      ┌────┴────┐     ┌────┴────┐                   │
│ │State │      │ Actions │     │ Getters │                   │
│ │状态  │      │ 操作    │     │ 计算属性 │                   │
│ └─────┘      └─────────┘     └─────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

## 状态定义

```typescript
// Loading 模式
export type LoadingMode = 'blocking' | 'non-blocking' | 'idle'

// Loading 阶段 - 诗意化
export type LoadingPhase = 
  | 'init'      // 初始化
  | 'connect'   // 连接中
  | 'metadata'  // 读取元数据
  | 'data'      // 加载数据
  | 'search'    // 搜索中
  | 'render'    // 渲染中
  | 'complete'  // 完成
  | 'error'     // 错误

// 统一 Loading 状态
export interface UnifiedLoadingState {
  mode: LoadingMode           // 当前模式
  phase: LoadingPhase         // 当前阶段
  title: string              // 主标题
  description: string        // 描述文案
  progress: number           // 进度 0-100
  current: number            // 当前进度数值
  total: number              // 总数值
  startTime: number          // 开始时间
  canCancel: boolean         // 是否可取消
  error?: string             // 错误信息
}
```

## API 设计

```typescript
export interface UseUnifiedLoadingReturn {
  // 状态（只读）
  readonly state: UnifiedLoadingState
  readonly isLoading: boolean
  readonly isBlocking: boolean
  readonly isNonBlocking: boolean
  readonly progressPercent: number
  readonly elapsedTime: number
  
  // 核心方法
  startBlocking: (title: string, description?: string) => void
  startNonBlocking: (title: string, description?: string) => void
  update: (updates: Partial<UnifiedLoadingState>) => void
  updatePhase: (phase: LoadingPhase, description?: string) => void
  updateProgress: (current: number, total: number, description?: string) => void
  finish: () => void
  error: (message: string) => void
  
  // 便捷方法 - 预定义流程
  startViewLoad: (viewName: string) => void
  startSearch: (keyword: string) => void
  startDataFetch: (dataType: string) => void
}
```

## 诗意文案库

```typescript
const phaseDescriptions: Record<LoadingPhase, string[]> = {
  init: [
    '文脉初启，正在唤醒千年诗魂...',
    '墨香浮动，正在铺展宣纸...',
    '笔尖轻触，正在研墨调锋...'
  ],
  connect: [
    '正在架设通往诗海的桥梁...',
    '正在拨动连接古今的琴弦...',
    '正在打开通往文脉的大门...'
  ],
  metadata: [
    '正在翻阅诗词典藏目录...',
    '正在整理诗人名录档案...',
    '正在检索千年文脉索引...'
  ],
  data: [
    '正在汇聚唐诗宋词精华...',
    '正在采撷历代诗词瑰宝...',
    '正在装载千古诗文典籍...'
  ],
  search: [
    '正在诗海中寻觅佳句...',
    '正在古籍中搜寻踪迹...',
    '正在词林间探寻意境...'
  ],
  render: [
    '正在描绘诗意画卷...',
    '正在勾勒文字之美...',
    '正在呈现诗境风华...'
  ],
  complete: [
    '文脉已通，请君品鉴...',
    '诗海已开，任君遨游...',
    '墨香已至，静候赏析...'
  ],
  error: [
    '墨尽纸枯，请稍后再试...',
    '文脉暂断，正在重连...',
    '诗海起波，请刷新页面...'
  ]
}
```

## View 修改清单

### 1. HomeView.vue
**当前状态**: 已使用 `useLoading`，使用 `startBlocking`
**修改内容**:
- 重构 `loadAllData` 函数，每一步都更新 Loading 状态
- 使用新的 `updatePhase` 和 `updateProgress` 方法

```typescript
const loadAllData = async () => {
  animationStarted.value = false
  
  // 步骤 1: 初始化
  loading.startBlocking('文脉初启', '正在唤醒诗魂...')
  
  // 步骤 2: 加载诗词元数据
  loading.updatePhase('metadata', '正在翻阅诗词典藏...')
  loading.updateProgress(0, 3)
  await poemsV2.loadMetadata()
  
  // 步骤 3: 加载诗人数据
  loading.updateProgress(1, 3, '正在整理诗人名录...')
  await authorsV2.loadMetadata()
  
  // 步骤 4: 加载词频数据
  loading.updateProgress(2, 3, '正在汇聚词频统计...')
  await wordSimilarityV2.loadMetadata()
  
  // 步骤 5: 完成
  loading.updatePhase('complete', '文脉已通，请君品鉴')
  loading.updateProgress(3, 3)
  
  setTimeout(() => {
    loading.finish()
    animationStarted.value = true
  }, 500)
}
```

### 2. PoemsView.vue
**当前状态**: 使用 `globalLoading` 变量但未实际调用
**修改内容**:
- 在 `onMounted` 中添加初始化 loading
- 在搜索时添加 non-blocking loading
- 在加载 chunk 时更新进度

```typescript
// 初始化
onMounted(async () => {
  loading.startBlocking('诗词典藏', '正在开启诗词宝库...')
  
  loading.updatePhase('metadata', '正在读取诗词索引...')
  await loadMetadata()
  
  loading.updatePhase('data', '正在加载诗词数据...')
  const cachedIds = await loadCachedChunks()
  
  if (cachedIds.length === 0) {
    loading.updatePhase('data', '首次访问，正在下载诗词...')
    await loadMoreChunks()
  }
  
  loading.updatePhase('complete', '诗词已备，请君赏析')
  loading.finish()
  isInitializing.value = false
})

// 搜索 - non-blocking
const performSearch = async () => {
  loading.startNonBlocking('诗海寻踪', `正在搜寻"${searchQuery.value}"...`)
  
  const result = await searchPoems(...)
  
  loading.updateProgress(result.items.length, result.total, `已找到 ${result.total} 首相关诗词`)
  
  loading.finish()
}
```

### 3. AuthorsView.vue
**当前状态**: 类似 PoemsView，使用 `globalLoading` 变量
**修改内容**:
- 初始化流程同 PoemsView
- 搜索使用 non-blocking

### 4. AuthorDetailView.vue
**当前状态**: 已使用 `startBlocking`
**修改内容**:
- 优化步骤粒度
- 在加载诗词作品时显示进度

```typescript
const loadAuthorData = async () => {
  loading.startBlocking('诗人详情', '正在寻访诗人足迹...')
  
  loading.updatePhase('metadata', '正在读取诗人档案...')
  author.value = await getAuthorByName(authorName.value)
  
  if (author.value?.poem_ids.length) {
    loading.updatePhase('data', `正在收集 ${author.value.poem_ids.length} 首作品...`)
    await loadAuthorPoems()
  }
  
  loading.updatePhase('complete', '诗人档案已备')
  loading.finish()
}

const loadAuthorPoems = async () => {
  const total = author.value!.poem_ids.length
  const batchSize = 50
  
  for (let i = 0; i < total; i += batchSize) {
    loading.updateProgress(i, total, `已加载 ${i}/${total} 首...`)
    // ... 加载逻辑
  }
}
```

### 5. PoemDetailView.vue
**当前状态**: 已使用 `startBlocking`
**修改内容**:
- 简化步骤，直接显示加载状态

```typescript
const loadPoemData = async () => {
  loading.startBlocking('诗词详情', '正在展开诗卷...')
  
  poem.value = await getPoemById(poemId.value, chunkId.value)
  
  if (poem.value) {
    loading.updatePhase('complete', '诗卷已展')
  } else {
    loading.error('未找到该诗词')
    return
  }
  
  loading.finish()
}
```

### 6. KeywordDetailView.vue
**当前状态**: 未使用 loading
**修改内容**:
- 添加 blocking loading 用于初始化
- 在批量加载诗词时更新进度

```typescript
onMounted(async () => {
  loading.startBlocking('词境探幽', `正在探寻"${keyword.value}"的诗意世界...`)
  
  loading.updatePhase('search', '正在检索相关诗词...')
  poemIds.value = await keywordIndex.getPoemIdsByKeyword(keyword.value)
  
  loading.updatePhase('data', `正在加载 ${poemIds.value.length} 首相关诗词...`)
  await loadPoemsBatch(poemIds.value, true)
  
  loading.updatePhase('complete', '词境已现')
  loading.finish()
})
```

### 7. WordCountView.vue
**当前状态**: 使用 `globalLoading` 变量
**修改内容**:
- 初始化使用 blocking
- 词境模块加载使用 non-blocking

### 8. DataView.vue / DataOverviewView.vue / DataDownloadView.vue / DataStorageView.vue
**当前状态**: DataView 未使用 loading，子 view 简单
**修改内容**:
- DataView 添加简单的页面切换 loading
- 子 view 在加载数据时添加 loading

### 9. ComponentDemoView.vue
**当前状态**: 演示页面，无数据加载
**修改内容**:
- 可选：添加模拟 loading 演示

### 10. TestView.vue
**当前状态**: 测试页面
**修改内容**:
- 每个测试函数添加 loading 状态

## 文件修改清单

### 核心文件（必须修改）
1. `web/src/composables/useLoading.ts` - 重构为统一 Loading 系统
2. `web/src/components/UnifiedLoading.vue` - 合并 GlobalLoading 和 SearchProgressFloat
3. `web/src/App.vue` - 更新组件引用

### View 文件（必须修改）
1. `web/src/views/HomeView.vue` - 优化 loading 步骤
2. `web/src/views/PoemsView.vue` - 添加完整 loading 流程
3. `web/src/views/AuthorsView.vue` - 添加完整 loading 流程
4. `web/src/views/AuthorDetailView.vue` - 优化 loading 步骤
5. `web/src/views/PoemDetailView.vue` - 优化 loading 步骤
6. `web/src/views/KeywordDetailView.vue` - 添加 loading
7. `web/src/views/WordCountView.vue` - 添加完整 loading 流程
8. `web/src/views/DataView.vue` - 添加简单 loading
9. `web/src/views/DataOverviewView.vue` - 添加 loading
10. `web/src/views/DataDownloadView.vue` - 添加 loading
11. `web/src/views/DataStorageView.vue` - 添加 loading
12. `web/src/views/TestView.vue` - 添加 loading

### 可选修改
13. `web/src/views/ComponentDemoView.vue` - 演示 loading

## 实施步骤

### Phase 1: 核心重构 ✅ 已完成
1. ✅ 重构 `useLoading.ts` - 支持单一实例和双模式
2. ✅ 创建 `UnifiedLoading.vue` - 合并 GlobalLoading 和 SearchProgressFloat
3. ✅ 更新 `App.vue` - 使用 UnifiedLoading 组件

### Phase 2: View 逐个迁移 ✅ 已完成
按优先级顺序：
1. ✅ HomeView - 已使用新 API，优化步骤
2. ✅ PoemsView - 已迁移，使用 blocking + non-blocking 模式
3. ✅ AuthorsView - 已迁移，使用 blocking + non-blocking 模式
4. ✅ AuthorDetailView - 已迁移，优化加载步骤
5. ✅ PoemDetailView - 已迁移，简化流程
6. ✅ KeywordDetailView - 已迁移，添加完整 loading 流程
7. ⏳ WordCountView - 需要继续完成
8. ✅ DataOverviewView - 已添加 loading

### Phase 3: 清理 ⏳ 待完成
1. ⏳ 删除 `GlobalLoading.vue`
2. ⏳ 删除 `SearchProgressFloat.vue`
3. ⏳ 测试所有 View

## UX 优化细节

### 1. 进度计算
- 有明确步骤时：按步骤平均分配进度
- 数据加载时：按已加载/总数计算
- 不确定时：显示循环动画

### 2. 文案动态更新
- 每 3-5 秒自动轮换同阶段的不同文案
- 进度变化时更新描述
- 支持自定义文案覆盖

### 3. 视觉反馈
- Blocking: 水墨风格全屏遮罩
- Non-blocking: 右上角浮动卡片
- 过渡动画：淡入淡出 + 位移动画

### 4. 错误处理
- 自动重试 3 次
- 显示友好错误文案
- 提供刷新按钮

## 代码示例

### View 中使用模板

```vue
<script setup lang="ts">
import { onMounted } from 'vue'
import { useLoading } from '@/composables/useLoading'

const loading = useLoading()

onMounted(async () => {
  // 开始 blocking loading
  loading.startBlocking('页面标题', '初始描述...')
  
  try {
    // 步骤 1
    loading.updatePhase('metadata', '步骤1描述...')
    loading.updateProgress(0, 3)
    await step1()
    
    // 步骤 2
    loading.updateProgress(1, 3, '步骤2描述...')
    await step2()
    
    // 步骤 3
    loading.updateProgress(2, 3, '步骤3描述...')
    await step3()
    
    // 完成
    loading.updatePhase('complete', '完成描述...')
    loading.updateProgress(3, 3)
    
    setTimeout(() => loading.finish(), 500)
  } catch (e) {
    loading.error('加载失败，请刷新重试')
  }
})

const handleSearch = async () => {
  // 开始 non-blocking loading
  loading.startNonBlocking('搜索标题', '搜索描述...')
  
  const result = await search()
  
  loading.updateProgress(result.loaded, result.total)
  
  loading.finish()
}
</script>
```
