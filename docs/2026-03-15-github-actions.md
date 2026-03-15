# GitHub Actions 部署优化方案

日期: 2026-03-15

## 概述

本文档描述了将中文诗词数据挖掘项目部署到 GitHub Pages 的完整方案，包括跨平台软连接问题的解决方案和性能优化建议。

---

## 1. 部署工作流设计

### 1.1 触发条件优化

```yaml
on:
  push:
    branches:
      - main
    paths:
      - 'web/**'
      - 'results/**'
      - '.github/workflows/deploy-pages.yml'
  workflow_dispatch:
```

**优化点**: 使用 `paths` 过滤，只在相关文件变更时触发部署，避免不必要的构建。

### 1.2 并发控制

```yaml
concurrency:
  group: 'pages'
  cancel-in-progress: true
```

**优化点**: 防止多个部署同时运行，节省 GitHub Actions 运行时间。

---

## 2. 跨平台软连接问题解决方案

### 2.1 问题背景

- Windows 本地开发使用 `mklink` 创建软连接：`web\public\data` → `results`
- GitHub Actions 运行在 Ubuntu 上，软连接可能无法正确解析
- Git 对软连接的处理在不同平台上有差异

### 2.2 解决方案：构建时复制

在 GitHub Actions 中采用**构建时复制**策略，而非依赖软连接：

```yaml
- name: Setup data directory (cross-platform symlink workaround)
  run: |
    mkdir -p web/public/data
    cp -r results/author web/public/data/
    cp -r results/preprocessed web/public/data/
    cp -r results/wordcount web/public/data/
```

**优点**:
- 完全跨平台兼容
- 可以选择性复制必要数据，减少部署体积
- 不依赖 Git 的软连接支持

---

## 3. 数据体积分析与优化建议

### 3.1 当前数据分布

| 目录 | 大小 | 文件数 | 用途 |
|------|------|--------|------|
| `results/author/` | ~52 MB | ~857 个 | 作者统计信息 |
| `results/preprocessed/` | ~243 MB | 多个CSV | 诗词预处理数据 |
| `results/wordcount/` | ~16 MB | 多个JSON | 词频统计 |
| `results/word_similarity_v2/` | ~1.8 GB | ~231 个 | 词相似度计算 |
| **总计** | **~12 GB** | **大量** | - |

### 3.2 当前部署策略

当前工作流只复制了**约 311 MB** 的必要数据：
- author: 52 MB
- preprocessed: 243 MB
- wordcount: 16 MB

排除了 word_similarity_v2 (1.8 GB) 等大数据集。

---

## 4. 进一步优化建议

### 4.1 短期优化（立即可实施）

#### A. 启用 Git LFS 管理大文件

```bash
# 安装 Git LFS
git lfs install

# 追踪大 JSON 文件
git lfs track "results/**/*.json"
git lfs track "results/**/*.csv"
```

**效果**: 减少 Git 仓库体积，加快 clone 速度。

#### B. 使用 actions/cache 缓存依赖

```yaml
- name: Cache node modules
  uses: actions/cache@v4
  with:
    path: web/node_modules
    key: ${{ runner.os }}-node-${{ hashFiles('web/package-lock.json') }}
```

**效果**: 减少 npm install 时间。

#### C. 数据压缩传输

```yaml
- name: Compress data
  run: |
    tar -czf data.tar.gz -C results author preprocessed wordcount

- name: Extract data
  run: |
    mkdir -p web/public/data
    tar -xzf data.tar.gz -C web/public/data
```

**效果**: 减少 I/O 操作时间。

### 4.2 中期优化（需要开发工作）

#### A. 数据懒加载 (Lazy Loading)

当前应用加载所有作者数据 (~857 个 chunks)，可以优化为：

```typescript
// 按需加载作者数据
const loadAuthorChunk = async (chunkId: number) => {
  const response = await fetch(`/data/author/author_chunk_${chunkId}.json`);
  return response.json();
};
```

**效果**: 减少初始页面加载时间。

#### B. 数据分版本存储

将数据分离到单独的仓库或存储服务：

```yaml
# 从 release 下载数据
- name: Download data from release
  run: |
    curl -L -o data.tar.gz \
      https://github.com/user/repo/releases/download/v1.0.0/data.tar.gz
```

**效果**: 
- 代码仓库保持轻量
- 数据版本独立管理
- 支持增量更新

#### C. 使用 CDN 或对象存储

将静态数据托管到：
- GitHub Release Assets
- Cloudflare R2 / AWS S3
- 国内：阿里云 OSS / 腾讯云 COS

```typescript
// 配置数据基地址
const DATA_BASE_URL = import.meta.env.VITE_DATA_URL || '/data';
```

**效果**: 
- 减少 GitHub Pages 带宽使用
- 提高国内访问速度
- 支持数据压缩和缓存

### 4.3 长期优化（架构层面）

#### A. 构建时数据预处理

在 CI 中执行数据转换，减少运行时开销：

```yaml
- name: Optimize data for web
  run: |
    # 合并小文件
    node scripts/merge-small-chunks.js
    # 生成压缩版本
    node scripts/compress-json.js
```

#### B. 使用 IndexedDB 缓存策略

应用已经使用了 IndexedDB，可以进一步优化：

```typescript
// 添加版本控制和增量更新
const DATA_VERSION = '1.0.0';

const checkForUpdates = async () => {
  const localVersion = await getCachedVersion();
  if (localVersion !== DATA_VERSION) {
    await updateData();
    await setCachedVersion(DATA_VERSION);
  }
};
```

#### C. Service Worker 缓存

```javascript
// sw.js
const DATA_CACHE = 'data-v1';

self.addEventListener('fetch', (event) => {
  if (event.request.url.includes('/data/')) {
    event.respondWith(
      caches.match(event.request).then((response) => {
        return response || fetch(event.request).then((fetchResponse) => {
          return caches.open(DATA_CACHE).then((cache) => {
            cache.put(event.request, fetchResponse.clone());
            return fetchResponse;
          });
        });
      })
    );
  }
});
```

---

## 5. 监控与维护

### 5.1 添加构建时间监控

```yaml
- name: Build with timing
  working-directory: ./web
  run: |
    echo "::group::Build Timing"
    time npm run build
    echo "::endgroup::"
```

### 5.2 部署后验证

```yaml
- name: Verify deployment
  run: |
    sleep 30  # 等待部署生效
    curl -s -o /dev/null -w "%{http_code}" \
      https://username.github.io/chinese-poetry-data-mining/
```

---

## 6. 总结

### 已实施的优化

1. ✅ 跨平台软连接问题解决（构建时复制）
2. ✅ 路径过滤减少不必要的构建
3. ✅ 并发控制避免资源浪费
4. ✅ 选择性复制数据（311 MB vs 12 GB）

### 建议的后续优化优先级
