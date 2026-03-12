#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诗词知识库启动脚本
一键启动后端API服务和前端页面
"""
import sys
import os
import webbrowser
import time
import threading
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socket

PROJECT_ROOT = Path(__file__).parent.parent
HTML_FILE = PROJECT_ROOT / "data" / "poetry_knowledge_base.html"


def get_free_port(start_port=5000, max_port=9000):
    """获取可用端口"""
    for port in range(start_port, max_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    raise RuntimeError("No free ports available")


def serve_html(html_path: Path, port: int):
    """启动静态文件服务器"""
    os.chdir(html_path.parent)

    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            super().end_headers()

    server = HTTPServer(('', port), Handler)
    print(f"📄 前端页面: http://localhost:{port}/{html_path.name}")
    server.serve_forever()


def main():
    print("="*60)
    print("🚀 诗词知识库启动中...")
    print("="*60)

    api_port = get_free_port(5000)
    html_port = get_free_port(8000)

    print(f"\n📊 API服务端口: {api_port}")
    print(f"📄 前端页面端口: {html_port}")

    api_thread = threading.Thread(target=lambda: os.system(
        f'start python "{PROJECT_ROOT}/scripts/05_api_server.py" --port {api_port}'
    ))
    api_thread.start()

    time.sleep(2)

    html_thread = threading.Thread(target=lambda: serve_html(HTML_FILE, html_port))
    html_thread.start()

    time.sleep(1)

    print("\n" + "="*60)
    print("✅ 启动成功！")
    print("="*60)
    print(f"\n请在浏览器中打开:")
    print(f"   http://localhost:{html_port}/{HTML_FILE.name}")
    print(f"\nAPI地址: http://127.0.0.1:{api_port}/api")
    print("\n按 Ctrl+C 停止服务\n")

    try:
        html_thread.join()
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
        sys.exit(0)


if __name__ == "__main__":
    main()
