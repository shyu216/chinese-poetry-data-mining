const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, '../public/data/preprocessed');
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
  }
  
  return { poems, dynasties: [...dynasties], genres: [...genres], authors: [...authors] };
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
  
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    const chunkNum = parseInt(file.match(/poems_chunk_(\d+)/)[1]);
    const filePath = path.join(DATA_DIR, file);
    const { poems, dynasties, genres } = extractChunkMetadata(filePath);
    
    chunks.push({
      id: chunkNum,
      file: file,
      count: poems.length,
      dynasties,
      genres
    });
    
    dynasties.forEach(d => allDynasties.add(d));
    genres.forEach(g => allGenres.add(g));
    totalPoems += poems.length;
    
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
      genres: [...allGenres].sort()
    },
    chunks
  };
  
  fs.writeFileSync(INDEX_FILE, JSON.stringify(index, null, 2));
  
  const stats = fs.statSync(INDEX_FILE);
  console.log(`\n✅ Index generated successfully!`);
  console.log(`Total poems: ${totalPoems}`);
  console.log(`Total chunks: ${files.length}`);
  console.log(`File size: ${(stats.size / 1024 / 1024).toFixed(2)} MB`);
  console.log(`Output: ${INDEX_FILE}`);
}

generateIndex().catch(console.error);
