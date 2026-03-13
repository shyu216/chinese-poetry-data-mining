"""
Pipeline Orchestrator - 管线统一入口

功能:
1. 管理所有处理步骤
2. 支持增量执行和强制重跑
3. 生成执行日志
4. 处理步骤依赖关系

用法:
    python scripts/pipeline.py --steps clean structure words similarity --data sample
    python scripts/pipeline.py --all --data full --force
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from src.config import get_settings


# 步骤定义
STEPS = {
    "clean": {
        "script": "scripts/steps/01_clean.py",
        "description": "Bronze层数据清洗",
        "depends_on": [],
        "output": "data/bronze/v1_poems_merged.csv"
    },
    "structure": {
        "script": "scripts/steps/02_structure.py",
        "description": "Silver层结构化处理",
        "depends_on": ["clean"],
        "output": "data/silver/v2_poems_structured.csv"
    },
    "words": {
        "script": "scripts/steps/03_analyze_words.py",
        "description": "词汇频率分析",
        "depends_on": ["structure"],
        "output": "data/gold/v3_word_frequency.json"
    },
    "similarity": {
        "script": "scripts/steps/04_analyze_similarity.py",
        "description": "文本相似度分析",
        "depends_on": ["structure", "words"],
        "output": "data/gold/v3_text_similarity.json"
    },
    "export": {
        "script": "scripts/export/web.py",
        "description": "导出Web数据",
        "depends_on": ["structure"],
        "output": "data/output/web/manifest.json"
    }
}


def run_step(step_name: str, data: str, force: bool) -> bool:
    """执行单个步骤
    
    Args:
        step_name: 步骤名称
        data: 数据类型 (sample/full)
        force: 是否强制重跑
        
    Returns:
        bool: 是否成功
    """
    step_info = STEPS.get(step_name)
    if not step_info:
        print(f"错误: 未知步骤 {step_name}")
        return False
    
    script_path = Path(step_info["script"])
    if not script_path.exists():
        print(f"错误: 脚本不存在 {script_path}")
        return False
    
    # 检查输出是否已存在
    output_path = Path(step_info["output"])
    if not force and output_path.exists():
        print(f"跳过: {step_name} (已存在: {output_path})")
        return True
    
    print(f"\n{'='*50}")
    print(f"执行: {step_name}")
    print(f"描述: {step_info['description']}")
    print(f"{'='*50}\n")
    
    # 构建命令
    cmd = f"python {script_path} --data {data}"
    if force:
        cmd += " --force"
    
    # 执行
    import subprocess
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode != 0:
        print(f"错误: {step_name} 执行失败")
        return False
    
    print(f"\n完成: {step_name}")
    return True


def resolve_dependencies(steps: List[str]) -> List[str]:
    """解析步骤依赖关系
    
    Args:
        steps: 用户指定的步骤列表
        
    Returns:
        List[str]: 按依赖顺序排列的步骤列表
    """
    resolved = []
    visited = set()
    
    def visit(step_name: str):
        if step_name in visited:
            return
        if step_name not in STEPS:
            print(f"警告: 未知步骤 {step_name}")
            return
        
        # 先处理依赖
        for dep in STEPS[step_name]["depends_on"]:
            visit(dep)
        
        visited.add(step_name)
        resolved.append(step_name)
    
    for step in steps:
        visit(step)
    
    return resolved


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline Orchestrator - 管线统一入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 执行所有步骤（采样数据）
  python scripts/pipeline.py --all
  
  # 执行指定步骤
  python scripts/pipeline.py --steps clean structure --data sample
  
  # 强制重跑
  python scripts/pipeline.py --all --force
  
  # 完整数据处理
  python scripts/pipeline.py --all --data full

可用步骤:
  clean       - Bronze层数据清洗
  structure   - Silver层结构化处理
  words       - 词汇频率分析
  similarity  - 文本相似度分析
  export      - 导出Web数据
        """
    )
    
    parser.add_argument(
        "--steps",
        nargs="+",
        choices=list(STEPS.keys()),
        help="指定要执行的步骤"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="执行所有步骤"
    )
    parser.add_argument(
        "--data",
        choices=["sample", "full"],
        default="sample",
        help="处理数据集类型 (默认: sample)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新生成所有步骤"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_steps",
        help="列出所有可用步骤"
    )
    
    args = parser.parse_args()
    
    # 列出步骤
    if args.list_steps:
        print("可用步骤:")
        for name, info in STEPS.items():
            deps = ", ".join(info["depends_on"]) if info["depends_on"] else "无"
            print(f"  {name:12} - {info['description']}")
            print(f"               依赖: {deps}")
            print(f"               输出: {info['output']}")
        return
    
    # 确定要执行的步骤
    if args.all:
        steps_to_run = list(STEPS.keys())
    elif args.steps:
        steps_to_run = args.steps
    else:
        parser.print_help()
        return
    
    # 解析依赖
    resolved_steps = resolve_dependencies(steps_to_run)
    
    print("="*50)
    print("Pipeline Orchestrator")
    print("="*50)
    print(f"数据类型: {args.data}")
    print(f"强制重跑: {args.force}")
    print(f"执行步骤: {', '.join(resolved_steps)}")
    print("="*50)
    
    # 执行步骤
    start_time = datetime.now()
    failed_steps = []
    
    for step in resolved_steps:
        success = run_step(step, args.data, args.force)
        if not success:
            failed_steps.append(step)
            print(f"\n步骤 {step} 失败，停止执行")
            break
    
    # 总结
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "="*50)
    print("执行总结")
    print("="*50)
    print(f"总耗时: {duration:.2f} 秒")
    print(f"成功: {len(resolved_steps) - len(failed_steps)}/{len(resolved_steps)}")
    
    if failed_steps:
        print(f"失败: {', '.join(failed_steps)}")
        sys.exit(1)
    else:
        print("全部完成!")


if __name__ == "__main__":
    main()
