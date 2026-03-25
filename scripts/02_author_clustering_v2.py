"""
script: 02_author_clustering_v2.py
stage: P4-聚类分析
artifact: 作者聚类结果 v2
purpose: 对作者向量或相似矩阵执行聚类并输出分组结果。
inputs:
- results/author
- results/author_v2
outputs:
- results/author_clusters
depends_on:
- 02_author_sim_v2.py
develop_date: 2026-03-22
last_modified_date: 2026-03-25
"""
import json
import argparse
import numpy as np
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Set
import warnings
warnings.filterwarnings('ignore')
# 聚类和降维
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN, SpectralClustering
from sklearn.preprocessing import StandardScaler, normalize
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, calinski_harabasz_score
from sklearn.metrics.pairwise import cosine_similarity, rbf_kernel
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import laplacian
# 可视化
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
# 路径配置
INPUT_DIR = Path("results/author")
OUTPUT_DIR = Path("results/author_clusters")
# 特征配置
MIN_POEMS = 20  # 最少诗作数量
TOP_WORDS = 30  # 每位诗人取前N个高频词
TOP_PATTERNS = 5  # 每位诗人取前N个格律模式
class BalancedFeatureExtractor:
    """平衡特征提取器 - 确保不同特征维度贡献均衡"""
    def __init__(self):
        self.word_to_idx = {}
        self.pattern_to_idx = {}
        self.poem_type_to_idx = {}
        self.feature_dims = {}
    def collect_vocab(self, authors_data: List[Dict]):
        """收集词汇表"""
        print("=" * 60)
        print("步骤1: 收集特征词汇表")
        print("=" * 60)
        all_words = set()
        all_patterns = set()
        all_poem_types = set()
        for author in authors_data:
            # 收集高频词
            word_freq = author.get('word_frequency', {})
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:TOP_WORDS]
            for word, _ in top_words:
                all_words.add(word)
            # 收集格律模式
            meter_patterns = author.get('meter_patterns', [])
            for mp in meter_patterns[:TOP_PATTERNS]:
                all_patterns.add(mp['pattern'])
            # 收集诗体类型
            poem_types = author.get('poem_type_counts', {})
            for ptype in poem_types.keys():
                all_poem_types.add(ptype)
        # 创建索引映射
        self.word_to_idx = {w: i for i, w in enumerate(sorted(all_words))}
        self.pattern_to_idx = {p: i for i, p in enumerate(sorted(all_patterns))}
        self.poem_type_to_idx = {t: i for i, t in enumerate(sorted(all_poem_types))}
        # 记录各维度大小
        self.feature_dims = {
            'words': len(all_words),
            'patterns': len(all_patterns),
            'types': len(all_poem_types)
        }
        print(f"词汇表: {len(all_words)} 词")
        print(f"格律模式: {len(all_patterns)} 种")
        print(f"诗体类型: {list(all_poem_types)}")
    def extract_features(self, author: Dict) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """提取分离的特征向量，便于分别归一化"""
        # 1. 词频特征 - 使用TF风格
        word_freq = author.get('word_frequency', {})
        word_vec = np.zeros(len(self.word_to_idx))
        for word, count in word_freq.items():
            if word in self.word_to_idx:
                word_vec[self.word_to_idx[word]] = np.log1p(count)
        # L2归一化
        if np.linalg.norm(word_vec) > 0:
            word_vec = word_vec / np.linalg.norm(word_vec)
        # 2. 诗体类型偏好
        poem_type_counts = author.get('poem_type_counts', {})
        total_poems = author.get('poem_count', 1)
        type_vec = np.zeros(len(self.poem_type_to_idx))
        for ptype, count in poem_type_counts.items():
            if ptype in self.poem_type_to_idx:
                type_vec[self.poem_type_to_idx[ptype]] = count / total_poems
        # L2归一化
        if np.linalg.norm(type_vec) > 0:
            type_vec = type_vec / np.linalg.norm(type_vec)
        # 3. 格律模式偏好
        meter_patterns = author.get('meter_patterns', [])
        pattern_vec = np.zeros(len(self.pattern_to_idx))
        for mp in meter_patterns[:TOP_PATTERNS]:
            pattern = mp['pattern']
            if pattern in self.pattern_to_idx:
                pattern_vec[self.pattern_to_idx[pattern]] = np.log1p(mp['count'])
        # L2归一化
        if np.linalg.norm(pattern_vec) > 0:
            pattern_vec = pattern_vec / np.linalg.norm(pattern_vec)
        return word_vec, type_vec, pattern_vec
    def combine_features(self, word_vec: np.ndarray, type_vec: np.ndarray, 
                        pattern_vec: np.ndarray, weights: Dict[str, float] = None) -> np.ndarray:
        """组合特征，应用权重"""
        if weights is None:
            # 默认等权重
            weights = {'words': 1.0, 'types': 1.0, 'patterns': 1.0}
        # 应用权重
        word_vec = word_vec * weights['words']
        type_vec = type_vec * weights['types']
        pattern_vec = pattern_vec * weights['patterns']
        return np.concatenate([word_vec, type_vec, pattern_vec])
class SimilarityNetworkBuilder:
    """构建诗人相似度网络"""
    def __init__(self, authors_data: List[Dict]):
        self.authors_data = authors_data
        self.author_to_idx = {a['author']: i for i, a in enumerate(authors_data)}
        self.similarity_matrix = None
    def build_from_similar_authors(self, threshold: float = 0.5) -> np.ndarray:
        """基于已有的相似诗人数据构建相似度矩阵"""
        n = len(self.authors_data)
        sim_matrix = np.zeros((n, n))
        # 对角线为1
        np.fill_diagonal(sim_matrix, 1.0)
        # 填充相似度
        for i, author in enumerate(self.authors_data):
            similar_authors = author.get('similar_authors', [])
            for sa in similar_authors:
                other_name = sa['author']
                similarity = sa['similarity']
                if other_name in self.author_to_idx and similarity >= threshold:
                    j = self.author_to_idx[other_name]
                    sim_matrix[i, j] = similarity
                    sim_matrix[j, i] = similarity
        self.similarity_matrix = sim_matrix
        return sim_matrix
    def build_from_features(self, feature_matrix: np.ndarray, metric: str = 'cosine') -> np.ndarray:
        """基于特征向量构建相似度矩阵"""
        if metric == 'cosine':
            self.similarity_matrix = cosine_similarity(feature_matrix)
        elif metric == 'rbf':
            # RBF核，自动计算gamma
            self.similarity_matrix = rbf_kernel(feature_matrix)
        else:
            raise ValueError(f"未知度量: {metric}")
        return self.similarity_matrix
    def get_affinity_matrix(self, k_neighbors: int = 10) -> np.ndarray:
        """获取K近邻亲和矩阵"""
        n = self.similarity_matrix.shape[0]
        affinity = np.zeros_like(self.similarity_matrix)
        for i in range(n):
            # 找到K个最近邻
            neighbors = np.argsort(self.similarity_matrix[i])[-k_neighbors-1:-1]
            for j in neighbors:
                affinity[i, j] = self.similarity_matrix[i, j]
                affinity[j, i] = self.similarity_matrix[i, j]
        return affinity
class AuthorClusteringV2:
    """诗人聚类分析器 v2"""
    def __init__(self, algorithm: str = 'spectral', n_clusters: int = 6, 
                 feature_weights: Dict[str, float] = None):
        self.algorithm = algorithm
        self.n_clusters = n_clusters
        self.feature_weights = feature_weights or {'words': 1.0, 'types': 1.5, 'patterns': 1.0}
        self.extractor = BalancedFeatureExtractor()
        self.scaler = StandardScaler()
        self.authors_data = []
        self.feature_matrix = None
        self.labels = None
        self.network_builder = None
    def load_data(self) -> List[Dict]:
        """加载诗人数据"""
        print("\n" + "=" * 60)
        print("加载诗人数据")
        print("=" * 60)
        chunk_files = sorted(INPUT_DIR.glob("author_chunk_*.json"))
        print(f"找到 {len(chunk_files)} 个数据文件")
        authors = []
        for chunk_file in chunk_files:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    authors.extend(data)
                else:
                    authors.append(data)
        # 过滤
        self.authors_data = [a for a in authors if a.get('poem_count', 0) >= MIN_POEMS]
        print(f"总诗人: {len(authors)}, 过滤后(≥{MIN_POEMS}首): {len(self.authors_data)}")
        # 初始化网络构建器
        self.network_builder = SimilarityNetworkBuilder(self.authors_data)
        return self.authors_data
    def build_features(self):
        """构建特征矩阵"""
        print("\n" + "=" * 60)
        print("步骤2: 构建特征矩阵")
        print("=" * 60)
        self.extractor.collect_vocab(self.authors_data)
        # 分别提取各类特征
        word_features = []
        type_features = []
        pattern_features = []
        for author in self.authors_data:
            w, t, p = self.extractor.extract_features(author)
            word_features.append(w)
            type_features.append(t)
            pattern_features.append(p)
        word_matrix = np.array(word_features)
        type_matrix = np.array(type_features)
        pattern_matrix = np.array(pattern_features)
        print(f"词特征: {word_matrix.shape}")
        print(f"诗体特征: {type_matrix.shape}")
        print(f"格律特征: {pattern_matrix.shape}")
        # 分别标准化
        word_matrix = normalize(word_matrix, norm='l2')
        type_matrix = normalize(type_matrix, norm='l2')
        pattern_matrix = normalize(pattern_matrix, norm='l2')
        # 应用权重并组合
        word_matrix *= self.feature_weights['words']
        type_matrix *= self.feature_weights['types']
        pattern_matrix *= self.feature_weights['patterns']
        self.feature_matrix = np.hstack([word_matrix, type_matrix, pattern_matrix])
        print(f"组合特征矩阵: {self.feature_matrix.shape}")
        # 最终标准化
        self.feature_matrix = StandardScaler().fit_transform(self.feature_matrix)
    def reduce_dimensions(self, n_components: int = 30):
        """降维"""
        print("\n" + "=" * 60)
        print("步骤3: PCA降维")
        print("=" * 60)
        if self.feature_matrix.shape[1] > n_components:
            pca = PCA(n_components=n_components)
            self.feature_matrix = pca.fit_transform(self.feature_matrix)
            explained = np.sum(pca.explained_variance_ratio_)
            print(f"降维至 {n_components} 维, 解释方差: {explained:.2%}")
    def find_optimal_clusters(self, max_k: int = 12) -> int:
        """寻找最优聚类数"""
        print("\n" + "=" * 60)
        print("步骤4: 确定最优聚类数")
        print("=" * 60)
        scores = []
        K_range = range(3, min(max_k + 1, len(self.authors_data) // 3))
        for k in K_range:
            if self.algorithm == 'spectral':
                model = SpectralClustering(n_clusters=k, affinity='nearest_neighbors', 
                                          n_neighbors=15, random_state=42)
            else:
                model = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = model.fit_predict(self.feature_matrix)
            # 确保有多个类
            if len(set(labels)) > 1:
                score = silhouette_score(self.feature_matrix, labels)
                scores.append((k, score))
                print(f"K={k}: 轮廓系数={score:.4f}")
        if scores:
            optimal_k = max(scores, key=lambda x: x[1])[0]
            self.n_clusters = optimal_k
            print(f"\n最优聚类数: {optimal_k}")
        return self.n_clusters
    def cluster(self):
        """执行聚类"""
        print("\n" + "=" * 60)
        print(f"步骤5: 执行 {self.algorithm} 聚类")
        print("=" * 60)
        if self.algorithm == 'kmeans':
            model = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
            self.labels = model.fit_predict(self.feature_matrix)
        elif self.algorithm == 'spectral':
            # 谱聚类
            model = SpectralClustering(n_clusters=self.n_clusters, 
                                      affinity='nearest_neighbors',
                                      n_neighbors=15, 
                                      random_state=42)
            self.labels = model.fit_predict(self.feature_matrix)
        elif self.algorithm == 'hierarchical':
            model = AgglomerativeClustering(n_clusters=self.n_clusters)
            self.labels = model.fit_predict(self.feature_matrix)
        elif self.algorithm == 'dbscan':
            # 估计eps
            from sklearn.neighbors import NearestNeighbors
            neigh = NearestNeighbors(n_neighbors=10)
            neigh.fit(self.feature_matrix)
            distances, _ = neigh.kneighbors(self.feature_matrix)
            distances = np.sort(distances[:, 9])
            eps = np.percentile(distances, 80)
            model = DBSCAN(eps=eps, min_samples=5)
            self.labels = model.fit_predict(self.feature_matrix)
            n_clusters = len(set(self.labels)) - (1 if -1 in self.labels else 0)
            print(f"DBSCAN 发现 {n_clusters} 个聚类")
        # 评估
        n_noise = list(self.labels).count(-1)
        n_clusters_real = len(set(self.labels)) - (1 if n_noise > 0 else 0)
        if n_clusters_real > 1:
            mask = self.labels != -1
            if np.sum(mask) > n_clusters_real:
                sil_score = silhouette_score(self.feature_matrix[mask], self.labels[mask])
                print(f"轮廓系数: {sil_score:.4f}")
        print(f"聚类数: {n_clusters_real}, 噪声点: {n_noise}")
        # 分布
        counts = Counter(self.labels)
        print("\n聚类分布:")
        for cid, cnt in sorted(counts.items()):
            if cid == -1:
                print(f"  噪声: {cnt} 人")
            else:
                print(f"  流派 {cid}: {cnt} 人")
    def analyze_clusters(self) -> Dict:
        """详细分析每个聚类"""
        print("\n" + "=" * 60)
        print("步骤6: 分析流派特征")
        print("=" * 60)
        analysis = {
            'algorithm': self.algorithm,
            'n_clusters': int(len(set(self.labels)) - (1 if -1 in self.labels else 0)),
            'total_authors': len(self.authors_data),
            'feature_weights': self.feature_weights,
            'clusters': {}
        }
        for cluster_id in sorted(set(self.labels)):
            if cluster_id == -1:
                continue
            mask = self.labels == cluster_id
            cluster_indices = np.where(mask)[0]
            cluster_authors = [self.authors_data[i] for i in cluster_indices]
            # 统计特征
            all_words = Counter()
            all_types = Counter()
            all_patterns = Counter()
            dynasty_counter = Counter()  # 如果有朝代信息
            for author in cluster_authors:
                # 词频
                for word, count in author.get('word_frequency', {}).items():
                    all_words[word] += count
                # 诗体
                for t, c in author.get('poem_type_counts', {}).items():
                    all_types[t] += c
                # 格律
                for mp in author.get('meter_patterns', [])[:3]:
                    all_patterns[mp['pattern']] += mp['count']
            # 找出该流派特有的词（相对于其他流派）
            other_words = Counter()
            for other_id in set(self.labels):
                if other_id == cluster_id or other_id == -1:
                    continue
                other_mask = self.labels == other_id
                for i in np.where(other_mask)[0]:
                    for word, count in self.authors_data[i].get('word_frequency', {}).items():
                        other_words[word] += count
            # 计算相对词频
            distinctive_words = []
            for word, count in all_words.most_common(50):
                other_count = other_words.get(word, 1)
                ratio = count / (other_count / max(len(cluster_authors), 1))
                distinctive_words.append((word, ratio, count))
            distinctive_words.sort(key=lambda x: x[1], reverse=True)
            # 代表性诗人
            representatives = sorted(cluster_authors, 
                                   key=lambda x: x.get('poem_count', 0), 
                                   reverse=True)[:8]
            analysis['clusters'][str(cluster_id)] = {
                'size': len(cluster_authors),
                'representative_authors': [a['author'] for a in representatives],
                'avg_poems': np.mean([a.get('poem_count', 0) for a in cluster_authors]),
                'top_words': [w for w, _, _ in distinctive_words[:15]],
                'distinctive_words': [{'word': w, 'ratio': round(r, 2), 'count': c} 
                                     for w, r, c in distinctive_words[:10]],
                'poem_types': [{'type': t, 'count': c} 
                              for t, c in all_types.most_common()],
                'patterns': [{'pattern': p, 'count': c} 
                            for p, c in all_patterns.most_common(5)]
            }
            print(f"\n{'='*50}")
            print(f"流派 {cluster_id} - {len(cluster_authors)}人")
            print('='*50)
            print(f"代表诗人: {', '.join([a['author'] for a in representatives[:5]])}")
            print(f"平均诗数: {np.mean([a.get('poem_count', 0) for a in cluster_authors]):.0f}")
            print(f"特色词汇: {', '.join([w for w, _, _ in distinctive_words[:8]])}")
            print(f"主要诗体: {', '.join([t for t, _ in all_types.most_common(3)])}")
        return analysis
    def visualize(self):
        """可视化"""
        print("\n" + "=" * 60)
        print("步骤7: 生成可视化")
        print("=" * 60)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        # 2D投影
        pca_2d = PCA(n_components=2)
        coords = pca_2d.fit_transform(self.feature_matrix)
        fig = plt.figure(figsize=(18, 6))
        # 图1: 聚类散点图
        ax1 = fig.add_subplot(131)
        unique_labels = sorted(set(self.labels))
        colors = plt.cm.Set2(np.linspace(0, 1, len(unique_labels)))
        for label, color in zip(unique_labels, colors):
            mask = self.labels == label
            if label == -1:
                ax1.scatter(coords[mask, 0], coords[mask, 1], 
                           c='gray', marker='x', label='噪声', alpha=0.3, s=20)
            else:
                ax1.scatter(coords[mask, 0], coords[mask, 1],
                           c=[color], label=f'流派 {label}', alpha=0.7, s=50)
        ax1.set_xlabel('PC1')
        ax1.set_ylabel('PC2')
        ax1.set_title(f'诗人流派分布 ({self.algorithm})')
        ax1.legend(loc='best', fontsize=8)
        ax1.grid(True, alpha=0.3)
        # 图2: 聚类大小
        ax2 = fig.add_subplot(132)
        counts = Counter(self.labels)
        labels_list = []
        sizes = []
        for k in sorted(counts.keys()):
            if k == -1:
                labels_list.append('噪声')
            else:
                labels_list.append(f'流派{k}')
            sizes.append(counts[k])
        colors_pie = plt.cm.Set2(np.linspace(0, 1, len(labels_list)))
        wedges, texts, autotexts = ax2.pie(sizes, labels=labels_list, autopct='%1.1f%%', 
                                           colors=colors_pie)
        ax2.set_title('流派占比')
        # 图3: 相似度网络（简化版）
        ax3 = fig.add_subplot(133)
        # 计算相似度
        sim_matrix = cosine_similarity(self.feature_matrix[:50])  # 只显示前50个
        im = ax3.imshow(sim_matrix, cmap='viridis', aspect='auto')
        ax3.set_title('诗人相似度矩阵 (前50位)')
        ax3.set_xlabel('诗人索引')
        ax3.set_ylabel('诗人索引')
        plt.colorbar(im, ax=ax3)
        plt.tight_layout()
        viz_path = OUTPUT_DIR / f'clustering_{self.algorithm}.png'
        plt.savefig(viz_path, dpi=150, bbox_inches='tight')
        print(f"可视化保存至: {viz_path}")
        plt.close()
    def save_results(self, analysis: Dict):
        """保存结果"""
        print("\n" + "=" * 60)
        print("步骤8: 保存结果")
        print("=" * 60)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        # 诗人-聚类映射
        mapping = []
        for i, author in enumerate(self.authors_data):
            mapping.append({
                'author': author['author'],
                'cluster': int(self.labels[i]),
                'poem_count': author.get('poem_count', 0),
                'types': list(author.get('poem_type_counts', {}).keys())
            })
        with open(OUTPUT_DIR / f'clusters_{self.algorithm}.json', 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        with open(OUTPUT_DIR / f'analysis_{self.algorithm}.json', 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        print(f"结果保存至 {OUTPUT_DIR}/")
    def run(self):
        """运行完整流程"""
        self.load_data()
        self.build_features()
        self.reduce_dimensions()
        if self.n_clusters is None or self.n_clusters <= 0:
            self.find_optimal_clusters()
        self.cluster()
        analysis = self.analyze_clusters()
        self.visualize()
        self.save_results(analysis)
        return analysis
def main():
    parser = argparse.ArgumentParser(description='诗人流派聚类分析 v2')
    parser.add_argument('--algorithm', choices=['kmeans', 'spectral', 'hierarchical', 'dbscan'],
                        default='spectral', help='聚类算法')
    parser.add_argument('--n-clusters', type=int, default=6, help='聚类数量')
    parser.add_argument('--min-poems', type=int, default=20, help='最少诗作数量')
    parser.add_argument('--word-weight', type=float, default=1.0, help='词特征权重')
    parser.add_argument('--type-weight', type=float, default=1.5, help='诗体特征权重')
    parser.add_argument('--pattern-weight', type=float, default=1.0, help='格律特征权重')
    args = parser.parse_args()
    global MIN_POEMS
    MIN_POEMS = args.min_poems
    weights = {
        'words': args.word_weight,
        'types': args.type_weight,
        'patterns': args.pattern_weight
    }
    clustering = AuthorClusteringV2(
        algorithm=args.algorithm,
        n_clusters=args.n_clusters,
        feature_weights=weights
    )
    clustering.run()
    print("\n" + "=" * 60)
    print("分析完成!")
    print("=" * 60)
if __name__ == "__main__":
    main()
