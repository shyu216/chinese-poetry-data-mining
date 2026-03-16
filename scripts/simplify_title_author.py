"""
诗词标题和作者繁简转换脚本

功能:
1. 读取 preprocessed 目录下的 CSV 文件
2. 使用 opencc 就地修改，将 title 和 author 列从繁体转换为简体
3. 维护两个 dict 记录繁简映射关系
4. 将映射保存为 JSON，格式 [[繁体, 简体], ...]

输入/输出（就地修改）:
- results/preprocessed/poems_chunk_*.csv （直接修改原文件）

其他输出:
- results/simplified_title_author/unique_authors.json ([[繁体, 简体], ...])
- results/simplified_title_author/unique_titles.json ([[繁体, 简体], ...])
"""

import csv
import json
import argparse
from pathlib import Path
from typing import Set, Dict, List
import opencc


class TitleAuthorSimplifier:
    def __init__(self, input_dir: Path, output_dir: Path):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.converter = opencc.OpenCC('t2s')
        
        # 使用 dict 存储繁简映射，key为繁体，value为简体
        self.author_mappings: Dict[str, str] = {}
        self.title_mappings: Dict[str, str] = {}
        
        # 缓存已转换的文本，避免重复转换
        self._author_cache: Dict[str, str] = {}
        self._title_cache: Dict[str, str] = {}
    
    def _simplify_author(self, author: str) -> str:
        """转换作者名，使用缓存加速"""
        if author in self._author_cache:
            print(f"  [缓存命中] 作者: '{author}' -> '{self._author_cache[author]}'")
            return self._author_cache[author]
        
        simplified = self.converter.convert(author)
        self._author_cache[author] = simplified
        print(f"  [转换] 作者: '{author}' -> '{simplified}'")
        return simplified
    
    def _simplify_title(self, title: str) -> str:
        """转换标题，使用缓存加速"""
        if title in self._title_cache:
            print(f"  [缓存命中] 标题: '{title}' -> '{self._title_cache[title]}'")
            return self._title_cache[title]
        
        simplified = self.converter.convert(title)
        self._title_cache[title] = simplified
        print(f"  [转换] 标题: '{title}' -> '{simplified}'")
        return simplified
    
    def _ensure_output_dir(self):
        """确保输出目录存在"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_input_files(self) -> List[Path]:
        """获取所有输入 CSV 文件，按文件名排序"""
        pattern = "poems_chunk_*.csv"
        files = sorted(self.input_dir.glob(pattern))
        return files
    
    def _process_single_file(self, input_file: Path) -> Dict[str, int]:
        """处理单个 CSV 文件（就地修改）
        
        直接修改原文件，将 title 和 author 列繁转简
        
        Returns:
            统计信息字典
        """
        print(f"\n[处理文件] {input_file.name}")
        print(f"  文件路径: {input_file.absolute()}")
        
        records_processed = 0
        records_with_title = 0
        records_with_author = 0
        
        # 读取所有行
        print(f"  正在读取文件...")
        with open(input_file, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            print(f"  CSV 列名: {fieldnames}")
            rows = list(reader)
            print(f"  读取到 {len(rows)} 行数据")
        
        # 就地修改：将 title 和 author 替换为简体
        print(f"  开始转换...")
        for i, row in enumerate(rows):
            if i < 3:  # 只打印前3行的详细信息
                print(f"    [行 {i+1}] id={row.get('id', 'N/A')[:8]}...")
            elif i == 3:
                print(f"    ... (后续行省略详细输出)")
            
            title_origin = row.get('title', '')
            author_origin = row.get('author', '')
            
            # 转换标题
            if title_origin:
                if i < 3:
                    print(f"      原标题: '{title_origin}'")
                title_simplified = self._simplify_title(title_origin)
                row['title'] = title_simplified
                self.title_mappings[title_origin] = title_simplified
                records_with_title += 1
            
            # 转换作者
            if author_origin:
                if i < 3:
                    print(f"      原作者: '{author_origin}'")
                author_simplified = self._simplify_author(author_origin)
                row['author'] = author_simplified
                self.author_mappings[author_origin] = author_simplified
                records_with_author += 1
            
            records_processed += 1
        
        # 写回原文件
        print(f"  正在写回原文件...")
        with open(input_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"  文件写入完成")
        
        print(f"  [文件统计] 处理记录: {records_processed}, 有标题: {records_with_title}, 有作者: {records_with_author}")
        
        return {
            'records_processed': records_processed,
            'records_with_title': records_with_title,
            'records_with_author': records_with_author
        }
    
    def _save_unique_names(self):
        """保存繁简映射到 JSON，格式为 [[繁体, 简体], ...]"""
        print(f"\n[保存映射文件]")
        
        authors_file = self.output_dir / 'unique_authors.json'
        titles_file = self.output_dir / 'unique_titles.json'
        
        print(f"  作者映射数量: {len(self.author_mappings)}")
        print(f"  标题映射数量: {len(self.title_mappings)}")
        
        # 转换为 [[繁体, 简体], ...] 格式，按繁体排序
        authors_list = sorted([[k, v] for k, v in self.author_mappings.items()])
        titles_list = sorted([[k, v] for k, v in self.title_mappings.items()])
        
        # 打印部分映射示例
        print(f"  作者映射示例 (前5个):")
        for item in authors_list[:5]:
            print(f"    {item}")
        if len(authors_list) > 5:
            print(f"    ... 共 {len(authors_list)} 个")
            
        print(f"  标题映射示例 (前5个):")
        for item in titles_list[:5]:
            print(f"    {item}")
        if len(titles_list) > 5:
            print(f"    ... 共 {len(titles_list)} 个")
        
        print(f"  正在保存 {authors_file.name}...")
        with open(authors_file, 'w', encoding='utf-8') as f:
            json.dump(authors_list, f, ensure_ascii=False, indent=2)
        
        print(f"  正在保存 {titles_file.name}...")
        with open(titles_file, 'w', encoding='utf-8') as f:
            json.dump(titles_list, f, ensure_ascii=False, indent=2)
        
        print(f"  映射文件保存完成")
        
        return authors_file, titles_file
    
    def process(self) -> Dict[str, any]:
        """处理所有文件
        
        Returns:
            处理结果统计
        """
        print("\n[初始化]")
        print(f"  创建输出目录: {self.output_dir}")
        self._ensure_output_dir()
        
        print(f"  查找输入文件...")
        input_files = self._get_input_files()
        print(f"  找到 {len(input_files)} 个文件")
        
        if not input_files:
            raise FileNotFoundError(f"在 {self.input_dir} 中未找到 poems_chunk_*.csv 文件")
        
        # 打印前5个文件名
        print(f"  文件列表 (前5个):")
        for f in input_files[:5]:
            print(f"    - {f.name}")
        if len(input_files) > 5:
            print(f"    ... 共 {len(input_files)} 个文件")
        
        total_stats = {
            'files_processed': 0,
            'total_records': 0,
            'total_with_title': 0,
            'total_with_author': 0
        }
        
        print(f"\n[开始处理文件]")
        for idx, input_file in enumerate(input_files, 1):
            print(f"\n[{idx}/{len(input_files)}] ", end="")
            stats = self._process_single_file(input_file)
            total_stats['files_processed'] += 1
            total_stats['total_records'] += stats['records_processed']
            total_stats['total_with_title'] += stats['records_with_title']
            total_stats['total_with_author'] += stats['records_with_author']
        
        # 保存唯一名字
        authors_file, titles_file = self._save_unique_names()
        
        return {
            **total_stats,
            'unique_authors_count': len(self.author_mappings),
            'unique_titles_count': len(self.title_mappings),
            'authors_file': str(authors_file),
            'titles_file': str(titles_file),
            'output_dir': str(self.output_dir)
        }


def main():
    parser = argparse.ArgumentParser(
        description='将诗词标题和作者从繁体转换为简体（就地修改）'
    )
    parser.add_argument(
        '--input-dir',
        type=str,
        default='results/preprocessed',
        help='输入/输出 CSV 文件目录 (默认: results/preprocessed，直接修改原文件)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='results/simplified_title_author',
        help='JSON 输出目录 (默认: results/simplified_title_author)'
    )
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    print("=" * 60)
    print("诗词标题和作者繁简转换（就地修改）")
    print("=" * 60)
    print(f"输入/输出目录: {input_dir.absolute()}（原文件将被修改）")
    print(f"JSON 输出目录: {output_dir.absolute()}")
    print()
    
    print(f"\n[创建转换器]")
    simplifier = TitleAuthorSimplifier(input_dir, output_dir)
    print(f"  输入目录: {simplifier.input_dir}")
    print(f"  输出目录: {simplifier.output_dir}")
    print(f"  OpenCC 配置: t2s (繁体转简体)")
    
    result = simplifier.process()
    
    print("\n" + "=" * 60)
    print("处理完成!")
    print("=" * 60)
    print(f"处理文件数: {result['files_processed']}")
    print(f"总记录数: {result['total_records']}")
    print(f"有标题的记录: {result['total_with_title']}")
    print(f"有作者的记录: {result['total_with_author']}")
    print()
    print(f"唯一作者映射数: {result['unique_authors_count']}")
    print(f"唯一标题映射数: {result['unique_titles_count']}")
    print()
    print(f"作者映射保存至: {result['authors_file']}")
    print(f"标题映射保存至: {result['titles_file']}")
    print("=" * 60)


if __name__ == '__main__':
    main()
