# Vue.js 项目开发指南

## 项目技术栈概览

本项目（chinese-poetry-data-mining）的前端采用 Vue 3 作为核心框架，结合现代前端工具链构建了一个诗词数据可视化应用。

### 核心技术版本

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | ^3.5.29 | 核心框架 |
| Vite | ^7.3.1 | 构建工具 |
| TypeScript | ~5.9.3 | 类型支持 |
| Vue Router | ^4.6.4 | 路由管理 |
| Naive UI | ^2.44.1 | UI 组件库 |
| @vueuse/core | ^14.2.1 | 组合式工具库 |

### 项目结构

```
web/
├── src/
│   ├── components/       # Vue 组件（按功能模块分组）
│   │   ├── author/       # 作者相关组件
│   │   ├── content/     # 内容展示组件
│   │   ├── data/        # 数据管理组件
│   │   ├── display/     # 可视化展示组件
│   │   ├── download/    # 下载功能组件
│   │   ├── feedback/    # 加载状态组件
│   │   ├── layout/      # 布局组件
│   │   ├── search/      # 搜索相关组件
│   │   └── ui/          # 基础 UI 组件
│   ├── composables/    # 组合式函数（Vue Composition API）
│   ├── router/          # 路由配置
│   ├── search/         # 搜索逻辑模块
│   ├── types/           # TypeScript 类型定义
│   ├── views/           # 页面视图组件
│   └── workers/         # Web Worker 配置
├── vite.config.ts       # Vite 配置
└── package.json         # 依赖配置
```

---

## Vue 3 核心特性

### 1. Composition API

本项目全面采用 Composition API 进行状态管理和逻辑复用，相比 Options API，Composition API 具有以下优势：

- **更好的逻辑复用**：通过 `composables` 目录组织可复用的状态逻辑
- **更好的类型推导**：与 TypeScript 无缝集成
- **更好的代码组织**：相关逻辑代码聚合在一起

```typescript
// composables/usePoemsV2.ts 示例
import { ref, computed, watch } from 'vue'
import type { Ref } from 'vue'

export function usePoemsV2() {
  const poems = ref([])
  const loading = ref(false)
  
  const filteredPoems = computed(() => {
    return poems.value.filter(poem => poem.content)
  })
  
  async function loadPoems() {
    loading.value = true
    // 加载逻辑
    loading.value = false
  }
  
  return {
    poems,
    loading,
    filteredPoems,
    loadPoems
  }
}
```

### 2. 响应式系统

Vue 3 的响应式系统基于 ES6 Proxy 实现，相比 Vue 2 的 Object.defineProperty：

- **深层响应**：默认支持深层响应式追踪
- **性能更好**：懒处理嵌套属性，初始化更快
- **数组支持更好**：可以直接监听数组变化

```typescript
// 项目中的响应式使用示例
const cacheData = ref<Map<string, any>>(new Map())

// 使用 computed 进行派生计算
const cachedData = computed(() => {
  return cacheData.value.get(cacheKey.value)
})
```

### 3. 组件系统

项目采用组件化架构，按功能模块分组：

- **单文件组件（SFC）**：`.vue` 文件包含 template、script、style
- **组件注册**：使用命名导出便于 tree-shaking
- **Props 定义**：使用 TypeScript 类型定义 props

```typescript
// components/content/index.ts - 组件统一导出
export { default as PoemCard } from './PoemCard.vue'
export { default as PoemContent } from './PoemContent.vue'
export { default as MeterPattern } from './MeterPattern.vue'
```

### 4. 路由管理

使用 Vue Router 4 进行单页应用路由管理：

```typescript
// router/index.ts
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue')
    },
    // ...其他路由
  ]
})
```

### 5. TypeScript 支持

项目使用 `vue-tsc` 进行类型检查，提供完整的类型支持：

- **类型推导**：组件 props、emits 自动推导
- **类型安全**：组合式函数返回类型明确
- **IDE 支持**：Volar 提供完整的 Vue SFC 类型支持

---

## 开发最佳实践

### 1. 组件设计原则

#### 单一职责

每个组件应该专注于单一功能，例如：

- `PoemCard.vue` - 仅负责诗词卡片展示
- `SearchInput.vue` - 仅负责搜索输入交互
- `AnimatedNumber.vue` - 仅负责数字动画

#### 组件分层

```
views/        # 页面级组件，处理路由和布局
components/   # 功能型组件，封装可复用 UI
ui/           # 基础 UI 组件，无业务逻辑
```

#### Props 定义规范

```typescript
// 使用 TypeScript 定义 props 类型
interface Props {
  title: string
  items: Poem[]
  loading?: boolean  // 可选 prop
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})
```

### 2. 组合式函数（Composables）

项目在 `composables/` 目录下封装了丰富的组合式函数：

| 文件 | 功能 |
|------|------|
| usePoemsV2.ts | 诗词数据加载与管理 |
| useAuthorsV2.ts | 作者数据管理 |
| useSearchIndexV2.ts | 搜索索引管理 |
| useCacheV2.ts | 数据缓存机制 |
| useChunkLoader.ts | 分块加载器 |
| useWorker.ts | Web Worker 管理 |

#### Composables 设计模式

```typescript
// 标准的 composable 函数结构
export function useXXX() {
  // 1. 响应式状态
  const data = ref<Type>(initialValue)
  
  // 2. 计算属性
  const processedData = computed(() => {
    return data.value.map(item => transform(item))
  })
  
  // 3. 方法
  async function fetchData() {
    // 异步逻辑
  }
  
  // 4. 生命周期
  onMounted(() => {
    fetchData()
  })
  
  // 5. 清理
  onUnmounted(() => {
    // 清理逻辑
  })
  
  return {
    data,
    processedData,
    fetchData
  }
}
```

### 3. 状态管理

#### 本地状态 vs 全局状态

- **组件本地状态**：使用 `ref/reactive`
- **跨组件共享**：使用 composables 封装
- **全局持久化**：结合 IndexedDB

```typescript
// 使用 composable 实现跨组件状态共享
const cacheState = ref<CacheRecord[]>([])

export function useCacheV2() {
  const cache = useSharedState('cache', () => cacheState)
  
  function setCache(key: string, value: any) {
    // 缓存逻辑
  }
  
  return { cache, setCache }
}
```

### 4. 性能优化实践

#### 懒加载路由

```typescript
// router/index.ts
const routes = [
  {
    path: '/poems',
    component: () => import('@/views/PoemsView.vue')
  }
]
```

#### Web Worker

对于耗时计算，使用 Web Worker 避免阻塞主线程：

```typescript
// workers/dataProcessor.worker.ts
self.onmessage = (e) => {
  const result = processHeavyData(e.data)
  self.postMessage(result)
}
```

#### 虚拟列表

对于长列表展示，考虑使用虚拟滚动：

```typescript
// 在大量数据展示场景使用
import { useVirtualList } from '@vueuse/core'
```

#### 依赖预构建

`vite.config.ts` 中配置预构建依赖：

```typescript
optimizeDeps: {
  include: [
    'vue',
    'vue-router',
    'naive-ui',
    '@vicons/ionicons5'
  ]
}
```

### 5. 代码规范

#### 命名规范

- **组件文件**：PascalCase（如 `PoemCard.vue`）
- **组合式函数**：camelCase，以 `use` 开头（如 `usePoemsV2.ts`）
- **类型文件**：PascalCase（如 `author.ts`）

#### 导入顺序

```typescript
// 1. Vue 核心
import { ref, computed, onMounted } from 'vue'
import type { Ref } from 'vue'

// 2. 外部库
import { useRouter } from 'vue-router'
import { NButton } from 'naive-ui'

// 3. 内部模块
import { usePoemsV2 } from '@/composables'
import PoemCard from '@/components/content/PoemCard.vue'

// 4. 类型
import type { Poem } from '@/types'
```

#### 响应式最佳实践

```typescript
// ✅ 正确：使用 ref 处理原始类型
const count = ref(0)

// ✅ 正确：使用 reactive 处理对象
const state = reactive({
  user: null,
  loading: false
})

// ✅ 正确：解构时使用 toRefs
const { user, loading } = toRefs(state)

// ❌ 避免：直接解构 reactive 对象
const { user, loading } = state  // 丢失响应性
```

### 6. 构建与部署

#### 开发环境

```bash
npm run dev
```

#### 生产构建

```bash
# 类型检查 + 构建
npm run build

# 带 hash 清单的构建（用于缓存优化）
npm run build:with-hash
```

#### 部署配置

项目配置了 GitHub Actions 自动部署到 GitHub Pages：

- 基础路径：`/chinese-poetry-data-mining/`
- 构建输出：`dist/` 目录

---

## 常用命令

| 命令 | 说明 |
|------|------|
| `npm install` | 安装依赖 |
| `npm run dev` | 启动开发服务器 |
| `npm run build` | 生产构建 |
| `npm run preview` | 预览构建结果 |
| `npm run type-check` | TypeScript 类型检查 |

---

## 扩展阅读

- [Vue 3 官方文档](https://vuejs.org/)
- [Vite 配置参考](https://vite.dev/config/)
- [Naive UI 组件库](https://www.naiveui.com/)
- [VueUse 工具库](https://vueuse.org/)
- [Vue Router 4](https://router.vuejs.org/)
