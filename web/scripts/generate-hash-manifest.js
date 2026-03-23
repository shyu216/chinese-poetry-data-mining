#!/usr/bin/env node
/**
 * 生成数据文件的 hash manifest
 * 在构建时运行，为所有数据文件生成 SHA-256 hash
 */

import fs from 'fs/promises'
import { createReadStream } from 'fs'
import path from 'path'
import crypto from 'crypto'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const DATA_DIR = path.resolve(__dirname, '../public/data')
const MANIFEST_PATH = path.resolve(DATA_DIR, 'hash-manifest.json')

// 需要计算 hash 的文件扩展名
const INCLUDE_EXTENSIONS = ['.json', '.csv', '.txt', '.bin']
// 排除的文件
const EXCLUDE_FILES = ['hash-manifest.json', 'manifest.json']
// 大文件阈值 (10MB)，使用流式读取
const LARGE_FILE_THRESHOLD = 10 * 1024 * 1024

/**
 * 使用流式读取计算大文件的 SHA-256 hash
 */
async function hashLargeFile(filePath) {
  return new Promise((resolve, reject) => {
    const hash = crypto.createHash('sha256')
    const stream = createReadStream(filePath)

    stream.on('error', reject)
    stream.on('data', chunk => hash.update(chunk))
    stream.on('end', () => {
      const hex = hash.digest('hex')
      resolve(hex.slice(0, 16))
    })
  })
}

/**
 * 计算文件的 SHA-256 hash
 */
async function hashFile(filePath) {
  const stats = await fs.stat(filePath)

  if (stats.size > LARGE_FILE_THRESHOLD) {
    // 大文件使用流式读取
    return hashLargeFile(filePath)
  }

  // 小文件直接读取
  const content = await fs.readFile(filePath)
  const hash = crypto.createHash('sha256').update(content).digest('hex')
  // 只取前 16 位，足够用于校验且减少 manifest 大小
  return hash.slice(0, 16)
}

/**
 * 递归扫描目录获取所有数据文件
 */
async function scanDirectory(dir, baseDir = dir) {
  const files = []
  const entries = await fs.readdir(dir, { withFileTypes: true })

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name)
    const relativePath = path.relative(baseDir, fullPath).replace(/\\/g, '/')

    if (entry.isDirectory()) {
      const subFiles = await scanDirectory(fullPath, baseDir)
      files.push(...subFiles)
    } else if (
      INCLUDE_EXTENSIONS.some(ext => entry.name.endsWith(ext)) &&
      !EXCLUDE_FILES.includes(entry.name)
    ) {
      files.push(relativePath)
    }
  }

  return files
}

/**
 * 生成 manifest
 */
async function generateManifest() {
  console.log('🔍 Scanning data files...')

  try {
    await fs.access(DATA_DIR)
  } catch {
    console.log('⚠️ Data directory not found, skipping manifest generation')
    return
  }

  const files = await scanDirectory(DATA_DIR)
  console.log(`📁 Found ${files.length} data files`)

  const manifest = {
    version: new Date().toISOString(),
    generatedAt: Date.now(),
    files: {}
  }

  // 串行计算所有文件的 hash（避免同时打开太多文件）
  const results = []
  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    const filePath = path.join(DATA_DIR, file)
    const hash = await hashFile(filePath)
    results.push({ file, hash })

    // 每处理 100 个文件显示进度
    if ((i + 1) % 100 === 0 || i === files.length - 1) {
      process.stdout.write(`\r⏳ Processing: ${i + 1}/${files.length} files...`)
    }
  }
  console.log() // 换行

  for (const { file, hash } of results) {
    manifest.files[file] = hash
  }

  // 写入 manifest 文件
  await fs.writeFile(
    MANIFEST_PATH,
    JSON.stringify(manifest, null, 2),
    'utf-8'
  )

  console.log(`✅ Manifest generated: ${MANIFEST_PATH}`)
  console.log(`📊 Total files: ${Object.keys(manifest.files).length}`)
}

// 运行
generateManifest().catch(err => {
  console.error('❌ Failed to generate manifest:', err)
  process.exit(1)
})
