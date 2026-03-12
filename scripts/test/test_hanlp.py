#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HanLP 综合测试脚本
测试 HanLP 2.1.3 的多种功能：分词、NER、依存句法、情感分析等
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


def test_hanlp_tokenization():
    """测试 HanLP 分词功能"""
    print("\n" + "="*60)
    print("测试 HanLP 分词")
    print("="*60)

    try:
        import hanlp

        print(f"\nHanLP 版本: {hanlp.__version__}")

        print("\n测试 1: 基础分词")
        print("-" * 40)
        text = "廖行之是宋代诗人，代表作有《挽黄承事三首》。"
        print(f"输入文本: {text}")

        try:
            tok = hanlp.load(hanlp.pretrained.tok.COARSE_ELECTRA_SMALL_ZH)
            tokens = tok(text)
            print(f"分词结果: {tokens}")
        except Exception as e:
            print(f"[!] 分词失败: {e}")
            return False

        print("\n测试 2: 诗词分词")
        print("-" * 40)
        poem = "十年徒有梦追随"
        print(f"输入文本: {poem}")

        try:
            tokens = tok(poem)
            print(f"分词结果: {tokens}")
        except Exception as e:
            print(f"[!] 分词失败: {e}")
            return False

        print("\n测试 3: 繁体分词")
        print("-" * 40)
        text = "廖行之是宋代詩人"
        print(f"输入文本: {text}")

        try:
            tok_trad = hanlp.load(hanlp.pretrained.tok.COARSE_ELECTRA_SMALL_ZH)
            tokens = tok_trad(text)
            print(f"分词结果: {tokens}")
        except Exception as e:
            print(f"[!] 分词失败: {e}")
            return False

        print("\n[OK] HanLP 分词测试完成")
        return True

    except ImportError:
        print("\n[!] HanLP 未安装")
        print("   安装命令: pip install hanlp")
        return False
    except Exception as e:
        print(f"\n[!] HanLP 分词测试失败: {e}")
        return False


def test_hanlp_ner():
    """测试 HanLP 命名实体识别"""
    print("\n" + "="*60)
    print("测试 HanLP NER")
    print("="*60)

    try:
        import hanlp

        print(f"\nHanLP 版本: {hanlp.__version__}")

        print("\n测试 1: 基础 NER")
        print("-" * 40)
        text = "李白字太白，唐代著名诗人，代表作有《静夜思》。杜甫字子美，唐代诗人。"
        print(f"输入文本: {text}")

        try:
            ner = hanlp.load(hanlp.pretrained.ner.MSRA_NER_ELECTRA_SMALL_ZH)
            entities = ner(text)
            print(f"命名实体: {entities}")
        except Exception as e:
            print(f"[!] NER 失败: {e}")
            return False

        print("\n测试 2: 诗词作者识别")
        print("-" * 40)
        text = "廖行之，字景行，南宋诗人，衡阳人。"
        print(f"输入文本: {text}")

        try:
            entities = ner(text)
            print(f"命名实体: {entities}")
        except Exception as e:
            print(f"[!] NER 失败: {e}")
            return False

        print("\n测试 3: 朝代识别")
        print("-" * 40)
        text = "宋代诗人廖行之于南宋时期创作了《挽黄承事三首》。"
        print(f"输入文本: {text}")

        try:
            entities = ner(text)
            print(f"命名实体: {entities}")
        except Exception as e:
            print(f"[!] NER 失败: {e}")
            return False

        print("\n[OK] HanLP NER 测试完成")
        return True

    except Exception as e:
        print(f"\n[!] HanLP NER 测试失败: {e}")
        return False


def test_hanlp_dependency_parsing():
    """测试 HanLP 依存句法分析"""
    print("\n" + "="*60)
    print("测试 HanLP 依存句法分析")
    print("="*60)

    try:
        import hanlp

        print(f"\nHanLP 版本: {hanlp.__version__}")

        print("\n测试 1: 基础依存句法")
        print("-" * 40)
        text = "廖行之写了一首诗"
        print(f"输入文本: {text}")

        try:
            dep = hanlp.load(hanlp.pretrained.dep.CTB7_BIAFFINE_DEP_ZH)
            result = dep(text)
            print(f"依存句法: {result}")
        except Exception as e:
            print(f"[!] 依存句法分析失败: {e}")
            return False

        print("\n测试 2: 诗词依存句法")
        print("-" * 40)
        poem = "十年徒有梦追随"
        print(f"输入文本: {poem}")

        try:
            result = dep(poem)
            print(f"依存句法: {result}")
        except Exception as e:
            print(f"[!] 依存句法分析失败: {e}")
            return False

        print("\n[OK] HanLP 依存句法分析测试完成")
        return True

    except Exception as e:
        print(f"\n[!] HanLP 依存句法分析测试失败: {e}")
        return False


def test_hanlp_srl():
    """测试 HanLP 语义角色标注"""
    print("\n" + "="*60)
    print("测试 HanLP 语义角色标注")
    print("="*60)

    try:
        import hanlp

        print(f"\nHanLP 版本: {hanlp.__version__}")

        print("\n测试 1: 基础语义角色标注")
        print("-" * 40)
        text = "廖行之写了一首诗"
        print(f"输入文本: {text}")

        try:
            srl = hanlp.load(hanlp.pretrained.srl.CPB3_SRL_ELECTRA_SMALL)
            result = srl(text)
            print(f"语义角色标注: {result}")
        except Exception as e:
            print(f"[!] 语义角色标注失败: {e}")
            return False

        print("\n[OK] HanLP 语义角色标注测试完成")
        return True

    except Exception as e:
        print(f"\n[!] HanLP 语义角色标注测试失败: {e}")
        return False


def test_hanlp_multi_task():
    """测试 HanLP 多任务联合模型"""
    print("\n" + "="*60)
    print("测试 HanLP 多任务联合模型")
    print("="*60)

    try:
        import hanlp

        print(f"\nHanLP 版本: {hanlp.__version__}")

        print("\n测试 1: 分词 + NER 联合")
        print("-" * 40)
        text = "李白字太白，唐代著名诗人，代表作有《静夜思》。"
        print(f"输入文本: {text}")

        try:
            tok = hanlp.load(hanlp.pretrained.tok.COARSE_ELECTRA_SMALL_ZH)
            ner = hanlp.load(hanlp.pretrained.ner.MSRA_NER_ELECTRA_SMALL_ZH)
            tokens = tok(text)
            entities = ner(tokens)
            print(f"分词结果: {tokens}")
            print(f"命名实体: {entities}")
        except Exception as e:
            print(f"[!] 多任务失败: {e}")
            return False

        print("\n[OK] HanLP 多任务联合模型测试完成")
        return True

    except Exception as e:
        print(f"\n[!] HanLP 多任务联合模型测试失败: {e}")
        return False


def main():
    """主函数"""
    print("="*60)
    print("HanLP 综合测试")
    print(f"测试诗歌: {SAMPLE_POEM['title']}")
    print(f"作者: {SAMPLE_POEM['author']} ({SAMPLE_POEM['dynasty']})")
    print("="*60)

    results = {}
    results['分词'] = test_hanlp_tokenization()
    results['NER'] = test_hanlp_ner()
    results['依存句法'] = test_hanlp_dependency_parsing()
    results['语义角色标注'] = test_hanlp_srl()
    results['多任务联合'] = test_hanlp_multi_task()

    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    for name, result in results.items():
        status = "[OK] 通过" if result else "[X] 失败"
        print(f"  {name}: {status}")

    print("\n所有测试完成!")


if __name__ == "__main__":
    main()
