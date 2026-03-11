#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诗词数据处理脚本 - 精简版
功能：
1. 读取全唐诗、全宋诗和宋词的所有JSON文件
2. 数据预处理和清洗
3. 只输出 all_poetry（包含朝代和体裁信息）
4. 生成1/1000随机采样数据集用于可行性测试
"""

import sys
import json
import random
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from src.core.text_utils import TextProcessor


def load_poetry_files(
    data_dir: Path, 
    pattern: str, 
    dynasty: str, 
    genre: str,
    data_type: str,
    target_dir_name: str = "全唐诗"
) -> List[Dict[str, Any]]:
    """
    通用函数：加载诗词JSON文件
    
    Args:
        data_dir: 数据根目录
        pattern: 文件匹配模式 (如 "poet.tang.*.json")
        dynasty: 朝代名称 (如 "唐代", "宋代")
        genre: 体裁 (如 "诗", "词")
        data_type: 数据类型描述 (如 "唐诗", "宋诗", "宋词")
        target_dir_name: 目标目录名
        
    Returns:
        所有诗词的列表
    """
    target_dir = data_dir / "chinese-poetry" / target_dir_name
    all_poems = []
    
    print(f"正在加载{data_type}数据...")
    print(f"目录: {target_dir}")
    
    # 获取所有匹配的JSON文件并排序
    json_files = sorted(target_dir.glob(pattern))
    print(f"找到 {len(json_files)} 个{data_type}数据文件")
    
    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 为每首诗添加朝代和体裁信息
                for poem in data:
                    poem["dynasty"] = dynasty
                    poem["genre"] = genre  # 诗 或 词
                    # 如果是词，确保有title字段
                    if "title" not in poem and "rhythmic" in poem:
                        poem["title"] = poem["rhythmic"]
                all_poems.extend(data)
                print(f"  ✓ 已加载 {json_file.name}: {len(data)} 首")
        except Exception as e:
            print(f"  ✗ 加载失败 {json_file.name}: {e}")
    
    print(f"{data_type}加载完成: 共 {len(all_poems)} 首\n")
    return all_poems


def load_all_tang_poems(data_dir: Path) -> List[Dict[str, Any]]:
    """加载所有唐诗 (poet.tang.*.json)"""
    return load_poetry_files(
        data_dir=data_dir,
        pattern="poet.tang.*.json",
        dynasty="唐代",
        genre="诗",
        data_type="唐诗"
    )


def load_all_song_poems(data_dir: Path) -> List[Dict[str, Any]]:
    """加载所有宋诗 (poet.song.*.json)"""
    return load_poetry_files(
        data_dir=data_dir,
        pattern="poet.song.*.json",
        dynasty="宋代",
        genre="诗",
        data_type="宋诗"
    )


def load_all_song_ci(data_dir: Path) -> List[Dict[str, Any]]:
    """加载所有宋词 (ci.song.*.json)"""
    return load_poetry_files(
        data_dir=data_dir,
        pattern="ci.song.*.json",
        dynasty="宋代",
        genre="词",
        data_type="宋词",
        target_dir_name="宋词"
    )


def preprocess_data(df: pd.DataFrame, preprocessor: TextProcessor) -> pd.DataFrame:
    """
    预处理诗词数据
    
    Args:
        df: 原始DataFrame
        preprocessor: 文本预处理器
        
    Returns:
        预处理后的DataFrame
    """
    print("开始数据预处理...")
    
    # 处理paragraphs列，转换为content字符串
    if "paragraphs" in df.columns:
        print("  - 转换paragraphs为content...")
        df["content"] = df["paragraphs"].apply(
            lambda x: "\n".join(x) if isinstance(x, list) else str(x)
        )
    
    # 繁体转简体
    print("  - 繁体转简体...")
    df["content"] = df["content"].apply(preprocessor.traditional_to_simplified)
    df["title"] = df["title"].apply(
        lambda x: preprocessor.traditional_to_simplified(str(x)) if pd.notna(x) else ""
    )
    
    # 清洗文本
    print("  - 清洗文本...")
    df["content"] = df["content"].apply(preprocessor.clean_text)
    df["title"] = df["title"].apply(preprocessor.clean_text)
    
    # 清洗作者字段
    if "author" in df.columns:
        df["author"] = df["author"].apply(
            lambda x: str(x).strip() if pd.notna(x) else ""
        )
    
    # 移除空内容
    initial_count = len(df)
    df = df[df["content"] != ""]
    removed_count = initial_count - len(df)
    if removed_count > 0:
        print(f"  - 移除 {removed_count} 条空内容记录")
    
    # 去重
    initial_count = len(df)
    df = df.drop_duplicates(subset=["author", "title", "content"], keep="first")
    dup_count = initial_count - len(df)
    if dup_count > 0:
        print(f"  - 移除 {dup_count} 条重复记录")
    
    print(f"预处理完成: 剩余 {len(df)} 条记录\n")
    return df


def save_dual_format(df: pd.DataFrame, output_dir: Path, filename_base: str):
    """
    双格式保存数据（Pickle + CSV）
    
    Args:
        df: 要保存的DataFrame
        output_dir: 输出目录
        filename_base: 文件名基础（不含扩展名）
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存为Pickle格式（保留数据类型，读取快）
    pickle_path = output_dir / f"{filename_base}.pkl"
    df.to_pickle(pickle_path)
    print(f"  ✓ Pickle格式已保存: {pickle_path}")
    
    # 保存为CSV格式（人类可读，兼容性好）
    csv_path = output_dir / f"{filename_base}.csv"
    # 对于CSV，将paragraphs列表转为字符串
    df_csv = df.copy()
    if "paragraphs" in df_csv.columns:
        df_csv["paragraphs"] = df_csv["paragraphs"].apply(
            lambda x: "\n".join(x) if isinstance(x, list) else str(x)
        )
    df_csv.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"  ✓ CSV格式已保存: {csv_path}")


def create_sample_dataset(
    df: pd.DataFrame, 
    sample_ratio: float = 0.001, 
    random_seed: int = 42
) -> pd.DataFrame:
    """
    创建随机采样数据集
    
    Args:
        df: 原始DataFrame
        sample_ratio: 采样比例（默认1/1000 = 0.001）
        random_seed: 随机种子，保证可复现
        
    Returns:
        采样后的DataFrame
    """
    sample_size = max(1, int(len(df) * sample_ratio))
    
    print(f"创建采样数据集...")
    print(f"  - 原始数据量: {len(df)}")
    print(f"  - 采样比例: {sample_ratio} (1/{int(1/sample_ratio)})")
    print(f"  - 采样数量: {sample_size}")
    
    # 设置随机种子保证可复现
    np.random.seed(random_seed)
    random.seed(random_seed)
    
    # 分层采样：保证每个朝代和体裁都有代表
    if "dynasty" in df.columns and "genre" in df.columns:
        # 按朝代和体裁组合分层
        sample_df = df.groupby(["dynasty", "genre"], group_keys=False).apply(
            lambda x: x.sample(min(len(x), max(1, int(len(x) * sample_ratio)))),
            include_groups=False
        )
        # 需要重新包含分组列
        sample_df = df.loc[sample_df.index]
    elif "dynasty" in df.columns:
        sample_df = df.groupby("dynasty", group_keys=False).apply(
            lambda x: x.sample(min(len(x), max(1, int(len(x) * sample_ratio)))),
            include_groups=False
        )
        sample_df = df.loc[sample_df.index]
    else:
        sample_df = df.sample(n=sample_size, random_state=random_seed)
    
    print(f"  - 实际采样数量: {len(sample_df)}")
    
    # 显示采样数据的分布
    if "dynasty" in sample_df.columns and "genre" in sample_df.columns:
        print(f"  - 采样数据分布:")
        for (dynasty, genre), count in sample_df.groupby(["dynasty", "genre"]).size().items():
            print(f"    {dynasty}-{genre}: {count}首")
    elif "dynasty" in sample_df.columns:
        print(f"  - 采样数据朝代分布:")
        for dynasty, count in sample_df["dynasty"].value_counts().items():
            print(f"    {dynasty}: {count}首")
    
    return sample_df


def generate_statistics(df: pd.DataFrame, name: str = "数据集"):
    """
    生成数据统计信息
    
    Args:
        df: DataFrame
        name: 数据集名称
    """
    print(f"\n{'='*50}")
    print(f"{name}统计信息")
    print(f"{'='*50}")
    
    print(f"总记录数: {len(df)}")
    
    if "dynasty" in df.columns:
        print(f"\n朝代分布:")
        for dynasty, count in df["dynasty"].value_counts().items():
            print(f"  {dynasty}: {count}首")
    
    if "genre" in df.columns:
        print(f"\n体裁分布:")
        for genre, count in df["genre"].value_counts().items():
            print(f"  {genre}: {count}首")
    
    if "dynasty" in df.columns and "genre" in df.columns:
        print(f"\n朝代-体裁交叉分布:")
        cross_tab = pd.crosstab(df["dynasty"], df["genre"])
        print(cross_tab)
    
    if "author" in df.columns:
        print(f"\n作者数量: {df['author'].nunique()}")
        print(f"作品最多的10位作者:")
        top_authors = df["author"].value_counts().head(10)
        for author, count in top_authors.items():
            print(f"  {author}: {count}首")
    
    if "content" in df.columns:
        df["char_count"] = df["content"].apply(len)
        print(f"\n内容长度统计:")
        print(f"  平均字数: {df['char_count'].mean():.1f}")
        print(f"  中位数: {df['char_count'].median():.1f}")
        print(f"  最短: {df['char_count'].min()}")
        print(f"  最长: {df['char_count'].max()}")


def main():
    """主函数"""
    print("="*60)
    print("诗词数据处理 - 精简版")
    print("="*60)
    
    # 设置路径
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    output_dir = data_dir / "processed_data"
    sample_dir = data_dir / "sample_data"
    
    print(f"\n项目根目录: {project_root}")
    print(f"数据目录: {data_dir}")
    print(f"输出目录: {output_dir}")
    print(f"采样目录: {sample_dir}\n")
    
    # 初始化预处理器
    preprocessor = TextProcessor()
    
    # ========== 1. 加载数据 ==========
    print("\n" + "="*60)
    print("步骤 1: 加载原始JSON数据")
    print("="*60)
    
    # 加载唐诗 (poet.tang.*.json)
    tang_poems = load_all_tang_poems(data_dir)
    
    # 加载宋诗 (poet.song.*.json)
    song_poems = load_all_song_poems(data_dir)
    
    # 加载宋词 (ci.song.*.json)
    song_ci = load_all_song_ci(data_dir)
    
    # ========== 2. 合并并预处理 ==========
    print("\n" + "="*60)
    print("步骤 2: 合并数据并预处理")
    print("="*60)
    
    # 合并所有数据
    all_poems = []
    all_poems.extend(tang_poems)
    all_poems.extend(song_poems)
    all_poems.extend(song_ci)
    
    print(f"合并原始数据: 共 {len(all_poems)} 首")
    print(f"  - 唐诗: {len(tang_poems)} 首")
    print(f"  - 宋诗: {len(song_poems)} 首")
    print(f"  - 宋词: {len(song_ci)} 首\n")
    
    # 创建DataFrame并预处理
    df = pd.DataFrame(all_poems)
    df = preprocess_data(df, preprocessor)
    
    # ========== 3. 保存完整数据 ==========
    print("\n" + "="*60)
    print("步骤 3: 保存完整数据（双格式）")
    print("="*60)
    
    print(f"\n保存全部数据: {len(df)} 首")
    save_dual_format(df, output_dir, "all_poetry")
    
    # ========== 4. 创建采样数据集 ==========
    print("\n" + "="*60)
    print("步骤 4: 创建1/1000采样数据集")
    print("="*60)
    
    sample_df = create_sample_dataset(df, sample_ratio=0.001, random_seed=42)
    print("\n保存采样数据...")
    save_dual_format(sample_df, sample_dir, "all_poetry")
    
    # ========== 5. 生成统计信息 ==========
    print("\n" + "="*60)
    print("步骤 5: 数据统计")
    print("="*60)
    
    generate_statistics(df, "完整数据集")
    generate_statistics(sample_df, "采样数据集(1/1000)")
    
    # ========== 完成 ==========
    print("\n" + "="*60)
    print("数据处理完成！")
    print("="*60)
    print(f"\n输出文件:")
    print(f"  完整数据: {output_dir}/all_poetry.pkl / .csv")
    print(f"  采样数据: {sample_dir}/all_poetry.pkl / .csv")
    print(f"\n数据字段说明:")
    print(f"  - author: 作者")
    print(f"  - title: 标题")
    print(f"  - content: 内容（清洗后）")
    print(f"  - dynasty: 朝代（唐代/宋代）")
    print(f"  - genre: 体裁（诗/词）")
    print(f"  - paragraphs: 原始段落列表")
    print(f"  - rhythmic: 词牌名（仅词有）")
    print(f"  - id: 唯一标识")


if __name__ == "__main__":
    main()
