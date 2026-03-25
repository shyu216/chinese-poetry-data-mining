/**
 * script: 05_patch-poem-index-with-chunk.cjs
 * stage: P4-检索索引构建
 * artifact: 带 chunk_id 的 poem_index
 * purpose: 为 poem_index 条目补齐 chunk_id 以加速跳转读取。
 * inputs:
 * - results/poem_index
 * - results/preprocessed
 * outputs:
 * - results/poem_index
 * depends_on:
 * - 05_generate-poem-index.cjs
 * - 01_generate-poem-chunk-meta.cjs
 * develop_date: 2026-03-22
 * last_modified_date: 2026-03-22
 */
const fs = require('fs');
const path = require('path');
const POEM_INDEX_DIR = path.join(__dirname, '../results/poem_index');
const CHUNK_DIR = path.join(__dirname, '../results/preprocessed');
const CHUNK_META_FILE = path.join(CHUNK_DIR, 'poems_chunk_meta.json');
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
/**
 * 从所有 chunk CSV 文件中提取 poem_id -> chunk_id 的映射
 */
async function buildPoemToChunkMap() {
  console.log('Building poem_id -> chunk_id mapping...');
  const poemToChunkMap = new Map();
  // 读取所有 chunk 文件
  const files = fs.readdirSync(CHUNK_DIR)
    .filter((f) => f.match(/poems_chunk_\d+\.csv$/))
    .sort();
  console.log(`Found ${files.length} chunk files`);
  for (const file of files) {
    const chunkMatch = file.match(/poems_chunk_(\d+)\.csv$/);
    if (!chunkMatch) continue;
    const chunkId = parseInt(chunkMatch[1], 10);
    const filePath = path.join(CHUNK_DIR, file);
    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.trim().split('\n');
    const dataLines = lines.slice(1); // 跳过表头
    for (const line of dataLines) {
      const cols = parseCSVLine(line);
      if (cols.length < 1) continue;
      const poemId = cols[0];
      if (poemId) {
        poemToChunkMap.set(poemId, chunkId);
      }
    }
    if (chunkId % 50 === 0) {
      console.log(`  Processed chunk ${chunkId}, total mappings: ${poemToChunkMap.size}`);
    }
  }
  console.log(`✅ Built ${poemToChunkMap.size} poem_id -> chunk_id mappings`);
  return poemToChunkMap;
}
/**
 * 更新单个 poem_index 文件，添加 chunk_id 字段
 */
async function patchPoemIndexFile(filePath, poemToChunkMap) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const poems = JSON.parse(content);
  let patchedCount = 0;
  let missingCount = 0;
  for (const [poemId, poemData] of Object.entries(poems)) {
    if (poemToChunkMap.has(poemId)) {
      poemData.chunk_id = poemToChunkMap.get(poemId);
      patchedCount++;
    } else {
      console.warn(`  ⚠️  Missing chunk mapping for poem: ${poemId}`);
      missingCount++;
    }
  }
  fs.writeFileSync(filePath, JSON.stringify(poems, null, 2));
  return { patchedCount, missingCount };
}
/**
 * 更新 poem_index_manifest.json，添加 chunk 相关信息
 */
async function updateManifest() {
  const manifestPath = path.join(POEM_INDEX_DIR, 'poem_index_manifest.json');
  if (!fs.existsSync(manifestPath)) {
    console.warn('⚠️  Manifest file not found, skipping manifest update');
    return;
  }
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
  manifest.metadata.hasChunkIds = true;
  manifest.metadata.chunkMappingVersion = '1.0';
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
  console.log('✅ Updated manifest with chunk mapping info');
}
/**
 * 主函数
 */
async function main() {
  console.log('========================================');
  console.log('Patching poem_index with chunk_id');
  console.log('========================================\n');
  const poemToChunkMap = await buildPoemToChunkMap();
  const indexFiles = fs.readdirSync(POEM_INDEX_DIR)
    .filter((f) => f.match(/^poems_[a-f0-9]{2}\.json$/))
    .sort();
  console.log(`\nFound ${indexFiles.length} poem_index files to patch\n`);
  let totalPatched = 0;
  let totalMissing = 0;
  for (let i = 0; i < indexFiles.length; i++) {
    const fileName = indexFiles[i];
    const filePath = path.join(POEM_INDEX_DIR, fileName);
    process.stdout.write(`[${i + 1}/${indexFiles.length}] Patching ${fileName}... `);
    const { patchedCount, missingCount } = await patchPoemIndexFile(filePath, poemToChunkMap);
    totalPatched += patchedCount;
    totalMissing += missingCount;
    console.log(`+${patchedCount} chunk_ids${missingCount > 0 ? ` (${missingCount} missing)` : ''}`);
  }
  await updateManifest();
  console.log('\n========================================');
  console.log('Patching complete!');
  console.log('========================================');
  console.log(`Total poems patched: ${totalPatched}`);
  console.log(`Total missing mappings: ${totalMissing}`);
  console.log('\nNext step: Update web/src/composables/usePoemsV2.ts to use chunk_id for faster lookup');
}
// 运行
main().catch((err) => {
  console.error('Error:', err);
  process.exit(1);
});
