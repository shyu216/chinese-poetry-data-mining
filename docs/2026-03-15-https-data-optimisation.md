# Web Dev 3 - 数据结构与 HTTPS 的故事

## 2026-03-15

---

## 背景

今天处理诗词数据挖掘项目，遇到了一个经典问题：**海量数据如何高效加载？**

从 6.8GB 压缩到 1.8GB，压缩比 3.8x，这是一个关于数据结构的真实故事。

---

## 问题：从 6.8GB 说起

诗人相似度分析生成了一个巨大的 `word_similarity_summary.json`：

```json
[
  {
    "word": "明月",
    "frequency": 5000,
    "similar_words": [
      {"word": "圆月", "similarity": 0.92},
      {"word": "皓月", "similarity": 0.89},
      ...
    ]
  }
]
```

- **原始大小**: 6,873 MB (6.8 GB!)
- **问题**: 浏览器根本无法加载

**罪魁祸首**：每个相似词都有 `{"word": xxx, "similarity": yyy}` 两个 key，重复了 thousands of times。

---

## 解决：紧凑数据结构

改为数组格式：

```json
[
  ["明月", 5000, [["圆月", 0.92], ["皓月", 0.89], ...]],
  ...
]
```

**结果**：
- 压缩到 **1,816 MB** (1.8 GB)
- 压缩比: **3.8x**

---

## HTTPS 的故事

等等，这和数据传输有什么关系？

HTTPS 本质上是在做两件事：
1. **加密** - 保护数据安全
2. **压缩** - （通过 TLS 压缩）提高传输效率

但更核心的是：**数据结构决定传输效率**

| 原始 JSON | 传输: 6.8GB | 解析: 慢 |
|---|---|---|
| 紧凑 JSON | 传输: 1.8GB | 解析: 快 |
| 二进制 | 传输: ~500MB | 解析: 极快 |

---

## 畅想：极快·高效的超多数据传输方案

### 未来方案 1: 流式 + 懒加载

```javascript
// 不一次性加载，按需获取
async function loadWordData(word) {
  const chunkId = await findChunk(word);
  return await fetch(`/data/word_chunk_${chunkId}.json`);
}
```

### 未来方案 2: WebAssembly + FlatBuffers

- FlatBuffers: 无需解析，直接读取内存
- WebAssembly: 接近原生的速度

```javascript
const data = FlatBuffers.decode(buffer);
console.log(data.word(0)); // O(1) 访问
```

### 未来方案 3: CRDT + P2P

- **CRDT** (无冲突复制数据类型): 分布式同步
- **P2P**: 去掉中心服务器，直接节点间传输

### 未来方案 4: 语义压缩

不只是 zlib 压缩，而是理解数据语义：

```
"similar_words": [{"word": "明月", "similarity": 0.99}]
→ 只传索引: [0, 99]  // 查表可得
```

### 未来方案 5: 边缘计算 + CDN

在 CDN 边缘节点预处理数据，客户端只获取精简结果。

---

## 结论

**数据结构 > 传输协议 > 压缩算法**

- 好的数据结构让 6.8GB → 1.8GB
- 好的传输协议让加载时间减少 50%
- 好的压缩算法让传输减少 30%

但最根本的，是**理解数据本质**，选择最合适的表达方式。

---

## 相关文件

- `scripts/rechunk_word_similarity.py` - 紧凑化脚本
- `results/word_similarity_v2/` - 紧凑数据输出
- `docs/2026-03-15-word-similarity.md` - 开发方案
