#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诗词分类模型
提供诗体识别、主题分类等功能
"""

from typing import List, Dict, Tuple
from collections import Counter

from src.core.text_utils import normalize_poem_lines
from src.features.rhyme_features import RhymeFeatureExtractor


class PoetryFormClassifier:
    """诗体分类器"""
    
    def classify(self, content: str) -> str:
        """
        识别诗歌体裁
        
        Args:
            content: 诗歌内容
        
        Returns:
            诗歌体裁字符串
        """
        lines = normalize_poem_lines(content)
        
        if not lines:
            return "未知"
        
        # 计算每行长度
        line_lengths = [len(line) for line in lines]
        line_count = len(lines)
        
        # 过滤空行
        valid_lines = [line for line in lines if line.strip()]
        if not valid_lines:
            return "未知"
        
        valid_lengths = [len(line) for line in valid_lines]
        valid_count = len(valid_lines)
        
        # 检查是否所有有效行长度相同
        if len(set(valid_lengths)) == 1:
            length = valid_lengths[0]
            
            if valid_count == 4:
                if length == 5:
                    return "五言绝句"
                elif length == 7:
                    return "七言绝句"
            elif valid_count == 8:
                if length == 5:
                    return "五言律诗"
                elif length == 7:
                    return "七言律诗"
        
        # 词
        if line_count > 0 and valid_lengths[0] != valid_lengths[-1]:
            return "词"
        
        return "古体诗"
    
    def classify_batch(self, contents: List[str]) -> List[str]:
        """批量分类"""
        return [self.classify(content) for content in contents]


class ThemeClassifier:
    """主题分类器"""
    
    # 主题关键词
    THEME_KEYWORDS = {
        '边塞诗': ['边', '塞', '征', '战', '军', '兵', '马', '刀', '弓', '胡', '虏', '羌', '戎', '将', '士'],
        '田园诗': ['田', '园', '农', '耕', '牧', '樵', '渔', '村', '舍', '篱', '菊', '桑', '麻', '禾', '稻'],
        '送别诗': ['送', '别', '离', '归', '去', '远', '帆', '舟', '酒', '泪', '柳', '亭', '桥', '岸', '津'],
        '咏史诗': ['史', '古', '旧', '宫', '陵', '墓', '秦', '汉', '唐', '兴', '亡', '衰', '盛', '朝', '代'],
        '山水诗': ['山', '水', '川', '河', '湖', '海', '峰', '岭', '瀑', '泉', '石', '云', '雾', '霞', '烟'],
        '爱情诗': ['情', '爱', '恋', '思', '念', '梦', '泪', '愁', '恨', '郎', '妾', '鸳鸯', '鸾', '凤', '心'],
        '咏物诗': ['梅', '兰', '竹', '菊', '松', '柏', '莲', '荷', '蝉', '雁', '鹤', '鸟', '花', '草', '木'],
        '羁旅诗': ['旅', '客', '游', '行', '孤', '独', '愁', '思', '乡', '家', '归', '夜', '宿', '泊', '渡']
    }
    
    def classify(self, content: str) -> Tuple[str, Dict[str, float]]:
        """
        分类诗词主题
        
        Args:
            content: 诗词内容
            
        Returns:
            (主要主题, 各主题得分)
        """
        scores = {}
        
        for theme, keywords in self.THEME_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in content)
            scores[theme] = score / len(keywords) if keywords else 0
        
        # 归一化
        total = sum(scores.values())
        if total > 0:
            scores = {k: v/total for k, v in scores.items()}
        
        # 获取最高分的主题
        primary_theme = max(scores, key=scores.get)
        
        return primary_theme, scores
    
    def classify_batch(self, contents: List[str]) -> List[Tuple[str, Dict[str, float]]]:
        """批量分类"""
        return [self.classify(content) for content in contents]


class PoetryAnalyzer:
    """诗词综合分析器"""
    
    def __init__(self):
        self.form_classifier = PoetryFormClassifier()
        self.theme_classifier = ThemeClassifier()
        self.rhyme_extractor = RhymeFeatureExtractor()
    
    def analyze(self, content: str) -> Dict:
        """
        综合分析诗词
        
        Args:
            content: 诗词内容
            
        Returns:
            综合分析结果
        """
        lines = normalize_poem_lines(content)
        
        # 诗体
        form = self.form_classifier.classify(content)
        
        # 主题
        theme, theme_scores = self.theme_classifier.classify(content)
        
        # 韵律特征
        rhythm_features = self.rhyme_extractor.extract_rhythm_features(lines)
        
        return {
            'form': form,
            'theme': theme,
            'theme_scores': theme_scores,
            'rhythm': rhythm_features,
            'line_count': len(lines),
            'char_count': sum(len(line) for line in lines)
        }
    
    def analyze_batch(self, contents: List[str]) -> List[Dict]:
        """批量分析"""
        return [self.analyze(content) for content in contents]


# 便捷函数
def identify_form(content: str) -> str:
    """识别诗体"""
    classifier = PoetryFormClassifier()
    return classifier.classify(content)


def classify_theme(content: str) -> Tuple[str, Dict[str, float]]:
    """分类主题"""
    classifier = ThemeClassifier()
    return classifier.classify(content)


def analyze_poetry(content: str) -> Dict:
    """综合分析"""
    analyzer = PoetryAnalyzer()
    return analyzer.analyze(content)
