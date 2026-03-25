"""
script: 99_wordfreq_distribution.py
stage: P2-分析验证
artifact: 词频分布分析图与统计
purpose: 分析词频分布并输出统计指标与图表。
inputs:
- results/wordcount/wordfreq.csv
outputs:
- results/wordcount
- results/wordfreq_analysis
depends_on:
- 03_wordcount.py
develop_date: 2026-03-15
last_modified_date: 2026-03-25
"""
import csv
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
def load_wordfreq(csv_path: str):
    """加载词频数据"""
    counts = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            counts.append(int(row['count']))
    return counts
def main():
    csv_path = "results/wordcount/wordfreq.csv"
    print("=" * 60)
    print("词频分布分析")
    print("=" * 60)
    print("\n加载数据...")
    counts = load_wordfreq(csv_path)
    counts.sort(reverse=True)
    total_words = sum(counts)
    unique_words = len(counts)
    print(f"总词数: {total_words:,}")
    print(f"不同词数: {unique_words:,}")
    counts_array = np.array(counts, dtype=np.float64)
    print("\n" + "=" * 60)
    print("基本统计")
    print("=" * 60)
    print(f"最大词频: {counts[0]:,}")
    print(f"最小词频: {counts[-1]:,}")
    print(f"平均词频: {total_words / unique_words:.2f}")
    print(f"中位数词频: {np.median(counts_array):.0f}")
    percentiles = [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99]
    print("\n" + "=" * 60)
    print("词频累积分布")
    print("=" * 60)
    print(f"{'百分位':<10} {'词频阈值':<15} {'覆盖词数':<15} {'覆盖率':<10}")
    print("-" * 50)
    total_coverage = 0
    for p in percentiles:
        idx = int(unique_words * p / 100) - 1
        if idx < 0:
            idx = 0
        threshold = counts[idx]
        coverage = sum(counts[:idx+1]) / total_words * 100
        print(f"前{p}%{'':<6} >= {threshold:<12,} {idx+1:<15,} {coverage:.2f}%")
    print("\n" + "=" * 60)
    print("按词频区间统计")
    print("=" * 60)
    ranges = [
        (1, 1, "=1"),
        (2, 5, "2-5"),
        (6, 10, "6-10"),
        (11, 50, "11-50"),
        (51, 100, "51-100"),
        (101, 1000, "101-1K"),
        (1001, 10000, "1K-10K"),
        (10001, float('inf'), ">10K"),
    ]
    print(f"{'区间':<15} {'词数':<15} {'占比':<10}")
    print("-" * 40)
    for low, high, label in ranges:
        if high == float('inf'):
            in_range = [c for c in counts if c >= low]
        else:
            in_range = [c for c in counts if low <= c <= high]
        pct = len(in_range) / unique_words * 100
        print(f"{label:<15} {len(in_range):<15,} {pct:.2f}%")
    print("\n" + "=" * 60)
    print("绘制分布图...")
    print("=" * 60)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Chinese Poetry Word Frequency Distribution', fontsize=14)
    ax1 = axes[0, 0]
    ax1.plot(range(1, unique_words + 1), counts, linewidth=0.5)
    ax1.set_xlabel('Rank')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Zipf\'s Law: Word Frequency vs Rank')
    ax1.set_xscale('log')
    ax1.set_yscale('log')
    ax1.grid(True, alpha=0.3)
    ax2 = axes[0, 1]
    ax2.hist(counts, bins=100, edgecolor='black', alpha=0.7)
    ax2.set_xlabel('Frequency')
    ax2.set_ylabel('Number of Words')
    ax2.set_title('Word Frequency Histogram')
    ax2.set_yscale('log')
    ax2.grid(True, alpha=0.3)
    cumulative = np.cumsum(counts) / total_words * 100
    ax3 = axes[1, 0]
    ax3.plot(range(1, unique_words + 1), cumulative, linewidth=1)
    ax3.set_xlabel('Rank (cumulative %)')
    ax3.set_ylabel('Coverage (%)')
    ax3.set_title('Cumulative Coverage')
    ax3.axhline(y=50, color='r', linestyle='--', alpha=0.5)
    ax3.axhline(y=80, color='g', linestyle='--', alpha=0.5)
    ax3.axhline(y=90, color='orange', linestyle='--', alpha=0.5)
    ax3.grid(True, alpha=0.3)
    for p in [50, 80, 90]:
        idx = int(unique_words * p / 100) - 1
        ax3.axvline(x=idx, color='gray', linestyle=':', alpha=0.3)
    ax4 = axes[1, 1]
    x_percentile = np.array(range(0, 101))
    y_freq = []
    for p in x_percentile:
        idx = int(unique_words * p / 100)
        if idx == 0:
            idx = 1
        idx = min(idx, unique_words) - 1
        y_freq.append(counts[idx])
    ax4.plot(x_percentile, y_freq, linewidth=2)
    ax4.set_xlabel('Top X % Words')
    ax4.set_ylabel('Minimum Frequency in Range')
    ax4.set_title('Frequency Threshold by Percentile')
    ax4.set_yscale('log')
    ax4.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('results/wordcount/frequency_distribution.png', dpi=150)
    print("图片已保存: results/wordcount/frequency_distribution.png")
    print("\n" + "=" * 60)
    print("关键发现")
    print("=" * 60)
    p50_idx = int(unique_words * 0.5)
    p90_idx = int(unique_words * 0.9)
    p99_idx = int(unique_words * 0.99)
    print(f"• 前50%的词，词频 >= {counts[p50_idx]}")
    print(f"• 前90%的词，词频 >= {counts[p90_idx]}")
    print(f"• 前99%的词，词频 >= {counts[p99_idx]}")
    coverage_50 = sum(counts[:p50_idx]) / total_words * 100
    coverage_90 = sum(counts[:p90_idx]) / total_words * 100
    coverage_99 = sum(counts[:p99_idx]) / total_words * 100
    print(f"\n• 前50%高频词覆盖了 {coverage_50:.1f}% 的总词次")
    print(f"• 前90%高频词覆盖了 {coverage_90:.1f}% 的总词次")
    print(f"• 前99%高频词覆盖了 {coverage_99:.1f}% 的总词次")
    print("\n" + "=" * 60)
if __name__ == "__main__":
    main()
