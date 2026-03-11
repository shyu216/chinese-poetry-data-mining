#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诗词数据可视化模块

提供多种可视化工具支持：
- Plotly: 交互式图表
- Pyecharts: 中文可视化
- Dash: Web交互式仪表板
"""

from .poetry_visualizer import PoetryVisualizer

__all__ = ['PoetryVisualizer']
