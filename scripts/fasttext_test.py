"""
FastText 测试脚本

功能:
1. 加载训练好的 FastText 模型
2. 测试各种功能：相似词、词向量运算、相似度计算
"""

from gensim.models import FastText


def main():
    print("=" * 60)
    print("FastText 模型测试")
    print("=" * 60)

    print("\n加载模型...")
    model = FastText.load("results/fasttext/poetry.model")
    print(f"词表大小: {len(model.wv)}")

    print("\n" + "=" * 60)
    print("测试1: 找相似词")
    print("=" * 60)

    test_words = ["明月", "春风", "青山", "离别", "思乡"]

    for word in test_words:
        if word in model.wv:
            print(f"\n与 '{word}' 最相似的词:")
            similar = model.wv.most_similar(word, topn=10)
            for i, (w, score) in enumerate(similar, 1):
                print(f"  {i}. {w}: {score:.4f}")
        else:
            print(f"\n'{word}' 不在词表中")

    print("\n" + "=" * 60)
    print("测试2: 计算词相似度")
    print("=" * 60)

    pairs = [
        ("明月", "圆月"),
        ("明月", "清风"),
        ("春风", "秋雨"),
        ("青山", "绿水"),
        ("离别", "相聚"),
    ]

    for w1, w2 in pairs:
        if w1 in model.wv and w2 in model.wv:
            sim = model.wv.similarity(w1, w2)
            print(f"  {w1} vs {w2}: {sim:.4f}")
        else:
            print(f"  {w1} vs {w2}: 词不在词表中")

    print("\n" + "=" * 60)
    print("测试3: 词向量运算")
    print("=" * 60)

    operations = [
        (["明月", "日"], ["月"]),  # 明月 - 月 + 日 ≈ ?
        (["春风", "秋"], ["春"]),  # 春风 - 春 + 秋 ≈ ?
        (["青山", "水"], ["山"]),  # 青山 - 山 + 水 ≈ ?
    ]

    for pos, neg in operations:
        try:
            result = model.wv.most_similar(positive=pos, negative=neg, topn=5)
            print(f"\n{pos[0]} - {neg[0]} + {pos[1]} ≈ ")
            for word, score in result:
                print(f"  {word}: {score:.4f}")
        except Exception as e:
            print(f"\n运算失败: {e}")

    print("\n" + "=" * 60)
    print("测试4: OOV 测试 (子词能力)")
    print("=" * 60)

    oov_words = ["明夜", "春雨", "秋月", "山川", "故园"]

    print("\n测试不在词表中的词 (FastText 可以通过子词推断):")
    for word in oov_words:
        if word not in model.wv:
            try:
                similar = model.wv.most_similar(word, topn=5)
                print(f"\n'{word}' (OOV) 相似词:")
                for w, score in similar:
                    print(f"  {w}: {score:.4f}")
            except Exception as e:
                print(f"'{word}' 无法处理: {e}")

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
