const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, '../public/data/preprocessed');
const OUTPUT_FILE = path.join(DATA_DIR, 'summary.json');

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
  
  // Skip header
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

async function generateSummary() {
  console.log('Generating summary.json...');
  
  const allPoems = [];
  let chunkCount = 0;
  
  // Find all chunk files
  const files = fs.readdirSync(DATA_DIR)
    .filter(f => f.match(/poems_chunk_\d+\.csv$/))
    .sort();
  
  console.log(`Found ${files.length} chunk files`);
  
  for (const file of files) {
    const filePath = path.join(DATA_DIR, file);
    const poems = extractMetadataFromCSV(filePath);
    allPoems.push(...poems);
    chunkCount++;
    
    if (chunkCount % 50 === 0) {
      console.log(`Processed ${chunkCount} chunks, ${allPoems.length} poems so far...`);
    }
  }
  
  const summary = {
    metadata: {
      total: allPoems.length,
      chunks: chunkCount,
      generatedAt: new Date().toISOString()
    },
    poems: allPoems
  };
  
  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(summary, null, 2));
  
  console.log(`\n✅ Summary generated successfully!`);
  console.log(`Total poems: ${allPoems.length}`);
  console.log(`Total chunks: ${chunkCount}`);
  console.log(`Output: ${OUTPUT_FILE}`);
}

generateSummary().catch(console.error);
