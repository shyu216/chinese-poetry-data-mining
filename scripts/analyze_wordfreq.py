"""分析词频数据特点"""
import csv
import os
from pathlib import Path

f = open('results/wordcount/wordfreq.csv', 'r', encoding='utf-8')
r = csv.reader(f)
next(r)

# 统计词频分布
counts = []
words = []
for row in r:
    words.append(row[0])
    counts.append(int(row[1]))

print(f'总词数: {len(counts):,}')
print(f'最高频词出现次数: {max(counts):,}')
print(f'最低频词出现次数: {min(counts)}')

# 词频分段统计
print('\n=== 词频分布 ===')
ranges = [
    (1, 1, '出现1次'),
    (2, 2, '出现2次'),
    (3, 5, '出现3-5次'),
    (6, 10, '出现6-10次'),
    (11, 100, '出现11-100次'),
    (101, 1000, '出现101-1000次'),
    (1001, 10000, '出现1001-10000次'),
    (10001, 100000, '出现10001-100000次'),
]

for min_c, max_c, label in ranges:
    c = sum(1 for x in counts if min_c <= x <= max_c)
    pct = c / len(counts) * 100
    print(f'{label}: {c:,} ({pct:.1f}%)')

# 高频词（出现>100次）
high_freq = sum(1 for x in counts if x > 100)
print(f'\n高频词(>100次): {high_freq:,} ({high_freq/len(counts)*100:.1f}%)')

# 文件大小
size = os.path.getsize('results/wordcount/wordfreq.csv')
print(f'\nCSV文件大小: {size / 1024 / 1024:.2f} MB')

# 估算内存占用
# 每个词平均长度约3字节(UTF-8中文) + count(4字节) + overhead
avg_word_len = sum(len(w.encode('utf-8')) for w in words) / len(words)
print(f'平均词长度: {avg_word_len:.1f} 字节')

# 估算FlatBuffers大小
# 每个entry: word(string) + count(int) + overhead
entry_size = avg_word_len + 4 + 8  # 粗略估算
estimated_fbs = len(counts) * entry_size
print(f'估算FlatBuffers大小: {estimated_fbs / 1024 / 1024:.2f} MB')
