/**
 * 词相似度数据加载器
 * 用于在 Vue 项目中读取 FlatBuffers 格式的词相似度数据
 */

import * as flatbuffers from 'flatbuffers';

// 类型定义
export interface SimilarWord {
  wordId: number;
  similarity: number; // 实际相似度值 (已除以 10000)
}

export interface WordEntry {
  wordId: number;
  frequency: number;
  similarWords: SimilarWord[];
}

export interface WordSimilarityData {
  words: WordEntry[];
}

export interface VocabMap {
  [word: string]: number;  // word -> id
}

export interface ReverseVocabMap {
  [id: number]: string;    // id -> word
}

// 基础 URL 配置
const DATA_BASE_URL = '/chinese-poetry-data-mining/results/word_similarity_v3';

/**
 * SimilarWord 表 (手动实现，避免依赖生成的代码)
 */
class SimilarWordWrapper {
  constructor(private bb: flatbuffers.ByteBuffer, private bb_pos: number) {}

  wordId(): number {
    const offset = this.bb.__offset(this.bb_pos, 4);
    return offset ? this.bb.readInt32(this.bb_pos + offset) : 0;
  }

  similarity(): number {
    const offset = this.bb.__offset(this.bb_pos, 6);
    return offset ? this.bb.readInt32(this.bb_pos + offset) : 0;
  }
}

/**
 * WordEntry 表
 */
class WordEntryWrapper {
  constructor(private bb: flatbuffers.ByteBuffer, private bb_pos: number) {}

  wordId(): number {
    const offset = this.bb.__offset(this.bb_pos, 4);
    return offset ? this.bb.readInt32(this.bb_pos + offset) : 0;
  }

  frequency(): number {
    const offset = this.bb.__offset(this.bb_pos, 6);
    return offset ? this.bb.readInt32(this.bb_pos + offset) : 0;
  }

  similarWords(index: number): SimilarWordWrapper | null {
    const offset = this.bb.__offset(this.bb_pos, 8);
    if (offset === 0) return null;
    const vectorOffset = this.bb.__vector(this.bb_pos + offset) + index * 4;
    const objectOffset = this.bb.readInt32(vectorOffset) + vectorOffset;
    return new SimilarWordWrapper(this.bb, objectOffset);
  }

  similarWordsLength(): number {
    const offset = this.bb.__offset(this.bb_pos, 8);
    return offset ? this.bb.__vector_len(this.bb_pos + offset) : 0;
  }
}

/**
 * WordSimilarityFile 根表
 */
class WordSimilarityFileWrapper {
  constructor(private bb: flatbuffers.ByteBuffer, private bb_pos: number) {}

  static getRootAsWordSimilarityFile(bb: flatbuffers.ByteBuffer): WordSimilarityFileWrapper {
    return new WordSimilarityFileWrapper(bb, bb.readInt32(bb.position()) + bb.position());
  }

  words(index: number): WordEntryWrapper | null {
    const offset = this.bb.__offset(this.bb_pos, 4);
    if (offset === 0) return null;
    const vectorOffset = this.bb.__vector(this.bb_pos + offset) + index * 4;
    const objectOffset = this.bb.readInt32(vectorOffset) + vectorOffset;
    return new WordEntryWrapper(this.bb, objectOffset);
  }

  wordsLength(): number {
    const offset = this.bb.__offset(this.bb_pos, 4);
    return offset ? this.bb.__vector_len(this.bb_pos + offset) : 0;
  }
}

/**
 * 词相似度数据加载器类
 */
export class WordSimilarityLoader {
  private vocab: VocabMap = {};
  private reverseVocab: ReverseVocabMap = {};
  private metadata: any = null;
  private chunkCache: Map<number, WordEntry[]> = new Map();
  private maxCacheSize = 5; // 最多缓存 5 个 chunk

  /**
   * 初始化加载器，加载词表和元数据
   */
  async initialize(): Promise<void> {
    await Promise.all([
      this.loadVocab(),
      this.loadMetadata()
    ]);
  }

  /**
   * 加载词表
   */
  private async loadVocab(): Promise<void> {
    const response = await fetch(`${DATA_BASE_URL}/vocab.json`);
    if (!response.ok) {
      throw new Error(`Failed to load vocab: ${response.status}`);
    }
    this.vocab = await response.json();
    // 构建反向映射
    this.reverseVocab = {};
    for (const [word, id] of Object.entries(this.vocab)) {
      this.reverseVocab[id as number] = word;
    }
  }

  /**
   * 加载元数据
   */
  private async loadMetadata(): Promise<void> {
    const response = await fetch(`${DATA_BASE_URL}/metadata.json`);
    if (!response.ok) {
      throw new Error(`Failed to load metadata: ${response.status}`);
    }
    this.metadata = await response.json();
  }

  /**
   * 加载指定 chunk
   */
  private async loadChunk(chunkIndex: number): Promise<WordEntry[]> {
    // 检查缓存
    if (this.chunkCache.has(chunkIndex)) {
      return this.chunkCache.get(chunkIndex)!;
    }

    const chunkPath = `${DATA_BASE_URL}/word_chunk_${chunkIndex.toString().padStart(4, '0')}.bin`;
    const response = await fetch(chunkPath);
    if (!response.ok) {
      throw new Error(`Failed to load chunk ${chunkIndex}: ${response.status}`);
    }

    const arrayBuffer = await response.arrayBuffer();
    const bytes = new Uint8Array(arrayBuffer);
    const bb = new flatbuffers.ByteBuffer(bytes);

    const file = WordSimilarityFileWrapper.getRootAsWordSimilarityFile(bb);
    const entries: WordEntry[] = [];

    for (let i = 0; i < file.wordsLength(); i++) {
      const entry = file.words(i);
      if (!entry) continue;

      const similarWords: SimilarWord[] = [];
      for (let j = 0; j < entry.similarWordsLength(); j++) {
        const sw = entry.similarWords(j);
        if (!sw) continue;
        similarWords.push({
          wordId: sw.wordId(),
          similarity: sw.similarity() / 10000 // 转换回实际相似度
        });
      }

      entries.push({
        wordId: entry.wordId(),
        frequency: entry.frequency(),
        similarWords
      });
    }

    // 缓存管理
    if (this.chunkCache.size >= this.maxCacheSize) {
      const firstKey = this.chunkCache.keys().next().value;
      if (firstKey !== undefined) {
        this.chunkCache.delete(firstKey);
      }
    }
    this.chunkCache.set(chunkIndex, entries);

    return entries;
  }

  /**
   * 获取词的 ID
   */
  getWordId(word: string): number | undefined {
    return this.vocab[word];
  }

  /**
   * 通过 ID 获取词
   */
  getWordById(id: number): string | undefined {
    return this.reverseVocab[id];
  }

  /**
   * 检查词是否存在
   */
  hasWord(word: string): boolean {
    return word in this.vocab;
  }

  /**
   * 获取词的相似词列表
   */
  async getSimilarWords(word: string, minSimilarity?: number): Promise<{ word: string; similarity: number }[]> {
    const wordId = this.vocab[word];
    if (wordId === undefined) {
      return [];
    }

    // 计算 chunk 索引
    const chunkSize = this.metadata?.chunk_size || 500;
    const chunkIndex = Math.floor(wordId / chunkSize);

    try {
      const entries = await this.loadChunk(chunkIndex);
      const entry = entries.find(e => e.wordId === wordId);

      if (!entry) {
        return [];
      }

      let similarWords = entry.similarWords.map(sw => ({
        word: this.reverseVocab[sw.wordId] || '',
        similarity: sw.similarity
      }));

      // 过滤最小相似度
      if (minSimilarity !== undefined) {
        similarWords = similarWords.filter(sw => sw.similarity >= minSimilarity);
      }

      // 按相似度排序
      similarWords.sort((a, b) => b.similarity - a.similarity);

      return similarWords;
    } catch (error) {
      console.error(`Error loading similar words for "${word}":`, error);
      return [];
    }
  }

  /**
   * 批量获取多个词的相似词
   */
  async getSimilarWordsBatch(
    words: string[],
    minSimilarity?: number
  ): Promise<Map<string, { word: string; similarity: number }[]>> {
    const result = new Map<string, { word: string; similarity: number }[]>();

    // 按 chunk 分组
    const chunkGroups = new Map<number, string[]>();
    const chunkSize = this.metadata?.chunk_size || 500;

    for (const word of words) {
      const wordId = this.vocab[word];
      if (wordId === undefined) {
        result.set(word, []);
        continue;
      }
      const chunkIndex = Math.floor(wordId / chunkSize);
      if (!chunkGroups.has(chunkIndex)) {
        chunkGroups.set(chunkIndex, []);
      }
      chunkGroups.get(chunkIndex)!.push(word);
    }

    // 并行加载各 chunk
    await Promise.all(
      Array.from(chunkGroups.entries()).map(async ([chunkIndex, chunkWords]) => {
        try {
          const entries = await this.loadChunk(chunkIndex);
          const entryMap = new Map(entries.map(e => [e.wordId, e]));

          for (const word of chunkWords) {
            const wordId = this.vocab[word];
            if (wordId === undefined) {
              result.set(word, []);
              continue;
            }
            const entry = entryMap.get(wordId);

            if (!entry) {
              result.set(word, []);
              continue;
            }

            let similarWords = entry.similarWords.map(sw => ({
              word: this.reverseVocab[sw.wordId] || '',
              similarity: sw.similarity
            }));

            if (minSimilarity !== undefined) {
              similarWords = similarWords.filter(sw => sw.similarity >= minSimilarity);
            }

            similarWords.sort((a, b) => b.similarity - a.similarity);
            result.set(word, similarWords);
          }
        } catch (error) {
          console.error(`Error loading chunk ${chunkIndex}:`, error);
          for (const word of chunkWords) {
            result.set(word, []);
          }
        }
      })
    );

    return result;
  }

  /**
   * 获取元数据
   */
  getMetadata(): any {
    return this.metadata;
  }

  /**
   * 获取词表大小
   */
  getVocabSize(): number {
    return Object.keys(this.vocab).length;
  }

  /**
   * 清除缓存
   */
  clearCache(): void {
    this.chunkCache.clear();
  }
}

// 导出单例实例
export const wordSimilarityLoader = new WordSimilarityLoader();

// 默认导出
export default wordSimilarityLoader;
