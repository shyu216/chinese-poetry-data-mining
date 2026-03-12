#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诗词数据挖掘工具包

提供诗词分析的全套工具，包括：
- core: 核心工具（文本处理、拼音）
- features: 特征提取（韵律、情感、语义）
- models: 分析模型（分类、社交网络）
- visualization: 可视化
- data: 数据处理
"""

__version__ = '0.1.0'

# 便捷导入
from src.core.text_utils import TextProcessor, preprocess_poem
from src.core.pinyin_utils import PinyinConverter, ToneAnalyzer
from src.features.rhyme_features import RhymeFeatureExtractor, extract_rhythm
from src.models.poetry_classifier import PoetryAnalyzer, identify_form, classify_theme

__all__ = [
    # Core
    'TextProcessor',
    'preprocess_poem',
    'PinyinConverter',
    'ToneAnalyzer',
    # Features
    'RhymeFeatureExtractor',
    'extract_rhythm',
    # Models
    'PoetryAnalyzer',
    'identify_form',
    'classify_theme',
]
