"""
诗词数据Pydantic模型定义

定义从原始数据到分析结果的全链路数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class Genre(str, Enum):
    """诗词体裁枚举"""
    POEM = "诗"       # 古体诗/近体诗
    CI = "词"         # 词
    QU = "曲"         # 曲
    FU = "赋"         # 赋
    OTHER = "其他"


class PoemType(str, Enum):
    """诗体类型枚举"""
    # 诗
    WUYE_JUEJU = "五言绝句"
    QIYUE_JUEJU = "七言绝句"
    WUYE_LVSHI = "五言律诗"
    QIYUE_LVSHI = "七言律诗"
    WUYE_GONGTI = "五言古体"
    QIYUE_GONGTI = "七言古体"
    # 词
    CI_CHANGDIAO = "长调"
    CI_ZHONGDIAO = "中调"
    CI_XIAODIAO = "小令"
    # 其他
    OTHER = "其他"


class Dynasty(str, Enum):
    """朝代枚举"""
    TANG = "唐代"
    SONG = "宋代"
    YUAN = "元代"
    MING = "明代"
    QING = "清代"
    OTHER = "其他"


class PoemBase(BaseModel):
    """诗词基础模型"""
    id: str = Field(..., description="唯一标识符")
    title: str = Field(..., description="标题")
    author: str = Field(..., description="作者")
    dynasty: str = Field(..., description="朝代")
    genre: str = Field(..., description="体裁: 诗/词/曲/赋")
    poem_type: Optional[str] = Field(None, description="诗体类型")


class PoemRaw(PoemBase):
    """原始数据模型（清洗后）"""
    paragraphs: List[str] = Field(default_factory=list, description="段落列表")
    content: str = Field("", description="原始内容（段落拼接）")
    content_simplified: Optional[str] = Field(None, description="简体内容")
    source_file: str = Field("", description="来源文件")
    source_type: str = Field("", description="来源类型: poet/ci/qu")
    hash: str = Field("", description="内容hash（去重用）")


class PoemProcessed(PoemBase):
    """结构化处理后的模型"""
    lines: List[str] = Field(default_factory=list, description="去标点后的诗句")
    line_char_counts: List[int] = Field(default_factory=list, description="每句字数")
    meter_pattern: str = Field("", description="格律模式，如 7,7,7,7")
    total_lines: int = Field(0, description="总行数")
    total_chars: int = Field(0, description="总字数")
    is_regular: bool = Field(False, description="是否为格律诗")
    meter_category: Optional[str] = Field(None, description="格律类别: 五言/七言")


class WordFrequency(BaseModel):
    """词汇频率模型"""
    word: str
    count: int
    pos: str  # 词性


class SimilarAuthor(BaseModel):
    """相似作者模型"""
    author: str
    score: float


class PoemWithAnalysis(PoemProcessed):
    """带分析结果的模型"""
    word_frequency: Optional[List[WordFrequency]] = Field(None, description="高频词汇")
    similar_authors: Optional[List[SimilarAuthor]] = Field(None, description="相似作者")


class AnalysisResult(BaseModel):
    """分析结果模型"""
    analyzer_name: str
    version: str
    timestamp: str
    data: Dict[str, Any]


class PipelineStep(BaseModel):
    """管线步骤模型"""
    name: str
    input_version: str
    output_version: str
    timestamp: str
    params: Dict[str, Any] = Field(default_factory=dict)
    record_count: int = 0


class PipelineMetadata(BaseModel):
    """管线元数据"""
    version: str = Field(..., description="管线版本")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    steps: List[PipelineStep] = Field(default_factory=list)
    total_records: int = Field(0, description="总记录数")
    source_files: List[str] = Field(default_factory=list)
    params: Dict[str, Any] = Field(default_factory=dict)


class AuthorStats(BaseModel):
    """作者统计模型"""
    author: str
    poem_count: int
    genre_distribution: Dict[str, int] = Field(default_factory=dict)
    avg_line_count: float
    avg_char_count: float


class MeterStats(BaseModel):
    """格律统计模型"""
    meter_type: str
    count: int
    percentage: float


class POSDistribution(BaseModel):
    """词性分布模型"""
    pos: str
    count: int
    percentage: float
