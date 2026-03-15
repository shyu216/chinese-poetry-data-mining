# 数据处理管线说明

> 记录诗词数据处理的完整流程和技术方案  
> **最后更新**: 2026-03-15

---

## 📊 数据规模概览

| 指标 | 数值 |
|------|------|
| 诗词总数 | 332,712 首 |
| 诗人数量 | 13,206 位 |
| 关键词数量 | 893,638 个 |
| 1-gram 数量 | 893,638 |
| 2-gram 数量 | 7,288,080 |
| 3-gram 数量 | 10,201,521 |

---

## 🔄 核心处理管线

### 管线一：词频统计与关键词索引

**脚本**: `scripts/word_frequency.py`

**功能**:
1. 读取 `results/preprocessed/poems_chunk_*.csv`
2. 使用 jieba 对每首诗进行分词
3. 添加 `words` 字段到 chunk 文件
4. 创建关键词到诗 hash 的映射索引

**输出**:
- `results/preprocessed/poems_chunk_*.csv` (更新后)
- `results/keyword_index/keyword_*.json`
- `results/keyword_index/metadata.json`

**运行**:
```bash
python scripts/word_frequency.py
```

---

### 管线二：N-gram 索引构建

**脚本**: `scripts/ngram_frequency.py`

**功能**:
1. 读取已分词的 chunk 文件
2. 提取 1-gram, 2-gram, 3-gram
3. 构建 N-gram 到诗 hash 的映射索引
4. 支持中间态恢复（checkpoint）

**输出**:
- `results/ngram_index/ngram_1_*.json`
- `results/ngram_index/ngram_2_*.json`
- `results/ngram_index/ngram_3_*.json`
- `results/ngram_index/metadata.json`

**运行**:
```bash
python scripts/ngram_frequency.py
```

---

### 管线三：FastText 词向量训练

**脚本**: 
- `scripts/fasttext_train.py` - 训练
- `scripts/fasttext_test.py` - 测试

**训练参数**:
```python
VECTOR_SIZE = 100   # 向量维度
MIN_COUNT = 5        # 最小词频
WINDOW = 5           # 上下文窗口
EPOCHS = 10          # 训练轮数
```

**输出**:
- `results/fasttext/poetry.model` (二进制模型)
- `results/fasttext/vocab.json` (词表)
- `results/fasttext/metadata.json` (元数据)

**运行**:
```bash
python scripts/fasttext_train.py
python scripts/fasttext_test.py
```

**测试效果**:
| 测试词 | 相似词 |
|--------|--------|
| 明月 | 望明月、明月光、秋月、皓月 |
| 春风 | 东风、春风来、借东风 |
| 青山 | 碧水青山、云山、留得青山 |
| 离别 | 别离、伤离别、别情 |

---

### 管线四：诗人相似度分析

**脚本**: `scripts/author_analyzer.py`

**算法**: TF-IDF 词频向量 + 余弦相似度

**验证案例** - 彭汝砺的相似诗人:
| 排名 | 相似诗人 | 相似度 | 历史身份 |
|------|----------|--------|----------|
| 1 | 王安石 | 0.8022 | 新党代表 |
| 2 | 苏轼 | 0.7778 | 旧党代表 |
| 3 | 张耒 | 0.772 | 苏门成员 |
| 4 | 黄庭坚 | 0.7707 | 苏门成员 |

**结论**: 算法成功发现诗人用词偏好与社交圈子的相关性

**输出**:
- `results/author/author_summary.json` - 诗人汇总
- `results/author/author_chunk_*.json` - 诗人详细数据
- `results/author-full/similarity_matrix.json` - 相似度矩阵

---

## 📁 数据目录结构

```
results/
├── preprocessed/          # 预处理后诗词数据
│   └── poems_chunk_*.csv
├── keyword_index/         # 关键词索引
│   ├── keyword_*.json
│   └── metadata.json
├── ngram_index/           # N-gram 索引
│   ├── ngram_1_*.json
│   ├── ngram_2_*.json
│   ├── ngram_3_*.json
│   └── metadata.json
├── fasttext/              # 词向量模型
│   ├── poetry.model
│   ├── vocab.json
│   └── metadata.json
├── author/                # 诗人分析结果
│   ├── author_summary.json
│   └── author_chunk_*.json
├── author-full/           # 完整诗人数据
│   ├── author_data_full.json
│   └── similarity_matrix.json
├── wordcount/             # 词频统计
│   └── wordfreq.csv
└── word_similarity_v2/    # 词相似度数据 (~1.8GB)
    └── word_chunk_*.json
```

---

## 🔧 辅助脚本

| 脚本 | 功能 |
|------|------|
| `wordcount.py` | 多进程词频统计 |
| `wordfreq_analysis.py` | 词频分布可视化 |
| `analyze_long_words.py` | 分析长词 (>3, >5 字符) |
| `analyze_unique_words.py` | 分析唯一词 |

---

## 📈 词频分析关键发现

### 基本统计
| 指标 | 数值 |
|------|------|
| 总词数 | 11,466,032 |
| 不同词数 | 893,638 |
| 最大词频 | 56,133 |
| 平均词频 | 12.83 |
| 中位数词频 | 1 |

### 词频分布
| 词频区间 | 词数 | 占比 |
|----------|------|------|
| =1 | 610,871 | 68.36% |
| 2-5 | 183,558 | 20.54% |
| 6-10 | 36,671 | 4.10% |
| 11-50 | 41,898 | 4.69% |
| >50 | 20,640 | 2.31% |

### 关键结论
- 68%的词只出现1次（长尾分布）
- 前10%高频词覆盖90%的总词次
- 建议 min_count=5~10 过滤低频噪声

---

## 🆚 技术对比

| 技术 | 用途 | 优点 | 缺点 |
|------|------|------|------|
| N-gram | 精确匹配检索 | 简单直接 | 不理解语义 |
| Word2Vec | 语义相似 | 捕捉语义 | 不支持OOV |
| FastText | 语义相似+子词 | 支持OOV | 效果略弱于Word2Vec |

---

## 💾 存储优化

### 数据结构优化案例

**原始格式** (6.8GB):
```json
{
  "word": "明月",
  "frequency": 5000,
  "similar_words": [
    {"word": "圆月", "similarity": 0.92},
    {"word": "皓月", "similarity": 0.89}
  ]
}
```

**紧凑格式** (1.8GB, 压缩比 3.8x):
```json
["明月", 5000, [["圆月", 0.92], ["皓月", 0.89]]]
```

---

## 🚀 运行完整管线

```bash
# 1. 词频统计与分词
python scripts/word_frequency.py

# 2. N-gram 索引构建
python scripts/ngram_frequency.py

# 3. FastText 词向量训练
python scripts/fasttext_train.py

# 4. 诗人相似度分析
python scripts/author_analyzer.py
```
