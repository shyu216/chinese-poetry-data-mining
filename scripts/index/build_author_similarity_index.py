"""
作者相似度索引生成器 (Task 13)

预计算所有作者间的相似度
- 基于用词习惯 (TF-IDF 向量)
- 为每位作者找出 Top 20 相似作者
- 生成作者相似度网络数据

输出: data/output/web/index/author_similarity_index.json
      data/output/web/index/author_network.json
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


def build_author_documents(df: pd.DataFrame) -> Tuple[Dict[str, str], Dict[str, Dict]]:
    """
    为每位作者构建文档
    
    将每位作者的所有诗词合并为一个文档
    """
    print("构建作者文档...")
    
    author_docs: Dict[str, List[str]] = defaultdict(list)
    author_info: Dict[str, Dict] = {}
    
    for idx, row in df.iterrows():
        author = str(row.get('author', '佚名'))
        title = str(row.get('title', ''))
        content = str(row.get('content', ''))
        dynasty = str(row.get('dynasty', '未知'))
        poem_id = str(row.get('id', idx))
        
        # 合并标题和内容
        poem_text = f"{title} {content}"
        author_docs[author].append(poem_text)
        
        # 收集作者信息
        if author not in author_info:
            author_info[author] = {
                "dynasty": dynasty,
                "poem_count": 0,
                "poem_ids": []
            }
        author_info[author]["poem_count"] += 1
        author_info[author]["poem_ids"].append(poem_id)
    
    # 合并为文档
    author_merged_docs = {
        author: " ".join(docs)
        for author, docs in author_docs.items()
    }
    
    print(f"作者文档构建完成: {len(author_merged_docs)} 位作者")
    return author_merged_docs, author_info


def extract_author_vocabulary(author_docs: Dict[str, str], 
                               min_df: int = 2, 
                               max_features: int = 3000) -> Tuple[List[str], Dict[str, np.ndarray], TfidfVectorizer]:
    """
    提取作者词汇特征
    
    使用 TF-IDF 将每位作者的文档转换为向量
    """
    print("提取作者词汇特征...")
    
    # 准备文档列表
    authors = list(author_docs.keys())
    docs = [author_docs[author] for author in authors]
    
    # 停用词
    stop_words = [
        '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也',
        '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那',
        '之', '而', '以', '其', '于', '与', '乃', '且', '即', '若', '所', '为', '兮', '乎',
        '者', '也', '矣', '焉', '哉', '耶', '耳', '欤', '夫', '盖', '故', '然', '则',
        '而', '虽', '既', '便', '又', '并', '及', '或', '但', '惟', '唯', '只', '个',
        '来', '把', '被', '让', '向', '从', '到', '在', '给', '为', '因', '比'
    ]
    
    # 使用 TF-IDF 向量化
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        min_df=min_df,
        stop_words=stop_words,
        ngram_range=(1, 2),  # 包含1-gram和2-gram
        token_pattern=r'(?u)\b\w+\b'  # 支持中文
    )
    
    try:
        author_vectors = vectorizer.fit_transform(docs)
    except Exception as e:
        print(f"向量化失败: {e}")
        # 尝试不使用停用词
        vectorizer = TfidfVectorizer(
            max_features=max_features,
            min_df=min_df,
            ngram_range=(1, 2)
        )
        author_vectors = vectorizer.fit_transform(docs)
    
    print(f"作者向量构建完成: {author_vectors.shape}")
    
    # 转换为字典
    author_vectors_dict = {
        author: author_vectors[i]
        for i, author in enumerate(authors)
    }
    
    return authors, author_vectors_dict, vectorizer


def compute_author_similarity(authors: List[str], 
                               author_vectors: Dict[str, np.ndarray],
                               threshold: float = 0.1,
                               top_k: int = 20) -> Tuple[Dict, List[Dict], List[Dict]]:
    """
    计算作者相似度
    
    Args:
        authors: 作者列表
        author_vectors: 作者向量字典
        threshold: 相似度阈值
        top_k: 每个作者保留的最相似作者数量
    
    Returns:
        similarities: 作者相似度字典
        network_nodes: 网络图节点
        network_links: 网络图边
    """
    print(f"计算作者相似度 (阈值={threshold}, TopK={top_k})...")
    
    n_authors = len(authors)
    similarities = {}
    
    # 构建向量矩阵
    vectors = np.vstack([author_vectors[author].toarray() for author in authors])
    
    # 计算相似度矩阵
    sim_matrix = cosine_similarity(vectors)
    
    # 提取相似度结果
    for i, author in enumerate(authors):
        sim_scores = sim_matrix[i]
        
        # 获取相似度大于阈值的作者 (排除自己)
        similar_authors = []
        for j, score in enumerate(sim_scores):
            if i != j and score > threshold:
                similar_authors.append({
                    "author": authors[j],
                    "score": round(float(score), 4)
                })
        
        # 按相似度排序，取Top K
        similar_authors = sorted(similar_authors, key=lambda x: x["score"], reverse=True)[:top_k]
        
        if similar_authors:
            similarities[author] = similar_authors
    
    print(f"相似度计算完成: {len(similarities)} 个作者有相似作者")
    
    # 构建网络图数据
    network_nodes = []
    network_links = []
    
    for author in authors:
        network_nodes.append({
            "id": author,
            "group": 1,  # 可以按朝代分组
            "poem_count": 0  # 稍后填充
        })
    
    # 添加边 (只保留相似度较高的)
    link_threshold = 0.3
    for author, sim_list in similarities.items():
        for sim in sim_list:
            if sim["score"] > link_threshold:
                network_links.append({
                    "source": author,
                    "target": sim["author"],
                    "value": sim["score"]
                })
    
    print(f"网络图数据: {len(network_nodes)} 个节点, {len(network_links)} 条边")
    
    return similarities, network_nodes, network_links


def find_common_words(author1: str, author2: str, 
                      author_docs: Dict[str, str], 
                      top_n: int = 5) -> List[str]:
    """
    找出两位作者的共同高频词
    """
    try:
        import jieba
    except ImportError:
        return []
    
    # 停用词
    stop_words = set([
        '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '上', '也',
        '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '这', '那',
        '之', '而', '以', '其', '于', '与', '乃', '且', '即', '若', '所', '为', '兮', '乎',
        '者', '也', '矣', '焉', '哉', '耶', '耳', '欤', '夫', '盖', '故', '然', '则'
    ])
    
    # 分词统计
    def get_word_freq(text: str) -> Dict[str, int]:
        words = jieba.lcut(text)
        freq = {}
        for word in words:
            word = word.strip()
            if len(word) >= 2 and word not in stop_words and not word.isdigit():
                freq[word] = freq.get(word, 0) + 1
        return freq
    
    freq1 = get_word_freq(author_docs.get(author1, ""))
    freq2 = get_word_freq(author_docs.get(author2, ""))
    
    # 找出共同词汇
    common = set(freq1.keys()) & set(freq2.keys())
    common_with_score = [
        (word, min(freq1[word], freq2[word]))
        for word in common
    ]
    common_with_score.sort(key=lambda x: x[1], reverse=True)
    
    return [word for word, _ in common_with_score[:top_n]]


def build_author_similarity_index(df: pd.DataFrame,
                                   min_df: int = 2,
                                   max_features: int = 3000,
                                   threshold: float = 0.1,
                                   top_k: int = 20) -> Tuple[Dict, Dict]:
    """
    构建作者相似度索引
    """
    print("=" * 60)
    print("构建作者相似度索引")
    print("=" * 60)
    
    # 构建作者文档
    author_docs, author_info = build_author_documents(df)
    
    if len(author_docs) < 5:
        print("警告: 作者数量太少，无法计算相似度")
        empty_result = {
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "total_authors": len(author_docs),
            "similarities": {}
        }
        return empty_result, {"nodes": [], "links": []}
    
    # 提取作者向量
    authors, author_vectors, vectorizer = extract_author_vocabulary(
        author_docs, min_df=min_df, max_features=max_features
    )
    
    # 计算相似度
    similarities, network_nodes, network_links = compute_author_similarity(
        authors, author_vectors, threshold=threshold, top_k=top_k
    )
    
    # 添加共同词汇信息
    print("计算共同词汇...")
    for author, sim_list in similarities.items():
        for sim in sim_list:
            common_words = find_common_words(author, sim["author"], author_docs, top_n=5)
            sim["common_words"] = common_words
    
    # 更新网络节点信息
    for node in network_nodes:
        author = node["id"]
        if author in author_info:
            node["poem_count"] = author_info[author]["poem_count"]
            node["dynasty"] = author_info[author]["dynasty"]
            # 按朝代分组
            dynasty_groups = {
                "先秦": 1, "两汉": 2, "魏晋": 3, "南北朝": 4,
                "隋代": 5, "唐代": 6, "五代": 7, "宋代": 8,
                "元代": 9, "明代": 10, "清代": 11, "近代": 12
            }
            node["group"] = dynasty_groups.get(author_info[author]["dynasty"], 0)
    
    # 构建索引
    index_data = {
        "version": "1.0.0",
        "created_at": datetime.now().isoformat(),
        "total_authors": len(authors),
        "threshold": threshold,
        "top_k": top_k,
        "similarities": similarities,
        "author_info": author_info
    }
    
    network_data = {
        "version": "1.0.0",
        "created_at": datetime.now().isoformat(),
        "nodes": network_nodes,
        "links": network_links
    }
    
    return index_data, network_data


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
    print("作者相似度索引生成器 (Task 13)")
    print("=" * 60)
    
    # 获取路径
    root_dir = get_project_root()
    data_dir = root_dir / "data"
    output_dir = root_dir / "data" / "output" / "web" / "index"
    
    try:
        # 加载数据
        df = load_poems(data_dir)
        
        # 构建作者相似度索引
        index_data, network_data = build_author_similarity_index(
            df,
            min_df=2,        # 最小文档频率
            max_features=2000,  # 最大特征数
            threshold=0.05,  # 相似度阈值 (降低以获得更多结果)
            top_k=20         # 每个作者保留20个最相似作者
        )
        
        # 保存索引
        save_index(index_data, output_dir, "author_similarity_index.json")
        save_index(network_data, output_dir, "author_network.json")
        
        # 输出统计信息
        print("\n" + "=" * 60)
        print("索引生成完成!")
        print("=" * 60)
        print(f"总作者数: {index_data['total_authors']}")
        print(f"有相似作者的人数: {len(index_data['similarities'])}")
        print(f"网络图节点: {len(network_data['nodes'])}")
        print(f"网络图边: {len(network_data['links'])}")
        print(f"相似度阈值: {index_data['threshold']}")
        print(f"Top K: {index_data['top_k']}")
        print(f"\n输出目录: {output_dir}")
        
        # 显示示例
        if index_data['similarities']:
            print("\n示例 (前3位作者):")
            for author in list(index_data['similarities'].keys())[:3]:
                sim_authors = index_data['similarities'][author][:3]
                sim_str = ", ".join([f"{s['author']}({s['score']})" for s in sim_authors])
                common = sim_authors[0].get('common_words', [])[:3] if sim_authors else []
                print(f"  {author} -> {sim_str}")
                print(f"    共同词汇: {', '.join(common)}")
        
        return 0
        
    except Exception as e:
        print(f"\n错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
