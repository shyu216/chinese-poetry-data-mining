"""
script: 02_author_clustering_v3.py
stage: P4-聚类分析
artifact: 作者聚类结果 v3
purpose: 迭代版作者聚类流程，生成更稳定或更细粒度分群。
inputs:
- results/author
- results/author_v2
outputs:
- results/author_clusters
depends_on:
- 02_author_clustering_v2.py
develop_date: 2026-03-22
last_modified_date: 2026-03-25
"""
import json
import numpy as np
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')
from sklearn.cluster import KMeans, SpectralClustering
from sklearn.preprocessing import StandardScaler, normalize
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity
# 路径配置
INPUT_DIR = Path("results/author")
OUTPUT_DIR = Path("results/author_clusters")
# 配置
MIN_POEMS = 30
TOP_WORDS = 30
N_CLUSTERS = 6
RANDOM_STATE = 42
def load_authors() -> List[Dict]:
    """加载诗人数据"""
    print("=" * 60)
    print("加载诗人数据")
    print("=" * 60)
    chunk_files = sorted(INPUT_DIR.glob("author_chunk_*.json"))
    authors = []
    for chunk_file in chunk_files:
        with open(chunk_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                authors.extend(data)
            else:
                authors.append(data)
    # 过滤
    filtered = [a for a in authors if a.get('poem_count', 0) >= MIN_POEMS]
    print(f"总诗人: {len(authors)}, 过滤后(≥{MIN_POEMS}首): {len(filtered)}")
    return filtered
def extract_features(authors: List[Dict]) -> Tuple[np.ndarray, Dict]:
    """提取特征向量"""
    print("\n" + "=" * 60)
    print("提取特征")
    print("=" * 60)
    # 收集词汇
    all_words = set()
    all_types = set()
    for author in authors:
        word_freq = author.get('word_frequency', {})
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:TOP_WORDS]
        for word, _ in top_words:
            all_words.add(word)
        for ptype in author.get('poem_type_counts', {}).keys():
            all_types.add(ptype)
    word_list = sorted(all_words)
    type_list = sorted(all_types)
    print(f"词汇表: {len(word_list)} 词")
    print(f"诗体类型: {len(type_list)} 种")
    # 构建特征
    features = []
    for author in authors:
        # 词频特征
        word_freq = author.get('word_frequency', {})
        word_vec = np.zeros(len(word_list))
        for word, count in word_freq.items():
            if word in word_list:
                word_vec[word_list.index(word)] = np.log1p(count)
        # 诗体特征
        type_counts = author.get('poem_type_counts', {})
        total = author.get('poem_count', 1)
        type_vec = np.zeros(len(type_list))
        for ptype, count in type_counts.items():
            if ptype in type_list:
                type_vec[type_list.index(ptype)] = count / total
        # 组合
        combined = np.concatenate([word_vec, type_vec])
        features.append(combined)
    feature_matrix = np.array(features)
    # 标准化
    feature_matrix = normalize(feature_matrix, norm='l2')
    feature_matrix = StandardScaler().fit_transform(feature_matrix)
    vocab_info = {
        'words': word_list,
        'types': type_list
    }
    print(f"特征矩阵: {feature_matrix.shape}")
    return feature_matrix, vocab_info
def reduce_dimensions(features: np.ndarray) -> Dict[str, np.ndarray]:
    """降维到2D和3D用于可视化"""
    print("\n" + "=" * 60)
    print("降维可视化")
    print("=" * 60)
    # PCA降维到50维
    pca = PCA(n_components=50, random_state=RANDOM_STATE)
    reduced = pca.fit_transform(features)
    # t-SNE到2D
    print("计算2D坐标 (t-SNE)...")
    tsne_2d = TSNE(n_components=2, random_state=RANDOM_STATE, perplexity=30, n_iter=1000)
    coords_2d = tsne_2d.fit_transform(reduced)
    # t-SNE到3D
    print("计算3D坐标 (t-SNE)...")
    tsne_3d = TSNE(n_components=3, random_state=RANDOM_STATE, perplexity=30, n_iter=1000)
    coords_3d = tsne_3d.fit_transform(reduced)
    print(f"2D坐标范围: X[{coords_2d[:,0].min():.2f}, {coords_2d[:,0].max():.2f}], "
          f"Y[{coords_2d[:,1].min():.2f}, {coords_2d[:,1].max():.2f}]")
    return {
        '2d': coords_2d,
        '3d': coords_3d,
        'pca': reduced
    }
def perform_clustering(features: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """执行谱聚类"""
    print("\n" + "=" * 60)
    print(f"谱聚类 (K={N_CLUSTERS})")
    print("=" * 60)
    model = SpectralClustering(
        n_clusters=N_CLUSTERS,
        affinity='nearest_neighbors',
        n_neighbors=15,
        random_state=RANDOM_STATE
    )
    labels = model.fit_predict(features)
    # 计算轮廓系数
    sil_score = silhouette_score(features, labels)
    print(f"轮廓系数: {sil_score:.4f}")
    # 统计
    counts = Counter(labels)
    print("\n聚类分布:")
    for cid, cnt in sorted(counts.items()):
        print(f"  流派 {cid}: {cnt} 人")
    return labels, features
def analyze_clusters(authors: List[Dict], labels: np.ndarray, 
                     coords: Dict[str, np.ndarray]) -> Dict:
    """分析每个聚类"""
    print("\n" + "=" * 60)
    print("分析流派特征")
    print("=" * 60)
    clusters_info = {}
    for cluster_id in range(N_CLUSTERS):
        mask = labels == cluster_id
        cluster_indices = np.where(mask)[0]
        cluster_authors = [authors[i] for i in cluster_indices]
        # 统计词频
        all_words = Counter()
        all_types = Counter()
        for author in cluster_authors:
            for word, count in author.get('word_frequency', {}).items():
                all_words[word] += count
            for t, c in author.get('poem_type_counts', {}).items():
                all_types[t] += c
        # 计算特色词（相对于其他流派）
        other_words = Counter()
        for other_id in range(N_CLUSTERS):
            if other_id == cluster_id:
                continue
            other_mask = labels == other_id
            for i in np.where(other_mask)[0]:
                for word, count in authors[i].get('word_frequency', {}).items():
                    other_words[word] += count
        # 特色词
        distinctive = []
        for word, count in all_words.most_common(100):
            other_count = other_words.get(word, 1)
            ratio = count / (other_count / max(len(cluster_authors), 1))
            distinctive.append({'word': word, 'ratio': round(ratio, 2), 'count': count})
        distinctive.sort(key=lambda x: x['ratio'], reverse=True)
        # 代表性诗人
        representatives = sorted(cluster_authors, 
                               key=lambda x: x.get('poem_count', 0), 
                               reverse=True)[:10]
        # 计算中心点
        center_2d = coords['2d'][mask].mean(axis=0).tolist()
        center_3d = coords['3d'][mask].mean(axis=0).tolist()
        clusters_info[str(cluster_id)] = {
            'id': cluster_id,
            'name': generate_cluster_name(distinctive[:5]),
            'size': len(cluster_authors),
            'center_2d': center_2d,
            'center_3d': center_3d,
            'representatives': [a['author'] for a in representatives[:5]],
            'top_words': distinctive[:20],
            'poem_types': [{'type': t, 'count': c} for t, c in all_types.most_common()],
            'avg_poems': round(np.mean([a.get('poem_count', 0) for a in cluster_authors]), 1),
            'color': get_cluster_color(cluster_id)
        }
        print(f"\n流派 {cluster_id}: {clusters_info[str(cluster_id)]['name']}")
        print(f"  人数: {len(cluster_authors)}, 平均诗数: {clusters_info[str(cluster_id)]['avg_poems']}")
        print(f"  代表: {', '.join(clusters_info[str(cluster_id)]['representatives'][:3])}")
        print(f"  特色词: {', '.join([w['word'] for w in distinctive[:5]])}")
    return clusters_info
def generate_cluster_name(top_words: List[Dict]) -> str:
    """根据特色词生成流派名称 - 使用前两个关键词组合命名
    例如: 特色词为 ["别", "梦", "愁"] -> 生成 "别梦派"
    """
    if not top_words:
        return "未知流派"
    # 取前两个关键词组合
    first_word = top_words[0]['word'] if len(top_words) > 0 else ''
    second_word = top_words[1]['word'] if len(top_words) > 1 else ''
    # 组合成流派名
    if first_word and second_word:
        return f"{first_word}{second_word}派"
    elif first_word:
        return f"{first_word}派"
    else:
        return "未知流派"
def get_cluster_color(cluster_id: int) -> str:
    """获取流派颜色"""
    colors = [
        '#e86b7c',  # 粉红 - 婉约
        '#2ecc71',  # 绿色 - 自然
        '#3498db',  # 蓝色 - 豪放
        '#9b59b6',  # 紫色 - 禅佛
        '#f39c12',  # 橙色 - 五言
        '#1abc9c',  # 青色 - 古文
    ]
    return colors[cluster_id % len(colors)]
def build_author_data(authors: List[Dict], labels: np.ndarray, 
                      coords: Dict[str, np.ndarray]) -> List[Dict]:
    """构建诗人数据（用于前端展示）"""
    print("\n" + "=" * 60)
    print("构建诗人数据")
    print("=" * 60)
    author_data = []
    for i, author in enumerate(authors):
        # 获取相似诗人
        similar = author.get('similar_authors', [])[:5]
        # 获取主要诗体
        types = author.get('poem_type_counts', {})
        main_type = max(types.items(), key=lambda x: x[1])[0] if types else '未知'
        author_data.append({
            'id': i,
            'name': author['author'],
            'cluster': int(labels[i]),
            'poem_count': author.get('poem_count', 0),
            'main_type': main_type,
            'coord_2d': coords['2d'][i].tolist(),
            'coord_3d': coords['3d'][i].tolist(),
            'similar': [s['author'] for s in similar],
            'similar_scores': [round(s['similarity'], 3) for s in similar]
        })
    print(f"生成 {len(author_data)} 位诗人数据")
    return author_data
def save_results(clusters_info: Dict, author_data: List[Dict], vocab_info: Dict):
    """保存结果"""
    print("\n" + "=" * 60)
    print("保存结果")
    print("=" * 60)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # 1. 元数据
    metadata = {
        'version': '3.0',
        'total_authors': len(author_data),
        'n_clusters': N_CLUSTERS,
        'min_poems': MIN_POEMS,
        'clusters': {k: {
            'id': v['id'],
            'name': v['name'],
            'size': v['size'],
            'color': v['color'],
            'center_2d': v['center_2d'],
            'representatives': v['representatives']
        } for k, v in clusters_info.items()}
    }
    with open(OUTPUT_DIR / 'clusters_metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"✓ 元数据: clusters_metadata.json")
    # 2. 诗人坐标数据
    with open(OUTPUT_DIR / 'clusters_data.json', 'w', encoding='utf-8') as f:
        json.dump(author_data, f, ensure_ascii=False)
    print(f"✓ 诗人数据: clusters_data.json ({len(author_data)} 人)")
    # 3. 流派详细特征
    with open(OUTPUT_DIR / 'cluster_features.json', 'w', encoding='utf-8') as f:
        json.dump(clusters_info, f, ensure_ascii=False, indent=2)
    print(f"✓ 流派特征: cluster_features.json")
    # 4. 词汇表
    with open(OUTPUT_DIR / 'vocab.json', 'w', encoding='utf-8') as f:
        json.dump(vocab_info, f, ensure_ascii=False)
    print(f"✓ 词汇表: vocab.json")
    print(f"\n所有文件保存至: {OUTPUT_DIR}/")
def main():
    print("\n" + "=" * 60)
    print("诗人流派聚类分析 v3")
    print("=" * 60)
    # 1. 加载数据
    authors = load_authors()
    # 2. 提取特征
    features, vocab_info = extract_features(authors)
    # 3. 降维
    coords = reduce_dimensions(features)
    # 4. 聚类
    labels, _ = perform_clustering(features)
    # 5. 分析
    clusters_info = analyze_clusters(authors, labels, coords)
    # 6. 构建诗人数据
    author_data = build_author_data(authors, labels, coords)
    # 7. 保存
    save_results(clusters_info, author_data, vocab_info)
    print("\n" + "=" * 60)
    print("完成!")
    print("=" * 60)
if __name__ == "__main__":
    main()
