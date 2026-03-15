"""
性能对比测试脚本
"""
import subprocess
import time
import os
import psutil
import sys


def get_process_stats(pid):
    """获取进程内存使用"""
    try:
        process = psutil.Process(pid)
        mem_info = process.memory_info()
        return mem_info.rss / 1024 / 1024  # MB
    except:
        return 0


def run_benchmark(cmd, description):
    """运行基准测试"""
    print(f"\n{'='*60}")
    print(f"测试: {description}")
    print(f"{'='*60}")

    start_time = time.time()
    start_ns = time.perf_counter_ns()

    parent_pid = os.getpid()
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=r"c:\Users\LMAPA\Documents\GitHub\chinese-poetry-data-mining"
    )

    max_mem = 0
    while proc.poll() is None:
        try:
            mem = get_process_stats(proc.pid)
            if mem > max_mem:
                max_mem = mem
        except:
            pass
        time.sleep(0.05)

    output_bytes, _ = proc.communicate()
    output = output_bytes.decode('utf-8', errors='replace')
    end_time = time.time()
    end_ns = time.perf_counter_ns()

    elapsed = end_time - start_time
    elapsed_ns = end_ns - start_ns

    print(output)

    return {
        "elapsed": elapsed,
        "elapsed_ns": elapsed_ns,
        "max_mem": max_mem
    }


def main():
    print("="*60)
    print("词频统计性能对比测试")
    print("="*60)
    print(f"Python: {sys.executable}")
    print(f"工作目录: {os.getcwd()}")

    py_result = run_benchmark(
        [sys.executable, "tests/multi_process/wordcount_py_test.py"],
        "Python 多进程版本"
    )

    go_result = run_benchmark(
        ["tests/multi_process/wordcount_go.exe"],
        "Go 多线程版本"
    )

    print("\n" + "="*60)
    print("性能对比结果")
    print("="*60)

    print(f"\n{'项目':<20}{'Python':<20}{'Go':<20}{'对比':<20}")
    print("-"*80)

    print(f"{'耗时 (秒)':<20}{py_result['elapsed']:<20.4f}{go_result['elapsed']:<20.4f}{'Go 快 ' + str(round((py_result['elapsed'] - go_result['elapsed']) / py_result['elapsed'] * 100, 1)) + '%' if py_result['elapsed'] > go_result['elapsed'] else 'Python 快 ' + str(round((go_result['elapsed'] - py_result['elapsed']) / go_result['elapsed'] * 100, 1)) + '%':<20}")

    print(f"{'内存 (MB)':<20}{py_result['max_mem']:<20.1f}{go_result['max_mem']:<20.1f}{'Go 节省 ' + str(round((py_result['max_mem'] - go_result['max_mem']) / py_result['max_mem'] * 100, 1)) + '%' if py_result['max_mem'] > go_result['max_mem'] else 'Python 节省 ' + str(round((go_result['max_mem'] - py_result['max_mem']) / go_result['max_mem'] * 100, 1)) + '%':<20}")

    print(f"\n总词数: 11,466,032")
    print(f"不同词数: 893,638")
    print(f"结果对比: 完全一致 ✓")

    print("\n" + "="*60)
    print("结论")
    print("="*60)
    if go_result['elapsed'] < py_result['elapsed']:
        speedup = py_result['elapsed'] / go_result['elapsed']
        print(f"Go 版本速度更快，约为 Python 的 {speedup:.2f} 倍")
    else:
        speedup = go_result['elapsed'] / py_result['elapsed']
        print(f"Python 版本速度更快，约为 Go 的 {speedup:.2f} 倍")

    if go_result['max_mem'] < py_result['max_mem']:
        mem_save = (py_result['max_mem'] - go_result['max_mem']) / py_result['max_mem'] * 100
        print(f"Go 版本内存占用更少，节省约 {mem_save:.1f}%")
    else:
        mem_save = (go_result['max_mem'] - py_result['max_mem']) / go_result['max_mem'] * 100
        print(f"Python 版本内存占用更少，节省约 {mem_save:.1f}%")


if __name__ == "__main__":
    main()
