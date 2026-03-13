"""
全局配置管理

集中管理所有配置项，支持环境变量覆盖
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class DataConfig(BaseModel):
    """数据路径配置"""
    raw_dir: Path = Field(default=Path("data/raw"))
    bronze_dir: Path = Field(default=Path("data/bronze"))
    silver_dir: Path = Field(default=Path("data/silver"))
    gold_dir: Path = Field(default=Path("data/gold"))
    output_dir: Path = Field(default=Path("data/output"))
    cache_dir: Path = Field(default=Path("data/cache"))
    
    # 采样比例
    sample_ratio: float = Field(default=0.001)  # 1/1000


class AnalysisConfig(BaseModel):
    """分析配置"""
    # 相似度分析
    similarity_threshold: float = Field(default=0.3)
    top_similar_authors: int = Field(default=10)
    
    # 词汇分析
    word_freq_top_n: int = Field(default=100)
    min_word_length: int = Field(default=2)
    
    # 分片导出
    chunk_size: int = Field(default=10000)  # 每片诗词数
    max_chunk_size_mb: int = Field(default=10)  # 每片最大MB


class VisualizationConfig(BaseModel):
    """可视化配置"""
    max_dom_nodes: int = Field(default=100)
    scatter_sample_size: int = Field(default=5000)
    network_max_nodes: int = Field(default=500)


class Settings(BaseModel):
    """全局配置"""
    project_root: Path = Field(default=Path(__file__).parent.parent.parent)
    
    data: DataConfig = Field(default_factory=DataConfig)
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)
    visualization: VisualizationConfig = Field(default_factory=VisualizationConfig)
    
    # 日志
    log_level: str = Field(default="INFO")
    
    class Config:
        env_prefix = "POETRY_"


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取全局配置（单例模式）"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
