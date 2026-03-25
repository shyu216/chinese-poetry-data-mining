/**
 * script: 05_fix-poem-index-dynasty.cjs
 * stage: P4-检索索引修补
 * artifact: 朝代修复后的 poem-index
 * purpose: 按 poem id 前缀修复 poem-index 中的朝代字段。
 * inputs:
 * - web/public/poem-index.json
 * outputs:
 * - web/public/poem-index.fixed.json
 * depends_on:
 * - 05_generate-poem-index.cjs
 * develop_date: 2026-03-24
 * last_modified_date: 2026-03-24
 */
const fs = require('fs');
const path = require('path');
const POEM_INDEX_FILE = path.join(__dirname, '../web/public/poem-index.json');
const OUTPUT_FILE = path.join(__dirname, '../web/public/poem-index.fixed.json');
function fixDynasty(poem) {
  const id = poem.id.toLowerCase();
  // 基于 ID 前缀判断朝代
  if (id.startsWith('song')) {
    return '宋';
  } else if (id.startsWith('tang')) {
    return '唐';
  }
  // 保持原有朝代（如果不是 song 或 tang 开头）
  return poem.dynasty;
}
function main() {
  console.log('========================================');
  console.log('Fixing poem-index dynasty information');
  console.log('========================================\n');
  try {
    // 1. 读取 poem-index.json 文件
    console.log(`Reading poem-index.json from: ${POEM_INDEX_FILE}`);
    const content = fs.readFileSync(POEM_INDEX_FILE, 'utf-8');
    const data = JSON.parse(content);
    console.log(`Found ${data.poems?.length || 0} poems in the index`);
    if (!data.poems || !Array.isArray(data.poems)) {
      console.error('❌ Invalid poem-index.json format');
      process.exit(1);
    }
    // 2. 统计修复前的朝代分布
    const beforeStats = {
      total: data.poems.length,
      唐: 0,
      宋: 0,
      other: 0
    };
    data.poems.forEach(poem => {
      if (poem.dynasty === '唐') {
        beforeStats.唐++;
      } else if (poem.dynasty === '宋') {
        beforeStats.宋++;
      } else {
        beforeStats.other++;
      }
    });
    console.log('\nBefore fix:');
    console.log(`  Total poems: ${beforeStats.total}`);
    console.log(`  唐诗: ${beforeStats.唐.toLocaleString()}`);
    console.log(`  宋诗: ${beforeStats.宋.toLocaleString()}`);
    console.log(`  其他: ${beforeStats.other.toLocaleString()}`);
    // 3. 修复朝代信息
    console.log('\nFixing dynasty information...');
    let fixedCount = 0;
    data.poems.forEach(poem => {
      const oldDynasty = poem.dynasty;
      const newDynasty = fixDynasty(poem);
      if (oldDynasty !== newDynasty) {
        poem.dynasty = newDynasty;
        fixedCount++;
      }
    });
    console.log(`Fixed ${fixedCount} poems`);
    // 4. 统计修复后的朝代分布
    const afterStats = {
      total: data.poems.length,
      唐: 0,
      宋: 0,
      other: 0
    };
    data.poems.forEach(poem => {
      if (poem.dynasty === '唐') {
        afterStats.唐++;
      } else if (poem.dynasty === '宋') {
        afterStats.宋++;
      } else {
        afterStats.other++;
      }
    });
    console.log('\nAfter fix:');
    console.log(`  Total poems: ${afterStats.total}`);
    console.log(`  唐诗: ${afterStats.唐.toLocaleString()}`);
    console.log(`  宋诗: ${afterStats.宋.toLocaleString()}`);
    console.log(`  其他: ${afterStats.other.toLocaleString()}`);
    // 5. 生成修正后的文件
    data.metadata.fixedAt = new Date().toISOString();
    data.metadata.fixedCount = fixedCount;
    fs.writeFileSync(OUTPUT_FILE, JSON.stringify(data, null, 2));
    console.log(`\n✅ Fixed poem-index.json saved to: ${OUTPUT_FILE}`);
    // 6. 替换原文件
    fs.copyFileSync(OUTPUT_FILE, POEM_INDEX_FILE);
    console.log(`✅ Replaced original poem-index.json`);
    console.log('\n========================================');
    console.log('Fix completed!');
    console.log('========================================');
    console.log(`Total poems: ${afterStats.total}`);
    console.log(`  - 唐诗: ${afterStats.唐.toLocaleString()}`);
    console.log(`  - 宋诗: ${afterStats.宋.toLocaleString()}`);
    console.log(`  - 其他: ${afterStats.other.toLocaleString()}`);
    console.log(`Fixed ${fixedCount} poems`);
  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  }
}
// 运行
main();
