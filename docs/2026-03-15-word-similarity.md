# 高频词相似词查找 - 开发方案

## 概述

本方案使用 FastText 词向量模型，查找诗词中高频词的相似词，用于分析诗词用词规律和语义关联。

---

## 输入数据

### FastText 模型
- **路径**: `results/fasttext/poetry.model`
- **参数**:
  - 向量维度: 100
  - 最小词频: 5
  - 词表大小: 115,255

### 全局词频
- **来源**: FastText 模型词表（vocab 中包含词频信息）
- **用途**: 获取全局高频词列表

---

## 输出数据

- **目录**: `results/word_similarity/`

### 1. word_similarity_summary.json

按词频排序的词汇列表，每个词包含所有相似词（相似度 > 阈值）：

```json
[
  {
    "word": "明月",
    "frequency": 5000,
    "similar_words": [
      {"word": "圆月", "similarity": 0.92},
      {"word": "皓月", "similarity": 0.89},
      {"word": "清风", "similarity": 0.85},
      ...
    ]
  },
  {
    "word": "清风",
    "frequency": 4500,
    "similar_words": [...]
  }
]
```

### 2. word_chunk_*.json（分块文件）

按词频排序，分块存储：
- 每N个词一个chunk文件
- 每个词保留完整相似词列表（相似度 > 阈值）
- 包含词频、相似词及相似度

---

## 处理流程

### 步骤1: 获取高频词列表

1. 从词频索引中获取全局高频词
2. 按词频降序排序
3. 分批次处理

### 步骤2: FastText 相似词查找

1. 加载 FastText 模型
2. 对每个词，查找所有相似词（相似度 > 阈值）
3. 保留完整结果

### 步骤3: 分块输出

1. 按词频排序
2. 分chunk输出到文件

---

## 技术参数

- 相似度阈值: 0.5（可调整）
- 每chunk词数: 1000

---

## 待实现脚本

- `scripts/find_word_similarity.py` - 主处理脚本

---

## 运行命令

```bash
python scripts/find_word_similarity.py
```
