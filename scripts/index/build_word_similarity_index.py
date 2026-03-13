"""
词汇相似度索引生成器 (Task 12)

预计算所有词汇对的相似度
- 使用 TF-IDF + Cosine Similarity
- 只保留相似度 > 0.3 的结果
- 为每个词汇找出 Top 20 相似词汇

输出: data/output/web/index/word_similarity_index.json
"""

import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent.parent


def load_poems(data_path: Path) -> pd.DataFrame:
    """加载诗词数据"""
    csv_path = data_path / "silver" / "v2_poems_structured.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"找不到诗词数据文件: {csv_path}")
    
    print(f"加载诗词数据: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"加载完成: {len(df)} 首诗词")
    return df


def extract_vocabulary(df: pd.DataFrame, min_df: int = 3, max_features: int = 5000) -> Tuple[List[str], Dict]:
    """
    提取词汇表
    
    Args:
        df: 诗词数据框
        min_df: 最小文档频率
        max_features: 最大特征数
    
    Returns:
        vocabulary: 词汇列表
        word_doc_freq: 词汇文档频率
    """
    print("提取词汇表...")
    
    try:
        import jieba
    except ImportError:
        raise ImportError("需要安装 jieba: pip install jieba")
    
    # 停用词
    stop_words = set([
        '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也',
        '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那',
        '之', '而', '以', '其', '于', '与', '乃', '且', '即', '若', '所', '为', '兮', '乎',
        '者', '也', '矣', '焉', '哉', '耶', '耳', '欤', '夫', '盖', '故', '然', '则',
        '而', '虽', '既', '便', '又', '并', '及', '或', '但', '惟', '唯', '只', '个',
        '来', '把', '被', '让', '向', '从', '到', '在', '给', '为', '因', '比'
    ])
    
    # 收集每个词的文档频率
    word_doc_freq: Dict[str, int] = defaultdict(int)
    word_contexts: Dict[str, List[str]] = defaultdict(list)
    
    total = len(df)
    for idx, row in df.iterrows():
        if idx % 100 == 0:
            print(f"  处理进度: {idx}/{total} ({idx/total*100:.1f}%)")
        
        content = str(row.get('content', ''))
        title = str(row.get('title', ''))
        text = f"{title} {content}"
        
        # 分词
        words = set(jieba.lcut(text))  # 使用set去重，每首诗词只计一次
        
        for word in words:
            word = word.strip()
            if len(word) < 2:
                continue
            if word in stop_words:
                continue
            if word.isdigit():
                continue
            
            word_doc_freq[word] += 1
            word_contexts[word].append(text)
    
    # 筛选词汇
    filtered_words = [
        word for word, freq in word_doc_freq.items()
        if freq >= min_df
    ]
    
    # 按频率排序，取前 max_features 个
    filtered_words = sorted(
        filtered_words,
        key=lambda w: word_doc_freq[w],
        reverse=True
    )[:max_features]
    
    print(f"词汇表构建完成: {len(filtered_words)} 个词汇 (原始 {len(word_doc_freq)} 个)")
    
    return filtered_words, dict(word_doc_freq), word_contexts


def build_word_vectors(vocabulary: List[str], word_contexts: Dict) -> np.ndarray:
    """
    构建词汇向量
    
    使用 TF-IDF 将每个词的上下文转换为向量
    """
    print("构建词汇向量...")
    
    # 为每个词构建文档
    word_docs = []
    for word in vocabulary:
        # 合并该词出现的所有上下文
        contexts = word_contexts.get(word, [])
        doc = " ".join(contexts[:50])  # 最多取50个上下文，避免文档过长
        word_docs.append(doc)
    
    # 使用 TF-IDF 向量化
    vectorizer = TfidfVectorizer(
        max_features=1000,  # 特征维度
        min_df=2,
        ngram_range=(1, 2)
    )
    
    word_vectors = vectorizer.fit_transform(word_docs)
    print(f"词汇向量构建完成: {word_vectors.shape}")
    
    return word_vectors, vectorizer


def compute_similarity_matrix(word_vectors: np.ndarray, vocabulary: List[str], 
                               threshold: float = 0.3, top_k: int = 20) -> Dict:
    """
    计算词汇相似度矩阵
    
    Args:
        word_vectors: 词汇向量矩阵
        vocabulary: 词汇列表
        threshold: 相似度阈值
        top_k: 每个词保留的最相似词数量
    
    Returns:
        similarities: 词汇相似度字典
    """
    print(f"计算相似度矩阵 (阈值={threshold}, TopK={top_k})...")
    
    n_words = len(vocabulary)
    similarities = {}
    
    # 批量计算相似度
    batch_size = 100
    for i in range(0, n_words, batch_size):
        end_i = min(i + batch_size, n_words)
        print(f"  处理词汇: {i}-{end_i}/{n_words}")
        
        # 计算当前批次与所有词汇的相似度
        batch_vectors = word_vectors[i:end_i]
        sim_matrix = cosine_similarity(batch_vectors, word_vectors)
        
        for idx_in_batch, word_idx in enumerate(range(i, end_i)):
            word = vocabulary[word_idx]
            sim_scores = sim_matrix[idx_in_batch]
            
            # 获取相似度大于阈值的词 (排除自己)
            similar_words = []
            for other_idx, score in enumerate(sim_scores):
                if other_idx != word_idx and score > threshold:
                    similar_words.append({
                        "word": vocabulary[other_idx],
                        "score": round(float(score), 4)
                    })
            
            # 按相似度排序，取Top K
            similar_words = sorted(similar_words, key=lambda x: x["score"], reverse=True)[:top_k]
            
            if similar_words:
                similarities[word] = similar_words
    
    print(f"相似度计算完成: {len(similarities)} 个词有相似词")
    return similarities


def build_word_similarity_index(df: pd.DataFrame, min_df: int = 3, 
                                 max_features: int = 5000,
                                 threshold: float = 0.3, 
                                 top_k: int = 20) -> Dict:
    """
    构建词汇相似度索引
    """
    print("=" * 60)
    print("构建词汇相似度索引")
    print("=" * 60)
    
    # 提取词汇表
    vocabulary, word_doc_freq, word_contexts = extract_vocabulary(
        df, min_df=min_df, max_features=max_features
    )
    
    if len(vocabulary) < 10:
        print("警告: 词汇表太小，无法计算相似度")
        return {
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "total_words": len(vocabulary),
            "similarities": {},
            "warning": "词汇表太小"
        }
    
    # 构建词汇向量
    word_vectors, vectorizer = build_word_vectors(vocabulary, word_contexts)
    
    # 计算相似度
    similarities = compute_similarity_matrix(
        word_vectors, vocabulary, threshold=threshold, top_k=top_k
    )
    
    # 构建索引
    index_data = {
        "version": "1.0.0",
        "created_at": datetime.now().isoformat(),
        "total_words": len(vocabulary),
        "threshold": threshold,
        "top_k": top_k,
        "similarities": similarities,
        "word_frequencies": {word: freq for word, freq in word_doc_freq.items() if word in vocabulary}
    }
    
    return index_data


def save_index(index_data: Dict, output_path: Path, filename: str):
    """保存索引文件"""
    output_path.mkdir(parents=True, exist_ok=True)
    file_path = output_path / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    file_size = file_path.stat().st_size
    print(f"保存索引: {file_path} ({file_size / 1024 / 1024:.2f} MB)")


def main():
    """主函数"""
    print("=" * 60)
    print("词汇相似度索引生成器 (Task 12)")
    print("=" * 60)
    
    # 获取路径
    root_dir = get_project_root()
    data_dir = root_dir / "data"
    output_dir = root_dir / "data" / "output" / "web" / "index"
    
    try:
        # 加载数据
        df = load_poems(data_dir)
        
        # 构建词汇相似度索引
        index_data = build_word_similarity_index(
            df,
            min_df=3,        # 最小文档频率
            max_features=3000,  # 最大词汇数
            threshold=0.2,   # 相似度阈值 (降低阈值以获得更多结果)
            top_k=20         # 每个词保留20个最相似词
        )
        
        # 保存索引
        save_index(index_data, output_dir, "word_similarity_index.json")
        
        # 输出统计信息
        print("\n" + "=" * 60)
        print("索引生成完成!")
        print("=" * 60)
        print(f"总词汇数: {index_data['total_words']}")
        print(f"有相似词的词汇: {len(index_data['similarities'])}")
        print(f"相似度阈值: {index_data['threshold']}")
        print(f"Top K: {index_data['top_k']}")
        print(f"\n输出目录: {output_dir}")
        
        # 显示示例
        if index_data['similarities']:
            print("\n示例 (前3个词):")
            for word in list(index_data['similarities'].keys())[:3]:
                sim_words = index_data['similarities'][word][:3]
                sim_str = ", ".join([f"{w['word']}({w['score']})" for w in sim_words])
                print(f"  {word} -> {sim_str}")
        
        return 0
        
    except Exception as e:
        print(f"\n错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
