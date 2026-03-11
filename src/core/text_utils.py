#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本处理工具模块
提供诗词文本的基础处理功能
"""

import re
from typing import List, Optional


class TextProcessor:
    """文本处理器"""
    
    def __init__(self):
        # 尝试导入OpenCC
        try:
            from opencc import OpenCC
            self.cc = OpenCC('t2s')
            self.has_opencc = True
        except ImportError:
            self.has_opencc = False
    
    def traditional_to_simplified(self, text: str) -> str:
        """繁体转简体"""
        if self.has_opencc and text:
            return self.cc.convert(text)
        return text
    
    def clean_text(self, text: str) -> str:
        """清洗文本"""
        if not text:
            return ""
        
        # 处理乱码
        text = self.fix_encoding(text)
        
        # 去除多余空格
        text = re.sub(r'\s+', ' ', text)
        
        # 去除特殊字符
        text = re.sub(r'[\r\n]+', '\n', text)
        
        # 统一标点
        text = self.normalize_punctuation(text)
        
        return text.strip()
    
    def normalize_punctuation(self, text: str) -> str:
        """统一标点符号"""
        replacements = {
            '，': ',', '。': '.', '！': '!', '？': '?',
            '；': ';', '：': ':', '“': '"', '”': '"',
            '‘': "'", '’': "'", '（': '(', '）': ')',
            '【': '[', '】': ']', '《': '<', '》': '>'
        }
        
        for cn, en in replacements.items():
            text = text.replace(cn, en)
        
        return text
    
    def fix_encoding(self, text: str) -> str:
        """修复编码问题"""
        if isinstance(text, bytes):
            return text.decode('utf-8', errors='ignore')
        return text
    
    def extract_chinese_chars(self, text: str) -> List[str]:
        """提取中文字符"""
        return [char for char in text if '\u4e00' <= char <= '\u9fff']
    
    def split_into_lines(self, text: str, delimiter: str = '.') -> List[str]:
        """将文本分割成行"""
        lines = text.split(delimiter)
        return [line.strip().replace(',', '') for line in lines if line.strip()]


# 全局实例
text_processor = TextProcessor()


def preprocess_poem(content: str) -> str:
    """
    预处理诗词文本
    
    Args:
        content: 原始诗词内容
        
    Returns:
        预处理后的文本
    """
    processor = TextProcessor()
    content = processor.traditional_to_simplified(content)
    content = processor.clean_text(content)
    return content


def normalize_poem_lines(content: str) -> List[str]:
    """
    标准化诗词行
    
    Args:
        content: 诗词内容
        
    Returns:
        诗句列表
    """
    processor = TextProcessor()
    content = processor.traditional_to_simplified(content)
    content = processor.clean_text(content)
    return processor.split_into_lines(content)
