#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诗词数据分析流水线
整合所有src工具，使用sample data进行完整分析
"""

import sys
from pathlib import Path
from typing import List, Dict, Any
from collections import Counter, defaultdict

sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from tqdm import tqdm

# 导入src工具
from src.core.text_utils import TextProcessor
from src.features.rhyme_features import RhymeFeatureExtractor
from src.features.sentiment_features import SentimentFeatureExtractor
from src.models.poetry_classifier import ThemeClassifier
from src.models.social_network_model import SocialNetworkModel
from src.visualization.poetry_visualizer import PoetryVisualizer


class PoetryAnalysisPipeline:
    """诗词数据分析流水线"""
    
    def __init__(self, data_path: str = None):
        """
        初始化流水线
        
        Args:
            data_path: 数据文件路径，默认为 sample_data/all_poetry.pkl
        """
        if data_path is None:
            project_root = Path(__file__).parent.parent
            data_path = project_root / "data" / "sample_data" / "all_poetry.pkl"
        
        self.data_path = Path(data_path)
        self.df = None
        
        # 初始化分析器
        self.text_processor = TextProcessor()
        self.rhyme_extractor = RhymeFeatureExtractor()
        self.sentiment_extractor = SentimentFeatureExtractor()
        self.theme_classifier = ThemeClassifier()
        self.social_model = SocialNetworkModel()
        self.visualizer = PoetryVisualizer()
        
        # 结果存储
        self.results = {}
    
    def load_data(self) -> pd.DataFrame:
        """加载数据"""
        print(f"加载数据: {self.data_path}")
        self.df = pd.read_pickle(self.data_path)
        print(f"  共 {len(self.df)} 条记录")
        print(f"  列: {list(self.df.columns)}")
        return self.df
    
    def analyze_rhyme(self) -> Dict:
        """韵律分析"""
        print("\n[1/6] 韵律分析...")
        
        rhyme_results = []
        for idx, row in tqdm(self.df.iterrows(), total=len(self.df), desc="韵律分析"):
            content = row.get('content', '')
            if not content:
                continue
            
            # 分割诗句
            lines = [line.strip() for line in content.split('.') if line.strip()]
            lines = [line.replace(',', '') for line in lines]
            
            # 分析韵律
            try:
                rhythm_features = self.rhyme_extractor.extract_rhythm_features(lines)
                form = self.rhyme_extractor.identify_form(lines)
                
                rhyme_results.append({
                    'id': row.get('id', idx),
                    'title': row.get('title', ''),
                    'author': row.get('author', ''),
                    'form': form,
                    'level_oblique': rhythm_features.get('level_oblique_patterns', []),
                    'rhyme_categories': rhythm_features.get('rhyme_categories', [])
                })
            except Exception as e:
                continue
        
        self.results['rhyme'] = rhyme_results
        
        # 统计诗体分布
        form_counts = Counter(r['form'] for r in rhyme_results)
        print(f"  诗体分布: {dict(form_counts)}")
        
        return rhyme_results
    
    def analyze_sentiment(self) -> Dict:
        """情感分析"""
        print("\n[2/6] 情感分析...")
        
        sentiment_results = []
        for idx, row in tqdm(self.df.iterrows(), total=len(self.df), desc="情感分析"):
            content = row.get('content', '')
            if not content:
                continue
            
            try:
                result = self.sentiment_extractor.extract_sentiment_features(content)
                sentiment_results.append({
                    'id': row.get('id', idx),
                    'title': row.get('title', ''),
                    'author': row.get('author', ''),
                    'sentiment_score': result['sentiment_score'],
                    'sentiment': result['sentiment']
                })
            except Exception as e:
                continue
        
        self.results['sentiment'] = sentiment_results
        
        # 统计情感分布
        sentiment_counts = Counter(r['sentiment'] for r in sentiment_results)
        print(f"  情感分布: {dict(sentiment_counts)}")
        
        avg_score = np.mean([r['sentiment_score'] for r in sentiment_results])
        print(f"  平均情感得分: {avg_score:.3f}")
        
        return sentiment_results
    
    def analyze_entities(self) -> Dict:
        """实体识别（简化版）"""
        print("\n[3/6] 实体识别...")
        
        # 简单的季节词检测
        season_words = ['春', '夏', '秋', '冬']
        entity_results = []
        
        for idx, row in tqdm(self.df.iterrows(), total=len(self.df), desc="实体识别"):
            content = row.get('content', '')
            if not content:
                continue
            
            seasons = [s for s in season_words if s in content]
            
            entity_results.append({
                'id': row.get('id', idx),
                'title': row.get('title', ''),
                'author': row.get('author', ''),
                'seasons': seasons
            })
        
        self.results['entities'] = entity_results
        
        # 统计
        all_seasons = []
        for r in entity_results:
            all_seasons.extend(r['seasons'])
        
        season_counts = Counter(all_seasons)
        print(f"  季节分布: {dict(season_counts.most_common(5))}")
        
        return entity_results
    
    def analyze_themes(self) -> Dict:
        """主题分类"""
        print("\n[4/6] 主题分类...")
        
        theme_results = []
        for idx, row in tqdm(self.df.iterrows(), total=len(self.df), desc="主题分类"):
            content = row.get('content', '')
            if not content:
                continue
            
            try:
                top_theme, themes = self.theme_classifier.classify(content)
                
                theme_results.append({
                    'id': row.get('id', idx),
                    'title': row.get('title', ''),
                    'author': row.get('author', ''),
                    'primary_theme': top_theme,
                    'theme_scores': themes
                })
            except Exception as e:
                continue
        
        self.results['themes'] = theme_results
        
        # 统计主题分布
        theme_counts = Counter(r['primary_theme'] for r in theme_results)
        print(f"  主题分布: {dict(theme_counts)}")
        
        return theme_results
    
    def analyze_social_network(self) -> Dict:
        """社交网络分析"""
        print("\n[5/6] 社交网络分析...")
        
        try:
            # 构建作者文本库
            author_texts = self.social_model.build_author_texts(self.df, min_poems=2)
            
            if len(author_texts) < 2:
                print("  作者数量不足，跳过社交网络分析")
                return {}
            
            # 计算相似度
            authors_list, texts_list, similarity_matrix = self.social_model.calculate_similarity(author_texts)
            
            # 构建网络
            G = self.social_model.build_network(authors_list, similarity_matrix, threshold=0.1)
            
            # 分析网络
            network_analysis = self.social_model.analyze_network(G)
            
            self.results['social_network'] = {
                'authors': authors_list,
                'similarity_matrix': similarity_matrix.tolist(),
                'network_analysis': network_analysis
            }
            
            print(f"  节点数: {network_analysis['network_properties']['nodes']}")
            print(f"  边数: {network_analysis['network_properties']['edges']}")
            print(f"  网络密度: {network_analysis['network_properties']['density']:.3f}")
            
            # 打印中心性最高的作者
            degree_cent = network_analysis['degree_centrality']
            top_authors = sorted(degree_cent.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"  中心性TOP5: {top_authors}")
            
            return self.results['social_network']
        
        except Exception as e:
            print(f"  社交网络分析失败: {e}")
            return {}
    
    def generate_visualizations(self, output_dir: str = None):
        """生成可视化"""
        print("\n[6/6] 生成可视化...")
        
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / "reports" / "visualizations"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 准备数据
        poems_data = []
        for idx, row in self.df.iterrows():
            sentiment = next((s for s in self.results.get('sentiment', []) if s['id'] == row.get('id')), {})
            theme = next((t for t in self.results.get('themes', []) if t['id'] == row.get('id')), {})
            
            poems_data.append({
                'title': row.get('title', ''),
                'author': row.get('author', ''),
                'dynasty': row.get('dynasty', ''),
                'char_count': len(row.get('content', '')),
                'sentiment_score': sentiment.get('sentiment_score', 0),
                'theme': theme.get('primary_theme', '未知')
            })
        
        # 生成可视化
        viz_results = self.visualizer.visualize_poem_features(poems_data)
        
        # 保存
        for name, fig in viz_results.items():
            if fig:
                filepath = output_dir / f"{name}.html"
                self.visualizer.save_visualization(fig, str(filepath))
        
        print(f"  可视化已保存到: {output_dir}")
    
    def save_results(self, output_dir: str = None):
        """保存分析结果"""
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / "reports" / "analysis_results"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存为JSON
        import json
        for name, data in self.results.items():
            filepath = output_dir / f"{name}_results.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n分析结果已保存到: {output_dir}")
    
    def run_full_analysis(self, generate_viz: bool = True):
        """运行完整分析"""
        print("=" * 60)
        print("诗词数据完整分析")
        print("=" * 60)
        
        # 加载数据
        self.load_data()
        
        # 运行各项分析
        self.analyze_rhyme()
        self.analyze_sentiment()
        self.analyze_entities()
        self.analyze_themes()
        self.analyze_social_network()
        
        # 生成可视化
        if generate_viz:
            self.generate_visualizations()
        
        # 保存结果
        self.save_results()
        
        print("\n" + "=" * 60)
        print("分析完成！")
        print("=" * 60)


def main():
    """主函数"""
    pipeline = PoetryAnalysisPipeline()
    pipeline.run_full_analysis(generate_viz=True)


if __name__ == "__main__":
    main()
