# Scripts 分组命名说明

脚本已按当前实际使用的 6 个数据块重命名为 `01~06_*.py/.cjs`。

不属于这 6 个核心产物的脚本统一放到 `99_*.py`。

## 1. results/preprocessed

目标：预处理诗词主数据（清洗、简繁处理、朝代修正）。

- `01_preprocess_poems.py`
- `01_simplify_title_author.py`
- `01_correct_dynasty.py`
- `01_generate-poem-chunk-meta.cjs`

## 2. results/author_v2

目标：作者维度数据与作者元信息。

- `02_author_sim_v1.py`
- `02_author_sim_v2.py`
- `02_generate-authors-meta-v2.py`
- `02_author_clustering_v2.py`（扩展分析）
- `02_author_clustering_v3.py`（扩展分析）

## 3. results/wordcount_v2

目标：词频统计与分块。

- `03_wordcount.py`
- `03_wordcount_v2.py`

## 4. results/word_similarity_v3

目标：词向量训练与相似词索引（含 FlatBuffers 产物）。

- `04_fasttext_train.py`
- `04_fasttext_test.py`
- `04_word_sim_v1.py`
- `04_word_sim_v2.py`
- `04_word_sim_v3.py`

## 5. results/poem_index

目标：诗词检索索引构建与修补。

- `05_generate-poem-index.cjs`
- `05_patch-poem-index-with-chunk.cjs`
- `05_fix-poem-index-dynasty.cjs`

## 6. results/keyword_index

目标：关键词索引与关键词 manifest。

- `06_word_frequency.py`
- `06_word_frequency_fast.py`
- `06_build-keyword-manifest.py`

## 99. 其他分析/实验/工具

目标：不直接属于以上 6 个核心数据块的辅助脚本。

- `99_analyze_long_words.py`
- `99_analyze_unique_words.py`
- `99_wordfreq_quick_stats.py`
- `99_find_largest_files.py`
- `99_ngram_frequency.py`
- `99_wordfreq_distribution.py`
