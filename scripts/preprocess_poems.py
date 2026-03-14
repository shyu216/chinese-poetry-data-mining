"""
诗词预处理脚本

功能:
1. 加载 chinese-poetry submodule 数据（全唐诗和宋词）
2. 统一诗/词字段名
3. 繁简转换
4. 去重
5. 解析诗句结构
6. 去掉标点后，提取格律模式
7. 判断是否为格律诗
8. 分类诗体类型

输入:
- data/chinese-poetry/全唐诗/
- data/chinese-poetry/宋词/

输出:
- results/preprocessed/poems_chunk_*.csv (分块文件)

命令行:
============================================================
统计信息
============================================================

体裁分布:
  诗: 311601 首
  词: 21111 首

诗体分布:
  七言绝句: 83595 首
  七言律诗: 68938 首
  五言律诗: 60688 首
  五言古体: 36176 首
  杂言: 29153 首
  词: 21111 首
  五言绝句: 17181 首
  七言古体: 15667 首
  其他: 203 首

朝代分布:
  唐: 311601 首
  宋: 21111 首

============================================================
完成!
  总记录: 332712
  输出目录: results\preprocessed
============================================================
"""

import json
import hashlib
import re
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
import string
import opencc

class Simplifier:
    def __init__(self):
        self.converter = opencc.OpenCC('t2s')

    def traditional_to_simplified(self, text: str) -> str:
        """繁体转简体"""     
        return self.converter.convert(text)

class TextCleaner:
    def __init__(self):
        self.punctuation = r'[' + string.punctuation +\
        '，。！？；：、""''（）()【】\[\]《》〈〉「」『』〔〕〖〗·—–…' +\
            r'\u2000-\u206F\u3000-\u303F\uFF00-\uFFEF\uFE30-\uFE4F\uFE50-\uFE6F' +\
                r'\s]+'
        
    def clean_text(self, text: str) -> str:
        """清理文本，去除标点，只保留中文字符和换行符"""
        cleaned = re.sub(self.punctuation, ' ', text)
        return cleaned


def split_lines(content: str) -> List[str]:
    """将内容分割为诗句"""
    lines = [line.strip() for line in content.split(' ') if line.strip()]
    return lines


def analyze_meter_pattern(lines: List[str]) -> Tuple[str, List[int], int, int]:
    """分析格律模式
    
    返回:
        pattern: 格律模式，如 "7,7,7,7"
        line_char_counts: 每句字数列表
        total_lines: 总行数
        total_chars: 总字数
    """
    line_char_counts = [len(line) for line in lines]
    total_lines = len(lines)
    total_chars = sum(line_char_counts)
    
    if line_char_counts:
        pattern = ','.join(map(str, line_char_counts))
    else:
        pattern = ""
    
    return pattern, line_char_counts, total_lines, total_chars


def classify_poem_type(pattern: str, genre: str) -> Tuple[bool, str]:
    """分类诗体类型
    
    返回:
        is_regular: 是否为格律诗
        poem_type: 诗体类型（如七言绝句）
    """
    if genre != "诗":
        return False, "词"
    
    counts = [int(x) for x in pattern.split(',') if x.isdigit()]
    
    if not counts:
        return False, "其他"
    
    unique_counts = set(counts)
    
    if len(unique_counts) == 1:
        char_count = list(unique_counts)[0]
        
        if char_count == 5:
            if len(counts) == 4:
                return True, "五言绝句"
            elif len(counts) == 8:
                return True, "五言律诗"
            else:
                return False, "五言古体"
        
        elif char_count == 7:
            if len(counts) == 4:
                return True, "七言绝句"
            elif len(counts) == 8:
                return True, "七言律诗"
            else:
                return False, "七言古体"
    
    return False, "杂言"


def calculate_hash(title: str, author: str, content: str) -> str:
    """计算hash用于去重"""
    hash_content = f"{title}_{author}_{content}"
    return hashlib.md5(hash_content.encode("utf-8")).hexdigest()


def load_tang_poems(tang_dir: Path) -> List[Dict[str, Any]]:
    """加载全唐诗数据"""
    print(f"\n>>> 开始加载全唐诗数据...")
    print(f"目录: {tang_dir}")
    
    poems = []
    
    # 查找所有JSON文件
    json_files = sorted(tang_dir.glob("*.json"))
    print(f"找到 {len(json_files)} 个JSON文件")
    
    for idx, file in enumerate(json_files, 1):
        print(f"\n  [{idx}/{len(json_files)}] 处理文件: {file.name}")
        
        try:
            with open(file, "r", encoding="utf-8") as f:
                items = json.load(f)
                print(f"    读取到 {len(items)} 条记录")
                
                for item in items:
                    # 处理全唐诗数据格式
                    paragraphs = item.get("paragraphs", [])
                    content = "\n".join(paragraphs) if paragraphs else ""
                    
                    poem = {
                        "id": item.get("id", ""),
                        "title": item.get("title", ""),
                        "author": item.get("author", "佚名"),
                        "dynasty": "唐",
                        "genre": "诗",
                        "content": content,
                        "paragraphs": paragraphs,
                        "source_file": str(file)
                    }
                    
                    poems.append(poem)
                
                print(f"    累计诗词: {len(poems)} 首")
                
        except Exception as e:
            print(f"    错误: 无法读取 {file}: {e}")
    
    print(f"\n>>> 全唐诗加载完成!")
    print(f"  总诗词数: {len(poems)} 首")
    
    return poems


def load_song_ci(song_dir: Path) -> List[Dict[str, Any]]:
    """加载宋词数据"""
    print(f"\n>>> 开始加载宋词数据...")
    print(f"目录: {song_dir}")
    
    poems = []
    
    # 查找所有JSON文件
    json_files = sorted(song_dir.glob("*.json"))
    print(f"找到 {len(json_files)} 个JSON文件")
    
    for idx, file in enumerate(json_files, 1):
        print(f"\n  [{idx}/{len(json_files)}] 处理文件: {file.name}")
        
        try:
            with open(file, "r", encoding="utf-8") as f:
                items = json.load(f)
                print(f"    读取到 {len(items)} 条记录")
                
                for item in items:
                    # 处理宋词数据格式
                    paragraphs = item.get("paragraphs", [])
                    content = "\n".join(paragraphs) if paragraphs else ""
                    
                    # 生成ID（宋词可能没有id字段）
                    poem_id = item.get("id", "")
                    if not poem_id:
                        poem_id = hashlib.md5(f"{item.get('author','')}_{item.get('rhythmic','')}_{content}".encode()).hexdigest()
                    
                    poem = {
                        "id": poem_id,
                        "title": item.get("rhythmic", ""),  # 宋词用rhythmic作为标题
                        "author": item.get("author", "佚名"),
                        "dynasty": "宋",
                        "genre": "词",
                        "content": content,
                        "paragraphs": paragraphs,
                        "source_file": str(file)
                    }
                    
                    poems.append(poem)
                
                print(f"    累计诗词: {len(poems)} 首")
                
        except Exception as e:
            print(f"    错误: 无法读取 {file}: {e}")
    
    print(f"\n>>> 宋词加载完成!")
    print(f"  总诗词数: {len(poems)} 首")
    
    return poems


def process_poem(poem: Dict[str, Any], simplifier: Simplifier, text_cleaner: TextCleaner) -> Dict[str, Any]:
    """处理单首诗词
    
    返回:
        Dict: 包含处理后的诗词信息
    """
    content = poem["content"]
    genre = poem["genre"]
    
    # 繁简转换
    content_simplified = simplifier.traditional_to_simplified(content)
    
    # 清理文本（去除标点）
    cleaned_content = text_cleaner.clean_text(content_simplified)
    
    # 分割诗句
    lines = split_lines(cleaned_content)

    # 重装诗句
    sentences_simplified = " ".join(lines)
    
    # 分析格律模式
    pattern, line_char_counts, total_lines, total_chars = analyze_meter_pattern(lines)
    
    # 分类诗体类型
    is_regular, poem_type = classify_poem_type(pattern, genre)
    
    # 计算hash
    poem_hash = calculate_hash(poem["title"], poem["author"], content_simplified)
    
    return {
        "id": poem["id"],
        "title": poem["title"],
        "author": poem["author"],
        "dynasty": poem["dynasty"],
        "genre": genre,
        "poem_type": poem_type,
        "sentences_simplified": sentences_simplified,
        "meter_pattern": pattern,
        "hash": poem_hash
    }


def remove_duplicates(poems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """基于hash去重"""
    print(f"\n>>> 开始去重...")
    print(f"输入诗词数: {len(poems)} 首")
    
    seen_hashes = set()
    unique_poems = []
    
    for idx, poem in enumerate(poems, 1):
        if idx % 10000 == 0:
            print(f"  去重进度: {idx}/{len(poems)} ({idx/len(poems)*100:.1f}%)")
            print(f"  已去重: {len(unique_poems)} 首")
        
        poem_hash = poem["hash"]
        if poem_hash not in seen_hashes:
            seen_hashes.add(poem_hash)
            unique_poems.append(poem)
    
    print(f"\n>>> 去重完成!")
    print(f"  去重前: {len(poems)} 首")
    print(f"  去重后: {len(unique_poems)} 首")
    print(f"  重复数: {len(poems) - len(unique_poems)} 首")
    print(f"  去重率: {(len(poems) - len(unique_poems))/len(poems)*100:.2f}%")
    
    return unique_poems


def save_chunks(poems: List[Dict[str, Any]], output_dir: Path, chunk_size: int = 1000):
    """分chunk保存数据"""
    print(f"\n>>> 开始分chunk保存...")
    print(f"  输出目录: {output_dir}")
    print(f"  Chunk大小: {chunk_size}")
    print(f"  总诗词数: {len(poems)}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    total_chunks = (len(poems) + chunk_size - 1) // chunk_size
    print(f"  计算chunk数: {total_chunks}")
    
    for chunk_idx in range(total_chunks):
        start_idx = chunk_idx * chunk_size
        end_idx = min((chunk_idx + 1) * chunk_size, len(poems))
        chunk_poems = poems[start_idx:end_idx]
        
        chunk_file = output_dir / f"poems_chunk_{chunk_idx:04d}.csv"
        
        # 写入CSV
        with open(chunk_file, "w", encoding="utf-8-sig", newline="") as f:
            f.write("id,title,author,dynasty,genre,poem_type,sentences_simplified,meter_pattern,hash\n")
            
            for poem in chunk_poems:
                # 转义CSV中的特殊字符
                row = [
                    poem["id"],
                    poem["title"],
                    poem["author"],
                    poem["dynasty"],
                    poem["genre"],
                    poem["poem_type"],
                    poem["sentences_simplified"].replace('"', '""').replace('\n', '\\n'),
                    poem["meter_pattern"],
                    poem["hash"]
                ]
                f.write(f'"{row[0]}","{row[1]}","{row[2]}","{row[3]}","{row[4]}","{row[5]}","{row[6]}","{row[7]}","{row[8]}"\n')
        
        if (chunk_idx + 1) % 10 == 0 or chunk_idx == total_chunks - 1:
            print(f"  [{chunk_idx+1}/{total_chunks}] 保存chunk {chunk_idx}: {len(chunk_poems)} 条记录 -> {chunk_file}")
    
    print(f"\n>>> 分chunk保存完成!")
    print(f"  总chunk数: {total_chunks}")
    print(f"  输出目录: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="诗词预处理脚本")
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/chinese-poetry",
        help="输入数据目录"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/preprocessed",
        help="输出数据目录"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="每个chunk的诗词数量"
    )
    args = parser.parse_args()
    
    print("=" * 60)
    print("诗词预处理脚本启动")
    print("=" * 60)
    print(f"输入目录: {args.input_dir}")
    print(f"输出目录: {args.output_dir}")
    print(f"Chunk大小: {args.chunk_size}")
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    # 1. 加载数据
    print("\n" + "=" * 60)
    print("[1/8] 加载数据")
    print("=" * 60)
    
    all_poems = []
    
    # 加载全唐诗
    tang_dir = input_dir / "全唐诗"
    if tang_dir.exists():
        tang_poems = load_tang_poems(tang_dir)
        all_poems.extend(tang_poems)
    else:
        print(f"警告: 全唐诗目录不存在: {tang_dir}")
    
    # 加载宋词
    song_dir = input_dir / "宋词"
    if song_dir.exists():
        song_poems = load_song_ci(song_dir)
        all_poems.extend(song_poems)
    else:
        print(f"警告: 宋词目录不存在: {song_dir}")
    
    print(f"\n>>> 数据加载完成!")
    print(f"  总诗词数: {len(all_poems)} 首")
    
    # 2. 处理诗词
    print("\n" + "=" * 60)
    print("[2/8] 处理诗词（繁简转换、格律分析、诗体分类）")
    print("=" * 60)
    
    processed_poems = []
    simplifier = Simplifier()
    text_cleaner = TextCleaner()

    for idx, poem in enumerate(all_poems, 1):
        if idx % 1000 == 0:
            print(f"  处理进度: {idx}/{len(all_poems)} ({idx/len(all_poems)*100:.1f}%)")
        
        processed_poem = process_poem(poem, simplifier, text_cleaner)
        processed_poems.append(processed_poem)
    
    print(f"\n>>> 诗词处理完成!")
    print(f"  处理诗词数: {len(processed_poems)} 首")
    
    # 3. 去重
    print("\n" + "=" * 60)
    print("[3/8] 去重")
    print("=" * 60)
    
    unique_poems = remove_duplicates(processed_poems)
    
    # 4. 保存结果
    print("\n" + "=" * 60)
    print("[4/8] 保存结果")
    print("=" * 60)
    
    save_chunks(unique_poems, output_dir, args.chunk_size)
    
    # 5. 统计信息
    print("\n" + "=" * 60)
    print("统计信息")
    print("=" * 60)
    
    genre_count = {}
    poem_type_count = {}
    dynasty_count = {}
    
    for poem in unique_poems:
        genre = poem["genre"]
        poem_type = poem["poem_type"]
        dynasty = poem["dynasty"]
        
        genre_count[genre] = genre_count.get(genre, 0) + 1
        poem_type_count[poem_type] = poem_type_count.get(poem_type, 0) + 1
        dynasty_count[dynasty] = dynasty_count.get(dynasty, 0) + 1
    
    print(f"\n体裁分布:")
    for genre, count in sorted(genre_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {genre}: {count} 首")
    
    print(f"\n诗体分布:")
    for poem_type, count in sorted(poem_type_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {poem_type}: {count} 首")
    
    print(f"\n朝代分布:")
    for dynasty, count in sorted(dynasty_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {dynasty}: {count} 首")
    
    print("\n" + "=" * 60)
    print("完成!")
    print(f"  总记录: {len(unique_poems)}")
    print(f"  输出目录: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()