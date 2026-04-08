/**
 * script: 06_patch-keyword-index-with-chunk.cjs
 * stage: P4-检索索引构建（补丁）
 * purpose: 为 keyword_index 注入 chunk 信息，避免前端二次查询
 * 
 * 数据流程:
 * - 输入: keyword_index/*.json (关键词 -> poem_ids) + poem_index/*.json (已打补丁，含 chunk_id)
 * - 输出: keyword_index/*.json (关键词 -> [{id, chunk_id}, ...])
 * 
 * 输入:
 * - results/keyword_index
 * - results/poem_index（需先执行 05_patch-poem-index-with-chunk.cjs）
 * 
 * 输出:
 * - results/keyword_index/*.json
 * 
 * depends_on:
 * - 05_patch-poem-index-with-chunk.cjs
 * 
 * develop_date: 2026-04-08
 * last_modified_date: 2026-04-08
 */

const fs = require('fs');
const path = require('path');

const KEYWORD_INDEX_DIR = path.join(__dirname, '../results/keyword_index');
const POEM_INDEX_DIR = path.join(__dirname, '../results/poem_index');

/**
 * 加载 poem_index 缓存（poem_id -> chunk_id 映射）
 * 由于 poem_index 已打补丁，我们可以直接从文件中提取
 */
async function loadPoemChunkMap() {
  console.log('Loading poem_id -> chunk_id mapping from poem_index...');
  const poemToChunkMap = new Map();
  
  const files = fs.readdirSync(POEM_INDEX_DIR)
    .filter(f => f.match(/^poems_[a-f0-9]{2}\.json$/))
    .sort();
  
  console.log(`Found ${files.length} poem_index files`);
  
  for (let i = 0; i < files.length; i++) {
    const fileName = files[i];
    const filePath = path.join(POEM_INDEX_DIR, fileName);
    
    try {
      const content = fs.readFileSync(filePath, 'utf-8');
      const poems = JSON.parse(content);
      
      for (const [poemId, poemData] of Object.entries(poems)) {
        if (poemData.chunk_id !== undefined) {
          poemToChunkMap.set(poemId, poemData.chunk_id);
        }
      }
    } catch (e) {
      console.warn(`  ⚠️  Error reading ${fileName}: ${e.message}`);
    }
    
    if ((i + 1) % 50 === 0) {
      console.log(`  Processed ${i + 1}/${files.length} files, ${poemToChunkMap.size} mappings`);
    }
  }
  
  console.log(`✅ Loaded ${poemToChunkMap.size} poem_id -> chunk_id mappings`);
  return poemToChunkMap;
}

/**
 * 检查 poem_index 是否已打补丁（有 chunk_id）
 */
async function checkPoemIndexPatched() {
  const sampleFile = path.join(POEM_INDEX_DIR, 'poems_00.json');
  if (!fs.existsSync(sampleFile)) {
    throw new Error('poem_index not found. Please run 05_patch-poem-index-with-chunk.cjs first.');
  }
  
  const content = fs.readFileSync(sampleFile, 'utf-8');
  const poems = JSON.parse(content);
  const firstPoem = Object.values(poems)[0];
  
  if (!firstPoem || firstPoem.chunk_id === undefined) {
    throw new Error('poem_index not patched yet. Please run 05_patch-poem-index-with-chunk.cjs first.');
  }
  
  return true;
}

/**
 * 更新单个 keyword_index 文件
 */
async function patchKeywordIndexFile(filePath, poemToChunkMap) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const keywordData = JSON.parse(content);
  
  let totalPoems = 0;
  let patchedPoems = 0;
  let missingPoems = 0;
  
  const newKeywordData = {};
  
  for (const [keyword, poemIds] of Object.entries(keywordData)) {
    if (!Array.isArray(poemIds)) {
      newKeywordData[keyword] = poemIds;
      continue;
    }
    
    totalPoems += poemIds.length;
    const newPoemRefs = [];
    
    for (const poemId of poemIds) {
      const chunkId = poemToChunkMap.get(poemId);
      
      if (chunkId !== undefined) {
        newPoemRefs.push({
          id: poemId,
          chunk_id: chunkId
        });
        patchedPoems++;
      } else {
        missingPoems++;
      }
    }
    
    newKeywordData[keyword] = newPoemRefs;
  }
  
  fs.writeFileSync(filePath, JSON.stringify(newKeywordData, null, 2));
  
  return { totalPoems, patchedPoems, missingPoems };
}

/**
 * 更新 manifest
 */
async function updateManifest() {
  const manifestPath = path.join(KEYWORD_INDEX_DIR, 'keyword_manifest.json');
  
  if (!fs.existsSync(manifestPath)) {
    console.warn('⚠️  Manifest file not found, skipping manifest update');
    return;
  }
  
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
  
  if (!manifest.metadata) {
    manifest.metadata = {};
  }
  
  manifest.metadata.hasChunkRefs = true;
  manifest.metadata.chunkRefVersion = '1.0';
  manifest.metadata.patchedAt = new Date().toISOString();
  
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
  console.log('✅ Updated manifest with chunk ref info');
}

/**
 * 主函数
 */
async function main() {
  console.log('========================================');
  console.log('Patching keyword_index with chunk refs');
  console.log('========================================\n');
  
  // Step 1: 检查 poem_index 是否已打补丁
  console.log('Step 1: Checking poem_index patch status...');
  try {
    await checkPoemIndexPatched();
    console.log('✅ poem_index is patched\n');
  } catch (e) {
    console.error(`❌ ${e.message}`);
    process.exit(1);
  }
  
  // Step 2: 加载 poem_id -> chunk_id 映射
  console.log('Step 2: Loading poem chunk mapping...');
  const poemToChunkMap = await loadPoemChunkMap();
  console.log();
  
  // Step 3: 处理所有 keyword_index 文件
  const indexFiles = fs.readdirSync(KEYWORD_INDEX_DIR)
    .filter(f => f.match(/^keyword_\d+\.json$/))
    .sort();
  
  console.log(`Step 3: Processing ${indexFiles.length} keyword_index files\n`);
  
  let totalPoems = 0;
  let totalPatched = 0;
  let totalMissing = 0;
  
  for (let i = 0; i < indexFiles.length; i++) {
    const fileName = indexFiles[i];
    const filePath = path.join(KEYWORD_INDEX_DIR, fileName);
    
    process.stdout.write(`[${i + 1}/${indexFiles.length}] Patching ${fileName}... `);
    
    const { totalPoems: fileTotal, patchedPoems, missingPoems } = 
      await patchKeywordIndexFile(filePath, poemToChunkMap);
    
    totalPoems += fileTotal;
    totalPatched += patchedPoems;
    totalMissing += missingPoems;
    
    console.log(`+${patchedPoems} refs${missingPoems > 0 ? ` (${missingPoems} missing)` : ''}`);
    
    // 每 100 个文件输出进度
    if ((i + 1) % 100 === 0) {
      console.log(`\n  📊 Progress: ${i + 1}/${indexFiles.length} files`);
      console.log(`     Total poems: ${totalPoems}, Patched: ${totalPatched}, Missing: ${totalMissing}\n`);
    }
  }
  
  // Step 4: 更新 manifest
  console.log('\nStep 4: Updating manifest...');
  await updateManifest();
  
  console.log('\n========================================');
  console.log('Patching complete!');
  console.log('========================================');
  console.log(`Total keyword files processed: ${indexFiles.length}`);
  console.log(`Total poem references: ${totalPoems}`);
  console.log(`Successfully patched: ${totalPatched}`);
  console.log(`Missing chunk mappings: ${totalMissing}`);
  
  if (totalMissing > 0) {
    console.log(`\n⚠️  Warning: ${totalMissing} poems don't have chunk mappings.`);
    console.log(`   This is normal for poems that weren't in the preprocessed chunks.`);
  }
  
  console.log('\n✅ Next step: Update web/src/composables to use new chunk ref format');
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
