#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
韵律特征提取模块
整合平仄分析、韵部分类、双声叠韵检测等功能
"""

from typing import List, Dict, Tuple, Optional
from collections import Counter
import re

from src.core.pinyin_utils import ToneAnalyzer, PinyinConverter


class RhymeFeatureExtractor:
    """韵律特征提取器"""
    
    # 韵部映射表（基于平水韵简化版）
    RHYME_CATEGORIES = {
        '一东': ['ong', 'iong'],
        '二冬': ['ong', 'iong'],
        '三江': ['iang', 'uang'],
        '四支': ['i', 'u', 'ü'],
        '五微': ['ei', 'ui'],
        '六鱼': ['ü'],
        '七虞': ['u'],
        '八齐': ['i'],
        '九佳': ['ai'],
        '十灰': ['ai', 'ui'],
        '十一真': ['en', 'in', 'un'],
        '十二文': ['en', 'in', 'un'],
        '十三元': ['uan', 'en'],
        '十四寒': ['an', 'ian', 'uan'],
        '十五删': ['an', 'ian', 'uan'],
        '一先': ['ian', 'uan'],
        '二萧': ['iao', 'ao'],
        '三肴': ['ao'],
        '四豪': ['ao'],
        '五歌': ['e', 'o'],
        '六麻': ['a', 'ia', 'ua'],
        '七阳': ['ang', 'iang', 'uang'],
        '八庚': ['eng', 'ing', 'ong', 'iong'],
        '九青': ['ing', 'in'],
        '十蒸': ['eng', 'ing'],
        '十一尤': ['ou', 'iu'],
        '十二侵': ['in', 'en'],
        '十三覃': ['an', 'ian'],
        '十四盐': ['an', 'ian'],
        '十五咸': ['an', 'ian']
    }
    
    def __init__(self):
        self.tone_analyzer = ToneAnalyzer()
        self.pinyin_converter = PinyinConverter()
    
    def extract_rhythm_features(self, lines: List[str]) -> Dict:
        """
        提取韵律特征
        
        Args:
            lines: 诗句列表
            
        Returns:
            韵律特征字典
        """
        features = {
            'line_count': len(lines),
            'line_lengths': [len(line) for line in lines],
            'level_oblique_patterns': [],
            'rhyme_categories': [],
            'rhyme_scheme': '',
            'alliteration_count': 0,
            'assonance_count': 0
        }
        
        # 分析每句的平仄
        for line in lines:
            pattern = self.tone_analyzer.get_level_oblique_pattern(line)
            features['level_oblique_patterns'].append(pattern)
        
        # 分析韵脚
        last_chars = []
        for line in lines:
            if line:
                last_chars.append(line[-1])
                rhyme_cat = self._get_rhyme_category(line[-1])
                features['rhyme_categories'].append(rhyme_cat)
        
        # 检测押韵模式
        if len(features['rhyme_categories']) >= 2:
            features['rhyme_scheme'] = self._detect_rhyme_scheme(features['rhyme_categories'])
        
        # 检测双声叠韵
        for line in lines:
            for i in range(len(line) - 1):
                if self.tone_analyzer.check_alliteration(line[i], line[i+1]):
                    features['alliteration_count'] += 1
                if self.tone_analyzer.check_assonance(line[i], line[i+1]):
                    features['assonance_count'] += 1
        
        return features
    
    def _get_rhyme_category(self, char: str) -> Optional[str]:
        """
        获取字的韵部
        
        Args:
            char: 单个汉字
            
        Returns:
            韵部名称或None
        """
        if not char:
            return None
        
        # 获取韵母
        finals = self.pinyin_converter.get_finals(char)
        if not finals or not finals[0]:
            return None
        
        final = finals[0].lower()
        
        # 查找韵部
        for category, finals_list in self.RHYME_CATEGORIES.items():
            if final in finals_list:
                return category
        
        return None
    
    def _detect_rhyme_scheme(self, rhyme_categories: List[Optional[str]]) -> str:
        """
        检测押韵模式
        
        Args:
            rhyme_categories: 韵部列表
            
        Returns:
            押韵模式描述
        """
        # 过滤None值
        valid_rhymes = [r for r in rhyme_categories if r]
        
        if not valid_rhymes:
            return '无韵'
        
        # 统计韵部频率
        rhyme_counter = Counter(valid_rhymes)
        most_common = rhyme_counter.most_common(1)
        
        if most_common:
            main_rhyme, count = most_common[0]
            if count >= len(valid_rhymes) * 0.5:
                return f'主要押{main_rhyme}韵'
        
        return '换韵或散句'
    
    def identify_form(self, lines: List[str]) -> str:
        """
        识别诗体
        
        Args:
            lines: 诗句列表
            
        Returns:
            诗体名称
        """
        if not lines:
            return "未知"
        
        # 过滤空行
        valid_lines = [line for line in lines if line.strip()]
        if not valid_lines:
            return "未知"
        
        # 计算每行长度
        line_lengths = [len(line) for line in valid_lines]
        line_count = len(valid_lines)
        
        # 检查是否所有有效行长度相同
        if len(set(line_lengths)) == 1:
            length = line_lengths[0]
            
            if line_count == 4:
                if length == 5:
                    return "五言绝句"
                elif length == 7:
                    return "七言绝句"
            elif line_count == 8:
                if length == 5:
                    return "五言律诗"
                elif length == 7:
                    return "七言律诗"
        
        # 词（检查是否有词牌信息）
        # 这里简化处理，实际可以通过其他字段判断
        if line_count > 0 and line_lengths[0] != line_lengths[-1]:
            return "词"
        
        return "古体诗"
    
    def to_vector(self, lines: List[str]) -> List[float]:
        """
        将韵律特征转换为向量
        
        Args:
            lines: 诗句列表
            
        Returns:
            特征向量
        """
        features = self.extract_rhythm_features(lines)
        
        vector = []
        
        # 1. 行数 (1维)
        vector.append(float(features['line_count']))
        
        # 2. 平均行长度 (1维)
        avg_length = sum(features['line_lengths']) / len(features['line_lengths']) if features['line_lengths'] else 0
        vector.append(avg_length)
        
        # 3. 行长度标准差 (1维)
        if len(features['line_lengths']) > 1:
            import numpy as np
            std_length = np.std(features['line_lengths'])
        else:
            std_length = 0
        vector.append(std_length)
        
        # 4. 平仄比例 (2维)
        all_patterns = ''.join(features['level_oblique_patterns'])
        level_count = all_patterns.count('平')
        oblique_count = all_patterns.count('仄')
        total = len(all_patterns)
        
        vector.append(level_count / total if total > 0 else 0)
        vector.append(oblique_count / total if total > 0 else 0)
        
        # 5. 双声叠韵数量 (2维)
        vector.append(float(features['alliteration_count']))
        vector.append(float(features['assonance_count']))
        
        # 6. 诗体one-hot编码 (5维: 五绝, 七绝, 五律, 七律, 其他)
        form = features.get('form', self.identify_form(lines))
        form_vector = [0.0] * 5
        form_map = {
            "五言绝句": 0,
            "七言绝句": 1,
            "五言律诗": 2,
            "七言律诗": 3
        }
        if form in form_map:
            form_vector[form_map[form]] = 1.0
        else:
            form_vector[4] = 1.0
        vector.extend(form_vector)
        
        return vector


# 便捷函数
def extract_rhythm(content: str) -> Dict:
    """
    提取诗词韵律特征
    
    Args:
        content: 诗词内容
        
    Returns:
        韵律特征
    """
    from src.core.text_utils import normalize_poem_lines
    
    lines = normalize_poem_lines(content)
    extractor = RhymeFeatureExtractor()
    return extractor.extract_rhythm_features(lines)


def get_tone_pattern(content: str) -> List[str]:
    """
    获取诗词平仄模式
    
    Args:
        content: 诗词内容
        
    Returns:
        每句的平仄模式列表
    """
    from src.core.text_utils import normalize_poem_lines
    
    lines = normalize_poem_lines(content)
    extractor = RhymeFeatureExtractor()
    
    patterns = []
    for line in lines:
        pattern = extractor.tone_analyzer.get_level_oblique_pattern(line)
        patterns.append(pattern)
    
    return patterns


def identify_poem_form(content: str) -> str:
    """
    识别诗体
    
    Args:
        content: 诗词内容
        
    Returns:
        诗体名称
    """
    from src.core.text_utils import normalize_poem_lines
    
    lines = normalize_poem_lines(content)
    extractor = RhymeFeatureExtractor()
    return extractor.identify_form(lines)
