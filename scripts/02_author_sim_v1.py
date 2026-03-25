"""
script: 02_author_sim_v1.py
stage: P3-作者建模
artifact: 作者相似度基础数据
purpose: 计算作者层面的相似度或作者词特征基础产物。
inputs:
- results/preprocessed
- results/keyword_index
outputs:
- results/author
depends_on:
- word_frequency.py
develop_date: 2026-03-15
last_modified_date: 2026-03-15
"""
import csv
import json
import hashlib
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
from typing import Dict, List, Any, Tuple, Set
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import opencc
import pickle
POEMS_DIR = Path("results/preprocessed")
OUTPUT_DIR = Path("results/author")
FULL_OUTPUT_DIR = Path("results/author-full")
HIGH_OUTPUT_THRESHOLD = 100
SIMILARITY_THRESHOLD = 0.5
TOP_WORDS = 100
CHECKPOINT_FILE = FULL_OUTPUT_DIR / "checkpoint.json"
class AuthorAnalyzer:
    def __init__(self):
        self.converter = opencc.OpenCC('t2s')
        self.author_data: Dict[str, Dict] = {}
        self.idf_cache: Dict[str, float] = {}
        self.checkpoint = self.load_checkpoint()
    def traditional_to_simplified(self, text: str) -> str:
        return self.converter.convert(text)
    def load_checkpoint(self) -> Dict:
        if CHECKPOINT_FILE.exists():
            with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"stage": "start", "completed_authors": [], "last_update": None}
    def save_checkpoint(self, stage: str, completed_authors: List[str] = None):
        self.checkpoint["stage"] = stage
        self.checkpoint["last_update"] = datetime.now().isoformat()
        if completed_authors is not None:
            self.checkpoint["completed_authors"] = completed_authors
        CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.checkpoint, f, ensure_ascii=False, indent=2)
    def load_poems(self) -> Tuple[Dict[str, List[Dict]], int]:
        print("=" * 60)
        print("步骤1: 加载诗词数据")
        print("=" * 60)
        chunk_files = sorted(POEMS_DIR.glob("poems_chunk_*.csv"))
        print(f"找到 {len(chunk_files)} 个chunk文件")
        author_poems: Dict[str, List[Dict]] = defaultdict(list)
        total_poems = 0
        for idx, chunk_file in enumerate(chunk_files, 1):
            if idx % 50 == 0:
                print(f"进度: [{idx}/{len(chunk_files)}] 已加载 {total_poems} 首诗")
            with open(chunk_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    author_tw = row.get('author', '').strip()
                    if not author_tw:
                        continue
                    author = self.traditional_to_simplified(author_tw)
                    poem_id = row.get('id', '')
                    poem_type = row.get('poem_type', '')
                    meter_pattern = row.get('meter_pattern', '')
                    words = row.get('words', '').split() if row.get('words') else []
                    author_poems[author].append({
                        'id': poem_id,
                        'poem_type': poem_type,
                        'meter_pattern': meter_pattern,
                        'words': words
                    })
                    total_poems += 1
        print(f"\n>>> 加载完成!")
        print(f"  总诗数: {total_poems}")
        print(f"  诗人数量: {len(author_poems)}")
        return author_poems, total_poems
    def analyze_author(self, author: str, poems: List[Dict]) -> Dict:
        poem_types = Counter()
        meter_patterns = Counter()
        all_words = []
        for poem in poems:
            if poem['poem_type']:
                poem_types[poem['poem_type']] += 1
            if poem['meter_pattern']:
                meter_patterns[poem['meter_pattern']] += 1
            all_words.extend(poem['words'])
        word_freq = Counter(all_words)
        top_words = dict(word_freq.most_common(TOP_WORDS))
        return {
            'author': author,
            'poem_count': len(poems),
            'poem_ids': [p['id'] for p in poems],
            'poem_type_counts': dict(poem_types),
            'meter_patterns': [
                {'pattern': pattern, 'count': count}
                for pattern, count in meter_patterns.most_common()
            ],
            'word_frequency': top_words,
            'all_words': all_words
        }
    def generate_author_summary(self, author_data: Dict[str, Dict]) -> List[Dict]:
        print("\n" + "=" * 60)
        print("步骤2: 生成诗人汇总")
        print("=" * 60)
        sorted_authors = sorted(
            author_data.items(),
            key=lambda x: x[1]['poem_count'],
            reverse=True
        )
        summary = [
            {
                'author': author,
                'poem_count': data['poem_count'],
                'poem_ids': data['poem_ids']
            }
            for author, data in sorted_authors
        ]
        print(f"  诗人总数: {len(summary)}")
        print(f"  高产诗人(>{HIGH_OUTPUT_THRESHOLD}首): {sum(1 for s in summary if s['poem_count'] > HIGH_OUTPUT_THRESHOLD)}")
        return summary
    def compute_tfidf_similarity(self, author_data: Dict[str, Dict]) -> Dict[str, List[Dict]]:
        print("\n" + "=" * 60)
        print("步骤3: 计算 TF-IDF 相似度")
        print("=" * 60)
        authors = list(author_data.keys())
        total = len(authors)
        print(f"  计算 {total} 位诗人的相似度...")
        documents = []
        for author in authors:
            words = author_data[author]['all_words']
            documents.append(' '.join(words))
        vectorizer = TfidfVectorizer(
            min_df=2,
            max_df=0.95,
            token_pattern=r'(?u)\b\w+\b'
        )
        tfidf_matrix = vectorizer.fit_transform(documents)
        feature_names = vectorizer.get_feature_names_out()
        print(f"  TF-IDF 矩阵: {tfidf_matrix.shape}")
        print(f"  特征词数: {len(feature_names)}")
        sim_matrix = cosine_similarity(tfidf_matrix)
        similar_authors = {}
        author_idx = {author: idx for idx, author in enumerate(authors)}
        for author in authors:
            idx = author_idx[author]
            similarities = []
            for other_author in authors:
                if other_author == author:
                    continue
                other_idx = author_idx[other_author]
                sim = float(sim_matrix[idx, other_idx])
                if sim > SIMILARITY_THRESHOLD:
                    similarities.append({
                        'author': other_author,
                        'similarity': round(sim, 4)
                    })
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            similar_authors[author] = similarities[:10]
        print(f"  相似度计算完成!")
        print(f"  有相似诗人的数量: {sum(1 for v in similar_authors.values() if v)}")
        return similar_authors
    def save_results(self, author_summary: List[Dict], author_data: Dict[str, Dict], similar_authors: Dict):
        print("\n" + "=" * 60)
        print("步骤4: 保存结果")
        print("=" * 60)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        FULL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        summary_path = OUTPUT_DIR / "author_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(author_summary, f, ensure_ascii=False, indent=2)
        print(f"  已保存: {summary_path}")
        high_output_authors = [
            a for a in author_summary if a['poem_count'] > HIGH_OUTPUT_THRESHOLD
        ]
        low_output_authors = [
            a for a in author_summary if a['poem_count'] <= HIGH_OUTPUT_THRESHOLD
        ]
        print(f"  高产诗人: {len(high_output_authors)}")
        print(f"  低产诗人: {len(low_output_authors)}")
        for idx, author_info in enumerate(high_output_authors):
            author = author_info['author']
            data = author_data[author]
            result = {
                'author': author,
                'poem_count': data['poem_count'],
                'poem_type_counts': data['poem_type_counts'],
                'meter_patterns': data['meter_patterns'],
                'poem_ids': data['poem_ids'],
                'word_frequency': data['word_frequency'],
                'similar_authors': similar_authors.get(author, [])
            }
            chunk_path = OUTPUT_DIR / f"author_chunk_{idx:04d}.json"
            with open(chunk_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  高产诗人 chunk 文件: {len(high_output_authors)} 个")
        chunk_size = 50
        for chunk_idx in range(0, len(low_output_authors), chunk_size):
            batch = low_output_authors[chunk_idx:chunk_idx + chunk_size]
            results = []
            for author_info in batch:
                author = author_info['author']
                data = author_data[author]
                result = {
                    'author': author,
                    'poem_count': data['poem_count'],
                    'poem_type_counts': data['poem_type_counts'],
                    'meter_patterns': data['meter_patterns'],
                    'poem_ids': data['poem_ids'],
                    'word_frequency': data['word_frequency'],
                    'similar_authors': similar_authors.get(author, [])
                }
                results.append(result)
            chunk_path = OUTPUT_DIR / f"author_chunk_{len(high_output_authors) + chunk_idx:04d}.json"
            with open(chunk_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        num_low_chunks = (len(low_output_authors) + chunk_size - 1) // chunk_size
        print(f"  低产诗人 chunk 文件: {num_low_chunks} 个")
        full_data_path = FULL_OUTPUT_DIR / "author_data_full.json"
        with open(full_data_path, 'w', encoding='utf-8') as f:
            json.dump(author_data, f, ensure_ascii=False, indent=2)
        print(f"  详细数据已保存: {full_data_path}")
        similar_path = FULL_OUTPUT_DIR / "similarity_matrix.json"
        with open(similar_path, 'w', encoding='utf-8') as f:
            json.dump(similar_authors, f, ensure_ascii=False, indent=2)
        print(f"  相似度数据已保存: {similar_path}")
        self.save_checkpoint("complete")
    def run(self):
        print("=" * 60)
        print("诗人分析脚本启动")
        print("=" * 60)
        print(f"输入目录: {POEMS_DIR}")
        print(f"输出目录: {OUTPUT_DIR}")
        print(f"详细输出: {FULL_OUTPUT_DIR}")
        print(f"高产阈值: >{HIGH_OUTPUT_THRESHOLD} 首")
        print(f"相似度阈值: >{SIMILARITY_THRESHOLD}")
        print(f"Top 词数: {TOP_WORDS}")
        if self.checkpoint["stage"] == "complete":
            print("\n>>> 已完成，跳过...")
            return
        if self.checkpoint["stage"] == "start":
            author_poems, total_poems = self.load_poems()
            print("\n>>> 分析每位诗人...")
            for idx, (author, poems) in enumerate(author_poems.items(), 1):
                if idx % 100 == 0:
                    print(f"  进度: [{idx}/{len(author_poems)}]")
                self.author_data[author] = self.analyze_author(author, poems)
            print(f"\n>>> 分析完成!")
            author_summary = self.generate_author_summary(self.author_data)
            similar_authors = self.compute_tfidf_similarity(self.author_data)
            self.save_results(author_summary, self.author_data, similar_authors)
        print("\n" + "=" * 60)
        print("完成!")
        print(f"  输出目录: {OUTPUT_DIR}")
        print(f"  详细目录: {FULL_OUTPUT_DIR}")
        print("=" * 60)
def main():
    analyzer = AuthorAnalyzer()
    analyzer.run()
if __name__ == "__main__":
    main()
