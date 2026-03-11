#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成本地完整可视化（包含完整数据处理）
用于在本地生成所有可视化，然后手动部署到 GitHub Pages
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))


def run_script(script_name: str, description: str) -> bool:
    """运行脚本并返回是否成功"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            [sys.executable, f"scripts/{script_name}"],
            cwd=Path(__file__).parent.parent,
            check=True,
            capture_output=False
        )
        print(f"✓ {script_name} 完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {script_name} 失败: {e}")
        return False


def main():
    """主函数"""
    print("="*60)
    print("生成完整可视化报告")
    print("="*60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    scripts = [
        # 数据处理（可选：如果数据已存在可以跳过）
        ("01_data_process.py", "步骤 1/9: 数据处理（完整33万首）"),
        
        # 分析脚本
        ("02_analysis_sentiment.py", "步骤 2/9: 情感分析"),
        ("02_analysis_network.py", "步骤 3/9: 社交网络分析"),
        ("02_analysis_meter.py", "步骤 4/9: 格律分析"),
        
        # 可视化脚本
        ("03_vis_sentiment.py", "步骤 5/9: 情感可视化"),
        ("03_vis_network.py", "步骤 6/9: 社交网络可视化"),
        ("03_vis_meter.py", "步骤 7/9: 格律可视化"),
        ("03_vis_dynasty.py", "步骤 8/9: 朝代可视化"),
        ("03_vis_author.py", "步骤 9/9: 诗人可视化"),
        
        # 构建索引
        ("build_index.py", "构建索引页面"),
    ]
    
    success_count = 0
    failed_scripts = []
    
    for script, desc in scripts:
        if run_script(script, desc):
            success_count += 1
        else:
            failed_scripts.append(script)
    
    # 总结
    print(f"\n{'='*60}")
    print("生成完成")
    print(f"{'='*60}")
    print(f"成功: {success_count}/{len(scripts)}")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if failed_scripts:
        print(f"\n失败的脚本:")
        for script in failed_scripts:
            print(f"  - {script}")
    else:
        print(f"\n✓ 所有脚本运行成功！")
        print(f"\n可视化文件位置: reports/visualizations/")
        print(f"索引页面: reports/visualizations/index.html")
        print(f"\n本地预览:")
        print(f"  python scripts/serve_visualizations.py")
        print(f"\n部署到 GitHub Pages:")
        print(f"  1. 提交更改: git add reports/visualizations/ && git commit -m 'Update visualizations'")
        print(f"  2. 推送: git push origin main")
        print(f"  3. 在 GitHub 设置中启用 Pages（如果还没启用）")
    
    print("="*60)
    
    return 0 if not failed_scripts else 1


if __name__ == "__main__":
    sys.exit(main())
