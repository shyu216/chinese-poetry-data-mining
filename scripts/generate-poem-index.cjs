const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, '../results/preprocessed');
const OUTPUT_DIR = path.join(__dirname, '../results/poem_index');
const POEM_INDEX_DIR = OUTPUT_DIR;

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

function extractMetadataFromCSV(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.trim().split('\n');

  const dataLines = lines.slice(1);
  const poems = [];

  for (const line of dataLines) {
    const cols = parseCSVLine(line);
    if (cols.length < 10) continue;

    const [id, title, author, dynasty, genre, poemType, sentences, meterPattern] = cols;

    poems.push({
      id,
      title: title || '',
      author: author || '佚名',
      dynasty,
      genre,
      poem_type: poemType,
      meter_pattern: meterPattern
    });
  }

  return poems;
}

function getPrefixFromId(id) {
  // 取 ID 的前 2 个字符作为前缀 (256 个分块)
  return id.substring(0, 2).toLowerCase();
}

async function generatePoemIndex() {
  console.log('Generating poem index...');

  // 确保输出目录存在
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }
  if (!fs.existsSync(POEM_INDEX_DIR)) {
    fs.mkdirSync(POEM_INDEX_DIR, { recursive: true });
  }

  const allPoems = [];
  const poemsByPrefix = new Map();
  let chunkCount = 0;

  // 查找所有 chunk 文件
  const files = fs.readdirSync(DATA_DIR)
    .filter(f => f.match(/poems_chunk_\d+\.csv$/))
    .sort();

  console.log(`Found ${files.length} chunk files`);

  for (const file of files) {
    const filePath = path.join(DATA_DIR, file);
    const poems = extractMetadataFromCSV(filePath);
    allPoems.push(...poems);
    chunkCount++;

    // 按前缀分组
    for (const poem of poems) {
      const prefix = getPrefixFromId(poem.id);
      if (!poemsByPrefix.has(prefix)) {
        poemsByPrefix.set(prefix, []);
      }
      poemsByPrefix.get(prefix).push(poem);
    }

    if (chunkCount % 50 === 0) {
      console.log(`Processed ${chunkCount} chunks, ${allPoems.length} poems so far...`);
    }
  }

  // 写入分块文件
  let indexFileCount = 0;
  const prefixToFileMap = {};

  for (const [prefix, poems] of poemsByPrefix) {
    const fileName = `poems_${prefix}.json`;
    const filePath = path.join(POEM_INDEX_DIR, fileName);

    // 转换为 Map 格式便于查找: { id: poem }
    const poemMap = {};
    for (const poem of poems) {
      poemMap[poem.id] = poem;
    }

    fs.writeFileSync(filePath, JSON.stringify(poemMap, null, 2));
    prefixToFileMap[prefix] = fileName;
    indexFileCount++;

    if (indexFileCount % 50 === 0) {
      console.log(`Written ${indexFileCount} index files...`);
    }
  }

  // 生成 manifest.json
  const manifest = {
    metadata: {
      total: allPoems.length,
      chunks: chunkCount,
      indexFiles: indexFileCount,
      prefixLength: 2,
      generatedAt: new Date().toISOString()
    },
    prefixMap: prefixToFileMap
  };

  fs.writeFileSync(
    path.join(OUTPUT_DIR, 'poem_index_manifest.json'),
    JSON.stringify(manifest, null, 2)
  );

  // 统计信息
  const fileSizes = Array.from(poemsByPrefix.values()).map(poems => poems.length);
  const avgSize = fileSizes.reduce((a, b) => a + b, 0) / fileSizes.length;
  const maxSize = Math.max(...fileSizes);
  const minSize = Math.min(...fileSizes);

  console.log(`\n✅ Poem index generated successfully!`);
  console.log(`Total poems: ${allPoems.length}`);
  console.log(`Total chunks: ${chunkCount}`);
  console.log(`Index files: ${indexFileCount}`);
  console.log(`Avg poems per file: ${Math.round(avgSize)}`);
  console.log(`Max poems in file: ${maxSize}`);
  console.log(`Min poems in file: ${minSize}`);
  console.log(`Output: ${POEM_INDEX_DIR}`);
  console.log(`Manifest: ${path.join(OUTPUT_DIR, 'poem_index_manifest.json')}`);
}

generatePoemIndex().catch(console.error);
