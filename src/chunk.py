"""
高级分块处理模块

提供支持进度跟踪、状态恢复、增量处理的分块系统
每个chunk包含指定数量的诗词（默认1000首）
"""

import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator, Union, Callable
from dataclasses import dataclass, asdict
from datetime import datetime

from src.config import get_settings


@dataclass
class ChunkInfo:
    """分块信息"""
    chunk_id: int
    start_index: int
    end_index: int
    count: int
    file_path: Path
    status: str = "pending"  # pending, processing, completed, failed


@dataclass
class ProcessingState:
    """处理状态"""
    step_name: str
    total_chunks: int
    completed_chunks: List[int]
    failed_chunks: List[int]
    current_chunk: int = -1
    start_time: str = ""
    last_update: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AdvancedChunkManager:
    """高级分块管理器
    
    支持进度跟踪、状态恢复、增量处理
    """
    
    def __init__(
        self,
        base_dir: Path,
        prefix: str = "chunk",
        chunk_size: Optional[int] = None,
        step_name: str = "default"
    ):
        """初始化分块管理器
        
        Args:
            base_dir: 分块文件存储的基础目录
            prefix: 分块文件名前缀
            chunk_size: 每个chunk的诗词数量，默认从配置读取
            step_name: 步骤名称，用于状态跟踪
        """
        self.base_dir = Path(base_dir)
        self.prefix = prefix
        self.chunk_size = chunk_size or get_settings().analysis.chunk_size
        self.step_name = step_name
        
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.base_dir / f"{self.prefix}_state.json"
        
        self._state: Optional[ProcessingState] = None
    
    def get_state(self) -> ProcessingState:
        """获取当前处理状态"""
        if self._state is None:
            self._load_state()
        return self._state
    
    def _load_state(self):
        """加载处理状态"""
        if self.state_file.exists():
            with open(self.state_file, "r", encoding="utf-8") as f:
                state_data = json.load(f)
            self._state = ProcessingState(**state_data)
        else:
            self._state = ProcessingState(
                step_name=self.step_name,
                total_chunks=0,
                completed_chunks=[],
                failed_chunks=[],
                current_chunk=-1,
                start_time=datetime.now().isoformat(),
                last_update=datetime.now().isoformat()
            )
    
    def _save_state(self):
        """保存处理状态"""
        if self._state:
            self._state.last_update = datetime.now().isoformat()
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(asdict(self._state), f, ensure_ascii=False, indent=2)
    
    def reset_state(self):
        """重置处理状态"""
        if self.state_file.exists():
            self.state_file.unlink()
        self._state = None
        print(f"  重置状态: {self.step_name}")
    
    def split_to_chunks(
        self,
        df: pd.DataFrame,
        output_format: str = "csv"
    ) -> List[ChunkInfo]:
        """将DataFrame分割成多个chunk文件
        
        Args:
            df: 输入的数据框
            output_format: 输出格式，支持 "csv" 或 "json"
            
        Returns:
            List[ChunkInfo]: 分块信息列表
        """
        print(f">>> 开始分块处理...")
        print(f"  输入数据: {len(df)} 条记录")
        print(f"  Chunk大小: {self.chunk_size}")
        print(f"  输出格式: {output_format}")
        print(f"  输出目录: {self.base_dir}")
        
        total_count = len(df)
        chunk_count = (total_count + self.chunk_size - 1) // self.chunk_size
        
        print(f"  计算chunk数: {chunk_count}")
        
        chunk_infos = []
        
        for i in range(chunk_count):
            start_idx = i * self.chunk_size
            end_idx = min((i + 1) * self.chunk_size, total_count)
            chunk_df = df.iloc[start_idx:end_idx]
            
            chunk_id = i
            if output_format == "csv":
                file_path = self.base_dir / f"{self.prefix}_{chunk_id:04d}.csv"
                chunk_df.to_csv(file_path, index=False, encoding="utf-8-sig")
            elif output_format == "json":
                file_path = self.base_dir / f"{self.prefix}_{chunk_id:04d}.json"
                chunk_df.to_json(file_path, orient="records", force_ascii=False, indent=2)
            else:
                raise ValueError(f"不支持的输出格式: {output_format}")
            
            chunk_info = ChunkInfo(
                chunk_id=chunk_id,
                start_index=start_idx,
                end_index=end_idx,
                count=len(chunk_df),
                file_path=file_path,
                status="completed"
            )
            chunk_infos.append(chunk_info)
            
            if (chunk_id + 1) % 10 == 0 or chunk_id == chunk_count - 1:
                print(f"  [{chunk_id+1}/{chunk_count}] 生成 chunk {chunk_id}: {len(chunk_df)} 条记录 -> {file_path}")
        
        # 保存分块元数据
        print(f"  保存分块元数据...")
        self._save_metadata(chunk_infos, total_count)
        
        # 更新状态
        print(f"  初始化处理状态...")
        self._state = ProcessingState(
            step_name=self.step_name,
            total_chunks=chunk_count,
            completed_chunks=[],
            failed_chunks=[],
            current_chunk=-1,
            start_time=datetime.now().isoformat(),
            last_update=datetime.now().isoformat()
        )
        self._save_state()
        
        print(f">>> 分块完成!")
        print(f"  总chunk数: {chunk_count}")
        print(f"  元数据文件: {self.base_dir / f'{self.prefix}_metadata.json'}")
        print(f"  状态文件: {self.state_file}")
        
        return chunk_infos
    
    def process_chunks(
        self,
        process_func: Callable[[pd.DataFrame], pd.DataFrame],
        input_path: Optional[Path] = None,
        input_chunk_manager: Optional['AdvancedChunkManager'] = None,
        output_format: str = "csv",
        resume: bool = True,
        force: bool = False
    ) -> List[ChunkInfo]:
        """处理所有chunk
        
        Args:
            process_func: 处理函数，接收DataFrame，返回处理后的DataFrame
            input_path: 输入文件路径（如果需要从单文件读取）
            input_chunk_manager: 输入chunk管理器（如果需要从另一个chunk管理器读取）
            output_format: 输出格式
            resume: 是否从上次中断处继续
            force: 是否强制重新处理所有chunk
            
        Returns:
            List[ChunkInfo]: 分块信息列表
        """
        print(f">>> 开始处理所有chunk...")
        print(f"  基础目录: {self.base_dir}")
        print(f"  前缀: {self.prefix}")
        print(f"  输出格式: {output_format}")
        print(f"  断点续传: {resume}")
        print(f"  强制重处理: {force}")
        
        state = self.get_state()
        print(f"  当前状态: 已完成 {len(state.completed_chunks)} 个chunk")
        print(f"  当前状态: 失败 {len(state.failed_chunks)} 个chunk")
        
        # 如果有输入文件且没有chunk，先分块
        if input_path and input_path.exists() and state.total_chunks == 0:
            print(f"  从输入文件分块: {input_path}")
            df = pd.read_csv(input_path)
            print(f"  读取到 {len(df)} 条记录")
            self.split_to_chunks(df, output_format)
            state = self.get_state()
            print(f"  分块完成: {state.total_chunks} 个chunk")
        
        # 如果有输入chunk管理器，使用其chunk信息
        if input_chunk_manager:
            print(f"  使用输入chunk管理器: {input_chunk_manager.base_dir}")
            input_chunk_infos = input_chunk_manager.get_chunk_infos()
            print(f"  输入chunk数: {len(input_chunk_infos)}")
            
            # 如果当前没有chunk，创建对应数量的chunk
            if state.total_chunks == 0:
                print(f"  创建输出chunk: {len(input_chunk_infos)} 个")
                for chunk_info in input_chunk_infos:
                    chunk_id = chunk_info.chunk_id
                    chunk_info_copy = ChunkInfo(
                        chunk_id=chunk_id,
                        start_index=chunk_info.start_index,
                        end_index=chunk_info.end_index,
                        count=chunk_info.count,
                        file_path=self.base_dir / f"{self.prefix}_{chunk_id:04d}.{output_format}",
                        status="pending"
                    )
                    # 保存空chunk
                    if output_format == "csv":
                        pd.DataFrame().to_csv(chunk_info_copy.file_path, index=False, encoding="utf-8-sig")
                    elif output_format == "json":
                        pd.DataFrame().to_json(chunk_info_copy.file_path, orient="records", force_ascii=False, indent=2)
                
                # 更新状态
                self._state = ProcessingState(
                    step_name=self.step_name,
                    total_chunks=len(input_chunk_infos),
                    completed_chunks=[],
                    failed_chunks=[],
                    current_chunk=-1,
                    start_time=datetime.now().isoformat(),
                    last_update=datetime.now().isoformat()
                )
                self._save_metadata([ChunkInfo(
                    chunk_id=ci.chunk_id,
                    start_index=ci.start_index,
                    end_index=ci.end_index,
                    count=ci.count,
                    file_path=self.base_dir / f"{self.prefix}_{ci.chunk_id:04d}.{output_format}",
                    status="pending"
                ) for ci in input_chunk_infos], sum(ci.count for ci in input_chunk_infos))
                self._save_state()
                state = self.get_state()
        
        chunk_infos = self.get_chunk_infos()
        print(f"  找到 {len(chunk_infos)} 个chunk")
        processed_chunks = []
        
        for idx, chunk_info in enumerate(chunk_infos, 1):
            chunk_id = chunk_info.chunk_id
            
            # 检查是否需要处理
            if not force and resume and chunk_id in state.completed_chunks:
                print(f"  [{idx}/{len(chunk_infos)}] 跳过 chunk {chunk_id} (已完成)")
                processed_chunks.append(chunk_info)
                continue
            
            # 标记为处理中
            state.current_chunk = chunk_id
            self._save_state()
            
            try:
                # 读取chunk（从输入chunk管理器或当前chunk管理器）
                if input_chunk_manager:
                    chunk_df = input_chunk_manager.read_chunk(chunk_id)
                    print(f"  [{idx}/{len(chunk_infos)}] 从输入chunk读取 chunk {chunk_id}: {len(chunk_df)} 条记录")
                else:
                    chunk_df = self.read_chunk(chunk_id)
                    print(f"  [{idx}/{len(chunk_infos)}] 处理 chunk {chunk_id}: {len(chunk_df)} 条记录")
                
                # 处理chunk
                processed_df = process_func(chunk_df)
                
                # 保存处理后的chunk
                output_path = self.base_dir / f"{self.prefix}_processed_{chunk_id:04d}.{output_format}"
                print(f"    保存到: {output_path}")
                
                if output_format == "csv":
                    processed_df.to_csv(output_path, index=False, encoding="utf-8-sig")
                elif output_format == "json":
                    processed_df.to_json(output_path, orient="records", force_ascii=False, indent=2)
                
                # 更新状态
                chunk_info.status = "completed"
                if chunk_id not in state.completed_chunks:
                    state.completed_chunks.append(chunk_id)
                if chunk_id in state.failed_chunks:
                    state.failed_chunks.remove(chunk_id)
                
                processed_chunks.append(chunk_info)
                print(f"  [{idx}/{len(chunk_infos)}] 完成 chunk {chunk_id}")
                
            except Exception as e:
                print(f"  [{idx}/{len(chunk_infos)}] 错误 chunk {chunk_id}: {e}")
                chunk_info.status = "failed"
                if chunk_id not in state.failed_chunks:
                    state.failed_chunks.append(chunk_id)
                raise
            
            finally:
                self._save_state()
        
        # 完成处理
        state.current_chunk = -1
        self._save_state()
        
        print(f">>> 所有chunk处理完成!")
        print(f"  成功: {len(processed_chunks)} 个chunk")
        print(f"  失败: {len(state.failed_chunks)} 个chunk")
        
        return processed_chunks
    
    def read_chunk(
        self,
        chunk_id: int,
        format: Optional[str] = None,
        processed: bool = False
    ) -> pd.DataFrame:
        """读取指定的chunk
        
        Args:
            chunk_id: chunk ID
            format: 文件格式，如果不指定则自动检测
            processed: 是否读取处理后的chunk
            
        Returns:
            pd.DataFrame: chunk数据
        """
        file_path = self._get_chunk_path(chunk_id, processed=processed)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Chunk文件不存在: {file_path}")
        
        if format is None:
            format = file_path.suffix[1:]  # 去掉点号
        
        if format == "csv":
            return pd.read_csv(file_path)
        elif format == "json":
            return pd.read_json(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {format}")
    
    def read_all_chunks(self, processed: bool = False) -> pd.DataFrame:
        """读取所有chunk并合并
        
        Args:
            processed: 是否读取处理后的chunk
            
        Returns:
            pd.DataFrame: 合并后的数据
        """
        chunk_infos = self.get_chunk_infos()
        print(f"  读取 {len(chunk_infos)} 个chunk...")
        
        dfs = []
        for chunk_info in chunk_infos:
            try:
                df = self.read_chunk(chunk_info.chunk_id, processed=processed)
                dfs.append(df)
            except FileNotFoundError:
                if processed:
                    continue
                raise
        
        if not dfs:
            return pd.DataFrame()
        
        print(f"  合并 {len(dfs)} 个chunk...")
        df = pd.concat(dfs, ignore_index=True)
        print(f"  合并完成: {len(df)} 条记录")
        
        return df
    
    def iter_chunks(self, processed: bool = False) -> Iterator[pd.DataFrame]:
        """迭代所有chunk
        
        Args:
            processed: 是否迭代处理后的chunk
            
        Yields:
            pd.DataFrame: 每个chunk的数据
        """
        chunk_infos = self.get_chunk_infos()
        
        for chunk_info in chunk_infos:
            try:
                yield self.read_chunk(chunk_info.chunk_id, processed=processed)
            except FileNotFoundError:
                if processed:
                    continue
                raise
    
    def get_chunk_infos(self) -> List[ChunkInfo]:
        """获取所有chunk信息
        
        Returns:
            List[ChunkInfo]: chunk信息列表
        """
        metadata_file = self.base_dir / f"{self.prefix}_metadata.json"
        
        if metadata_file.exists():
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            return [
                ChunkInfo(
                    chunk_id=info["chunk_id"],
                    start_index=info["start_index"],
                    end_index=info["end_index"],
                    count=info["count"],
                    file_path=Path(info["file_path"]),
                    status=info.get("status", "pending")
                )
                for info in metadata["chunks"]
            ]
        else:
            # 如果没有元数据，扫描目录
            chunk_infos = []
            pattern = f"{self.prefix}_*.csv"
            for file_path in sorted(self.base_dir.glob(pattern)):
                chunk_id = int(file_path.stem.split("_")[-1])
                df = pd.read_csv(file_path)
                chunk_info = ChunkInfo(
                    chunk_id=chunk_id,
                    start_index=0,
                    end_index=len(df),
                    count=len(df),
                    file_path=file_path,
                    status="pending"
                )
                chunk_infos.append(chunk_info)
            return chunk_infos
    
    def get_total_count(self) -> int:
        """获取总记录数
        
        Returns:
            int: 总记录数
        """
        chunk_infos = self.get_chunk_infos()
        return sum(info.count for info in chunk_infos)
    
    def get_chunk_count(self) -> int:
        """获取chunk总数
        
        Returns:
            int: chunk数量
        """
        return len(self.get_chunk_infos())
    
    def get_progress(self) -> Dict[str, Any]:
        """获取处理进度
        
        Returns:
            Dict[str, Any]: 进度信息
        """
        state = self.get_state()
        total = state.total_chunks
        completed = len(state.completed_chunks)
        failed = len(state.failed_chunks)
        
        return {
            "step_name": state.step_name,
            "total_chunks": total,
            "completed_chunks": completed,
            "failed_chunks": failed,
            "current_chunk": state.current_chunk,
            "progress_percent": (completed / total * 100) if total > 0 else 0,
            "start_time": state.start_time,
            "last_update": state.last_update,
            "metadata": state.metadata
        }
    
    def _get_chunk_path(self, chunk_id: int, processed: bool = False) -> Path:
        """获取chunk文件路径
        
        Args:
            chunk_id: chunk ID
            processed: 是否获取处理后的chunk路径
            
        Returns:
            Path: 文件路径
        """
        if processed:
            # 尝试处理后的CSV格式
            csv_path = self.base_dir / f"{self.prefix}_processed_{chunk_id:04d}.csv"
            if csv_path.exists():
                return csv_path
            
            # 尝试处理后的JSON格式
            json_path = self.base_dir / f"{self.prefix}_processed_{chunk_id:04d}.json"
            if json_path.exists():
                return json_path
        else:
            # 尝试原始CSV格式
            csv_path = self.base_dir / f"{self.prefix}_{chunk_id:04d}.csv"
            if csv_path.exists():
                return csv_path
            
            # 尝试原始JSON格式
            json_path = self.base_dir / f"{self.prefix}_{chunk_id:04d}.json"
            if json_path.exists():
                return json_path
        
        raise FileNotFoundError(f"找不到chunk {chunk_id}的文件")
    
    def _save_metadata(self, chunk_infos: List[ChunkInfo], total_count: int):
        """保存分块元数据
        
        Args:
            chunk_infos: chunk信息列表
            total_count: 总记录数
        """
        metadata = {
            "prefix": self.prefix,
            "chunk_size": self.chunk_size,
            "total_count": total_count,
            "chunk_count": len(chunk_infos),
            "chunks": [
                {
                    "chunk_id": info.chunk_id,
                    "start_index": info.start_index,
                    "end_index": info.end_index,
                    "count": info.count,
                    "file_path": str(info.file_path),
                    "status": info.status
                }
                for info in chunk_infos
            ]
        }
        
        metadata_file = self.base_dir / f"{self.prefix}_metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"  保存元数据: {metadata_file}")
    
    def clear_chunks(self):
        """清除所有chunk文件"""
        chunk_infos = self.get_chunk_infos()
        
        for chunk_info in chunk_infos:
            if chunk_info.file_path.exists():
                chunk_info.file_path.unlink()
                print(f"  删除: {chunk_info.file_path}")
        
        # 删除处理后的文件
        for file_path in self.base_dir.glob(f"{self.prefix}_processed_*"):
            if file_path.exists():
                file_path.unlink()
                print(f"  删除: {file_path}")
        
        # 删除元数据
        metadata_file = self.base_dir / f"{self.prefix}_metadata.json"
        if metadata_file.exists():
            metadata_file.unlink()
            print(f"  删除: {metadata_file}")
        
        # 重置状态
        self.reset_state()


def create_chunk_manager(
    data_type: str = "bronze",
    prefix: str = "chunk",
    chunk_size: Optional[int] = None,
    step_name: str = "default"
) -> AdvancedChunkManager:
    """创建分块管理器的便捷函数
    
    Args:
        data_type: 数据类型，可选 "bronze", "silver", "gold"
        prefix: 分块文件名前缀
        chunk_size: 每个chunk的诗词数量
        step_name: 步骤名称
        
    Returns:
        AdvancedChunkManager: 分块管理器实例
    """
    settings = get_settings()
    
    if data_type == "bronze":
        base_dir = settings.data.results_dir / "bronze"
    elif data_type == "silver":
        base_dir = settings.data.results_dir / "silver"
    elif data_type == "gold":
        base_dir = settings.data.results_dir / "gold"
    else:
        raise ValueError(f"不支持的数据类型: {data_type}")
    
    return AdvancedChunkManager(base_dir, prefix, chunk_size, step_name)
