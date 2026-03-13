"""
文本相似度分析步骤

使用 TextSimilarityAnalyzer 计算作者用词相似度
"""

import json
import argparse
from pathlib import Path
from datetime import datetime

import pandas as pd

from src.analyzers import TextSimilarityAnalyzer
from src.schema import PipelineMetadata, PipelineStep
from src.config import get_settings


def main():
    parser = argparse.ArgumentParser(description="文本相似度分析")
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
    
    output_json = gold_dir / "v3_text_similarity.json"
    output_metadata = gold_dir / "v3_text_similarity_metadata.json"
    
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
    print("文本相似度分析")
    print("=" * 50)
    
    # 加载数据
    print(f"\n加载数据: {input_csv}")
    df = pd.read_csv(input_csv)
    print(f"记录数: {len(df)}")
    
    # 创建分析器
    analyzer = TextSimilarityAnalyzer(config={
        "max_features": settings.analysis.max_features,
        "min_df": settings.analysis.min_df,
        "top_n": settings.analysis.top_similar_authors,
        "similarity_threshold": settings.analysis.similarity_threshold
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
                name="text_similarity",
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
    print(f"网络边数: {len(result.data.get('network_edges', []))}")
    print("=" * 50)


if __name__ == "__main__":
    main()
