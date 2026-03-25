/**
 * script: 01_generate-poem-chunk-meta.cjs
 * stage: P1-数据预处理
 * artifact: chunk 元数据
 * purpose: 扫描 poems_chunk CSV 并输出 chunks 元信息。
 * inputs:
 * - results/preprocessed
 * outputs:
 * - results/preprocessed/poems_chunk_meta.json
 * depends_on:
 * - 01_preprocess_poems.py
 * develop_date: 2026-03-15
 * last_modified_date: 2026-03-17
 */
const fs = require('fs');
const path = require('path');
const DATA_DIR = path.join(__dirname, '../results/preprocessed');
const INDEX_FILE = path.join(DATA_DIR, 'poems_chunk_meta.json');
function parseCSVLine(line) {
  const result = [];
  let current = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  result.push(current.trim());
  return result;
}
function extractChunkMetadata(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.trim().split('\n');
  const dataLines = lines.slice(1);
  const poems = [];
  const dynasties = new Set();
  const genres = new Set();
  const authors = new Set();
  // 分类计数
  let songshiCount = 0;  // 宋诗
  let songciCount = 0;   // 宋词
  let tangshiCount = 0;  // 唐诗
  for (const line of dataLines) {
    const cols = parseCSVLine(line);
    if (cols.length < 10) continue;
    const [id, title, author, dynasty, genre] = cols;
    poems.push({
      id,
      title: title || '',
      author: author || '佚名',
      dynasty,
      genre
    });
    dynasties.add(dynasty);
    genres.add(genre);
    authors.add(author || '佚名');
    // 分类统计
    if (dynasty === '宋' && genre === '诗') {
      songshiCount++;
    } else if (dynasty === '宋' && genre === '词') {
      songciCount++;
    } else if (dynasty === '唐' && genre === '诗') {
      tangshiCount++;
    }
  }
  return { 
    poems, 
    dynasties: [...dynasties], 
    genres: [...genres], 
    authors: [...authors],
    counts: {
      songshi: songshiCount,
      songci: songciCount,
      tangshi: tangshiCount
    }
  };
}
async function generateIndex() {
  console.log('Generating lightweight index...');
  const files = fs.readdirSync(DATA_DIR)
    .filter(f => f.match(/poems_chunk_\d+\.csv$/))
    .sort();
  console.log(`Found ${files.length} chunk files`);
  const chunks = [];
  const allDynasties = new Set();
  const allGenres = new Set();
  let totalPoems = 0;
  // 全局分类计数
  let totalSongshi = 0;
  let totalSongci = 0;
  let totalTangshi = 0;
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    const chunkNum = parseInt(file.match(/poems_chunk_(\d+)/)[1]);
    const filePath = path.join(DATA_DIR, file);
    const { poems, dynasties, genres, counts } = extractChunkMetadata(filePath);
    chunks.push({
      id: chunkNum,
      file: file,
      count: poems.length,
      dynasties,
      genres,
      // counts
    });
    dynasties.forEach(d => allDynasties.add(d));
    genres.forEach(g => allGenres.add(g));
    totalPoems += poems.length;
    // 累加全局计数
    totalSongshi += counts.songshi;
    totalSongci += counts.songci;
    totalTangshi += counts.tangshi;
    if ((i + 1) % 50 === 0) {
      console.log(`Processed ${i + 1} chunks...`);
    }
  }
  const index = {
    metadata: {
      total: totalPoems,
      chunks: files.length,
      generatedAt: new Date().toISOString()
    },
    stats: {
      dynasties: [...allDynasties].sort(),
      genres: [...allGenres].sort(),
      counts: {
        songshi: totalSongshi,
        songci: totalSongci,
        tangshi: totalTangshi
      }
    },
    chunks
  };
  fs.writeFileSync(INDEX_FILE, JSON.stringify(index, null, 2));
  const stats = fs.statSync(INDEX_FILE);
  console.log(`\n✅ Index generated successfully!`);
  console.log(`Total poems: ${totalPoems}`);
  console.log(`  - 宋诗 (Song Shi): ${totalSongshi}`);
  console.log(`  - 宋词 (Song Ci): ${totalSongci}`);
  console.log(`  - 唐诗 (Tang Shi): ${totalTangshi}`);
  console.log(`Total chunks: ${files.length}`);
  console.log(`File size: ${(stats.size / 1024 / 1024).toFixed(2)} MB`);
  console.log(`Output: ${INDEX_FILE}`);
}
generateIndex().catch(console.error);
