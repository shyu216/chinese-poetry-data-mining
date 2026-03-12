/**
 * 分片数据加载器
 * 支持按需加载和缓存
 */

class ChunkedDataLoader {
    constructor(basePath = '../data/') {
        this.basePath = basePath;
        this.cache = new Map();
        this.manifests = {};
    }

    /**
     * 加载manifest文件
     */
    async loadManifest(type) {
        const manifestKey = `${type}_manifest`;
        if (this.manifests[manifestKey]) {
            return this.manifests[manifestKey];
        }

        const response = await fetch(`${this.basePath}${type}_manifest.json`);
        if (!response.ok) {
            throw new Error(`Failed to load ${type} manifest: ${response.status}`);
        }

        const manifest = await response.json();
        this.manifests[manifestKey] = manifest;
        return manifest;
    }

    /**
     * 加载单个分片
     */
    async loadChunk(type, index) {
        const cacheKey = `${type}_${index}`;
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }

        const manifest = await this.loadManifest(type);
        const chunkInfo = manifest.files.find(f => f.index === index);
        if (!chunkInfo) {
            throw new Error(`Chunk ${index} not found in ${type} manifest`);
        }

        const response = await fetch(`${this.basePath}${chunkInfo.file}`);
        if (!response.ok) {
            throw new Error(`Failed to load chunk ${index}: ${response.status}`);
        }

        let data;
        if (type === 'poems') {
            data = await response.json();
        } else if (type === 'structure') {
            // CSV需要解析
            const csvText = await response.text();
            data = this.parseCSV(csvText);
        }

        this.cache.set(cacheKey, data);
        return data;
    }

    /**
     * 解析CSV文本
     */
    parseCSV(csvText) {
        const lines = csvText.trim().split('\n');
        const headers = lines[0].split(',').map(h => h.trim());
        
        const rows = [];
        for (let i = 1; i < lines.length; i++) {
            const values = lines[i].split(',');
            const row = {};
            headers.forEach((header, idx) => {
                row[header] = values[idx] ? values[idx].trim() : '';
            });
            rows.push(row);
        }
        
        return { headers, rows };
    }

    /**
     * 加载所有分片（用于需要完整数据的场景）
     */
    async loadAllChunks(type, onProgress = null) {
        const manifest = await this.loadManifest(type);
        const allData = [];

        for (let i = 0; i < manifest.chunks; i++) {
            const chunkData = await this.loadChunk(type, i);
            
            if (type === 'poems') {
                allData.push(...chunkData);
            } else if (type === 'structure') {
                allData.push(...chunkData.rows);
            }

            if (onProgress) {
                onProgress(i + 1, manifest.chunks);
            }
        }

        return allData;
    }

    /**
     * 按条件过滤加载（只加载符合条件的分片）
     */
    async loadFilteredChunks(type, filterFn, onProgress = null) {
        const manifest = await this.loadManifest(type);
        const filteredData = [];

        for (let i = 0; i < manifest.chunks; i++) {
            const chunkData = await this.loadChunk(type, i);
            
            let chunkItems;
            if (type === 'poems') {
                chunkItems = chunkData;
            } else if (type === 'structure') {
                chunkItems = chunkData.rows;
            }

            const filtered = chunkItems.filter(filterFn);
            filteredData.push(...filtered);

            if (onProgress) {
                onProgress(i + 1, manifest.chunks, filtered.length);
            }
        }

        return filteredData;
    }

    /**
     * 清空缓存
     */
    clearCache() {
        this.cache.clear();
    }

    /**
     * 获取缓存统计
     */
    getCacheStats() {
        let totalSize = 0;
        for (const [key, value] of this.cache) {
            totalSize += JSON.stringify(value).length;
        }
        return {
            entries: this.cache.size,
            size_mb: (totalSize / 1024 / 1024).toFixed(2)
        };
    }
}

// 全局实例
const dataLoader = new ChunkedDataLoader();

/**
 * 加载诗词数据（支持分片）
 */
async function loadPoemsChunked(options = {}) {
    const { 
        onProgress = null,
        filter = null,
        useCache = true 
    } = options;

    if (!useCache) {
        dataLoader.clearCache();
    }

    if (filter) {
        return await dataLoader.loadFilteredChunks('poems', filter, onProgress);
    } else {
        return await dataLoader.loadAllChunks('poems', onProgress);
    }
}

/**
 * 加载结构数据（支持分片）
 */
async function loadStructureChunked(options = {}) {
    const { 
        onProgress = null,
        filter = null,
        useCache = true 
    } = options;

    if (!useCache) {
        dataLoader.clearCache();
    }

    if (filter) {
        return await dataLoader.loadFilteredChunks('structure', filter, onProgress);
    } else {
        return await dataLoader.loadAllChunks('structure', onProgress);
    }
}

/**
 * 按格律模式加载诗词（优化版）
 */
async function loadPoemsByMeter(meterPattern, onProgress = null) {
    return await loadPoemsChunked({
        filter: poem => poem.m === meterPattern,
        onProgress
    });
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ChunkedDataLoader, loadPoemsChunked, loadStructureChunked, loadPoemsByMeter };
}
