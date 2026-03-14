"""
文本相似度分析步骤

使用 TextSimilarityAnalyzer 计算作者用词相似度

输入:
- results/silver/poems_chunk_processed_*.csv (处理后分块文件)

输出:
- results/gold/text_similarity/authors_chunk_*.json (作者相似度chunk文件)
- results/gold/text_similarity/authors_index.json (作者索引)
- data/gold/v3_text_similarity.json (分析结果摘要)
- data/gold/v3_text_similarity_metadata.json (元数据)
"""

import json
import argparse
from pathlib import Path
from datetime import datetime

import pandas as pd

from src.analyzers import TextSimilarityAnalyzer
from src.schema import PipelineMetadata, PipelineStep
from src.config import get_settings
from src.chunk import AdvancedChunkManager, create_chunk_manager


def main():
    parser = argparse.ArgumentParser(description="文本相似度分析")
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
    
    output_json = gold_dir / "v3_text_similarity.json"
    output_metadata = gold_dir / "v3_text_similarity_metadata.json"
    
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
    print("文本相似度分析")
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
    analyzer = TextSimilarityAnalyzer(config={
        "max_features": settings.analysis.max_features,
        "min_df": settings.analysis.min_df,
        "top_n": settings.analysis.top_similar_authors,
        "similarity_threshold": settings.analysis.similarity_threshold,
        "output_dir": str(settings.data.results_dir / "gold/text_similarity"),
        "chunk_size": 100,
        "top_poems": 1
    })
    
    # 执行分析
    print("\n执行分析...")
    result = analyzer.analyze(df)
    
    # 保存结果摘要（不包含详细数据）
    print(f"\n保存结果摘要: {output_json}")
    gold_dir.mkdir(parents=True, exist_ok=True)
    
    # 只保存摘要信息，不保存详细的similar_authors和similarity_matrix
    summary_data = {
        "analyzer_name": result.analyzer_name,
        "version": result.version,
        "timestamp": result.timestamp,
        "data": {
            "authors": result.data.get("authors", []),
            "network_edges": result.data.get("network_edges", []),
            "vocabulary_size": result.data.get("vocabulary_size", 0),
            "author_count": result.data.get("author_count", 0),
            "chunk_size": result.data.get("chunk_size", 0),
            "chunk_count": result.data.get("chunk_count", 0),
            "output_dir": result.data.get("output_dir", ""),
            "most_similar_poems_count": len(result.data.get("most_similar_poems", {}))
        }
    }
    
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)
    
    # 保存元数据
    metadata = PipelineMetadata(
        version="v3",
        steps=[
            PipelineStep(
                name="text_similarity",
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
    print(f"网络边数: {len(result.data.get('network_edges', []))}")
    print(f"最像诗词对数: {len(result.data.get('most_similar_poems', {}))}")
    print("=" * 50)


if __name__ == "__main__":
    main()
