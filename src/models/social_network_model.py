#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
社交网络分析模型
提供诗人社交网络构建和分析功能
"""

from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import numpy as np


class SocialNetworkModel:
    """社交网络模型"""
    
    def __init__(self):
        self._check_sklearn()
        self._check_networkx()
    
    def _check_sklearn(self):
        """检查sklearn是否可用"""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            self.TfidfVectorizer = TfidfVectorizer
            self.cosine_similarity = cosine_similarity
            self.has_sklearn = True
        except ImportError:
            self.has_sklearn = False
            self.TfidfVectorizer = None
            self.cosine_similarity = None
    
    def _check_networkx(self):
        """检查networkx是否可用"""
        try:
            import networkx as nx
            self.nx = nx
            self.has_networkx = True
        except ImportError:
            self.has_networkx = False
            self.nx = None
    
    def build_author_texts(self, df, min_poems: int = 2) -> Dict[str, str]:
        """
        构建作者文本库
        
        Args:
            df: 诗词DataFrame
            min_poems: 最少诗数阈值
            
        Returns:
            {作者名: 合并文本, ...}
        """
        author_texts = defaultdict(list)
        
        for _, row in df.iterrows():
            author = row.get('author', '')
            content = row.get('content', '')
            if author and content:
                author_texts[author].append(content)
        
        # 过滤并合并
        result = {}
        for author, texts in author_texts.items():
            if len(texts) >= min_poems:
                result[author] = ' '.join(texts)
        
        return result
    
    def calculate_similarity(self, author_texts: Dict[str, str]) -> Tuple[List[str], List[str], np.ndarray]:
        """
        计算作者间相似度
        
        Args:
            author_texts: 作者文本字典
            
        Returns:
            (作者列表, 文本列表, 相似度矩阵)
        """
        if not self.has_sklearn:
            raise ImportError("需要安装scikit-learn")
        
        authors = list(author_texts.keys())
        texts = list(author_texts.values())
        
        # 计算TF-IDF
        vectorizer = self.TfidfVectorizer(max_features=1000, min_df=1)
        tfidf_matrix = vectorizer.fit_transform(texts)
        
        # 计算余弦相似度
        similarity_matrix = self.cosine_similarity(tfidf_matrix)
        
        return authors, texts, similarity_matrix
    
    def build_network(self, authors: List[str], similarity_matrix: np.ndarray, 
                     threshold: float = 0.1) -> Optional:
        """
        构建社交网络
        
        Args:
            authors: 作者列表
            similarity_matrix: 相似度矩阵
            threshold: 相似度阈值
            
        Returns:
            NetworkX图对象
        """
        if not self.has_networkx:
            raise ImportError("需要安装networkx")
        
        G = self.nx.Graph()
        
        # 添加节点
        for author in authors:
            G.add_node(author)
        
        # 添加边
        for i in range(len(authors)):
            for j in range(i + 1, len(authors)):
                similarity = similarity_matrix[i][j]
                if similarity > threshold:
                    G.add_edge(authors[i], authors[j], weight=float(similarity))
        
        return G
    
    def analyze_network(self, G) -> Dict:
        """
        分析网络属性
        
        Args:
            G: NetworkX图对象
            
        Returns:
            网络分析结果
        """
        if not self.has_networkx:
            raise ImportError("需要安装networkx")
        
        analysis = {
            'network_properties': {
                'nodes': G.number_of_nodes(),
                'edges': G.number_of_edges(),
                'density': self.nx.density(G),
                'average_clustering': self.nx.average_clustering(G) if G.number_of_edges() > 0 else 0
            }
        }
        
        # 中心性分析
        if G.number_of_nodes() > 0:
            analysis['degree_centrality'] = self.nx.degree_centrality(G)
            analysis['betweenness_centrality'] = self.nx.betweenness_centrality(G)
            analysis['closeness_centrality'] = self.nx.closeness_centrality(G)
        else:
            analysis['degree_centrality'] = {}
            analysis['betweenness_centrality'] = {}
            analysis['closeness_centrality'] = {}
        
        return analysis
    
    def find_communities(self, G) -> List[List[str]]:
        """
        发现社区（使用贪心模块度最大化）
        
        Args:
            G: NetworkX图对象
            
        Returns:
            社区列表，每个社区是作者列表
        """
        if not self.has_networkx:
            raise ImportError("需要安装networkx")
        
        if G.number_of_edges() == 0:
            return [[node] for node in G.nodes()]
        
        try:
            from networkx.algorithms.community import greedy_modularity_communities
            communities = list(greedy_modularity_communities(G))
            return [list(c) for c in communities]
        except:
            # 如果社区发现失败，返回每个节点一个社区
            return [[node] for node in G.nodes()]
    
    def get_top_similar_pairs(self, authors: List[str], similarity_matrix: np.ndarray, 
                             top_k: int = 10) -> List[Dict]:
        """
        获取最相似的作者对
        
        Args:
            authors: 作者列表
            similarity_matrix: 相似度矩阵
            top_k: 返回前k对
            
        Returns:
            相似作者对列表
        """
        pairs = []
        
        for i in range(len(authors)):
            for j in range(i + 1, len(authors)):
                pairs.append({
                    'author1': authors[i],
                    'author2': authors[j],
                    'similarity': float(similarity_matrix[i][j])
                })
        
        # 排序
        pairs.sort(key=lambda x: x['similarity'], reverse=True)
        
        return pairs[:top_k]


# 便捷函数
def build_poet_network(df, min_poems: int = 2, similarity_threshold: float = 0.1) -> Dict:
    """
    构建诗人网络
    
    Args:
        df: 诗词DataFrame
        min_poems: 最少诗数
        similarity_threshold: 相似度阈值
        
    Returns:
        网络分析结果
    """
    model = SocialNetworkModel()
    
    # 构建作者文本
    author_texts = model.build_author_texts(df, min_poems)
    
    if len(author_texts) < 2:
        return {'error': '作者数量不足'}
    
    # 计算相似度
    authors, texts, similarity_matrix = model.calculate_similarity(author_texts)
    
    # 构建网络
    G = model.build_network(authors, similarity_matrix, similarity_threshold)
    
    # 分析网络
    analysis = model.analyze_network(G)
    
    # 发现社区
    communities = model.find_communities(G)
    
    # 获取最相似对
    top_pairs = model.get_top_similar_pairs(authors, similarity_matrix, top_k=20)
    
    return {
        'authors': authors,
        'similarity_matrix': similarity_matrix.tolist(),
        'network_properties': analysis['network_properties'],
        'centrality': {
            'degree': analysis['degree_centrality'],
            'betweenness': analysis['betweenness_centrality'],
            'closeness': analysis['closeness_centrality']
        },
        'communities': communities,
        'top_similar_pairs': top_pairs
    }
