"""
词汇频率分析步骤

使用 WordFrequencyAnalyzer 分析诗词词汇

输入:
- results/silver/poems_chunk_processed_*.csv (处理后分块文件)

输出:
- results/gold/word_frequency/authors_chunk_*.json (作者词汇chunk文件)
- results/gold/word_frequency/authors_index.json (作者索引)
- data/gold/v3_word_frequency.json (分析结果摘要)
- data/gold/v3_word_frequency_metadata.json (元数据)
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd

from src.analyzers import WordFrequencyAnalyzer
from src.schema import PipelineMetadata, PipelineStep
from src.config import get_settings
from src.chunk import AdvancedChunkManager, create_chunk_manager


def main():
    parser = argparse.ArgumentParser(description="词汇频率分析")
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新生成"
    )
    args = parser.parse_args()
    
    settings = get_settings()
    
    # 路径
    silver_dir = settings.data.silver_dir
    gold_dir = settings.data.gold_dir
    
    output_json = gold_dir / "v3_word_frequency.json"
    output_metadata = gold_dir / "v3_word_frequency_metadata.json"
    
    # 创建chunk管理器
    silver_chunk_manager = create_chunk_manager(
        data_type="silver",
        prefix="poems_chunk",
        step_name="structure"
    )
    
    # 检查输入
    if silver_chunk_manager.get_chunk_count() == 0:
        print(f"错误: 未找到silver层数据")
        print(f"请先运行: python scripts/steps/02_structure.py")
        return
    
    # 检查是否已存在
    if not args.force and output_json.exists():
        print(f"已存在: {output_json}，使用 --force 重新生成")
        return
    
    print("=" * 50)
    print("词汇频率分析")
    print("=" * 50)
    
    # 加载数据（使用chunk）
    print(f"\n加载数据...")
    progress = silver_chunk_manager.get_progress()
    print(f"  chunk数量: {progress['total_chunks']}")
    print(f"  总记录数: {silver_chunk_manager.get_total_count()}")
    
    all_dfs = []
    for chunk_df in silver_chunk_manager.iter_chunks(processed=True):
        all_dfs.append(chunk_df)
    df = pd.concat(all_dfs, ignore_index=True)
    print(f"加载: {len(df)} 条记录")
    
    # 创建分析器
    analyzer = WordFrequencyAnalyzer(config={
        "top_n": settings.analysis.word_freq_top_n,
        "min_word_length": settings.analysis.min_word_length,
        "output_dir": str(settings.data.results_dir / "gold/word_frequency"),
        "chunk_size": 100
    })
    
    # 执行分析
    print("\n执行分析...")
    result = analyzer.analyze(df)
    
    # 保存结果摘要（不包含详细数据）
    print(f"\n保存结果摘要: {output_json}")
    gold_dir.mkdir(parents=True, exist_ok=True)
    
    # 只保存摘要信息，不保存详细的author_words
    summary_data = {
        "analyzer_name": result.analyzer_name,
        "version": result.version,
        "timestamp": result.timestamp,
        "data": {
            "author_count": result.data.get("author_count", 0),
            "global_top_words": result.data.get("global_top_words", []),
            "pos_distribution": result.data.get("pos_distribution", {}),
            "vocabulary_size": result.data.get("vocabulary_size", 0),
            "chunk_size": result.data.get("chunk_size", 0),
            "chunk_count": result.data.get("chunk_count", 0),
            "output_dir": result.data.get("output_dir", "")
        }
    }
    
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)
    
    # 保存元数据
    metadata = PipelineMetadata(
        version="v3",
        steps=[
            PipelineStep(
                name="word_frequency",
                input_version="v2",
                output_version="v3",
                timestamp=datetime.now().isoformat(),
                params={"force": args.force},
                record_count=len(df)
            )
        ],
        total_records=len(df),
        source_files=[],
        params={"analyzer": analyzer.get_info()}
    )
    
    with open(output_metadata, "w", encoding="utf-8") as f:
        f.write(metadata.model_dump_json(indent=2))
    
    print("\n" + "=" * 50)
    print("完成!")
    print(f"作者数: {result.data.get('author_count', 0)}")
    print(f"词汇表大小: {result.data.get('vocabulary_size', 0)}")
    print("=" * 50)


if __name__ == "__main__":
    main()
