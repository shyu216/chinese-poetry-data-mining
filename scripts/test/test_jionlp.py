#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JioNLP 时间解析测试脚本
测试 JioNLP 的时间解析和其他功能
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


def test_jionlp_time_parsing():
    """测试 JioNLP 时间解析"""
    print("\n" + "="*60)
    print("测试 JioNLP 时间解析")
    print("="*60)

    try:
        import jionlp as jio

        print(f"\nJioNLP 版本: {jio.__version__}")

        print("\n测试 1: 绝对时间解析")
        print("-" * 40)
        time_str = "2023年10月1日"
        print(f"输入时间: {time_str}")

        try:
            result = jio.parse_time(time_str)
            print(f"解析结果: {result}")
        except Exception as e:
            print(f"[!] 时间解析失败: {e}")
            return False

        print("\n测试 2: 相对时间解析")
        print("-" * 40)
        time_str = "三天前"
        print(f"输入时间: {time_str}")

        try:
            result = jio.parse_time(time_str)
            print(f"解析结果: {result}")
        except Exception as e:
            print(f"[!] 时间解析失败: {e}")
            return False

        print("\n测试 3: 诗词中的时间表达")
        print("-" * 40)
        poem = "畴昔云天一覩披，十年徒有梦追随。"
        print(f"输入文本: {poem}")

        try:
            time_list = jio.parse_time("十年")
            print(f"'十年' 解析结果: {time_list}")
        except Exception as e:
            print(f"[!] 时间解析失败: {e}")

        print("\n测试 4: 多个时间表达")
        print("-" * 40)
        text = "宋代诗人廖行之于南宋时期创作了《挽黄承事三首》，十年后仍有梦追随。"
        print(f"输入文本: {text}")

        try:
            result1 = jio.parse_time("南宋时期")
            result2 = jio.parse_time("十年后")
            print(f"'南宋时期' 解析结果: {result1}")
            print(f"'十年后' 解析结果: {result2}")
        except Exception as e:
            print(f"[!] 时间解析失败: {e}")

        print("\n[OK] JioNLP 时间解析测试完成")
        return True

    except ImportError:
        print("\n[!] JioNLP 未安装")
        print("   安装命令: pip install jionlp")
        return False
    except Exception as e:
        print(f"\n[!] JioNLP 时间解析测试失败: {e}")
        return False


def test_jionlp_sentiment():
    """测试 JioNLP 情感分析"""
    print("\n" + "="*60)
    print("测试 JioNLP 情感分析")
    print("="*60)

    try:
        import jionlp as jio

        print(f"\nJioNLP 版本: {jio.__version__}")

        print("\n测试 1: 情感分析")
        print("-" * 40)
        text = "这首诗非常感人，让人伤心落泪。"
        print(f"输入文本: {text}")

        try:
            result = jio.sentiment(text)
            print(f"情感分析: {result}")
        except Exception as e:
            print(f"[!] 情感分析失败: {e}")

        print("\n测试 2: 诗词情感分析")
        print("-" * 40)
        poem = "少微名在世空悲，掩袂伤心陨泪洟。"
        print(f"输入文本: {poem}")

        try:
            result = jio.sentiment(poem)
            print(f"情感分析: {result}")
        except Exception as e:
            print(f"[!] 情感分析失败: {e}")

        print("\n[OK] JioNLP 情感分析测试完成")
        return True

    except Exception as e:
        print(f"\n[!] JioNLP 情感分析测试失败: {e}")
        return False


def test_jionlp_other_features():
    """测试 JioNLP 其他功能"""
    print("\n" + "="*60)
    print("测试 JioNLP 其他功能")
    print("="*60)

    try:
        import jionlp as jio

        print(f"\nJioNLP 版本: {jio.__version__}")

        print("\n测试 1: 关键词提取")
        print("-" * 40)
        text = "廖行之是南宋著名诗人，代表作有《挽黄承事三首》。"
        print(f"输入文本: {text}")

        try:
            kpe = jio.keyphrase.ChineseKeyPhrasesExtractor()
            keywords = kpe(text)
            print(f"关键词: {keywords}")
        except Exception as e:
            print(f"[!] 关键词提取失败: {e}")

        print("\n测试 2: 句子分割")
        print("-" * 40)
        text = "畴昔云天一覩披。十年徒有梦追随。"
        print(f"输入文本: {text}")

        try:
            sentences = jio.split_sentence(text)
            print(f"句子分割: {sentences}")
        except Exception as e:
            print(f"[!] 句子分割失败: {e}")

        print("\n测试 3: 地名识别")
        print("-" * 40)
        text = "廖行之，字景行，南宋诗人，衡阳人。"
        print(f"输入文本: {text}")

        try:
            locations = jio.parse_location(text)
            print(f"地名识别: {locations}")
        except Exception as e:
            print(f"[!] 地名识别失败: {e}")

        print("\n[OK] JioNLP 其他功能测试完成")
        return True

    except Exception as e:
        print(f"\n[!] JioNLP 其他功能测试失败: {e}")
        return False


def main():
    """主函数"""
    print("="*60)
    print("JioNLP 时间解析测试")
    print(f"测试诗歌: {SAMPLE_POEM['title']}")
    print(f"作者: {SAMPLE_POEM['author']} ({SAMPLE_POEM['dynasty']})")
    print("="*60)

    results = {}
    results['时间解析'] = test_jionlp_time_parsing()
    results['情感分析'] = test_jionlp_sentiment()
    results['其他功能'] = test_jionlp_other_features()

    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    for name, result in results.items():
        status = "[OK] 通过" if result else "[X] 失败"
        print(f"  {name}: {status}")

    print("\n所有测试完成!")


if __name__ == "__main__":
    main()
