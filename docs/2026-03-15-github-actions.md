# 2026-03-15 GitHub Actions 部署优化

## 核心问题：跨平台软连接

**问题**: Windows本地使用`mklink`，GitHub Actions(Ubuntu)无法解析

**解决方案**: 构建时复制

```yaml
- name: Setup data directory
  run: |
    mkdir -p web/public/data
    cp -r results/author web/public/data/
    cp -r results/preprocessed web/public/data/
    cp -r results/wordcount web/public/data/
```

## 触发条件优化

```yaml
on:
  push:
    branches: [main]
    paths:
      - 'web/**'
      - 'results/**'
      - '.github/workflows/deploy-pages.yml'
```

## 数据体积分析

| 目录 | 大小 | 部署状态 |
|------|------|----------|
| results/author/ | ~52 MB | ✅ 部署 |
| results/preprocessed/ | ~243 MB | ✅ 部署 |
| results/wordcount/ | ~16 MB | ✅ 部署 |
| results/word_similarity_v2/ | ~1.8 GB | ❌ 排除 |
| **部署总计** | **~311 MB** | - |

## 并发控制

```yaml
concurrency:
  group: 'pages'
  cancel-in-progress: true
```

## 大数据部署选项（1.8GB）

| 方案 | 复杂度 | 成本 | 部署体积 |
|------|--------|------|----------|
| Git LFS + Release | 低 | 免费 | ~500MB |
| 外部CDN (R2/S3) | 中 | 免费额度 | 1.8GB |
| 数据压缩+按需加载 | 高 | 免费 | ~400MB |
| 功能降级/采样 | 低 | 免费 | ~100MB |
