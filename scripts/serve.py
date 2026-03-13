"""
REST API v2

功能:
1. 实现 Flask Blueprint
2. 提供相似度和词汇分析端点
3. 支持版本控制和CORS

端点:
- /api/v2/similarity/<author_id> - 获取相似作者
- /api/v2/similarity/words - 词汇相似度
- /api/v2/words/<author_id> - 作者常用词汇
- /api/v2/pos/<poem_id> - 词性标注
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from flask import Flask, Blueprint, jsonify, request, abort
from flask_cors import CORS

from src.config import get_settings


# 创建 Blueprint
api_v2 = Blueprint('api_v2', __name__)
CORS(api_v2)


class APIServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.settings = get_settings()
        self._load_data()
        
        # 注册路由
        self.app.register_blueprint(api_v2, url_prefix='/api/v2')
        
        # 健康检查
        @self.app.route('/health')
        def health():
            return jsonify({
                'status': 'ok',
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0'
            })
    
    def _load_data(self):
        """加载分析数据"""
        self.similarity_data = {}
        self.word_freq_data = {}
        self.poems_data = {}
        
        # 加载相似度数据
        similarity_path = self.settings.data.gold_dir / "v3_text_similarity.json"
        if similarity_path.exists():
            try:
                with open(similarity_path, 'r', encoding='utf-8') as f:
                    self.similarity_data = json.load(f)
                print(f"加载相似度数据: {len(self.similarity_data.get('data', {}).get('authors', []))} 位作者")
            except Exception as e:
                print(f"加载相似度数据失败: {e}")
        
        # 加载词汇频率数据
        word_freq_path = self.settings.data.gold_dir / "v3_word_frequency.json"
        if word_freq_path.exists():
            try:
                with open(word_freq_path, 'r', encoding='utf-8') as f:
                    self.word_freq_data = json.load(f)
                print(f"加载词汇频率数据: {len(self.word_freq_data.get('data', {}).get('author_words', {}))} 位作者")
            except Exception as e:
                print(f"加载词汇频率数据失败: {e}")
        
        # 加载诗词数据
        silver_path = self.settings.data.silver_dir / "v2_poems_structured.csv"
        if silver_path.exists():
            try:
                import pandas as pd
                df = pd.read_csv(silver_path)
                self.poems_data = df.to_dict('records')
                print(f"加载诗词数据: {len(self.poems_data)} 首")
            except Exception as e:
                print(f"加载诗词数据失败: {e}")
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """启动服务器"""
        print(f"启动 API 服务器: http://{host}:{port}/api/v2")
        print("可用端点:")
        print("  GET /api/v2/similarity/<author_id> - 获取相似作者")
        print("  GET /api/v2/similarity/words - 词汇相似度")
        print("  GET /api/v2/words/<author_id> - 作者常用词汇")
        print("  GET /api/v2/pos/<poem_id> - 词性标注")
        print("  GET /health - 健康检查")
        
        self.app.run(host=host, port=port, debug=debug)


# 全局服务器实例
server = None


def get_server():
    """获取服务器实例"""
    global server
    if server is None:
        server = APIServer()
    return server


@api_v2.route('/similarity/<author_id>', methods=['GET'])
def get_similar_authors(author_id):
    """获取相似作者"""
    server = get_server()
    data = server.similarity_data.get('data', {})
    
    if not data:
        return jsonify({
            'error': '相似度数据未加载',
            'status': 'error'
        }), 500
    
    authors = data.get('authors', [])
    similar_authors = data.get('similar_authors', {})
    
    # 查找作者索引
    author_index = None
    for i, author in enumerate(authors):
        if author == author_id:
            author_index = i
            break
    
    if author_index is None:
        return jsonify({
            'error': f'作者 {author_id} 未找到',
            'status': 'error'
        }), 404
    
    # 获取相似作者
    author_similar = similar_authors.get(author_id, [])
    
    return jsonify({
        'author': author_id,
        'similar_authors': author_similar,
        'total_similar': len(author_similar),
        'status': 'success'
    })


@api_v2.route('/similarity/words', methods=['GET'])
def get_word_similarity():
    """词汇相似度"""
    server = get_server()
    word1 = request.args.get('word1')
    word2 = request.args.get('word2')
    
    if not word1 or not word2:
        return jsonify({
            'error': '缺少参数 word1 或 word2',
            'status': 'error'
        }), 400
    
    # 简单的词汇相似度计算（基于共同出现）
    word_freq = server.word_freq_data.get('data', {}).get('author_words', {})
    
    # 统计两个词在作者中的出现频率
    word1_authors = set()
    word2_authors = set()
    
    for author, words in word_freq.items():
        author_words = [w['word'] for w in words]
        if word1 in author_words:
            word1_authors.add(author)
        if word2 in author_words:
            word2_authors.add(author)
    
    # 计算 Jaccard 相似度
    intersection = len(word1_authors & word2_authors)
    union = len(word1_authors | word2_authors)
    similarity = intersection / union if union > 0 else 0
    
    return jsonify({
        'word1': word1,
        'word2': word2,
        'similarity': round(similarity, 3),
        'common_authors': list(word1_authors & word2_authors),
        'word1_authors': len(word1_authors),
        'word2_authors': len(word2_authors),
        'status': 'success'
    })


@api_v2.route('/words/<author_id>', methods=['GET'])
def get_author_words(author_id):
    """作者常用词汇"""
    server = get_server()
    word_freq = server.word_freq_data.get('data', {}).get('author_words', {})
    
    if author_id not in word_freq:
        return jsonify({
            'error': f'作者 {author_id} 未找到',
            'status': 'error'
        }), 404
    
    # 获取参数
    limit = request.args.get('limit', 50, type=int)
    pos = request.args.get('pos')  # 可选的词性过滤
    
    words = word_freq[author_id]
    
    # 词性过滤
    if pos:
        words = [w for w in words if w.get('pos') == pos]
    
    # 限制数量
    words = words[:limit]
    
    return jsonify({
        'author': author_id,
        'words': words,
        'total_words': len(words),
        'status': 'success'
    })


@api_v2.route('/pos/<poem_id>', methods=['GET'])
def get_poem_pos(poem_id):
    """词性标注"""
    server = get_server()
    poems = server.poems_data
    
    # 查找诗词
    poem = None
    for p in poems:
        if str(p.get('id')) == poem_id:
            poem = p
            break
    
    if not poem:
        return jsonify({
            'error': f'诗词 {poem_id} 未找到',
            'status': 'error'
        }), 404
    
    # 进行词性标注
    try:
        import jieba
        import jieba.posseg as pseg
        
        content = poem.get('content', '')
        if not content:
            return jsonify({
                'error': '诗词内容为空',
                'status': 'error'
            }), 400
        
        # 分词并标注词性
        words_with_pos = []
        for word, flag in pseg.cut(content):
            if word.strip():
                words_with_pos.append({
                    'word': word,
                    'pos': flag
                })
        
        return jsonify({
            'poem_id': poem_id,
            'title': poem.get('title', ''),
            'author': poem.get('author', ''),
            'pos_tags': words_with_pos,
            'total_words': len(words_with_pos),
            'status': 'success'
        })
    
    except ImportError:
        return jsonify({
            'error': '需要安装 jieba: pip install jieba',
            'status': 'error'
        }), 500
    except Exception as e:
        return jsonify({
            'error': f'词性标注失败: {str(e)}',
            'status': 'error'
        }), 500


@api_v2.route('/stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    server = get_server()
    
    stats = {
        'similarity_data': {
            'authors': len(server.similarity_data.get('data', {}).get('authors', [])),
            'network_edges': len(server.similarity_data.get('data', {}).get('network_edges', []))
        },
        'word_freq_data': {
            'authors': len(server.word_freq_data.get('data', {}).get('author_words', {})),
            'global_words': len(server.word_freq_data.get('data', {}).get('global_top_words', []))
        },
        'poems_data': {
            'total': len(server.poems_data)
        },
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    }
    
    return jsonify({
        'stats': stats,
        'status': 'success'
    })


def main():
    parser = argparse.ArgumentParser(description="API 服务器")
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='服务器主机'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='服务器端口'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='调试模式'
    )
    args = parser.parse_args()
    
    global server
    server = APIServer()
    server.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
