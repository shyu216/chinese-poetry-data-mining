# 🏮 中国古代文学时空图谱

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Vue 3](https://img.shields.io/badge/Vue-3+-42b883.svg)](https://vuejs.org/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-在线访问-brightgreen)](https://shyu216.github.io/chinese-poetry-data-mining)

> 用数据科学的方法，挖掘中国古典诗词中隐藏的时空模式与文学规律

[English Version](README.md) · [在线演示](https://shyu216.github.io/chinese-poetry-data-mining)

---

## ✨ 核心特性

| 功能 | 描述 |
|:---|:---|
| 🔍 **全文检索** | 跨朝代、跨体裁的诗词智能搜索，支持多重筛选条件 |
| 👤 **诗人图谱** | 按朝代查看诗人分布，了解诗词盛世的历史脉络 |
| 📊 **词频统计** | 统计诗词中的高频词汇，洞察不同时代的用词偏好 |
| ☁️ **词云可视化** | 生成直观的词云图，感受诗词的意象分布 |
| 🔗 **词汇相似度** | 基于词向量技术，发现语义相近的词汇关联 |
| 👥 **诗人相似度** | 分析诗人创作风格，找出"意气相投"的诗人 |
| 🎵 **格律分析** | 解析诗词格律模式，探索古典诗词的音韵之美 |
| 📈 **数据仪表盘** | 一览古籍数据全貌，掌握整体分布情况 |

---

## 🚀 快速开始

### 前端预览

```bash
# 克隆项目
git clone https://github.com/shyu216/chinese-poetry-data-mining.git

# 进入前端目录
cd web

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 生产构建

```bash
# 构建静态文件
npm run build

# 预览构建结果
npm run preview
```

---

## 🛠️ 技术栈

### 前端
- **框架**: Vue 3 + Composition API
- **语言**: TypeScript
- **构建**: Vite
- **路由**: Vue Router
- **可视化**: Plotly.js, D3.js

### 数据处理
- **数据格式**: FlatBuffers (高性能二进制序列化)
- **中文处理**: jieba 分词
- **词向量**: FastText
- **多进程**: multiprocessing (Python)

### 部署
- **平台**: GitHub Pages
- **方式**: 纯静态部署，无需后端服务器

---

## 📁 项目结构

```
chinese-poetry-data-mining/
├── web/                      # Vue 3 前端项目
│   ├── src/
│   │   ├── components/       # UI 组件
│   │   ├── composables/      # 组合式函数
│   │   ├── views/            # 页面视图
│   │   ├── generated/        # 生成的类型定义
│   │   └── router/           # 路由配置
│   └── index.html
├── scripts/                  # 数据处理脚本
│   ├── word_sim_v3.py        # 词汇相似度计算
│   ├── author_sim_v2.py      # 诗人相似度分析
│   ├── wordcount_v2.py       # 词频统计
│   └── flatbuffers_generated/# FlatBuffers  schema
└── data/                     # 原始诗词数据
    └── chinese-poetry/       # 古诗词数据库
        ├── 全唐诗/           # 唐诗全集
        ├── 宋词/             # 宋词全集
        ├── 元曲/             # 元曲全集
        └── 四书五经/         # 儒家经典
```

---

## 📈 数据规模

- **全唐诗**: 逾 5 万首
- **宋词**: 逾 2 万首
- **元曲**: 数千首
- **四书五经**: 完整收录

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

---

## 🙏 致谢

- [chinese-poetry](https://github.com/chinese-poetry/chinese-poetry) - 全面的中华古诗词数据库
- [ccpoems](https://github.com/shyu216/ccpoems) - React Native 移动应用配套项目

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

<p align="center">
  <i>用数据科学的方式，重新发现中国古典诗词之美 🏮</i>
</p>
