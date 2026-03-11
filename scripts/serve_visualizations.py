#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地静态网页服务器
用于预览可视化结果
"""

import sys
import argparse
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser
import socket


def get_free_port(start_port=8000, max_port=9000):
    """获取可用端口"""
    for port in range(start_port, max_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    raise RuntimeError("No free ports available")


def create_handler(visualizations_dir: Path):
    """创建自定义请求处理器"""
    class VisualizationHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(visualizations_dir), **kwargs)
        
        def log_message(self, format, *args):
            """自定义日志格式"""
            print(f"[{self.log_date_time_string()}] {args[0]}")
        
        def end_headers(self):
            """添加CORS头"""
            self.send_header('Access-Control-Allow-Origin', '*')
            super().end_headers()
    
    return VisualizationHandler


def serve(visualizations_dir: Path, port: int = None, open_browser: bool = True):
    """
    启动静态文件服务器
    
    Args:
        visualizations_dir: 可视化文件目录
        port: 端口号（None则自动选择）
        open_browser: 是否自动打开浏览器
    """
    if port is None:
        port = get_free_port()
    
    handler = create_handler(visualizations_dir)
    
    with HTTPServer(('', port), handler) as httpd:
        url = f"http://localhost:{port}"
        print("=" * 60)
        print("可视化报告服务器已启动")
        print("=" * 60)
        print(f"\n访问地址: {url}")
        print(f"文件目录: {visualizations_dir}")
        print("\n按 Ctrl+C 停止服务器")
        print("=" * 60)
        
        if open_browser:
            # 延迟打开浏览器，确保服务器已启动
            import threading
            def open_browser_delayed():
                import time
                time.sleep(1)
                webbrowser.open(url)
            
            threading.Thread(target=open_browser_delayed, daemon=True).start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n服务器已停止")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='启动可视化报告本地服务器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python serve_visualizations.py              # 自动选择端口
  python serve_visualizations.py -p 8080      # 指定端口8080
  python serve_visualizations.py --no-browser # 不自动打开浏览器
        '''
    )
    
    parser.add_argument(
        '-p', '--port',
        type=int,
        default=None,
        help='服务器端口号（默认自动选择）'
    )
    
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='不自动打开浏览器'
    )
    
    parser.add_argument(
        '--dir',
        type=str,
        default=None,
        help='可视化文件目录（默认 reports/visualizations）'
    )
    
    args = parser.parse_args()
    
    # 设置路径
    if args.dir:
        visualizations_dir = Path(args.dir)
    else:
        project_root = Path(__file__).parent.parent
        visualizations_dir = project_root / "reports" / "visualizations"
    
    if not visualizations_dir.exists():
        print(f"错误: 目录不存在 {visualizations_dir}")
        print("请先运行可视化脚本生成报告")
        return 1
    
    # 检查是否有HTML文件
    html_files = list(visualizations_dir.glob("*.html"))
    if not html_files:
        print(f"警告: 目录中没有HTML文件 {visualizations_dir}")
        print("请先运行: python scripts/03_vis_*.py")
    else:
        print(f"找到 {len(html_files)} 个可视化文件")
    
    # 启动服务器
    serve(visualizations_dir, args.port, not args.no_browser)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
