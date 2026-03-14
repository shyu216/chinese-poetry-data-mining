"""
词汇频率分析器

统计每位作者的高频词汇，用于分析用词习惯
支持按chunk保存结果
"""

from datetime import datetime
from typing import Dict, Any, List, Tuple
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from src.schema import AnalysisResult, WordFrequency
from src.analyzers.base import BaseAnalyzer, register_analyzer


@register_analyzer
class WordFrequencyAnalyzer(BaseAnalyzer):
    """词汇频率分析器
    
    使用 jieba 分词，统计每位作者的高频实词
    排除停用词，保留名词、动词、形容词
    支持按chunk保存结果
    """
    
    NAME = "word_frequency"
    VERSION = "1.0.0"
    DESCRIPTION = "统计作者常用词汇"
    DEPENDS_ON = []  # 无依赖
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.top_n = config.get("top_n", 100)  # Top N 高频词
        self.min_word_length = config.get("min_word_length", 2)  # 最小词长
        self.pos_filter = config.get("pos_filter", ["n", "v", "a"])  # 词性筛选
        self.output_dir = Path(config.get("output_dir", "results/gold/word_frequency"))
        self.chunk_size = config.get("chunk_size", 100)  # 每个chunk的作者数量
    
    def analyze(self, df: pd.DataFrame) -> AnalysisResult:
        """执行词汇频率分析
        
        Args:
            df: 包含诗词的数据框，需有 author 和 content 列
            
        Returns:
            AnalysisResult: 包含词汇频率统计
        """
        try:
            import jieba
            import jieba.posseg as pseg
        except ImportError:
            raise ImportError("需要安装 jieba: pip install jieba")
        
        print("分词统计中...")
        
        # 统计每位作者的词汇
        author_words = defaultdict(Counter)
        author_pos_dist = defaultdict(Counter)
        author_poem_counts = defaultdict(int)
        
        total_rows = len(df)
        progress_interval = max(1000, total_rows // 100)  # 每处理1%或1000条显示一次进度
        save_interval = 10000  # 每处理10000条保存一次中间状态
        
        # 检查是否有中间状态
        import json
        from pathlib import Path
        
        temp_file = Path("data/cache/word_frequency_temp.json")
        temp_file.parent.mkdir(parents=True, exist_ok=True)
        
        if temp_file.exists():
            print("发现中间状态，继续处理...")
            with open(temp_file, "r", encoding="utf-8") as f:
                temp_data = json.load(f)
                author_words = defaultdict(Counter, {k: Counter(v) for k, v in temp_data["author_words"].items()})
                author_pos_dist = defaultdict(Counter, {k: Counter(v) for k, v in temp_data["author_pos_dist"].items()})
                author_poem_counts = defaultdict(int, temp_data.get("author_poem_counts", {}))
                start_idx = temp_data.get("last_idx", 0)
        else:
            start_idx = 0
            
        for idx, row in df.iterrows():
            if idx < start_idx:
                continue
                
            if idx % progress_interval == 0:
                print(f"  处理: {idx}/{total_rows} ({idx/total_rows*100:.1f}%)")
                
            author = row.get("author", "佚名")
            content = row.get("content", "")
            
            author_poem_counts[author] += 1
            
            # 处理非字符串类型的内容
            if not isinstance(content, str):
                content = str(content) if content is not None else ''
            
            if not content:
                continue
            
            try:
                # 分词并标注词性
                words_with_pos = pseg.cut(content)
                
                for word, flag in words_with_pos:
                    # 筛选条件
                    if len(word) < self.min_word_length:
                        continue
                    
                    if word in self._get_stop_words():
                        continue
                    
                    # 只保留指定词性
                    if not any(flag.startswith(pos) for pos in self.pos_filter):
                        continue
                    
                    # 统计
                    author_words[author][word] += 1
                    author_pos_dist[author][flag] += 1
            except Exception as e:
                print(f"  警告: 处理 {author} 的诗词时出错: {e}")
                continue
                
            # 保存中间状态
            if idx % save_interval == 0 and idx > 0:
                print(f"  保存中间状态: {idx}")
                temp_data = {
                    "author_words": {k: dict(v) for k, v in author_words.items()},
                    "author_pos_dist": {k: dict(v) for k, v in author_pos_dist.items()},
                    "author_poem_counts": dict(author_poem_counts),
                    "last_idx": idx
                }
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(temp_data, f, ensure_ascii=False, indent=2)
        
        print(f"处理完成: {len(author_words)} 位作者")
        
        # 删除临时文件
        if temp_file.exists():
            temp_file.unlink()
            print("临时文件已删除")
        
        # 提取 Top N 高频词
        print("提取 Top N 高频词...")
        author_top_words = {}
        total_authors = len(author_words)
        author_progress_interval = max(100, total_authors // 100)  # 每处理1%或100位作者显示一次进度
        
        for idx, (author, word_counter) in enumerate(author_words.items()):
            if idx % author_progress_interval == 0:
                print(f"  处理作者: {idx}/{total_authors} ({idx/total_authors*100:.1f}%)")
                
            top_words = [
                {
                    "word": word,
                    "count": count,
                    "pos": self._get_main_pos(word, df, author)
                }
                for word, count in word_counter.most_common(self.top_n)
            ]
            author_top_words[author] = {
                "words": top_words,
                "poem_count": author_poem_counts.get(author, 0),
                "total_word_count": sum(word_counter.values())
            }
        
        # 全局词频统计
        print("全局词频统计...")
        global_counter = Counter()
        total_author_counters = len(author_words)
        global_progress_interval = max(100, total_author_counters // 100)  # 每处理1%或100位作者显示一次进度
        
        for idx, word_counter in enumerate(author_words.values()):
            if idx % global_progress_interval == 0:
                print(f"  统计作者: {idx}/{total_author_counters} ({idx/total_author_counters*100:.1f}%)")
                
            global_counter.update(word_counter)
        
        global_top_words = [
            {"word": word, "count": count}
            for word, count in global_counter.most_common(self.top_n)
        ]
        
        # 按chunk保存作者数据
        print(f"按chunk保存作者数据 (每chunk {self.chunk_size} 位作者)...")
        self._save_author_chunks(author_top_words)
        
        # 构建结果
        result_data = {
            "author_count": len(author_words),
            "global_top_words": global_top_words,
            "pos_distribution": dict(author_pos_dist),
            "vocabulary_size": len(global_counter),
            "chunk_size": self.chunk_size,
            "chunk_count": (len(author_words) + self.chunk_size - 1) // self.chunk_size,
            "output_dir": str(self.output_dir)
        }
        
        print(f"词汇表大小: {result_data['vocabulary_size']}")
        print(f"保存了 {result_data['chunk_count']} 个chunk")
        
        return AnalysisResult(
            analyzer_name=self.NAME,
            version=self.VERSION,
            timestamp=datetime.now().isoformat(),
            data=result_data
        )
    
    def _save_author_chunks(self, author_data: Dict[str, Dict[str, Any]]):
        """按chunk保存作者数据
        
        Args:
            author_data: 作者数据字典
        """
        import json
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        authors = list(author_data.keys())
        chunk_count = (len(authors) + self.chunk_size - 1) // self.chunk_size
        
        for chunk_idx in range(chunk_count):
            start = chunk_idx * self.chunk_size
            end = start + self.chunk_size
            chunk_authors = authors[start:end]
            
            chunk_data = {
                "chunk_id": chunk_idx,
                "authors": chunk_authors,
                "author_count": len(chunk_authors),
                "data": {author: author_data[author] for author in chunk_authors}
            }
            
            chunk_file = self.output_dir / f"authors_chunk_{chunk_idx:04d}.json"
            with open(chunk_file, "w", encoding="utf-8") as f:
                json.dump(chunk_data, f, ensure_ascii=False, indent=2)
            
            print(f"  保存 chunk {chunk_idx}: {len(chunk_authors)} 位作者")
        
        # 保存索引文件
        index_data = {
            "total_authors": len(authors),
            "chunk_count": chunk_count,
            "chunk_size": self.chunk_size,
            "authors": authors
        }
        
        index_file = self.output_dir / "authors_index.json"
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        print(f"  保存索引: {index_file}")
    
    def _get_main_pos(self, word: str, df: pd.DataFrame, author: str) -> str:
        """获取词汇的主要词性
        
        Args:
            word: 词汇
            df: 数据框
            author: 作者
            
        Returns:
            str: 主要词性
        """
        try:
            import jieba.posseg as pseg
        except ImportError:
            return "unknown"
        
        # 获取该作者的诗词
        author_poems = df[df["author"] == author]["content"].tolist()
        
        pos_counter = Counter()
        for poem in author_poems:
            for w, flag in pseg.cut(poem):
                if w == word:
                    pos_counter[flag] += 1
        
        if pos_counter:
            return pos_counter.most_common(1)[0][0]
        return "unknown"
    
    def _get_stop_words(self) -> set:
        """获取停用词集合"""
        stop_words = {
            # 常用虚词
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
            "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
            "你", "会", "着", "没有", "看", "好", "自己", "这", "那",
            "之", "与", "及", "而", "或", "但", "为", "以", "被", "将",
            "把", "向", "从", "于", "至", "并", "等", "且", "则", "若",
            "虽", "故", "乃", "既", "因", "所以", "因此", "因为",
            # 诗词常用虚词
            "兮", "矣", "焉", "哉", "乎", "也", "者", "所", "其", "何",
            "乃", "而", "于", "则", "即", "若", "虽", "故", "夫", "盖",
            "岂", "安", "胡", "奚", "曷", "盍", "惟", "唯", "维", "斯",
            "此", "彼", "其", "夫", "且", "或", "若", "如", "若夫",
            "至若", "若乃", "于是", "然后", "然则", "虽然", "然而",
        }
        return stop_words
    
    def get_author_words(self, author: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取指定作者的常用词汇
        
        Args:
            author: 作者名
            data: 分析结果数据
            
        Returns:
            List[Dict]: 词汇列表
        """
        # 从chunk文件中读取
        index_file = self.output_dir / "authors_index.json"
        if not index_file.exists():
            return []
        
        with open(index_file, "r", encoding="utf-8") as f:
            index_data = json.load(f)
        
        # 找到作者所在的chunk
        chunk_idx = index_data["authors"].index(author) // self.chunk_size
        chunk_file = self.output_dir / f"authors_chunk_{chunk_idx:04d}.json"
        
        if not chunk_file.exists():
            return []
        
        with open(chunk_file, "r", encoding="utf-8") as f:
            chunk_data = json.load(f)
        
        return chunk_data["data"].get(author, {}).get("words", [])
    
    def compare_authors(
        self,
        author1: str,
        author2: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """比较两位作者的用词习惯
        
        Args:
            author1: 作者1
            author2: 作者2
            data: 分析结果数据
            
        Returns:
            Dict: 比较结果
        """
        words1 = self.get_author_words(author1, data)
        words2 = self.get_author_words(author2, data)
        
        words1_dict = {w["word"]: w for w in words1}
        words2_dict = {w["word"]: w for w in words2}
        
        # 共同词汇
        common_words = set(words1_dict.keys()) & set(words2_dict.keys())
        
        # 独有词汇
        unique_to_1 = set(words1_dict.keys()) - set(words2_dict.keys())
        unique_to_2 = set(words2_dict.keys()) - set(words1_dict.keys())
        
        # 共同词汇详情
        common_details = []
        for word in common_words:
            common_details.append({
                "word": word,
                "author1_count": words1_dict[word]["count"],
                "author2_count": words2_dict[word]["count"],
                "pos": words1_dict[word].get("pos", "unknown")
            })
        
        # 按总频次排序
        common_details.sort(
            key=lambda x: x["author1_count"] + x["author2_count"],
            reverse=True
        )
        
        return {
            "author1": author1,
            "author2": author2,
            "common_words_count": len(common_words),
            "common_words": common_details[:20],  # Top 20
            "unique_to_author1": list(unique_to_1)[:20],
            "unique_to_author2": list(unique_to_2)[:20],
            "similarity_score": len(common_words) / max(len(words1_dict), len(words2_dict))
        }
