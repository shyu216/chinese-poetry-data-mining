"""
搜索索引生成器 (Task 11)

构建倒排索引 (Inverted Index) 用于纯前端搜索
- 词 -> 诗词ID列表映射
- 作者索引
- 朝代索引

输出: data/output/web/index/search_index.json
      data/output/web/index/author_index.json
      data/output/web/index/dynasty_index.json
"""

import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

import pandas as pd


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent.parent


def load_poems(data_path: Path) -> pd.DataFrame:
    """加载诗词数据"""
    csv_path = data_path / "silver" / "v2_poems_structured.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"找不到诗词数据文件: {csv_path}")
    
    print(f"加载诗词数据: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"加载完成: {len(df)} 首诗词")
    return df


def build_inverted_index(df: pd.DataFrame) -> Dict:
    """
    构建倒排索引
    
    对每首诗词的标题、内容、作者进行分词
    建立 词 -> 诗词ID列表 的映射
    """
    print("构建倒排索引...")
    
    try:
        import jieba
    except ImportError:
        raise ImportError("需要安装 jieba: pip install jieba")
    
    # 倒排索引: term -> set of poem_ids
    term_to_poems: Dict[str, Set[str]] = defaultdict(set)
    
    # 停用词
    stop_words = set([
        '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也',
        '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那',
        '之', '而', '以', '其', '于', '与', '乃', '且', '即', '若', '所', '为', '兮', '乎',
        '者', '也', '矣', '焉', '哉', '耶', '耳', '欤', '乎', '夫', '盖', '故', '然', '则',
        '而', '虽', '既', '即', '便', '就', '又', '并', '及', '或', '但', '惟', '唯'
    ])
    
    total = len(df)
    for idx, row in df.iterrows():
        if idx % 100 == 0:
            print(f"  处理进度: {idx}/{total} ({idx/total*100:.1f}%)")
        
        poem_id = str(row.get('id', idx))
        title = str(row.get('title', ''))
        content = str(row.get('content', ''))
        author = str(row.get('author', ''))
        dynasty = str(row.get('dynasty', ''))
        
        # 合并文本进行分词
        text = f"{title} {content} {author} {dynasty}"
        
        # 分词
        words = jieba.lcut(text)
        
        for word in words:
            word = word.strip().lower()
            # 过滤条件
            if len(word) < 2:  # 至少2个字符
                continue
            if word in stop_words:
                continue
            if word.isdigit():  # 排除纯数字
                continue
            
            term_to_poems[word].add(poem_id)
    
    # 转换为列表并排序
    index_data = {
        "version": "1.0.0",
        "created_at": datetime.now().isoformat(),
        "total_poems": len(df),
        "total_terms": len(term_to_poems),
        "terms": {term: sorted(list(poems)) for term, poems in sorted(term_to_poems.items())}
    }
    
    print(f"倒排索引构建完成: {len(term_to_poems)} 个词条")
    return index_data


def build_author_index(df: pd.DataFrame) -> Dict:
    """构建作者索引: 作者 -> 诗词ID列表"""
    print("构建作者索引...")
    
    author_to_poems: Dict[str, List[str]] = defaultdict(list)
    author_stats: Dict[str, Dict] = {}
    
    for idx, row in df.iterrows():
        poem_id = str(row.get('id', idx))
        author = str(row.get('author', '佚名'))
        dynasty = str(row.get('dynasty', '未知'))
        
        author_to_poems[author].append(poem_id)
        
        # 统计作者信息
        if author not in author_stats:
            author_stats[author] = {
                "dynasty": dynasty,
                "poem_count": 0,
                "poem_ids": []
            }
        author_stats[author]["poem_count"] += 1
        author_stats[author]["poem_ids"].append(poem_id)
    
    index_data = {
        "version": "1.0.0",
        "created_at": datetime.now().isoformat(),
        "total_authors": len(author_to_poems),
        "authors": {
            author: {
                "dynasty": stats["dynasty"],
                "poem_count": stats["poem_count"],
                "poem_ids": stats["poem_ids"]
            }
            for author, stats in sorted(author_stats.items())
        }
    }
    
    print(f"作者索引构建完成: {len(author_to_poems)} 位作者")
    return index_data


def build_dynasty_index(df: pd.DataFrame) -> Dict:
    """构建朝代索引: 朝代 -> 诗词ID列表"""
    print("构建朝代索引...")
    
    dynasty_to_poems: Dict[str, List[str]] = defaultdict(list)
    dynasty_stats: Dict[str, Dict] = {}
    
    for idx, row in df.iterrows():
        poem_id = str(row.get('id', idx))
        dynasty = str(row.get('dynasty', '未知'))
        
        dynasty_to_poems[dynasty].append(poem_id)
        
        # 统计朝代信息
        if dynasty not in dynasty_stats:
            dynasty_stats[dynasty] = {
                "poem_count": 0,
                "poem_ids": []
            }
        dynasty_stats[dynasty]["poem_count"] += 1
        dynasty_stats[dynasty]["poem_ids"].append(poem_id)
    
    index_data = {
        "version": "1.0.0",
        "created_at": datetime.now().isoformat(),
        "total_dynasties": len(dynasty_to_poems),
        "dynasties": {
            dynasty: {
                "poem_count": stats["poem_count"],
                "poem_ids": stats["poem_ids"]
            }
            for dynasty, stats in sorted(dynasty_stats.items())
        }
    }
    
    print(f"朝代索引构建完成: {len(dynasty_to_poems)} 个朝代")
    return index_data


def save_index(index_data: Dict, output_path: Path, filename: str):
    """保存索引文件"""
    output_path.mkdir(parents=True, exist_ok=True)
    file_path = output_path / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    file_size = file_path.stat().st_size
    print(f"保存索引: {file_path} ({file_size / 1024 / 1024:.2f} MB)")


def main():
    """主函数"""
    print("=" * 60)
    print("搜索索引生成器 (Task 11)")
    print("=" * 60)
    
    # 获取路径
    root_dir = get_project_root()
    data_dir = root_dir / "data"
    output_dir = root_dir / "data" / "output" / "web" / "index"
    
    try:
        # 加载数据
        df = load_poems(data_dir)
        
        # 构建倒排索引
        search_index = build_inverted_index(df)
        save_index(search_index, output_dir, "search_index.json")
        
        # 构建作者索引
        author_index = build_author_index(df)
        save_index(author_index, output_dir, "author_index.json")
        
        # 构建朝代索引
        dynasty_index = build_dynasty_index(df)
        save_index(dynasty_index, output_dir, "dynasty_index.json")
        
        # 输出统计信息
        print("\n" + "=" * 60)
        print("索引生成完成!")
        print("=" * 60)
        print(f"倒排索引: {search_index['total_terms']} 个词条")
        print(f"作者索引: {author_index['total_authors']} 位作者")
        print(f"朝代索引: {dynasty_index['total_dynasties']} 个朝代")
        print(f"\n输出目录: {output_dir}")
        
        return 0
        
    except Exception as e:
        print(f"\n错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
