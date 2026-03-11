#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诗词数据可视化模块
集成 Plotly、Pyecharts、Dash 等可视化工具
应用场景：
- Plotly: 交互式图表（散点图、热力图、网络图）
- Pyecharts: 中文可视化（词云、地图、关系图）
- Dash: Web交互式仪表板
"""

from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
import json


class PoetryVisualizer:
    """诗词数据可视化器"""
    
    def __init__(self):
        self.plotly_available = False
        self.pyecharts_available = False
        self.dash_available = False
        self._check_libraries()
    
    def _check_libraries(self):
        """检查可用的可视化库"""
        try:
            import plotly
            self.plotly_available = True
        except ImportError:
            pass
        
        try:
            import pyecharts
            self.pyecharts_available = True
        except ImportError:
            pass
        
        try:
            import dash
            self.dash_available = True
        except ImportError:
            pass
        
        print(f"可视化库检查: Plotly={self.plotly_available}, Pyecharts={self.pyecharts_available}, Dash={self.dash_available}")
    
    # ========== Plotly 可视化 ==========
    
    def create_scatter_plot(self, data: List[Dict], x_key: str, y_key: str, 
                           color_key: Optional[str] = None, 
                           hover_keys: List[str] = None,
                           title: str = "散点图") -> Optional[Any]:
        """
        创建散点图
        
        Args:
            data: 数据列表
            x_key: X轴字段
            y_key: Y轴字段
            color_key: 颜色分组字段
            hover_keys: 悬停显示字段
            title: 图表标题
            
        Returns:
            Plotly图表对象
        """
        if not self.plotly_available:
            print("Plotly 未安装")
            return None
        
        import plotly.express as px
        import pandas as pd
        
        df = pd.DataFrame(data)
        
        fig = px.scatter(df, x=x_key, y=y_key, color=color_key,
                        hover_data=hover_keys,
                        title=title)
        
        return fig
    
    def create_heatmap(self, matrix: List[List[float]], 
                      labels: List[str],
                      title: str = "热力图") -> Optional[Any]:
        """
        创建热力图
        
        Args:
            matrix: 二维数据矩阵
            labels: 标签列表
            title: 图表标题
            
        Returns:
            Plotly图表对象
        """
        if not self.plotly_available:
            print("Plotly 未安装")
            return None
        
        import plotly.graph_objects as go
        
        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=labels,
            y=labels,
            colorscale='Viridis'
        ))
        
        fig.update_layout(title=title)
        return fig
    
    def create_network_graph(self, nodes: List[Dict], edges: List[Dict],
                            title: str = "网络图") -> Optional[Any]:
        """
        创建网络图
        
        Args:
            nodes: [{'id': 'node1', 'label': 'Node 1', 'size': 10}, ...]
            edges: [{'source': 'node1', 'target': 'node2', 'weight': 1}, ...]
            title: 图表标题
            
        Returns:
            Plotly图表对象
        """
        if not self.plotly_available:
            print("Plotly 未安装")
            return None
        
        import plotly.graph_objects as go
        import networkx as nx
        
        # 创建NetworkX图
        G = nx.Graph()
        
        for node in nodes:
            G.add_node(node['id'], label=node.get('label', node['id']), 
                      size=node.get('size', 10))
        
        for edge in edges:
            G.add_edge(edge['source'], edge['target'], 
                      weight=edge.get('weight', 1))
        
        # 计算布局
        pos = nx.spring_layout(G)
        
        # 创建边
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines')
        
        # 创建节点
        node_x = []
        node_y = []
        node_text = []
        node_size = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(G.nodes[node].get('label', node))
            node_size.append(G.nodes[node].get('size', 10))
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            textposition="top center",
            marker=dict(
                showscale=True,
                size=node_size,
                colorscale='YlGnBu',
                line_width=2))
        
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title=title,
                           showlegend=False,
                           hovermode='closest'))
        
        return fig
    
    def create_time_series(self, data: List[Dict], time_key: str, value_key: str,
                          group_key: Optional[str] = None,
                          title: str = "时间序列") -> Optional[Any]:
        """
        创建时间序列图
        
        Args:
            data: 数据列表
            time_key: 时间字段
            value_key: 数值字段
            group_key: 分组字段
            title: 图表标题
            
        Returns:
            Plotly图表对象
        """
        if not self.plotly_available:
            print("Plotly 未安装")
            return None
        
        import plotly.express as px
        import pandas as pd
        
        df = pd.DataFrame(data)
        
        fig = px.line(df, x=time_key, y=value_key, color=group_key,
                     title=title, markers=True)
        
        return fig
    
    # ========== Pyecharts 可视化 ==========
    
    def create_wordcloud(self, words: List[Tuple[str, int]], 
                        title: str = "词云") -> Optional[Any]:
        """
        创建词云图
        
        Args:
            words: [(词语, 频率), ...]
            title: 图表标题
            
        Returns:
            Pyecharts图表对象
        """
        if not self.pyecharts_available:
            print("Pyecharts 未安装，使用备用方法")
            return self._fallback_wordcloud(words, title)
        
        try:
            from pyecharts.charts import WordCloud
            from pyecharts import options as opts
            
            wc = WordCloud()
            wc.add("", words, word_size_range=[20, 100])
            wc.set_global_opts(title_opts=opts.TitleOpts(title=title))
            
            return wc
        except Exception as e:
            print(f"Pyecharts 词云创建失败: {e}")
            return self._fallback_wordcloud(words, title)
    
    def _fallback_wordcloud(self, words: List[Tuple[str, int]], title: str) -> Dict:
        """备用词云（返回数据）"""
        return {
            'type': 'wordcloud_data',
            'title': title,
            'words': words[:50]  # 返回前50个词
        }
    
    def create_china_map(self, data: List[Dict], 
                        location_key: str, value_key: str,
                        title: str = "中国地图") -> Optional[Any]:
        """
        创建中国地图
        
        Args:
            data: [{'location': '北京', 'value': 100}, ...]
            location_key: 地点字段
            value_key: 数值字段
            title: 图表标题
            
        Returns:
            Pyecharts图表对象
        """
        if not self.pyecharts_available:
            print("Pyecharts 未安装")
            return None
        
        try:
            from pyecharts.charts import Map
            from pyecharts import options as opts
            
            # 提取数据
            map_data = [(d[location_key], d[value_key]) for d in data]
            
            map_chart = Map()
            map_chart.add("", map_data, "china")
            map_chart.set_global_opts(
                title_opts=opts.TitleOpts(title=title),
                visualmap_opts=opts.VisualMapOpts()
            )
            
            return map_chart
        except Exception as e:
            print(f"Pyecharts 地图创建失败: {e}")
            return None
    
    def create_relation_graph(self, nodes: List[Dict], links: List[Dict],
                             title: str = "关系图") -> Optional[Any]:
        """
        创建关系图
        
        Args:
            nodes: [{'name': '节点1', 'symbolSize': 50}, ...]
            links: [{'source': '节点1', 'target': '节点2'}, ...]
            title: 图表标题
            
        Returns:
            Pyecharts图表对象
        """
        if not self.pyecharts_available:
            print("Pyecharts 未安装")
            return None
        
        try:
            from pyecharts.charts import Graph
            from pyecharts import options as opts
            
            graph = Graph()
            graph.add("", nodes, links,
                     repulsion=8000,
                     label_opts=opts.LabelOpts(is_show=True))
            graph.set_global_opts(title_opts=opts.TitleOpts(title=title))
            
            return graph
        except Exception as e:
            print(f"Pyecharts 关系图创建失败: {e}")
            return None
    
    def create_timeline(self, events: List[Dict], title: str = "时间轴") -> Optional[Any]:
        """
        创建时间轴
        
        Args:
            events: [{'time': '2020', 'event': '事件', 'description': '描述'}, ...]
            title: 图表标题
            
        Returns:
            Pyecharts图表对象
        """
        if not self.pyecharts_available:
            print("Pyecharts 未安装")
            return None
        
        try:
            from pyecharts.charts import Timeline
            from pyecharts import options as opts
            
            timeline = Timeline()
            
            for event in events:
                # 这里简化处理，实际可以创建更复杂的图表
                pass
            
            timeline.add_schema(play_interval=1000, is_loop_play=False)
            timeline.set_global_opts(title_opts=opts.TitleOpts(title=title))
            
            return timeline
        except Exception as e:
            print(f"Pyecharts 时间轴创建失败: {e}")
            return None
    
    # ========== Dash 仪表板 ==========
    
    def create_dashboard(self, data: Dict, title: str = "诗词分析仪表板") -> Optional[Any]:
        """
        创建Dash仪表板
        
        Args:
            data: 数据字典
            title: 仪表板标题
            
        Returns:
            Dash应用对象
        """
        if not self.dash_available or not self.plotly_available:
            print("Dash 或 Plotly 未安装")
            return None
        
        try:
            import dash
            from dash import dcc, html
            from dash.dependencies import Input, Output
            
            app = dash.Dash(__name__)
            
            app.layout = html.Div([
                html.H1(title),
                
                # 添加筛选器
                html.Div([
                    html.Label("选择诗人:"),
                    dcc.Dropdown(
                        id='author-dropdown',
                        options=[{'label': author, 'value': author} 
                                for author in data.get('authors', [])],
                        multi=True
                    )
                ]),
                
                # 添加图表
                html.Div([
                    dcc.Graph(id='main-chart')
                ]),
                
                # 添加统计信息
                html.Div(id='stats-display')
            ])
            
            @app.callback(
                Output('main-chart', 'figure'),
                Input('author-dropdown', 'value')
            )
            def update_chart(selected_authors):
                # 根据选择更新图表
                filtered_data = [d for d in data.get('poems', []) 
                               if not selected_authors or d.get('author') in selected_authors]
                
                if not filtered_data:
                    return {}
                
                fig = self.create_scatter_plot(
                    filtered_data, 
                    'char_count', 'sentiment_score',
                    hover_keys=['title', 'author'],
                    title="诗词特征散点图"
                )
                return fig
            
            return app
        except Exception as e:
            print(f"Dash 仪表板创建失败: {e}")
            return None
    
    # ========== 诗词专用可视化 ==========
    
    def visualize_poem_features(self, poems: List[Dict]) -> Dict[str, Any]:
        """
        可视化诗词特征
        
        Args:
            poems: 诗词数据列表
            
        Returns:
            可视化结果字典
        """
        results = {}
        
        # 1. 诗人作品数量分布
        from collections import Counter
        author_counts = Counter(poem.get('author', '未知') for poem in poems)
        
        if self.plotly_available:
            import plotly.express as px
            import pandas as pd
            
            df = pd.DataFrame([
                {'author': author, 'count': count} 
                for author, count in author_counts.most_common(20)
            ])
            
            fig = px.bar(df, x='author', y='count', title='诗人作品数量TOP20')
            results['author_distribution'] = fig
        
        # 2. 朝代分布
        dynasty_counts = Counter(poem.get('dynasty', '未知') for poem in poems)
        
        if self.plotly_available:
            import plotly.express as px
            import pandas as pd
            
            df = pd.DataFrame([
                {'dynasty': dynasty, 'count': count} 
                for dynasty, count in dynasty_counts.items()
            ])
            
            fig = px.pie(df, values='count', names='dynasty', title='朝代分布')
            results['dynasty_distribution'] = fig
        
        # 3. 词云
        all_text = ' '.join(poem.get('content', '') for poem in poems)
        
        try:
            import jieba
            words = jieba.lcut(all_text)
            word_counts = Counter(words)
            top_words = [(word, count) for word, count in word_counts.most_common(100) 
                        if len(word) > 1]
            
            wordcloud = self.create_wordcloud(top_words, "诗词词云")
            results['wordcloud'] = wordcloud
        except ImportError:
            pass
        
        return results
    
    def save_visualization(self, fig: Any, filepath: str, format: str = 'html'):
        """
        保存可视化结果
        
        Args:
            fig: 图表对象
            filepath: 保存路径
            format: 格式 ('html', 'png', 'json')
        """
        if fig is None:
            print("图表对象为空")
            return
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if format == 'html':
                if hasattr(fig, 'write_html'):
                    fig.write_html(str(filepath))
                elif hasattr(fig, 'render'):
                    fig.render(str(filepath))
                else:
                    # 保存为JSON
                    with open(filepath.with_suffix('.json'), 'w', encoding='utf-8') as f:
                        json.dump(fig, f, ensure_ascii=False, indent=2)
            
            elif format == 'png':
                if hasattr(fig, 'write_image'):
                    fig.write_image(str(filepath))
                else:
                    print("不支持PNG格式保存")
            
            elif format == 'json':
                with open(filepath.with_suffix('.json'), 'w', encoding='utf-8') as f:
                    if hasattr(fig, 'to_json'):
                        f.write(fig.to_json())
                    else:
                        json.dump(fig, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"可视化已保存: {filepath}")
        except Exception as e:
            print(f"保存失败: {e}")


if __name__ == "__main__":
    # 测试
    visualizer = PoetryVisualizer()
    
    # 测试数据
    test_data = [
        {'title': '静夜思', 'author': '李白', 'dynasty': '唐代', 
         'char_count': 20, 'sentiment_score': -0.3},
        {'title': '望庐山瀑布', 'author': '李白', 'dynasty': '唐代', 
         'char_count': 28, 'sentiment_score': 0.5},
        {'title': '春晓', 'author': '孟浩然', 'dynasty': '唐代', 
         'char_count': 20, 'sentiment_score': 0.2},
        {'title': '登鹳雀楼', 'author': '王之涣', 'dynasty': '唐代', 
         'char_count': 20, 'sentiment_score': 0.4}
    ]
    
    # 创建散点图
    fig = visualizer.create_scatter_plot(
        test_data, 'char_count', 'sentiment_score',
        color_key='author',
        hover_keys=['title', 'dynasty'],
        title="诗词特征分析"
    )
    
    if fig:
        visualizer.save_visualization(fig, 'test_scatter.html')
