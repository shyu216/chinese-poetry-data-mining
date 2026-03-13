"""
文本相似度分析器

基于 TF-IDF + Cosine Similarity 计算作者用词相似度
用于发现风格相近的诗人
"""

from datetime import datetime
from typing import Dict, Any, List, Tuple
from collections import defaultdict

import pandas as pd
import numpy as np

from src.schema import AnalysisResult, SimilarAuthor
from src.analyzers.base import BaseAnalyzer, register_analyzer


@register_analyzer
class TextSimilarityAnalyzer(BaseAnalyzer):
    """文本相似度分析器
    
    使用 TF-IDF 向量化作者文档，计算 Cosine Similarity
    构建相似度矩阵，用于发现风格相近的诗人
    """
    
    NAME = "text_similarity"
    VERSION = "1.0.0"
    DESCRIPTION = "基于用词习惯计算作者相似度"
    DEPENDS_ON = ["word_frequency"]  # 依赖词汇分析
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.max_features = config.get("max_features", 5000)
        self.min_df = config.get("min_df", 2)  # 至少出现在2位作者的作品中
        self.top_n = config.get("top_n", 10)  # Top N 相似作者
        self.similarity_threshold = config.get("similarity_threshold", 0.3)
    
    def analyze(self, df: pd.DataFrame) -> AnalysisResult:
        """执行相似度分析
        
        Args:
            df: 包含诗词的数据框，需有 author 和 content 列
            
        Returns:
            AnalysisResult: 包含相似度矩阵和相似作者列表
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
        except ImportError:
            raise ImportError("需要安装 scikit-learn: pip install scikit-learn")
        
        # 为每位作者构建文档（所有诗词拼接）
        print("构建作者文档...")
        author_docs = self._build_author_documents(df)
        
        if len(author_docs) < 2:
            return AnalysisResult(
                analyzer_name=self.NAME,
                version=self.VERSION,
                timestamp=datetime.now().isoformat(),
                data={
                    "error": "作者数量不足，无法计算相似度",
                    "author_count": len(author_docs)
                }
            )
        
        authors = list(author_docs.keys())
        docs = [author_docs[a] for a in authors]
        
        print(f"分析 {len(authors)} 位作者...")
        
        # TF-IDF 向量化
        print("TF-IDF 向量化...")
        vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            min_df=self.min_df,
            stop_words=self._get_chinese_stop_words()
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(docs)
        except ValueError as e:
            print(f"TF-IDF 错误: {e}")
            return AnalysisResult(
                analyzer_name=self.NAME,
                version=self.VERSION,
                timestamp=datetime.now().isoformat(),
                data={"error": str(e)}
            )
        
        # 计算相似度矩阵
        print("计算相似度矩阵...")
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        # 为每位作者找出最相似的 Top N
        print("提取相似作者...")
        similar_authors = self._extract_similar_authors(
            authors, similarity_matrix, self.top_n
        )
        
        # 构建网络边（用于可视化）
        edges = self._build_network_edges(authors, similarity_matrix)
        
        result_data = {
            "similarity_matrix": similarity_matrix.tolist(),
            "authors": authors,
            "similar_authors": similar_authors,
            "network_edges": edges,
            "vocabulary_size": len(vectorizer.vocabulary_),
            "author_count": len(authors)
        }
        
        print(f"完成! 词汇表大小: {result_data['vocabulary_size']}")
        
        return AnalysisResult(
            analyzer_name=self.NAME,
            version=self.VERSION,
            timestamp=datetime.now().isoformat(),
            data=result_data
        )
    
    def _build_author_documents(self, df: pd.DataFrame) -> Dict[str, str]:
        """为每位作者构建文档
        
        Args:
            df: 诗词数据框
            
        Returns:
            Dict[str, str]: 作者 -> 文档内容
        """
        author_docs = defaultdict(list)
        
        for _, row in df.iterrows():
            author = row.get("author", "佚名")
            content = row.get("content", "")
            if content:
                author_docs[author].append(content)
        
        # 拼接每位作者的所有诗词
        return {
            author: " ".join(contents)
            for author, contents in author_docs.items()
            if contents
        }
    
    def _extract_similar_authors(
        self,
        authors: List[str],
        similarity_matrix: np.ndarray,
        top_n: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """提取每位作者的相似作者
        
        Args:
            authors: 作者列表
            similarity_matrix: 相似度矩阵
            top_n: Top N 数量
            
        Returns:
            Dict[str, List[Dict]]: 作者 -> 相似作者列表
        """
        similar_authors = {}
        
        for i, author in enumerate(authors):
            similarities = similarity_matrix[i]
            
            # 排除自己（相似度为1）
            similar_indices = np.argsort(similarities)[::-1][1:top_n+1]
            
            similar_authors[author] = [
                {
                    "author": authors[j],
                    "score": float(similarities[j]),
                    "rank": rank + 1
                }
                for rank, j in enumerate(similar_indices)
                if similarities[j] > self.similarity_threshold
            ]
        
        return similar_authors
    
    def _build_network_edges(
        self,
        authors: List[str],
        similarity_matrix: np.ndarray
    ) -> List[Dict[str, Any]]:
        """构建网络边（用于可视化）
        
        Args:
            authors: 作者列表
            similarity_matrix: 相似度矩阵
            
        Returns:
            List[Dict]: 边列表
        """
        edges = []
        
        for i in range(len(authors)):
            for j in range(i + 1, len(authors)):
                score = similarity_matrix[i][j]
                if score > self.similarity_threshold:
                    edges.append({
                        "source": authors[i],
                        "target": authors[j],
                        "weight": float(score)
                    })
        
        return edges
    
    def _get_chinese_stop_words(self) -> List[str]:
        """获取中文停用词列表"""
        # 基础停用词
        stop_words = [
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
            "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
            "你", "会", "着", "没有", "看", "好", "自己", "这", "那",
            "之", "与", "及", "而", "或", "但", "为", "以", "被", "将",
            "把", "向", "从", "于", "至", "并", "等", "且", "则", "若",
            "虽", "故", "乃", "既", "因", "所以", "因此", "因为", "所以",
            "兮", "矣", "焉", "哉", "乎", "也", "者", "所", "其", "何",
            "乃", "而", "于", "则", "即", "若", "虽", "故"
        ]
        return stop_words
    
    def get_similar_authors(self, author: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取指定作者的相似作者
        
        Args:
            author: 作者名
            data: 分析结果数据
            
        Returns:
            List[Dict]: 相似作者列表
        """
        similar_authors = data.get("similar_authors", {})
        return similar_authors.get(author, [])
    
    def calculate_word_similarity(self, word1: str, word2: str) -> Dict[str, Any]:
        """计算两个词汇的语义相似度（预留接口）
        
        Args:
            word1: 词汇1
            word2: 词汇2
            
        Returns:
            Dict: 相似度结果
        """
        # TODO: 使用预训练词向量（如 gensim 加载 word2vec）
        # 或基于共现矩阵计算
        return {
            "word1": word1,
            "word2": word2,
            "similarity": None,
            "method": "not_implemented",
            "note": "词汇相似度计算需要预训练词向量模型"
        }
