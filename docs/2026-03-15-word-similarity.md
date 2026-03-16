# 2026-03-15 高频词相似词查找

## 方案

使用FastText词向量模型，查找诗词中高频词的相似词。

## 输入

- FastText模型: `results/fasttext/poetry.model`
- 向量维度: 100
- 词表大小: 115,255

## 输出

**word_similarity_summary.json**:
```json
[
  {
    "word": "明月",
    "frequency": 5000,
    "similar_words": [
      {"word": "圆月", "similarity": 0.92},
      {"word": "皓月", "similarity": 0.89}
    ]
  }
]
```

**word_chunk_*.json**: 分块存储，每块1000词

## 技术参数

- 相似度阈值: 0.5
- 每chunk词数: 1000

## 后续优化

紧凑数组格式减少体积：
```json
["明月", 5000, [["圆月", 0.92], ["皓月", 0.89]]]
```
