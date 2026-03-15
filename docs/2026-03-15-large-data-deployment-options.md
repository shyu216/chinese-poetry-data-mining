# 大数据部署方案对比 - word_similarity_v2 (~1.8GB)

日期: 2026-03-15

## 背景

当前 `results/word_similarity_v2/` 约 1.8 GB，已被排除在 GitHub Pages 部署之外。
如果需要部署这部分数据，需要考虑 GitHub Pages 的 1GB 仓库限制和性能问题。

---

## 方案对比总览

| 方案 | 复杂度 | 成本 | 部署体积 | 访问速度 | 维护难度 |
|------|--------|------|----------|----------|----------|
| **A. Git LFS + Release** | 低 | 免费 | ~500MB (压缩后) | 中等 | 低 |
| **B. 外部 CDN (R2/S3)** | 中 | 免费额度 | 1.8GB | 快 | 中 |
| **C. 数据压缩 + 按需加载** | 高 | 免费 | ~400MB | 中等 | 高 |
| **D. 分仓库部署** | 中 | 免费 | 1.8GB | 中等 | 中 |
| **E. 功能降级/采样** | 低 | 免费 | ~100MB | 快 | 低 |

---

## 方案 A: Git LFS + GitHub Release

### 思路
将大数据打包上传到 GitHub Release，部署时下载解压。

### 实现步骤

1. **创建数据包**
```bash
# 压缩数据
tar -czf word_similarity_v2.tar.gz -C results word_similarity_v2

# 创建 Release
gh release create data-v1.0 word_similarity_v2.tar.gz \
  --title "Data v1.0" \
  --notes "Word similarity data"
```

2. **工作流修改**
```yaml
- name: Download word_similarity data
  run: |
    mkdir -p web/public/data
    curl -L -o /tmp/data.tar.gz \
      "https://github.com/${{ github.repository }}/releases/download/data-v1.0/word_similarity_v2.tar.gz"
    tar -xzf /tmp/data.tar.gz -C web/public/data/
```

### 优点
- 纯 GitHub 生态，无需外部服务
- 版本管理方便
- 实现简单

### 缺点
- 每次部署都要下载 500MB+ 数据
- 构建时间增加
- GitHub Release 也有带宽限制

---

## 方案 B: 外部 CDN (Cloudflare R2 / AWS S3)

### 思路
将数据托管到对象存储，前端直接访问 CDN 链接。

### 实现步骤

1. **上传数据到 R2**
```bash
# 使用 rclone
rclone copy results/word_similarity_v2 r2:poetry-data/word_similarity_v2

# 或使用 AWS CLI
aws s3 sync results/word_similarity_v2 s3://poetry-data-bucket/word_similarity_v2/
```

2. **配置 CORS**
```json
{
  "AllowedOrigins": ["https://username.github.io"],
  "AllowedMethods": ["GET", "HEAD"],
  "AllowedHeaders": ["*"]
}
```

3. **前端配置**
```typescript
// .env.production
VITE_DATA_URL=https://your-account.r2.cloudflarestorage.com/poetry-data

// 代码中使用
const DATA_URL = import.meta.env.VITE_DATA_URL || '/data'
fetch(`${DATA_URL}/word_similarity_v2/word_chunk_0000.json`)
```

### 优点
- 不占用 GitHub Pages 空间
- 访问速度快（全球 CDN）
- 可按需加载，无需打包

### 缺点
- 需要配置外部服务
- 国内访问可能需要额外配置
- 有出站流量费用（超出免费额度）

### 成本估算 (Cloudflare R2)
- 存储: 1.8GB × $0.015/GB = ~$0.03/月
- 请求: 前 1000 万次/月免费
- **实际成本: 基本免费**

---

## 方案 C: 数据压缩 + 按需解压

### 思路
将 JSON 数据压缩打包，前端使用 JavaScript 解压。

### 实现步骤

1. **构建时打包**
```yaml
- name: Pack word_similarity data
  run: |
    mkdir -p web/public/data/word_similarity_packed
    cd results/word_similarity_v2
    
    # 每 50 个文件打包
    for i in $(seq 0 50 230); do
      start=$(printf "%04d" $i)
      end=$(printf "%04d" $((i+49)))
      tar -czf "../../web/public/data/word_similarity_packed/pack_${start}_${end}.tar.gz" \
        word_chunk_${start..$end}.json
    done
```

2. **前端解压**
```typescript
import { decompress } from 'fflate'

const loadWordPack = async (word: string) => {
  const packIndex = Math.floor(getWordIndex(word) / 50)
  const start = String(packIndex * 50).padStart(4, '0')
  const end = String(packIndex * 50 + 49).padStart(4, '0')
  
  const response = await fetch(`/data/word_similarity_packed/pack_${start}_${end}.tar.gz`)
  const compressed = new Uint8Array(await response.arrayBuffer())
  
  // 解压
  const decompressed = await new Promise((resolve, reject) => {
    decompress(compressed, (err, data) => {
      if (err) reject(err)
      else resolve(data)
    })
  })
  
  return JSON.parse(new TextDecoder().decode(decompressed))
}
```

### 优点
- 部署体积减小 60-70%
- 减少传输时间
- 保持单域名部署

### 缺点
- 实现复杂
- 客户端解压有性能开销
- 需要引入解压库

---

## 方案 D: 分仓库部署

### 思路
创建独立的数据仓库，使用 GitHub Pages 或 Netlify 单独部署数据。

### 实现步骤

1. **创建数据仓库** `poetry-data-assets`
```
poetry-data-assets/
├── word_similarity_v2/
│   └── ...
└── .github/workflows/deploy-data.yml
```

2. **数据仓库工作流**
```yaml
# poetry-data-assets/.github/workflows/deploy-data.yml
name: Deploy Data
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/upload-pages-artifact@v3
        with:
          path: .
      - uses: actions/deploy-pages@v4
```

3. **主仓库配置**
```typescript
const DATA_BASE_URL = 'https://username.github.io/poetry-data-assets'
fetch(`${DATA_BASE_URL}/word_similarity_v2/...`)
```

### 优点
- 数据和代码完全分离
- 独立版本管理
- 可复用数据仓库

### 缺点
- 需要管理多个仓库
- 跨域问题需要处理
- 部署复杂度增加

---

## 方案 E: 功能降级/采样

### 思路
不部署全部数据，只部署高频词或采样数据。

### 实现方式

1. **高频词筛选**
```python
# 只保留出现频率 top 10000 的词
with open('word_freq.json') as f:
    freq = json.load(f)
    top_words = set(sorted(freq, key=freq.get, reverse=True)[:10000])

# 过滤相似度数据
for chunk in word_similarity_chunks:
    filtered = {k: v for k, v in chunk.items() if k in top_words}
    save(filtered)
```

2. **数据采样**
```python
# 每 10 个词保留 1 个
for i, chunk in enumerate(chunks):
    if i % 10 == 0:
        save(chunk)
```

### 优点
- 部署体积极小 (~100MB)
- 实现最简单
- 核心功能保留

### 缺点
- 功能不完整
- 部分词无法查询相似度
- 需要权衡采样策略

---

## 决策建议

### 如果追求简单快速
→ **方案 A** 或 **方案 E**

### 如果追求完整功能 + 性能
→ **方案 B** (Cloudflare R2)

### 如果追求极致优化
→ **方案 C** (需要开发时间)

### 如果追求架构清晰
→ **方案 D** (长期维护友好)

---

## 待决策问题

1. **word_similarity_v2 的使用场景是什么？**
   - 是否所有词都需要相似度查询？
   - 用户查询频率如何？

2. **预算考虑？**
   - 是否接受外部 CDN 服务？
   - 国内访问是否需要优化？

3. **开发资源？**
   - 是否有时间实现压缩/解压逻辑？
   - 是否愿意维护多仓库？

4. **数据更新频率？**
   - word_similarity 数据是否会频繁更新？
   - 更新时是否需要重新部署？

---

## 参考文档

- [GitHub Pages 限制](https://docs.github.com/en/pages/getting-started-with-github-pages/about-github-pages#usage-limits)
- [Cloudflare R2 定价](https://developers.cloudflare.com/r2/pricing/)
- [AWS S3 静态网站托管](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteHosting.html)
