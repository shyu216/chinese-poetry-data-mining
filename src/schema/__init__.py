"""
数据Schema定义模块

提供诗词数据的Pydantic模型定义
"""

from .poetry import (
    Genre,
    PoemType,
    PoemBase,
    PoemRaw,
    PoemProcessed,
    PoemWithAnalysis,
    AnalysisResult,
    PipelineMetadata,
    PipelineStep,
    SimilarAuthor,
    WordFrequency,
)

__all__ = [
    "Genre",
    "PoemType",
    "PoemBase",
    "PoemRaw",
    "PoemProcessed",
    "PoemWithAnalysis",
    "AnalysisResult",
    "PipelineMetadata",
    "PipelineStep",
    "SimilarAuthor",
    "WordFrequency",
]
