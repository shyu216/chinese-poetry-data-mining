"""
词汇频率分析步骤

使用 WordFrequencyAnalyzer 分析诗词词汇
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


def main():
    parser = argparse.ArgumentParser(description="词汇频率分析")
    parser.add_argument(
        "--data",
        choices=["sample", "full"],
        default="sample",
        help="处理数据集类型"
    )
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
    
    # 输入文件
    if args.data == "sample":
        input_csv = silver_dir / "v2_poems_structured.csv"
    else:
        input_csv = silver_dir / "v2_poems_structured.csv"
    
    output_json = gold_dir / "v3_word_frequency.json"
    output_metadata = gold_dir / "v3_word_frequency_metadata.json"
    
    # 检查输入
    if not input_csv.exists():
        print(f"错误: 输入文件不存在 {input_csv}")
        print("请先运行: python scripts/steps/02_structure.py")
        return
    
    # 检查是否已存在
    if not args.force and output_json.exists():
        print(f"已存在: {output_json}，使用 --force 重新生成")
        return
    
    print("=" * 50)
    print("词汇频率分析")
    print("=" * 50)
    
    # 加载数据
    print(f"\n加载数据: {input_csv}")
    df = pd.read_csv(input_csv)
    print(f"记录数: {len(df)}")
    
    # 创建分析器
    analyzer = WordFrequencyAnalyzer(config={
        "top_n": settings.analysis.word_freq_top_n,
        "min_word_length": settings.analysis.min_word_length
    })
    
    # 执行分析
    print("\n执行分析...")
    result = analyzer.analyze(df)
    
    # 保存结果
    print(f"\n保存结果: {output_json}")
    gold_dir.mkdir(parents=True, exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)
    
    # 保存元数据
    metadata = PipelineMetadata(
        version="v3",
        steps=[
            PipelineStep(
                name="word_frequency",
                input_version="v2",
                output_version="v3",
                timestamp=datetime.now().isoformat(),
                params={"data": args.data},
                record_count=len(df)
            )
        ],
        total_records=len(df),
        source_files=[str(input_csv)],
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
