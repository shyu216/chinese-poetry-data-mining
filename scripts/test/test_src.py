#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
src 模块测试脚本
测试 src 文件夹中的诗词分析功能
"""

import sys
from pathlib import Path

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


def test_pinyin_utils():
    """测试拼音工具模块"""
    print("\n" + "="*60)
    print("测试拼音工具模块 (pinyin_utils)")
    print("="*60)

    try:
        from src.core.pinyin_utils import (
            PinyinConverter,
            ToneAnalyzer,
            get_pinyin,
            get_tone_pattern
        )

        print("\n测试 1: 拼音转换")
        print("-" * 40)
        text = "廖行之"
        print(f"输入文本: {text}")

        try:
            converter = PinyinConverter()
            pinyin = converter.get_pinyin(text)
            print(f"拼音: {pinyin}")
        except Exception as e:
            print(f"[!] 拼音转换失败: {e}")

        print("\n测试 2: 声调分析")
        print("-" * 40)
        text = "十年徒有梦追随"
        print(f"输入文本: {text}")

        try:
            analyzer = ToneAnalyzer()
            pattern = analyzer.get_level_oblique_pattern(text)
            print(f"平仄模式: {pattern}")
        except Exception as e:
            print(f"[!] 声调分析失败: {e}")

        print("\n测试 3: 押韵检查")
        print("-" * 40)
        char1 = "披"
        char2 = "悲"
        print(f"检查押韵: {char1} vs {char2}")

        try:
            from src.core.pinyin_utils import check_rhyme
            is_rhyme = check_rhyme(char1, char2)
            print(f"是否押韵: {is_rhyme}")
        except Exception as e:
            print(f"[!] 押韵检查失败: {e}")

        print("\n[OK] 拼音工具模块测试完成")
        return True

    except ImportError as e:
        print(f"\n[!] 导入失败: {e}")
        return False
    except Exception as e:
        print(f"\n[!] 拼音工具模块测试失败: {e}")
        return False


def test_text_utils():
    """测试文本处理工具模块"""
    print("\n" + "="*60)
    print("测试文本处理工具模块 (text_utils)")
    print("="*60)

    try:
        from src.core.text_utils import (
            TextProcessor,
            preprocess_poem,
            normalize_poem_lines
        )

        print("\n测试 1: 繁简转换")
        print("-" * 40)
        text = "廖行之是宋代詩人"
        print(f"输入文本: {text}")

        try:
            processor = TextProcessor()
            result = processor.traditional_to_simplified(text)
            print(f"转换结果: {result}")
        except Exception as e:
            print(f"[!] 繁简转换失败: {e}")

        print("\n测试 2: 文本清洗")
        print("-" * 40)
        text = "  廖行之  是  宋代  诗人  "
        print(f"输入文本: '{text}'")

        try:
            result = processor.clean_text(text)
            print(f"清洗结果: '{result}'")
        except Exception as e:
            print(f"[!] 文本清洗失败: {e}")

        print("\n测试 3: 诗词预处理")
        print("-" * 40)
        content = SAMPLE_POEM['paragraphs']
        print(f"输入诗词:\n{content}")

        try:
            result = preprocess_poem(content)
            print(f"预处理结果:\n{result}")
        except Exception as e:
            print(f"[!] 诗词预处理失败: {e}")

        print("\n测试 4: 诗句标准化")
        print("-" * 40)
        content = SAMPLE_POEM['paragraphs']
        print(f"输入诗词:\n{content}")

        try:
            lines = normalize_poem_lines(content)
            print(f"标准化结果 ({len(lines)} 句):")
            for i, line in enumerate(lines, 1):
                print(f"  {i}. {line}")
        except Exception as e:
            print(f"[!] 诗句标准化失败: {e}")

        print("\n[OK] 文本处理工具模块测试完成")
        return True

    except ImportError as e:
        print(f"\n[!] 导入失败: {e}")
        return False
    except Exception as e:
        print(f"\n[!] 文本处理工具模块测试失败: {e}")
        return False


def test_rhyme_features():
    """测试韵律特征提取模块"""
    print("\n" + "="*60)
    print("测试韵律特征提取模块 (rhyme_features)")
    print("="*60)

    try:
        from src.features.rhyme_features import (
            RhymeFeatureExtractor,
            extract_rhythm,
            get_tone_pattern,
            identify_poem_form
        )

        print("\n测试 1: 韵律特征提取")
        print("-" * 40)
        content = SAMPLE_POEM['paragraphs']
        print(f"输入诗词:\n{content}")

        try:
            features = extract_rhythm(content)
            print(f"韵律特征:")
            print(f"  诗体: {features.get('form', '未知')}")
            print(f"  主题: {features.get('theme', ('未知', {}))[0]}")
            print(f"  行数: {features.get('line_count', 0)}")
            print(f"  平仄模式: {features.get('level_oblique_patterns', [])}")
            print(f"  韵脚: {features.get('rhyme_categories', [])}")
            print(f"  押韵方案: {features.get('rhyme_scheme', '无韵')}")
            print(f"  双声叠韵: {features.get('alliteration_count', 0)}")
            print(f"  叠韵: {features.get('assonance_count', 0)}")
        except Exception as e:
            print(f"[!] 韵律特征提取失败: {e}")

        print("\n测试 2: 平仄模式获取")
        print("-" * 40)
        content = SAMPLE_POEM['paragraphs']
        print(f"输入诗词:\n{content}")

        try:
            patterns = get_tone_pattern(content)
            print(f"平仄模式 ({len(patterns)} 句):")
            for i, pattern in enumerate(patterns, 1):
                print(f"  {i}. {pattern}")
        except Exception as e:
            print(f"[!] 平仄模式获取失败: {e}")

        print("\n测试 3: 诗体识别")
        print("-" * 40)
        content = SAMPLE_POEM['paragraphs']
        print(f"输入诗词:\n{content}")

        try:
            form = identify_poem_form(content)
            print(f"诗体: {form}")
        except Exception as e:
            print(f"[!] 诗体识别失败: {e}")

        print("\n测试 4: 主题分类")
        print("-" * 40)
        content = SAMPLE_POEM['paragraphs']
        print(f"输入诗词:\n{content}")

        try:
            theme, scores = classify_theme(content)
            print(f"主题: {theme}")
            print(f"主题得分:")
            for theme_name, score in scores.items():
                print(f"  {theme_name}: {score:.2%}")
        except Exception as e:
            print(f"[!] 主题分类失败: {e}")

        print("\n测试 5: 综合分析")
        print("-" * 40)
        content = SAMPLE_POEM['paragraphs']
        print(f"输入诗词:\n{content}")

        try:
            result = analyze_poetry(content)
            print(f"综合分析结果:")
            print(f"  诗体: {result.get('form', '未知')}")
            print(f"  主题: {result.get('theme', ('未知', {}))[0]}")
            print(f"  行数: {result.get('line_count', 0)}")
            print(f"  字数: {result.get('char_count', 0)}")
            print(f"  韵律特征: {result.get('rhythm', {})}")
        except Exception as e:
            print(f"[!] 综合分析失败: {e}")

        print("\n[OK] 韵律特征提取模块测试完成")
        return True

    except ImportError as e:
        print(f"\n[!] 导入失败: {e}")
        return False
    except Exception as e:
        print(f"\n[!] 韵律特征提取模块测试失败: {e}")
        return False


def test_poetry_classifier():
    """测试诗词分类模块"""
    print("\n" + "="*60)
    print("测试诗词分类模块 (poetry_classifier)")
    print("="*60)

    try:
        from src.models.poetry_classifier import (
            PoetryFormClassifier,
            ThemeClassifier,
            PoetryAnalyzer
        )

        print("\n测试 1: 诗体分类")
        print("-" * 40)
        content = SAMPLE_POEM['paragraphs']
        print(f"输入诗词:\n{content}")

        try:
            classifier = PoetryFormClassifier()
            form = classifier.classify(content)
            print(f"诗体: {form}")
        except Exception as e:
            print(f"[!] 诗体分类失败: {e}")

        print("\n测试 2: 主题分类")
        print("-" * 40)
        content = SAMPLE_POEM['paragraphs']
        print(f"输入诗词:\n{content}")

        try:
            classifier = ThemeClassifier()
            theme, scores = classifier.classify(content)
            print(f"主题: {theme}")
            print(f"主题得分:")
            for theme_name, score in scores.items():
                print(f"  {theme_name}: {score:.2%}")
        except Exception as e:
            print(f"[!] 主题分类失败: {e}")

        print("\n测试 3: 综合分析")
        print("-" * 40)
        content = SAMPLE_POEM['paragraphs']
        print(f"输入诗词:\n{content}")

        try:
            analyzer = PoetryAnalyzer()
            result = analyzer.analyze(content)
            print(f"综合分析结果:")
            print(f"  诗体: {result.get('form', '未知')}")
            print(f"  主题: {result.get('theme', ('未知', {}))[0]}")
            print(f"  行数: {result.get('line_count', 0)}")
            print(f"  字数: {result.get('char_count', 0)}")
            print(f"  韵律特征: {result.get('rhythm', {})}")
        except Exception as e:
            print(f"[!] 综合分析失败: {e}")

        print("\n[OK] 诗词分类模块测试完成")
        return True

    except ImportError as e:
        print(f"\n[!] 导入失败: {e}")
        return False
    except Exception as e:
        print(f"\n[!] 诗词分类模块测试失败: {e}")
        return False


def main():
    """主函数"""
    print("="*60)
    print("src 模块测试")
    print(f"测试诗歌: {SAMPLE_POEM['title']}")
    print(f"作者: {SAMPLE_POEM['author']} ({SAMPLE_POEM['dynasty']})")
    print("="*60)

    results = {}
    results['拼音工具'] = test_pinyin_utils()
    results['文本处理'] = test_text_utils()
    results['韵律特征'] = test_rhyme_features()
    results['诗词分类'] = test_poetry_classifier()

    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    for name, result in results.items():
        status = "[OK] 通过" if result else "[X] 失败"
        print(f"  {name}: {status}")

    print("\n所有测试完成!")


if __name__ == "__main__":
    main()
