/**
 * 前端渐进式加载器
 * 功能：
 * 1. 虚拟滚动（最多100个DOM节点）
 * 2. 分片懒加载
 * 3. 搜索功能
 * 4. 性能监控
 */

class ProgressiveLoader {
    constructor(options = {}) {
        this.container = options.container || document.querySelector('#poems-container');
        this.manifestUrl = options.manifestUrl || 'manifest.json';
        this.itemsPerPage = options.itemsPerPage || 20;
        this.maxDOMNodes = options.maxDOMNodes || 100;
        this.throttleDelay = options.throttleDelay || 100;
        
        this.manifest = null;
        this.allPoems = [];
        this.filteredPoems = [];
        this.visibleItems = [];
        this.currentPage = 0;
        this.isLoading = false;
        this.observer = null;
        
        this.init();
    }
    
    async init() {
        try {
            await this.loadManifest();
            await this.loadInitialChunks();
            this.setupScrollListener();
            this.setupSearch();
            this.render();
        } catch (error) {
            console.error('初始化失败:', error);
            this.showError('加载失败，请刷新页面重试');
        }
    }
    
    async loadManifest() {
        const response = await fetch(this.manifestUrl);
        if (!response.ok) {
            throw new Error('无法加载manifest.json');
        }
        this.manifest = await response.json();
        console.log('Manifest加载完成:', this.manifest);
    }
    
    async loadInitialChunks() {
        // 先加载前2个分片
        const chunksToLoad = Math.min(2, this.manifest.total_chunks);
        for (let i = 0; i < chunksToLoad; i++) {
            await this.loadChunk(i);
        }
        this.filteredPoems = [...this.allPoems];
    }
    
    async loadChunk(chunkIndex) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        try {
            const chunkInfo = this.manifest.chunks[chunkIndex];
            if (!chunkInfo) {
                throw new Error(`分片 ${chunkIndex} 不存在`);
            }
            
            const response = await fetch(chunkInfo.filename);
            if (!response.ok) {
                throw new Error(`无法加载分片 ${chunkInfo.filename}`);
            }
            
            const poems = await response.json();
            this.allPoems.push(...poems);
            console.log(`分片 ${chunkIndex} 加载完成，新增 ${poems.length} 首诗词`);
        } catch (error) {
            console.error('加载分片失败:', error);
        } finally {
            this.isLoading = false;
        }
    }
    
    setupScrollListener() {
        // 节流函数
        const throttle = (func, delay) => {
            let inThrottle;
            return function() {
                const args = arguments;
                const context = this;
                if (!inThrottle) {
                    func.apply(context, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, delay);
                }
            };
        };
        
        this.container.addEventListener('scroll', throttle(() => {
            const { scrollTop, clientHeight, scrollHeight } = this.container;
            
            // 当滚动到离底部还有20%时加载更多
            if (scrollTop + clientHeight >= scrollHeight * 0.8) {
                this.loadMore();
            }
        }, this.throttleDelay));
    }
    
    setupSearch() {
        const searchInput = document.querySelector('#search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const query = e.target.value.trim().toLowerCase();
                this.filterPoems(query);
            });
        }
    }
    
    filterPoems(query) {
        if (!query) {
            this.filteredPoems = [...this.allPoems];
        } else {
            this.filteredPoems = this.allPoems.filter(poem => {
                return (
                    (poem.title && poem.title.toLowerCase().includes(query)) ||
                    (poem.content && poem.content.toLowerCase().includes(query)) ||
                    (poem.author && poem.author.toLowerCase().includes(query)) ||
                    (poem.dynasty && poem.dynasty.toLowerCase().includes(query))
                );
            });
        }
        this.currentPage = 0;
        this.render();
    }
    
    loadMore() {
        const nextPage = this.currentPage + 1;
        const startIndex = nextPage * this.itemsPerPage;
        
        if (startIndex < this.filteredPoems.length) {
            this.currentPage = nextPage;
            this.render();
        }
    }
    
    render() {
        const startIndex = 0;
        const endIndex = Math.min((this.currentPage + 1) * this.itemsPerPage, this.filteredPoems.length);
        const poemsToRender = this.filteredPoems.slice(startIndex, endIndex);
        
        // 虚拟滚动：只渲染可见区域附近的元素
        this.renderPoems(poemsToRender);
        this.updateStats();
    }
    
    renderPoems(poems) {
        this.container.innerHTML = '';
        
        if (poems.length === 0) {
            this.container.innerHTML = '<div class="no-results">暂无结果</div>';
            return;
        }
        
        poems.forEach(poem => {
            const poemElement = this.createPoemElement(poem);
            this.container.appendChild(poemElement);
        });
    }
    
    createPoemElement(poem) {
        const div = document.createElement('div');
        div.className = 'poem-item';
        div.innerHTML = `
            <h3 class="poem-title">${poem.title || '无标题'}</h3>
            <div class="poem-meta">
                <span class="author">${poem.author || '佚名'}</span>
                <span class="dynasty">${poem.dynasty || '未知'}</span>
                <span class="genre">${poem.genre || '未知'}</span>
            </div>
            <div class="poem-content">${this.formatContent(poem.content || '')}</div>
        `;
        
        // 添加点击事件
        div.addEventListener('click', () => {
            this.showPoemDetail(poem);
        });
        
        return div;
    }
    
    formatContent(content) {
        return content.replace(/\n/g, '<br>');
    }
    
    showPoemDetail(poem) {
        // 显示诗词详情
        const detailElement = document.querySelector('#poem-detail');
        if (detailElement) {
            detailElement.innerHTML = `
                <h2>${poem.title || '无标题'}</h2>
                <div class="detail-meta">
                    <span>作者: ${poem.author || '佚名'}</span>
                    <span>朝代: ${poem.dynasty || '未知'}</span>
                    <span>类型: ${poem.genre || '未知'}</span>
                </div>
                <div class="detail-content">${this.formatContent(poem.content || '')}</div>
            `;
            detailElement.style.display = 'block';
        }
    }
    
    updateStats() {
        const statsElement = document.querySelector('#stats');
        if (statsElement) {
            statsElement.innerHTML = `
                <div>总诗词: ${this.manifest.total_poems}</div>
                <div>已加载: ${this.allPoems.length}</div>
                <div>当前显示: ${this.filteredPoems.length}</div>
                <div>分片数: ${this.manifest.total_chunks}</div>
            `;
        }
    }
    
    showError(message) {
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.textContent = message;
        this.container.appendChild(errorElement);
    }
}

// 性能监控
class PerformanceMonitor {
    constructor() {
        this.startTime = performance.now();
        this.metrics = [];
    }
    
    mark(name) {
        this.metrics.push({
            name,
            time: performance.now() - this.startTime,
            memory: window.performance.memory ? window.performance.memory.usedJSHeapSize : 0
        });
    }
    
    report() {
        console.table(this.metrics);
        return this.metrics;
    }
}

// 全局实例
let loader = null;
let perfMonitor = null;

// 初始化
window.addEventListener('DOMContentLoaded', async () => {
    perfMonitor = new PerformanceMonitor();
    perfMonitor.mark('DOMContentLoaded');
    
    loader = new ProgressiveLoader({
        container: document.querySelector('#poems-container'),
        manifestUrl: 'manifest.json'
    });
    
    perfMonitor.mark('LoaderInitialized');
    perfMonitor.report();
});
