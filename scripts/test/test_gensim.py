#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gensim Word2Vec 测试脚本
测试 gensim 的 Word2Vec 词向量功能
"""

import sys
from pathlib import Path
from typing import List

sys.path.append(str(Path(__file__).parent.parent.parent))

SAMPLE_POEM = {
    "author": "廖行之",
    "paragraphs": "畴昔云天一覩披，十年徒有梦追随。\n担簦已负异时志，仰斗今余后学师。\n夜壑舟亡人孰秘，少微名在世空悲。\n嗟嗟莫致徐芻奠，掩袂伤心隕淚洟。",
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


def prepare_poem_sentences(poem: str) -> List[List[str]]:
    """准备诗词句子数据"""
    sentences = poem.replace(',', '.').split('.')
    sentences = [s.strip() for s in sentences if s.strip()]

    word_sentences = []
    for sent in sentences:
        words = [c for c in sent if c not in '，。、；：？！""''（）【】《》']
        if words:
            word_sentences.append(words)

    return word_sentences


def test_gensim_word2vec_basic():
    """测试 gensim Word2Vec 基础功能"""
    print("\n" + "="*60)
    print("测试 gensim Word2Vec 基础功能")
    print("="*60)

    try:
        from gensim.models import Word2Vec

        print(f"\ngensim 版本: {__import__('gensim').__version__}")

        print("\n测试 1: 基础 Word2Vec 训练")
        print("-" * 40)

        sentences = [
            ["十年", "徒有", "梦", "追随"],
            ["担簦", "已负", "异时", "志"],
            ["仰斗", "今余", "后学", "师"],
            ["夜壑", "舟亡", "人", "孰", "秘"],
            ["少微", "名在", "世", "空", "悲"],
            ["嗟嗟", "莫致", "徐", "刍", "奠"],
            ["掩袂", "伤心", "陨", "泪", "洟"],
        ]

        print(f"训练数据 ({len(sentences)} 句):")
        for i, sent in enumerate(sentences, 1):
            print(f"  {i}. {' '.join(sent)}")

        model = Word2Vec(
            sentences,
            vector_size=100,
            window=5,
            min_count=1,
            workers=4,
            epochs=100,
            seed=42
        )

        print(f"\n词向量维度: {model.wv.vector_size}")
        print(f"词汇表大小: {len(model.wv)}")
        print(f"词汇表: {list(model.wv.key_to_index.keys())}")

        print("\n测试 2: 词向量查看")
        print("-" * 40)
        word = "十年"
        if word in model.wv:
            vector = model.wv[word]
            print(f"'{word}' 的词向量 (前10维):")
            print(f"  {vector[:10]}")
        else:
            print(f"[!] 词汇 '{word}' 不在词汇表中")

        print("\n测试 3: 词相似度计算")
        print("-" * 40)
        word_pairs = [("十年", "梦"), ("追随", "志"), ("伤心", "悲")]
        for word1, word2 in word_pairs:
            if word1 in model.wv and word2 in model.wv:
                similarity = model.wv.similarity(word1, word2)
                print(f"'{word1}' 与 '{word2}' 的相似度: {similarity:.4f}")
            else:
                print(f"[!] 词汇 '{word1}' 或 '{word2}' 不在词汇表中")

        print("\n测试 4: 最相似词查询")
        print("-" * 40)
        query_word = "十年"
        if query_word in model.wv:
            similar_words = model.wv.most_similar(query_word, topn=5)
            print(f"与 '{query_word}' 最相似的 5 个词:")
            for word, score in similar_words:
                print(f"  {word}: {score:.4f}")

        print("\n[OK] gensim Word2Vec 基础功能测试完成")
        return True

    except ImportError:
        print("\n[!] gensim 未安装")
        print("   安装命令: pip install gensim")
        return False
    except Exception as e:
        print(f"\n[!] gensim Word2Vec 基础功能测试失败: {e}")
        return False


def test_gensim_word2vec_poem():
    """测试 gensim Word2Vec 在诗词上的应用"""
    print("\n" + "="*60)
    print("测试 gensim Word2Vec 在诗词上的应用")
    print("="*60)

    try:
        from gensim.models import Word2Vec

        print(f"\ngensim 版本: {__import__('gensim').__version__}")

        print("\n测试 1: 使用诗词内容训练")
        print("-" * 40)

        poem = SAMPLE_POEM['content']
        print(f"诗词内容: {poem}")

        sentences = prepare_poem_sentences(poem)
        print(f"\n分句结果 ({len(sentences)} 句):")
        for i, sent in enumerate(sentences, 1):
            print(f"  {i}. {' '.join(sent)}")

        if len(sentences) < 2:
            print("[!] 句子数量不足，无法训练 Word2Vec")
            return False

        model = Word2Vec(
            sentences,
            vector_size=50,
            window=3,
            min_count=1,
            workers=4,
            epochs=200,
            seed=42
        )

        print(f"\n词向量维度: {model.wv.vector_size}")
        print(f"词汇表大小: {len(model.wv)}")

        print("\n测试 2: 诗词词汇分析")
        print("-" * 40)
        vocabulary = list(model.wv.key_to_index.keys())
        print(f"词汇表 ({len(vocabulary)} 个词):")
        print(f"  {', '.join(vocabulary)}")

        print("\n测试 3: 词向量相似度矩阵")
        print("-" * 40)
        if len(vocabulary) >= 3:
            words = vocabulary[:5]
            print(f"词相似度矩阵 (前5个词):")
            print(f"      ", end="")
            for w in words:
                print(f"{w:>6}", end=" ")
            print()
            for w1 in words:
                print(f"{w1:>5} ", end="")
                for w2 in words:
                    if w1 == w2:
                        print(f"  1.000", end=" ")
                    else:
                        sim = model.wv.similarity(w1, w2)
                        print(f"  {sim:.3f}", end=" ")
                print()

        print("\n测试 4: 词语类比")
        print("-" * 40)
        if "梦" in model.wv and "追随" in model.wv and "志" in model.wv:
            try:
                result = model.wv.most_similar(
                    positive=["梦", "志"],
                    negative=["追随"],
                    topn=3
                )
                print(f"'梦' + '志' - '追随' 最相似的词:")
                for word, score in result:
                    print(f"  {word}: {score:.4f}")
            except Exception as e:
                print(f"[!] 词语类比失败: {e}")

        print("\n[OK] gensim Word2Vec 诗词应用测试完成")
        return True

    except Exception as e:
        print(f"\n[!] gensim Word2Vec 诗词应用测试失败: {e}")
        return False


def test_gensim_word2vec_advanced():
    """测试 gensim Word2Vec 高级功能"""
    print("\n" + "="*60)
    print("测试 gensim Word2Vec 高级功能")
    print("="*60)

    try:
        from gensim.models import Word2Vec
        import numpy as np

        print(f"\ngensim 版本: {__import__('gensim').__version__}")

        print("\n测试 1: 模型保存和加载")
        print("-" * 40)

        sentences = [
            ["十年", "徒有", "梦", "追随"],
            ["担簦", "已负", "异时", "志"],
            ["仰斗", "今余", "后学", "师"],
        ]

        model = Word2Vec(sentences, vector_size=50, window=3, min_count=1, epochs=50, seed=42)

        save_path = Path(__file__).parent / "test_word2vec.model"
        model.save(str(save_path))
        print(f"模型已保存到: {save_path}")

        loaded_model = Word2Vec.load(str(save_path))
        print(f"模型已加载，词汇表大小: {len(loaded_model.wv)}")

        print("\n测试 2: 词向量可视化准备")
        print("-" * 40)
        vectors = []
        words = list(loaded_model.wv.key_to_index.keys())
        for word in words:
            vectors.append(loaded_model.wv[word])

        vectors_array = np.array(vectors)
        print(f"词向量矩阵形状: {vectors_array.shape}")
        print(f"向量维度: {vectors_array.shape[1]}")

        print("\n测试 3: 词向量统计")
        print("-" * 40)
        print(f"向量均值: {np.mean(vectors_array):.4f}")
        print(f"向量标准差: {np.std(vectors_array):.4f}")
        print(f"向量最小值: {np.min(vectors_array):.4f}")
        print(f"向量最大值: {np.max(vectors_array):.4f}")

        print("\n测试 4: 词汇不匹配检测")
        print("-" * 40)
        test_words = ["十年", "梦", "不存在的词"]
        for word in test_words:
            if word in loaded_model.wv:
                print(f"[OK] '{word}' 在词汇表中")
            else:
                print(f"[X] '{word}' 不在词汇表中")

        print("\n[OK] gensim Word2Vec 高级功能测试完成")
        return True

    except Exception as e:
        print(f"\n[!] gensim Word2Vec 高级功能测试失败: {e}")
        return False


def main():
    """主函数"""
    print("="*60)
    print("gensim Word2Vec 测试")
    print(f"测试诗歌: {SAMPLE_POEM['title']}")
    print(f"作者: {SAMPLE_POEM['author']} ({SAMPLE_POEM['dynasty']})")
    print("="*60)

    test_gensim_word2vec_basic()
    test_gensim_word2vec_poem()
    test_gensim_word2vec_advanced()

    print("\n" + "="*60)
    print("gensim Word2Vec 测试完成")
    print("="*60)


if __name__ == "__main__":
    main()
