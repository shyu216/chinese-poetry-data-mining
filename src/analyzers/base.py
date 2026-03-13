"""
分析器基类和注册表

提供插件化架构支持
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Type, List, Optional
import pandas as pd

from src.schema import AnalysisResult


class BaseAnalyzer(ABC):
    """分析器基类"""
    
    # 子类必须定义
    NAME: str = ""  # 分析器名称
    VERSION: str = "1.0.0"  # 版本号
    DESCRIPTION: str = ""  # 描述
    DEPENDS_ON: List[str] = []  # 依赖的其他分析器
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化分析器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
    
    @abstractmethod
    def analyze(self, df: pd.DataFrame) -> AnalysisResult:
        """执行分析
        
        Args:
            df: 输入数据框
            
        Returns:
            AnalysisResult: 分析结果
        """
        pass
    
    def validate_input(self, df: pd.DataFrame) -> bool:
        """验证输入数据
        
        Args:
            df: 输入数据框
            
        Returns:
            bool: 是否通过验证
        """
        return True
    
    def get_info(self) -> Dict[str, Any]:
        """获取分析器信息"""
        return {
            "name": self.NAME,
            "version": self.VERSION,
            "description": self.DESCRIPTION,
            "depends_on": self.DEPENDS_ON,
        }


class AnalyzerRegistry:
    """分析器注册表"""
    
    _analyzers: Dict[str, Type[BaseAnalyzer]] = {}
    
    @classmethod
    def register(cls, analyzer_class: Type[BaseAnalyzer]) -> Type[BaseAnalyzer]:
        """注册分析器
        
        Args:
            analyzer_class: 分析器类
            
        Returns:
            分析器类（装饰器模式）
        """
        cls._analyzers[analyzer_class.NAME] = analyzer_class
        return analyzer_class
    
    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseAnalyzer]]:
        """获取分析器类
        
        Args:
            name: 分析器名称
            
        Returns:
            分析器类或None
        """
        return cls._analyzers.get(name)
    
    @classmethod
    def create(cls, name: str, config: Optional[Dict[str, Any]] = None) -> Optional[BaseAnalyzer]:
        """创建分析器实例
        
        Args:
            name: 分析器名称
            config: 配置参数
            
        Returns:
            分析器实例或None
        """
        analyzer_class = cls.get(name)
        if analyzer_class:
            return analyzer_class(config)
        return None
    
    @classmethod
    def list_analyzers(cls) -> List[Dict[str, Any]]:
        """列出所有已注册的分析器"""
        return [
            {
                "name": name,
                "class": analyzer_class.__name__,
                "version": analyzer_class.VERSION,
                "description": analyzer_class.DESCRIPTION,
            }
            for name, analyzer_class in cls._analyzers.items()
        ]


def register_analyzer(analyzer_class: Type[BaseAnalyzer]) -> Type[BaseAnalyzer]:
    """装饰器：注册分析器"""
    return AnalyzerRegistry.register(analyzer_class)
