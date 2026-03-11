#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情感特征提取模块
提供诗词情感分析功能
"""

from typing import List, Dict, Tuple, Set
from collections import Counter


class SentimentFeatureExtractor:
    """情感特征提取器"""
    
    # 情感词典
    POSITIVE_WORDS = {
        '爱', '喜', '乐', '欢', '笑', '美', '好', '善', '良', '真',
        '福', '禄', '寿', '吉', '祥', '瑞', '恩', '德', '仁', '义',
        '礼', '智', '信', '忠', '孝', '廉', '勇', '勤', '俭', '朴',
        '实', '诚', '友', '和', '平', '安', '康', '宁', '顺', '利',
        '春', '花', '月', '明', '清', '幽', '雅', '逸', '闲', '舒'
    }
    
    NEGATIVE_WORDS = {
        '悲', '哀', '痛', '苦', '忧', '愁', '怨', '恨', '恼', '怒',
        '愤', '憎', '恶', '丑', '坏', '邪', '奸', '诈', '伪', '假',
        '虚', '空', '幻', '灭', '亡', '死', '病', '老', '弱', '贫',
        '穷', '难', '困', '厄', '灾', '祸', '患', '伤', '泪', '泣',
        '秋', '寒', '冷', '孤', '独', '寂', '寥', '落', '暮', '昏'
    }
    
    INTENSIFIERS = {'极', '最', '甚', '殊', '尤', '绝', '太', '非常', '十分'}
    NEGATORS = {'不', '未', '无', '莫', '勿', '别', '休'}
    
    def __init__(self):
        self._check_jieba()
    
    def _check_jieba(self):
        """检查jieba是否可用"""
        try:
            import jieba
            self.jieba = jieba
            self.has_jieba = True
        except ImportError:
            self.has_jieba = False
            self.jieba = None
    
    def extract_sentiment_features(self, text: str) -> Dict:
        """
        提取情感特征
        
        Args:
            text: 诗词文本
            
        Returns:
            情感特征字典
        """
        # 分词
        words = self._segment(text)
        
        # 统计情感词
        positive_count = 0
        negative_count = 0
        intensifier_count = 0
        negator_count = 0
        
        for word in words:
            if word in self.POSITIVE_WORDS:
                positive_count += 1
            elif word in self.NEGATIVE_WORDS:
                negative_count += 1
            
            if word in self.INTENSIFIERS:
                intensifier_count += 1
            if word in self.NEGATORS:
                negator_count += 1
        
        # 计算情感得分
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            sentiment_score = 0
        else:
            sentiment_score = (positive_count - negative_count) / total_sentiment_words
        
        # 确定情感倾向
        if sentiment_score > 0.1:
            sentiment = '积极'
        elif sentiment_score < -0.1:
            sentiment = '消极'
        else:
            sentiment = '中性'
        
        return {
            'positive_count': positive_count,
            'negative_count': negative_count,
            'intensifier_count': intensifier_count,
            'negator_count': negator_count,
            'sentiment_score': sentiment_score,
            'sentiment': sentiment,
            'total_words': len(words)
        }
    
    def _segment(self, text: str) -> List[str]:
        """分词"""
        if self.has_jieba:
            return list(self.jieba.cut(text))
        else:
            # 简单按字符分割
            return list(text)
    
    def to_vector(self, text: str) -> List[float]:
        """
        转换为特征向量
        
        Args:
            text: 诗词文本
            
        Returns:
            特征向量 [pos_ratio, neg_ratio, intensifier_ratio, negator_ratio, sentiment_score]
        """
        features = self.extract_sentiment_features(text)
        total = features['total_words']
        
        if total == 0:
            return [0.0, 0.0, 0.0, 0.0, 0.0]
        
        return [
            features['positive_count'] / total,
            features['negative_count'] / total,
            features['intensifier_count'] / total,
            features['negator_count'] / total,
            features['sentiment_score']
        ]


# 便捷函数
def analyze_sentiment(text: str) -> Dict:
    """
    分析文本情感
    
    Args:
        text: 文本内容
        
    Returns:
        情感分析结果
    """
    extractor = SentimentFeatureExtractor()
    return extractor.extract_sentiment_features(text)


def get_sentiment_score(text: str) -> float:
    """
    获取情感得分
    
    Args:
        text: 文本内容
        
    Returns:
        情感得分 (-1到1)
    """
    extractor = SentimentFeatureExtractor()
    features = extractor.extract_sentiment_features(text)
    return features['sentiment_score']
