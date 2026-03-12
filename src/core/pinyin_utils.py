#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拼音工具模块
提供汉字拼音、声调相关的工具函数
"""

from typing import List, Tuple, Optional
import re
from pypinyin import lazy_pinyin, Style


class PinyinConverter:
    """拼音转换器"""
    
    def __init__(self):
        self.pypinyin = lazy_pinyin
        self.Style = Style
    
    def get_pinyin(self, text: str, style: str = 'normal') -> List[str]:
        """
        获取拼音
        
        Args:
            text: 中文文本
            style: 拼音风格 ('normal', 'tone', 'tone3', 'initials')
            
        Returns:
            拼音列表
        """
        style_map = {
            'normal': Style.NORMAL,
            'tone': Style.TONE,
            'tone3': Style.TONE3,
            'initials': Style.INITIALS,
            'finals': Style.FINALS
        }
        
        py_style = style_map.get(style, Style.NORMAL)
        return self.pypinyin(text, style=py_style)
    
    def get_tone(self, char: str) -> Optional[str]:
        """
        获取单个字的声调
        
        Args:
            char: 单个汉字
            
        Returns:
            声调数字('1', '2', '3', '4')或None
        """
        if len(char) != 1:
            return None
        
        pinyin = lazy_pinyin(char, style=Style.TONE3)[0]
        match = re.search(r'[1-4]', pinyin)
        return match.group(0) if match else None
    
    def get_tones(self, text: str) -> List[Optional[str]]:
        """
        获取文本中每个字的声调
        
        Args:
            text: 中文文本
            
        Returns:
            声调列表
        """
        return [self.get_tone(char) for char in text]
    
    def get_initials(self, text: str) -> List[str]:
        """
        获取声母
        
        Args:
            text: 中文文本
            
        Returns:
            声母列表
        """
        return self.pypinyin(text, style=Style.INITIALS)
    
    def get_finals(self, text: str) -> List[str]:
        """
        获取韵母
        
        Args:
            text: 中文文本
            
        Returns:
            韵母列表
        """
        return self.pypinyin(text, style=Style.FINALS)


class ToneAnalyzer:
    """声调分析器"""
    
    # 平仄映射
    LEVEL_TONES = {'1': '平', '2': '平'}    # 一声、二声为平
    OBLIQUE_TONES = {'3': '仄', '4': '仄'}  # 三声、四声为仄
    
    def __init__(self):
        self.converter = PinyinConverter()
    
    def analyze_level_oblique(self, text: str) -> List[str]:
        """
        分析平仄
        
        Args:
            text: 中文文本
            
        Returns:
            平仄列表 ('平', '仄', '?')
        """
        tones = self.converter.get_tones(text)
        result = []
        
        for tone in tones:
            if tone in self.LEVEL_TONES:
                result.append(self.LEVEL_TONES[tone])
            elif tone in self.OBLIQUE_TONES:
                result.append(self.OBLIQUE_TONES[tone])
            else:
                result.append('?')
        
        return result
    
    def get_level_oblique_pattern(self, text: str) -> str:
        """
        获取平仄模式字符串
        
        Args:
            text: 中文文本
            
        Returns:
            平仄模式 (如: "平平仄仄平")
        """
        pattern = self.analyze_level_oblique(text)
        return ''.join(pattern)
    
    def check_alliteration(self, char1: str, char2: str) -> bool:
        """
        检查是否双声（声母相同）
        
        Args:
            char1: 第一个字
            char2: 第二个字
            
        Returns:
            是否双声
        """
        initials = self.converter.get_initials(char1 + char2)
        return len(initials) == 2 and initials[0] == initials[1] and initials[0] != ''
    
    def check_assonance(self, char1: str, char2: str) -> bool:
        """
        检查是否叠韵（韵母相同）
        
        Args:
            char1: 第一个字
            char2: 第二个字
            
        Returns:
            是否叠韵
        """
        finals = self.converter.get_finals(char1 + char2)
        return len(finals) == 2 and finals[0] == finals[1] and finals[0] != ''


# 便捷函数
def get_pinyin(text: str, style: str = 'normal') -> List[str]:
    """获取拼音"""
    converter = PinyinConverter()
    return converter.get_pinyin(text, style)


def get_tone_pattern(text: str) -> str:
    """获取平仄模式"""
    analyzer = ToneAnalyzer()
    return analyzer.get_level_oblique_pattern(text)


def check_rhyme(char1: str, char2: str) -> bool:
    """
    简单押韵检查（韵母相同）
    
    Args:
        char1: 第一个字
        char2: 第二个字
        
    Returns:
        是否押韵
    """
    converter = PinyinConverter()
    finals = converter.get_finals(char1 + char2)
    return len(finals) == 2 and finals[0] == finals[1] and finals[0] != ''
