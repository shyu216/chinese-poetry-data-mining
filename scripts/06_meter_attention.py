#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版格律注意力机制
功能：
1. 计算诗句中每个字的格律权重
2. 识别押韵位置
3. 识别平仄模式
4. 可视化展示
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import re
from pathlib import Path
from typing import List, Dict, Tuple
import json


class MeterAttention:
    """格律注意力机制 - 简化版"""
    
    def __init__(self):
        # 简化的平仄映射（基于常见汉字）
        self.pingze_map = self._build_pingze_map()
        
        # 常见韵部（简化版）
        self.rhyme_groups = self._build_rhyme_groups()
    
    def _build_pingze_map(self) -> Dict:
        """构建简化的平仄映射"""
        # 常见汉字的平仄（简化版，基于声旁）
        ping_chars = set('天地人和日月星辰山河湖海风云雨雪花草木鸟虫鱼虫龙凤龟麒麟珠玉金银铜铁石玉竹松柏杨柳桃花杏花荷花菊花梅花兰草虫鸟雀鸦鹭鸿鹤鸽鸾凤蝴螺蜻蜓蝴蝶蜂蚁蛛')
        ze_chars = set('竹菊墨色白黑赤黄青紫红绿蓝灰白帛玉屋木石竹笛笔墨纸绢丝弦声曲调乐歌诗赋词章经史子集圣贤君子丈夫女儿父母兄弟夫妇姊妹翁姑舅姨亲友宾客主人翁')
        
        return {'平': ping_chars, '仄': ze_chars}
    
    def _build_rhyme_groups(self) -> Dict:
        """构建韵部"""
        return {
            '平声韵': set('山花烟天年弦仙泉川前田眠船钱元喧原冤泉然宣迁篇砖悬圆员捐鞭'),
            '仄声韵': set('雨府树路去故步素暮渡午女浦武苦鲁橹卤'),
        }
    
    def get_pingze(self, char: str) -> str:
        """判断单个字的平仄"""
        if char in self.pingze_map['平']:
            return '平'
        elif char in self.pingze_map['仄']:
            return '仄'
        return '中'
    
    def analyze_line(self, line: str) -> Dict:
        """分析单句诗的格律"""
        result = {
            'text': line,
            'length': len(line),
            'pingze': [self.get_pingze(c) for c in line],
            'rhyme_pos': [],
            'attention_weights': [],
        }
        
        # 计算注意力权重
        weights = []
        for i, char in enumerate(line):
            weight = 1.0
            
            # 句尾字权重最高（押韵位置）
            if i == len(line) - 1:
                weight = 1.5
            # 偶数位置（2,4,6）通常更重要
            elif (i + 1) % 2 == 0:
                weight = 1.2
            
            weights.append(weight)
        
        # 归一化权重
        total = sum(weights)
        result['attention_weights'] = [w / total * len(weights) for w in weights]
        
        # 识别押韵位置（句尾）
        result['rhyme_pos'] = [len(line) - 1]
        
        return result
    
    def analyze_poem(self, lines: List[str]) -> Dict:
        """分析整首诗的格律"""
        result = {
            'lines': [],
            'meter_pattern': ','.join([str(len(l)) for l in lines]),
            'total_lines': len(lines),
            'is_regular': self._check_regular(lines),
            'cross_line_rhyme': self._check_rhyme(lines),
        }
        
        for line in lines:
            line_analysis = self.analyze_line(line)
            result['lines'].append(line_analysis)
        
        return result
    
    def _check_regular(self, lines: List[str]) -> bool:
        """检查是否格律诗"""
        if len(lines) < 2:
            return False
        
        lengths = [len(l) for l in lines if l]
        return len(set(lengths)) == 1
    
    def _check_rhyme(self, lines: List[str]) -> bool:
        """检查是否押韵（简化版）"""
        if len(lines) < 2:
            return False
        
        # 检查偶数句是否押韵
        rhyme_chars = []
        for i in range(1, len(lines), 2):
            if lines[i]:
                rhyme_chars.append(lines[i][-1])
        
        # 简化判断：句尾字相同或音近
        return len(set(rhyme_chars[:4])) <= 2


def visualize_attention(analysis: Dict) -> str:
    """可视化格律注意力"""
    output = []
    output.append("=" * 60)
    output.append("格律注意力分析")
    output.append("=" * 60)
    output.append(f"格律模式: {analysis['meter_pattern']}")
    output.append(f"总句数: {analysis['total_lines']}")
    output.append(f"格律诗: {'✓ 是' if analysis['is_regular'] else '○ 否'}")
    output.append("")
    
    for i, line_data in enumerate(analysis['lines']):
        line = line_data['text']
        weights = line_data['attention_weights']
        
        output.append(f"【第{i+1}句】 {line}")
        
        # 可视化权重
        viz = ""
        for j, (char, weight) in enumerate(zip(line, weights)):
            if weight > 1.3:
                viz += f"[{char}]"
            elif weight > 1.0:
                viz += f"({char})"
            else:
                viz += char
        
        output.append(f"  注意力: {viz}")
        
        # 平仄
        pingze = line_data['pingze']
        pz_str = " ".join(pingze)
        output.append(f"  平仄:   {pz_str}")
        output.append("")
    
    return "\n".join(output)


def visualize_html(analysis: Dict) -> str:
    """生成HTML可视化"""
    html_parts = []
    
    for i, line_data in enumerate(analysis['lines']):
        line = line_data['text']
        weights = line_data['attention_weights']
        
        # 根据权重设置颜色
        chars_html = ""
        for char, weight in zip(line, weights):
            if weight > 1.3:
                # 句尾 - 高亮
                chars_html += f'<span class="attention-high">{char}</span>'
            elif weight > 1.0:
                # 偶数位 - 中等
                chars_html += f'<span class="attention-mid">{char}</span>'
            else:
                chars_html += f'<span>{char}</span>'
        
        html_parts.append(f'<div class="line">{chars_html}</div>')
    
    return "\n".join(html_parts)


def demo():
    """演示"""
    attention = MeterAttention()
    
    # 测试诗词
    poems = [
        ["床前明月光", "疑是地上霜", "举头望明月", "低头思故乡"],  # 五言绝句
        ["秦川雄帝宅", "函谷壮皇居", "绮殿千寻起", "离宫百雉余"],  # 七言绝句
        ["国破山河在", "城春草木深", "感时花溅泪", "恨别鸟惊心"],  # 五言律诗
    ]
    
    for i, poem in enumerate(poems):
        print(f"\n{'='*60}")
        print(f"示例 {i+1}: {poem[0][:5]}...")
        print('='*60)
        
        analysis = attention.analyze_poem(poem)
        print(visualize_attention(analysis))


if __name__ == "__main__":
    demo()
