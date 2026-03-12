#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诗歌数据挖掘测试脚本
测试 Pandas/NumPy、OpenCC/pypinyin、Plotly、scikit-learn、NetworkX 等库的经典用法
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.text_utils import TextProcessor
from src.core.pinyin_utils import PinyinConverter, ToneAnalyzer


SAMPLE_POEM = {
    "author": "廖行之",
    "paragraphs": "畴昔云天一覩披，十年徒有梦追随。\n担簦已负异时志，仰斗今余后学师。\n夜壑舟亡人孰秘，少微名在世空悲。\n嗟嗟莫致徐刍奠，掩袂伤心陨泪洟。",
    "title": "挽黄承事三首 其三",
    "id": "ee8045c8-7c9c-4201-ba4a-5f058fe8e09f",
    "dynasty": "宋代",
    "genre": "诗",
    "tags": "",
    "notes": "",
    "rhythmic": "",
    "prologue": "",
    "content": "畴昔云天一覩披,十年徒有梦追随. 担簦已负异时志,仰斗今余后学师. 夜壑舟亡人孰秘,少微名在世空悲. 嗟嗟莫致徐刍奠,掩袂伤心陨泪洟."
}


def test_pandas_numpy():
    """测试 Pandas/NumPy 数据处理"""
    print("\n" + "="*60)
    print("测试 Pandas/NumPy")
    print("="*60)

    df = pd.DataFrame([SAMPLE_POEM])

    print(f"\n原始数据:")
    print(df[['title', 'author', 'dynasty']].to_string())

    content = SAMPLE_POEM['content']
    sentences = content.replace(',', '.').split('.')
    sentences = [s.strip() for s in sentences if s.strip()]

    char_counts = [len(s) for s in sentences]
    print(f"\n诗句长度统计:")
    print(f"  每句字符数: {char_counts}")
    print(f"  平均长度: {np.mean(char_counts):.2f}")
    print(f"  标准差: {np.std(char_counts):.2f}")
    print(f"  最大长度: {np.max(char_counts)}")
    print(f"  最小长度: {np.min(char_counts)}")

    all_chars = ''.join(sentences)
    char_freq = pd.Series(list(all_chars)).value_counts().head(10)
    print(f"\n高频字符 Top 10:")
    print(char_freq.to_string())

    arr = np.array([[ord(c) for c in s] for s in sentences[:2]])
    print(f"\n字符ASCII矩阵 (前2句):")
    print(arr)

    print("\n✅ Pandas/NumPy 测试通过")
    return df


def test_opencc_pypinyin():
    """测试 OpenCC/pypinyin 文本处理"""
    print("\n" + "="*60)
    print("测试 OpenCC/pypinyin")
    print("="*60)

    processor = TextProcessor()
    print(f"\nOpenCC 可用: {processor.has_opencc}")

    traditional = SAMPLE_POEM['paragraphs'].split('\n')[0]
    print(f"\n繁体: {traditional}")

    simplified = processor.traditional_to_simplified(traditional)
    print(f"简体: {simplified}")

    converter = PinyinConverter()
    print(f"\npypinyin 可用: {converter.has_pypinyin}")

    text = "十年徒有梦追随"
    pinyin_normal = converter.get_pinyin(text, 'normal')
    pinyin_tone = converter.get_pinyin(text, 'tone')
    pinyin_initials = converter.get_pinyin(text, 'initials')

    print(f"\n文本: {text}")
    print(f"拼音(无调): {pinyin_normal}")
    print(f"拼音(带调): {pinyin_tone}")
    print(f"声母: {pinyin_initials}")

    analyzer = ToneAnalyzer()
    pattern = analyzer.get_level_oblique_pattern(text)
    print(f"平仄: {pattern}")

    print("\n✅ OpenCC/pypinyin 测试通过")
    return True


def test_sklearn():
    """测试 scikit-learn TF-IDF 和聚类"""
    print("\n" + "="*60)
    print("测试 scikit-learn (TF-IDF + 聚类)")
    print("="*60)

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA

    corpus = [
        "十年徒有梦追随",
        "担簦已负异时志",
        "仰斗今余后学师",
        "夜壑舟亡人孰秘",
        "少微名在世空悲",
        "嗟嗟莫致徐刍奠",
        "掩袂伤心陨泪洟",
    ]

    vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(corpus)

    print(f"\nTF-IDF 矩阵形状: {tfidf_matrix.shape}")
    print(f"特征数量: {len(vectorizer.get_feature_names_out())}")

    feature_names = vectorizer.get_feature_names_out()[:10]
    print(f"特征名(前10): {list(feature_names)}")

    n_clusters = 2
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(tfidf_matrix)

    print(f"\n聚类结果 (K={n_clusters}):")
    for i in range(n_clusters):
        cluster_poems = [corpus[j] for j in range(len(corpus)) if labels[j] == i]
        print(f"  簇 {i}: {cluster_poems}")

    if tfidf_matrix.shape[1] > 1:
        pca = PCA(n_components=2, random_state=42)
        coords = pca.fit_transform(tfidf_matrix.toarray())
        print(f"\nPCA 降维坐标 (前2句):")
        for i in range(min(2, len(coords))):
            print(f"  句子{i}: ({coords[i][0]:.4f}, {coords[i][1]:.4f})")

    print("\n✅ scikit-learn 测试通过")
    return True


def test_plotly():
    """测试 Plotly 可视化"""
    print("\n" + "="*60)
    print("测试 Plotly 可视化")
    print("="*60)

    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    content = SAMPLE_POEM['content']
    sentences = [s.strip() for s in content.replace(',', '.').split('.') if s.strip()]
    char_counts = [len(s) for s in sentences]

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("诗句长度分布", "字符频率 Top 10"),
        specs=[[{"type": "bar"}, {"type": "bar"}]]
    )

    fig.add_trace(
        go.Bar(x=[f'句{i+1}' for i in range(len(char_counts))], y=char_counts, name='长度'),
        row=1, col=1
    )

    all_chars = ''.join(sentences)
    char_freq = pd.Series(list(all_chars)).value_counts().head(10)
    fig.add_trace(
        go.Bar(x=char_freq.index.tolist(), y=char_freq.values, name='频率'),
        row=1, col=2
    )

    fig.update_layout(
        title_text=f"诗词分析: {SAMPLE_POEM['title']}",
        showlegend=False,
        height=400
    )

    output_path = Path(__file__).parent / "test_poem_visualization.html"
    fig.write_html(output_path)
    print(f"\n可视化已保存到: {output_path}")

    print("\n✅ Plotly 测试通过")
    return True


def test_networkx():
    """测试 NetworkX 社交网络分析"""
    print("\n" + "="*60)
    print("测试 NetworkX 社交网络分析")
    print("="*60)

    import networkx as nx

    G = nx.Graph()

    authors = ["李白", "杜甫", "白居易", "王维", "孟浩然"]
    G.add_nodes_from(authors, node_type='author')

    edges = [
        ("李白", "杜甫", {"weight": 5}),
        ("李白", "白居易", {"weight": 3}),
        ("杜甫", "王维", {"weight": 4}),
        ("王维", "孟浩然", {"weight": 2}),
        ("白居易", "王维", {"weight": 3}),
    ]
    G.add_edges_from(edges)

    print(f"\n网络节点数: {G.number_of_nodes()}")
    print(f"网络边数: {G.number_of_edges()}")
    print(f"节点: {list(G.nodes())}")
    print(f"边: {list(G.edges(data=True))}")

    degree_centrality = nx.degree_centrality(G)
    betweenness_centrality = nx.betweenness_centrality(G)
    pagerank = nx.pagerank(G)

    print(f"\n度中心性: {dict(sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True))}")
    print(f"介数中心性: {dict(sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True))}")
    print(f"PageRank: {dict(sorted(pagerank.items(), key=lambda x: x[1], reverse=True))}")

    components = list(nx.connected_components(G))
    print(f"\n连通分量数: {len(components)}")

    try:
        shortest_path = nx.shortest_path(G, "李白", "孟浩然")
        print(f"李白到孟浩然最短路径: {' -> '.join(shortest_path)}")
    except nx.NetworkXNoPath:
        print("无路径")

    output_path = Path(__file__).parent / "test_network.html"
    fig = nx.draw(G, with_labels=True, node_color='lightblue', font_size=10)
    import matplotlib.pyplot as plt
    plt.savefig(output_path.with_suffix('.png'), dpi=100, bbox_inches='tight')
    plt.close()
    print(f"\n网络图已保存到: {output_path.with_suffix('.png')}")

    print("\n✅ NetworkX 测试通过")
    return True


def test_hanlp():
    """测试 HanLP NER (如果可用)"""
    print("\n" + "="*60)
    print("测试 HanLP (NER)")
    print("="*60)

    try:
        import hanlp

        text = "李白字太白，唐代著名诗人，代表作有《静夜思》。"
        tok = hanlp.load(hanlp.pretrained.tok.COARSE_ELECTRA_SMALL_ZH)
        ner = hanlp.load(hanlp.pretrained.ner.NER_CONLL_ELECTRA_SMALL_ZH)

        tokens = tok(text)
        print(f"\n分词结果: {tokens}")

        entities = ner.predict(tokens)
        print(f"命名实体: {entities}")

        print("\n✅ HanLP 测试通过")
        return True
    except ImportError:
        print("\n⚠️ HanLP 未安装，跳过测试")
        print("   安装命令: pip install hanlp")
        return False
    except Exception as e:
        print(f"\n⚠️ HanLP 测试失败: {e}")
        return False


def test_jionlp():
    """测试 JioNLP 时间解析 (如果可用)"""
    print("\n" + "="*60)
    print("测试 JioNLP (时间解析)")
    print("="*60)

    try:
        import jionlp as jio

        text = "2023年10月1日，李白写了一首诗。"
        time_extractor = jio.TimeExtractor()

        time_list = time_extractor(text)
        print(f"\n文本: {text}")
        print(f"时间实体: {time_list}")

        print("\n✅ JioNLP 测试通过")
        return True
    except ImportError:
        print("\n⚠️ JioNLP 未安装，跳过测试")
        print("   安装命令: pip install jionlp")
        return False
    except Exception as e:
        print(f"\n⚠️ JioNLP 测试失败: {e}")
        return False


def test_gensim():
    """测试 gensim Word2Vec (如果可用)"""
    print("\n" + "="*60)
    print("测试 gensim (Word2Vec)")
    print("="*60)

    try:
        from gensim.models import Word2Vec

        sentences = [
            ["十年", "徒有", "梦", "追随"],
            ["担簦", "已负", "异时", "志"],
            ["仰斗", "今余", "后学", "师"],
            ["夜壑", "舟亡", "人", "孰", "秘"],
            ["少微", "名在", "世", "空", "悲"],
        ]

        model = Word2Vec(sentences, vector_size=10, window=2, min_count=1, workers=1, epochs=100)

        print(f"\n词向量维度: {model.wv.vector_size}")
        print(f"词汇表: {list(model.wv.key_to_index.keys())}")

        if "十年" in model.wv and "梦" in model.wv:
            similarity = model.wv.similarity("十年", "梦")
            print(f"'十年'与'梦'的相似度: {similarity:.4f}")

        print("\n✅ gensim 测试通过")
        return True
    except ImportError:
        print("\n⚠️ gensim 未安装，跳过测试")
        print("   安装命令: pip install gensim")
        return False
    except Exception as e:
        print(f"\n⚠️ gensim 测试失败: {e}")
        return False


def main():
    """主函数"""
    print("="*60)
    print("诗歌数据挖掘综合测试")
    print(f"测试诗歌: {SAMPLE_POEM['title']}")
    print(f"作者: {SAMPLE_POEM['author']} ({SAMPLE_POEM['dynasty']})")
    print("="*60)

    results = {}

    results['Pandas/NumPy'] = test_pandas_numpy() is not None
    results['OpenCC/pypinyin'] = test_opencc_pypinyin()
    results['scikit-learn'] = test_sklearn()
    results['Plotly'] = test_plotly()
    results['NetworkX'] = test_networkx()
    results['HanLP'] = test_hanlp()
    results['JioNLP'] = test_jionlp()
    results['gensim'] = test_gensim()

    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败/跳过"
        print(f"  {name}: {status}")

    print("\n所有测试完成!")


if __name__ == "__main__":
    main()
