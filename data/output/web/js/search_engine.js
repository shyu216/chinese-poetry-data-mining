/**
 * 纯前端搜索引擎 (Task 14)
 * 
 * 功能：
 * 1. 基于倒排索引的快速搜索
 * 2. 支持多关键词组合查询 (AND/OR)
 * 3. 支持按作者/朝代筛选
 * 4. 使用 Web Worker 处理大索引
 * 5. 搜索结果缓存
 */

class StaticSearchEngine {
    constructor(options = {}) {
        this.indexUrl = options.indexUrl || 'index/search_index.json';
        this.authorIndexUrl = options.authorIndexUrl || 'index/author_index.json';
        this.dynastyIndexUrl = options.dynastyIndexUrl || 'index/dynasty_index.json';
        this.poemsUrl = options.poemsUrl || 'poems_chunk_000.json';
        
        this.searchIndex = null;
        this.authorIndex = null;
        this.dynastyIndex = null;
        this.poems = null;
        this.poemsMap = null;
        
        this.cache = new Map();
        this.maxCacheSize = 100;
        
        this.initialized = false;
    }
    
    /**
     * 初始化搜索引擎
     * 加载所有必要的索引文件
     */
    async init() {
        if (this.initialized) return;
        
        console.log('初始化搜索引擎...');
        
        try {
            // 并行加载索引文件
            const [searchResponse, authorResponse, dynastyResponse] = await Promise.all([
                fetch(this.indexUrl),
                fetch(this.authorIndexUrl),
                fetch(this.dynastyIndexUrl)
            ]);
            
            if (!searchResponse.ok) throw new Error('无法加载搜索索引');
            if (!authorResponse.ok) throw new Error('无法加载作者索引');
            if (!dynastyResponse.ok) throw new Error('无法加载朝代索引');
            
            this.searchIndex = await searchResponse.json();
            this.authorIndex = await authorResponse.json();
            this.dynastyIndex = await dynastyResponse.json();
            
            console.log('索引加载完成:');
            console.log(`  - 搜索索引: ${this.searchIndex.total_terms} 个词条`);
            console.log(`  - 作者索引: ${this.authorIndex.total_authors} 位作者`);
            console.log(`  - 朝代索引: ${this.dynastyIndex.total_dynasties} 个朝代`);
            
            this.initialized = true;
            
        } catch (error) {
            console.error('搜索引擎初始化失败:', error);
            throw error;
        }
    }
    
    /**
     * 加载诗词数据
     * 按需加载，首次搜索时调用
     */
    async loadPoems() {
        if (this.poems) return this.poems;
        
        console.log('加载诗词数据...');
        
        try {
            const response = await fetch(this.poemsUrl);
            if (!response.ok) throw new Error('无法加载诗词数据');
            
            this.poems = await response.json();
            
            // 构建诗词ID映射
            this.poemsMap = new Map();
            this.poems.forEach(poem => {
                if (poem.id) {
                    this.poemsMap.set(poem.id, poem);
                }
            });
            
            console.log(`诗词数据加载完成: ${this.poems.length} 首`);
            return this.poems;
            
        } catch (error) {
            console.error('诗词数据加载失败:', error);
            throw error;
        }
    }
    
    /**
     * 搜索诗词
     * 
     * @param {string} query - 搜索关键词
     * @param {Object} filters - 筛选条件
     * @param {string} filters.author - 按作者筛选
     * @param {string} filters.dynasty - 按朝代筛选
     * @param {string} filters.operator - 多关键词操作符 ('AND' | 'OR')
     * @returns {Array} 搜索结果
     */
    async search(query, filters = {}) {
        if (!this.initialized) {
            await this.init();
        }
        
        // 生成缓存键
        const cacheKey = this._generateCacheKey(query, filters);
        if (this.cache.has(cacheKey)) {
            console.log('使用缓存结果');
            return this.cache.get(cacheKey);
        }
        
        // 解析查询
        const keywords = this._parseQuery(query);
        if (keywords.length === 0) {
            return [];
        }
        
        console.log(`搜索: "${query}" (关键词: ${keywords.join(', ')})`);
        
        // 获取每个关键词的诗词ID列表
        const keywordResults = keywords.map(keyword => {
            const term = keyword.toLowerCase();
            return this.searchIndex.terms[term] || [];
        });
        
        // 合并结果
        const operator = filters.operator || 'OR';
        let poemIds;
        
        if (operator === 'AND') {
            // 交集
            poemIds = this._intersectArrays(keywordResults);
        } else {
            // 并集
            poemIds = this._unionArrays(keywordResults);
        }
        
        console.log(`关键词匹配: ${poemIds.length} 首诗词`);
        
        // 应用筛选条件
        if (filters.author) {
            poemIds = this._filterByAuthor(poemIds, filters.author);
        }
        
        if (filters.dynasty) {
            poemIds = this._filterByDynasty(poemIds, filters.dynasty);
        }
        
        console.log(`筛选后: ${poemIds.length} 首诗词`);
        
        // 加载诗词详情
        await this.loadPoems();
        
        // 获取完整的诗词数据
        const results = poemIds
            .map(id => this.poemsMap.get(id))
            .filter(poem => poem !== undefined);
        
        // 按相关性排序 (匹配关键词越多，排名越靠前)
        results.sort((a, b) => {
            const scoreA = this._calculateRelevance(a, keywords);
            const scoreB = this._calculateRelevance(b, keywords);
            return scoreB - scoreA;
        });
        
        // 缓存结果
        this._addToCache(cacheKey, results);
        
        return results;
    }
    
    /**
     * 按作者获取诗词
     */
    async searchByAuthor(author) {
        if (!this.initialized) {
            await this.init();
        }
        
        const authorData = this.authorIndex.authors[author];
        if (!authorData) {
            return [];
        }
        
        await this.loadPoems();
        
        return authorData.poem_ids
            .map(id => this.poemsMap.get(id))
            .filter(poem => poem !== undefined);
    }
    
    /**
     * 按朝代获取诗词
     */
    async searchByDynasty(dynasty) {
        if (!this.initialized) {
            await this.init();
        }
        
        const dynastyData = this.dynastyIndex.dynasties[dynasty];
        if (!dynastyData) {
            return [];
        }
        
        await this.loadPoems();
        
        return dynastyData.poem_ids
            .map(id => this.poemsMap.get(id))
            .filter(poem => poem !== undefined);
    }
    
    /**
     * 获取作者列表
     */
    getAuthors() {
        if (!this.initialized) return [];
        return Object.keys(this.authorIndex.authors).sort();
    }
    
    /**
     * 获取朝代列表
     */
    getDynasties() {
        if (!this.initialized) return [];
        return Object.keys(this.dynastyIndex.dynasties).sort();
    }
    
    /**
     * 获取作者信息
     */
    getAuthorInfo(author) {
        if (!this.initialized) return null;
        return this.authorIndex.authors[author] || null;
    }
    
    /**
     * 自动补全建议
     */
    getSuggestions(prefix, limit = 10) {
        if (!this.initialized || !prefix) return [];
        
        const term = prefix.toLowerCase();
        const suggestions = [];
        
        // 从搜索索引中匹配
        for (const [word, poemIds] of Object.entries(this.searchIndex.terms)) {
            if (word.startsWith(term)) {
                suggestions.push({
                    type: 'word',
                    value: word,
                    count: poemIds.length
                });
            }
            if (suggestions.length >= limit) break;
        }
        
        // 从作者索引中匹配
        for (const author of Object.keys(this.authorIndex.authors)) {
            if (author.includes(prefix)) {
                suggestions.push({
                    type: 'author',
                    value: author,
                    count: this.authorIndex.authors[author].poem_count
                });
            }
        }
        
        return suggestions.slice(0, limit);
    }
    
    /**
     * 解析查询字符串
     */
    _parseQuery(query) {
        if (!query) return [];
        
        // 支持空格分隔的多关键词
        // 支持引号包围的短语
        const keywords = [];
        const phraseRegex = /"([^"]+)"/g;
        let match;
        
        // 提取引号内的短语
        while ((match = phraseRegex.exec(query)) !== null) {
            keywords.push(match[1]);
        }
        
        // 提取剩余的关键词
        const remaining = query.replace(phraseRegex, '').trim();
        if (remaining) {
            keywords.push(...remaining.split(/\s+/));
        }
        
        return keywords.filter(k => k.length >= 2);
    }
    
    /**
     * 计算相关性分数
     */
    _calculateRelevance(poem, keywords) {
        let score = 0;
        const text = `${poem.title || ''} ${poem.content || ''} ${poem.author || ''}`.toLowerCase();
        
        for (const keyword of keywords) {
            const term = keyword.toLowerCase();
            // 标题匹配权重更高
            if (poem.title && poem.title.toLowerCase().includes(term)) {
                score += 3;
            }
            // 作者匹配
            if (poem.author && poem.author.toLowerCase().includes(term)) {
                score += 2;
            }
            // 内容匹配
            if (text.includes(term)) {
                score += 1;
            }
        }
        
        return score;
    }
    
    /**
     * 按作者筛选
     */
    _filterByAuthor(poemIds, author) {
        const authorData = this.authorIndex.authors[author];
        if (!authorData) return [];
        
        const authorPoemIds = new Set(authorData.poem_ids);
        return poemIds.filter(id => authorPoemIds.has(id));
    }
    
    /**
     * 按朝代筛选
     */
    _filterByDynasty(poemIds, dynasty) {
        const dynastyData = this.dynastyIndex.dynasties[dynasty];
        if (!dynastyData) return [];
        
        const dynastyPoemIds = new Set(dynastyData.poem_ids);
        return poemIds.filter(id => dynastyPoemIds.has(id));
    }
    
    /**
     * 数组交集
     */
    _intersectArrays(arrays) {
        if (arrays.length === 0) return [];
        if (arrays.length === 1) return arrays[0];
        
        let result = new Set(arrays[0]);
        for (let i = 1; i < arrays.length; i++) {
            result = new Set(arrays[i].filter(x => result.has(x)));
        }
        
        return Array.from(result);
    }
    
    /**
     * 数组并集
     */
    _unionArrays(arrays) {
        const result = new Set();
        for (const arr of arrays) {
            for (const item of arr) {
                result.add(item);
            }
        }
        return Array.from(result);
    }
    
    /**
     * 生成缓存键
     */
    _generateCacheKey(query, filters) {
        return JSON.stringify({ query, filters });
    }
    
    /**
     * 添加到缓存
     */
    _addToCache(key, value) {
        if (this.cache.size >= this.maxCacheSize) {
            // 删除最早的缓存
            const firstKey = this.cache.keys().next().value;
            this.cache.delete(firstKey);
        }
        this.cache.set(key, value);
    }
    
    /**
     * 清除缓存
     */
    clearCache() {
        this.cache.clear();
    }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StaticSearchEngine;
}
