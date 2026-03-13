#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 20: 完整数据索引构建与测试
构建所有索引文件并生成性能测试报告
"""

import json
import sys
import time
import gzip
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import pandas as pd

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def get_file_size(file_path: Path) -> float:
    """获取文件大小（MB）"""
    return file_path.stat().st_size / (1024 * 1024)


def build_all_indexes():
    """构建所有索引"""
    print("=" * 70)
    print("Task 20: 完整数据索引构建与测试")
    print("=" * 70)
    print()
    
    start_time = time.time()
    results = []
    
    # 1. 搜索索引
    print("【1/5】构建搜索索引...")
    try:
        from build_search_index import main as build_search
        build_search()
        results.append(("搜索索引", True, None))
    except Exception as e:
        results.append(("搜索索引", False, str(e)))
        print(f"  ❌ 失败: {e}")
    print()
    
    # 2. 词汇相似度索引
    print("【2/5】构建词汇相似度索引...")
    try:
        from build_word_similarity_index import main as build_word_sim
        build_word_sim()
        results.append(("词汇相似度索引", True, None))
    except Exception as e:
        results.append(("词汇相似度索引", False, str(e)))
        print(f"  ❌ 失败: {e}")
    print()
    
    # 3. 作者相似度索引
    print("【3/5】构建作者相似度索引...")
    try:
        from build_author_similarity_index import main as build_author_sim
        build_author_sim()
        results.append(("作者相似度索引", True, None))
    except Exception as e:
        results.append(("作者相似度索引", False, str(e)))
        print(f"  ❌ 失败: {e}")
    print()
    
    # 4. 词性标注索引
    print("【4/5】构建词性标注索引...")
    try:
        from build_pos_index import main as build_pos
        build_pos()
        results.append(("词性标注索引", True, None))
    except Exception as e:
        results.append(("词性标注索引", False, str(e)))
        print(f"  ❌ 失败: {e}")
    print()
    
    # 5. 推荐系统索引
    print("【5/5】构建推荐系统索引...")
    try:
        from build_recommendation_index import main as build_rec
        build_rec()
        results.append(("推荐系统索引", True, None))
    except Exception as e:
        results.append(("推荐系统索引", False, str(e)))
        print(f"  ❌ 失败: {e}")
    print()
    
    end_time = time.time()
    total_time = end_time - start_time
    
    return results, total_time


def analyze_index_files() -> Dict:
    """分析所有索引文件"""
    index_dir = project_root / "data" / "output" / "web" / "index"
    
    index_files = {
        "search_index.json": "搜索索引",
        "author_index.json": "作者索引",
        "dynasty_index.json": "朝代索引",
        "word_similarity_index.json": "词汇相似度索引",
        "author_similarity_index.json": "作者相似度索引",
        "author_network.json": "作者网络图数据",
        "pos_index.json": "词性标注索引",
        "recommendation_index.json": "推荐系统索引"
    }
    
    analysis = {
        "files": [],
        "total_size": 0,
        "total_compressed_size": 0
    }
    
    for filename, description in index_files.items():
        file_path = index_dir / filename
        compressed_path = index_dir / f"{filename}.gz"
        
        if file_path.exists():
            size = get_file_size(file_path)
            analysis["total_size"] += size
            
            compressed_size = 0
            if compressed_path.exists():
                compressed_size = get_file_size(compressed_path)
                analysis["total_compressed_size"] += compressed_size
            
            # 读取文件获取条目数
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 根据不同文件类型统计条目数
                if "total_terms" in data:
                    entries = data["total_terms"]
                elif "total_words" in data:
                    entries = data["total_words"]
                elif "total_authors" in data:
                    entries = data["total_authors"]
                elif "total_poems" in data:
                    entries = data["total_poems"]
                else:
                    entries = len(data.get("recommendations", {}))
                    
            except:
                entries = "N/A"
            
            analysis["files"].append({
                "name": filename,
                "description": description,
                "size_mb": round(size, 2),
                "compressed_size_mb": round(compressed_size, 2) if compressed_size else 0,
                "compression_ratio": round((1 - compressed_size/size) * 100, 1) if compressed_size else 0,
                "entries": entries
            })
    
    return analysis


def generate_performance_report(results: List, total_time: float, analysis: Dict):
    """生成性能测试报告"""
    report = []
    report.append("=" * 70)
    report.append("索引构建性能报告")
    report.append("=" * 70)
    report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"总构建时间: {total_time:.2f} 秒")
    report.append("")
    
    # 构建结果
    report.append("【构建结果】")
    success_count = sum(1 for _, success, _ in results if success)
    report.append(f"成功: {success_count}/{len(results)}")
    report.append("")
    
    for name, success, error in results:
        status = "✅ 成功" if success else f"❌ 失败: {error}"
        report.append(f"  {name}: {status}")
    report.append("")
    
    # 文件分析
    report.append("【索引文件分析】")
    report.append(f"总文件数: {len(analysis['files'])}")
    report.append(f"总大小: {analysis['total_size']:.2f} MB")
    report.append(f"压缩后总大小: {analysis['total_compressed_size']:.2f} MB")
    report.append(f"总压缩率: {(1 - analysis['total_compressed_size']/analysis['total_size'])*100:.1f}%")
    report.append("")
    
    report.append("【文件详情】")
    report.append("-" * 70)
    report.append(f"{'文件名':<30} {'大小(MB)':<12} {'压缩后':<12} {'压缩率':<10} {'条目数':<10}")
    report.append("-" * 70)
    
    for file_info in analysis["files"]:
        report.append(
            f"{file_info['name']:<30} "
            f"{file_info['size_mb']:<12.2f} "
            f"{file_info['compressed_size_mb']:<12.2f} "
            f"{file_info['compression_ratio']:<10.1f}% "
            f"{str(file_info['entries']):<10}"
        )
    
    report.append("-" * 70)
    report.append("")
    
    # 性能目标检查
    report.append("【性能目标检查】")
    targets = [
        ("索引文件总大小 < 100MB", analysis['total_size'] < 100),
        ("压缩后总大小 < 50MB", analysis['total_compressed_size'] < 50),
        ("构建时间 < 600秒", total_time < 600),
    ]
    
    for target, passed in targets:
        status = "✅ 通过" if passed else "❌ 未通过"
        report.append(f"  {target}: {status}")
    report.append("")
    
    # 建议
    report.append("【优化建议】")
    if analysis['total_size'] > 100:
        report.append("  - 索引文件总大小超过100MB，建议增加压缩率或分层加载")
    if total_time > 600:
        report.append("  - 构建时间超过10分钟，建议优化构建脚本性能")
    report.append("  - 建议启用Gzip压缩传输")
    report.append("  - 建议实施懒加载策略")
    report.append("")
    
    report.append("=" * 70)
    
    return "\n".join(report)


def save_report(report: str):
    """保存报告到文件"""
    report_dir = project_root / "docs" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = report_dir / f"index_build_report_{timestamp}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n报告已保存: {report_file}")


def main():
    """主函数"""
    print("开始构建所有索引...\n")
    
    # 构建所有索引
    results, total_time = build_all_indexes()
    
    # 分析索引文件
    print("分析索引文件...")
    analysis = analyze_index_files()
    
    # 生成报告
    report = generate_performance_report(results, total_time, analysis)
    
    # 打印报告
    print("\n" + report)
    
    # 保存报告
    save_report(report)
    
    # 检查是否全部成功
    success_count = sum(1 for _, success, _ in results if success)
    if success_count == len(results):
        print("\n✅ Task 20 完成! 所有索引构建成功")
        return 0
    else:
        print(f"\n⚠️ Task 20 部分完成: {success_count}/{len(results)} 个索引构建成功")
        return 1


if __name__ == '__main__':
    sys.exit(main())
