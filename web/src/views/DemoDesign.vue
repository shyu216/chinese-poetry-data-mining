<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { CopyOutline, DownloadOutline, EyeOutline, ColorPaletteOutline, TextOutline, GridOutline, CodeOutline } from '@vicons/ionicons5'

interface ColorVariable {
  name: string
  value: string
  category: string
}

interface FontVariable {
  name: string
  value: string
}

interface SpacingVariable {
  name: string
  value: string
}

const activeTab = ref<'colors' | 'fonts' | 'spacing' | 'preview' | 'export'>('colors')

const getFontFamily = (fontValue: string): string => {
  const first = fontValue.split(',')[0]
  return first ? first.replace(/"/g, '').replace(/'/g, '') : 'sans-serif'
}

const customColors = reactive<ColorVariable[]>([
  { name: '--ink-black', value: '#0D0D0D', category: 'ink' },
  { name: '--ink-dark', value: '#1A1A1A', category: 'ink' },
  { name: '--ink-medium', value: '#3D3D3D', category: 'ink' },
  { name: '--ink-gray', value: '#6B6B6B', category: 'ink' },
  { name: '--ink-light', value: '#A3A3A3', category: 'ink' },
  { name: '--ink-mist', value: '#D4D4D4', category: 'ink' },
  { name: '--ink-fog', value: '#E8E8E8', category: 'ink' },
  { name: '--paper-white', value: '#FAFAF8', category: 'paper' },
  { name: '--paper-cream', value: '#F5F5F0', category: 'paper' },
  { name: '--accent-teal', value: '#2D6A6A', category: 'accent' },
  { name: '--accent-jade', value: '#3D8B7A', category: 'accent' },
  { name: '--accent-amber', value: '#B8860B', category: 'accent' },
  { name: '--dynasty-tang', value: '#B45309', category: 'dynasty' },
  { name: '--dynasty-song', value: '#1E40AF', category: 'dynasty' },
  { name: '--dynasty-yuan', value: '#047857', category: 'dynasty' },
  { name: '--dynasty-ming', value: '#8B4513', category: 'dynasty' },
])

const customFonts = reactive<FontVariable[]>([
  { name: '--font-serif', value: '"Noto Serif SC", "Source Han Serif SC", "Songti SC", Georgia, serif' },
  { name: '--font-sans', value: '"Noto Sans SC", "Source Han Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif' },
  { name: '--font-mono', value: '"SF Mono", "Fira Code", "Consolas", monospace' },
])

const customSpacing = reactive<SpacingVariable[]>([
  { name: '--space-1', value: '0.25rem' },
  { name: '--space-2', value: '0.5rem' },
  { name: '--space-3', value: '0.75rem' },
  { name: '--space-4', value: '1rem' },
  { name: '--space-5', value: '1.25rem' },
  { name: '--space-6', value: '1.5rem' },
  { name: '--space-8', value: '2rem' },
  { name: '--space-10', value: '2.5rem' },
  { name: '--space-12', value: '3rem' },
  { name: '--space-16', value: '4rem' },
])

const previewStyles = computed(() => {
  const vars: Record<string, string> = {}
  
  customColors.forEach(c => {
    vars[c.name] = c.value
  })
  
  customFonts.forEach(f => {
    vars[f.name] = f.value
  })
  
  customSpacing.forEach(s => {
    vars[s.name] = s.value
  })
  
  vars['--color-primary'] = customColors.find(c => c.name === '--ink-dark')?.value || '#1A1A1A'
  vars['--color-secondary'] = customColors.find(c => c.name === '--ink-gray')?.value || '#6B6B6B'
  vars['--color-accent'] = customColors.find(c => c.name === '--accent-teal')?.value || '#2D6A6A'
  vars['--bg-primary'] = customColors.find(c => c.name === '--paper-white')?.value || '#FAFAF8'
  vars['--bg-secondary'] = customColors.find(c => c.name === '--paper-cream')?.value || '#F5F5F0'
  vars['--bg-card'] = '#FFFFFF'
  vars['--text-base'] = '1rem'
  vars['--text-lg'] = '1.125rem'
  vars['--text-xl'] = '1.25rem'
  vars['--text-2xl'] = '1.5rem'
  vars['--radius-md'] = '8px'
  vars['--radius-lg'] = '12px'
  vars['--shadow-sm'] = '0 1px 2px rgba(0, 0, 0, 0.04)'
  vars['--shadow-md'] = '0 4px 12px rgba(0, 0, 0, 0.06)'
  vars['--shadow-lg'] = '0 8px 24px rgba(0, 0, 0, 0.08)'
  
  return vars
})

const generatedCSS = computed(() => {
  const lines: string[] = []
  
  lines.push(':root {')
  lines.push('  /* ═══════════════════════════════════════════════════════════════')
  lines.push('     水墨诗韵 · 设计系统 - 自定义版本')
  lines.push('  ═══════════════════════════════════════════════════════════════ */')
  lines.push('')
  lines.push('  /* 色彩系统 */')
  customColors.forEach(c => {
    lines.push(`  ${c.name}: ${c.value};`)
  })
  
  lines.push('')
  lines.push('  /* 语义色 */')
  lines.push('  --color-primary: var(--ink-dark);')
  lines.push('  --color-secondary: var(--ink-gray);')
  lines.push('  --color-accent: var(--accent-teal);')
  lines.push('  --color-success: var(--accent-jade);')
  lines.push('  --color-warning: var(--accent-amber);')
  lines.push('')
  lines.push('  /* 背景 */')
  lines.push('  --bg-primary: var(--paper-white);')
  lines.push('  --bg-secondary: var(--paper-cream);')
  lines.push('  --bg-card: #FFFFFF;')
  lines.push('')
  lines.push('  /* 字体 */')
  customFonts.forEach(f => {
    lines.push(`  ${f.name}: ${f.value};`)
  })
  
  lines.push('')
  lines.push('  /* 字号 */')
  lines.push('  --text-xs: 0.75rem;')
  lines.push('  --text-sm: 0.875rem;')
  lines.push('  --text-base: 1rem;')
  lines.push('  --text-lg: 1.125rem;')
  lines.push('  --text-xl: 1.25rem;')
  lines.push('  --text-2xl: 1.5rem;')
  lines.push('  --text-3xl: 1.875rem;')
  lines.push('  --text-4xl: 2.25rem;')
  lines.push('')
  lines.push('  /* 间距 */')
  customSpacing.forEach(s => {
    lines.push(`  ${s.name}: ${s.value};`)
  })
  
  lines.push('')
  lines.push('  /* 圆角 */')
  lines.push('  --radius-sm: 4px;')
  lines.push('  --radius-md: 8px;')
  lines.push('  --radius-lg: 12px;')
  lines.push('  --radius-xl: 16px;')
  lines.push('')
  lines.push('  /* 阴影 */')
  lines.push('  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.04);')
  lines.push('  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.06);')
  lines.push('  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.08);')
  lines.push('  --shadow-float: 0 12px 40px rgba(0, 0, 0, 0.12);')
  lines.push('')
  lines.push('  /* 动画 */')
  lines.push('  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);')
  lines.push('  --duration-fast: 150ms;')
  lines.push('  --duration-normal: 300ms;')
  lines.push('}')
  
  return lines.join('\n')
})

const exportFile = () => {
  const blob = new Blob([generatedCSS.value], { type: 'text/css' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'design-system-custom.css'
  a.click()
  URL.revokeObjectURL(url)
}

const copyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(generatedCSS.value)
    alert('CSS 已复制到剪贴板')
  } catch {
    alert('复制失败')
  }
}

const selectedPreviewItem = ref<'card' | 'button' | 'typography' | 'list'>('card')
</script>

<template>
  <div class="design-studio">
    <div class="studio-sidebar">
      <div class="studio-logo">
        <ColorPaletteOutline />
        <span>墨韵设计室</span>
      </div>
      
      <nav class="studio-nav">
        <button 
          :class="{ active: activeTab === 'colors' }"
          @click="activeTab = 'colors'"
        >
          <ColorPaletteOutline />
          <span>色彩</span>
        </button>
        <button 
          :class="{ active: activeTab === 'fonts' }"
          @click="activeTab = 'fonts'"
        >
          <TextOutline />
          <span>字体</span>
        </button>
        <button 
          :class="{ active: activeTab === 'spacing' }"
          @click="activeTab = 'spacing'"
        >
          <GridOutline />
          <span>间距</span>
        </button>
        <button 
          :class="{ active: activeTab === 'preview' }"
          @click="activeTab = 'preview'"
        >
          <EyeOutline />
          <span>预览</span>
        </button>
        <button 
          :class="{ active: activeTab === 'export' }"
          @click="activeTab = 'export'"
        >
          <CodeOutline />
          <span>导出</span>
        </button>
      </nav>
      
      <div class="studio-actions">
        <button class="action-btn" @click="exportFile" title="导出CSS">
          <DownloadOutline />
        </button>
      </div>
    </div>
    
    <div class="studio-main">
      <div class="studio-header">
        <h2 class="studio-title">
          {{ { colors: '色彩系统', fonts: '字体系统', spacing: '间距系统', preview: '实时预览', export: '导出 CSS' }[activeTab] }}
        </h2>
      </div>
      
      <div class="studio-content">
        <!-- 色彩面板 -->
        <div v-if="activeTab === 'colors'" class="panel-colors">
          <div class="color-category">
            <h3>墨色系</h3>
            <div class="color-grid">
              <div 
                v-for="color in customColors.filter(c => c.category === 'ink')" 
                :key="color.name"
                class="color-item"
              >
                <div 
                  class="color-swatch" 
                  :style="{ backgroundColor: color.value }"
                ></div>
                <div class="color-info">
                  <span class="color-name">{{ color.name }}</span>
                  <input 
                    type="color" 
                    v-model="color.value" 
                    class="color-picker"
                  />
                  <span class="color-value">{{ color.value }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="color-category">
            <h3>纸张色</h3>
            <div class="color-grid">
              <div 
                v-for="color in customColors.filter(c => c.category === 'paper')" 
                :key="color.name"
                class="color-item"
              >
                <div 
                  class="color-swatch" 
                  :style="{ backgroundColor: color.value }"
                ></div>
                <div class="color-info">
                  <span class="color-name">{{ color.name }}</span>
                  <input 
                    type="color" 
                    v-model="color.value" 
                    class="color-picker"
                  />
                  <span class="color-value">{{ color.value }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="color-category">
            <h3>强调色</h3>
            <div class="color-grid">
              <div 
                v-for="color in customColors.filter(c => c.category === 'accent')" 
                :key="color.name"
                class="color-item"
              >
                <div 
                  class="color-swatch" 
                  :style="{ backgroundColor: color.value }"
                ></div>
                <div class="color-info">
                  <span class="color-name">{{ color.name }}</span>
                  <input 
                    type="color" 
                    v-model="color.value" 
                    class="color-picker"
                  />
                  <span class="color-value">{{ color.value }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="color-category">
            <h3>朝代色</h3>
            <div class="color-grid">
              <div 
                v-for="color in customColors.filter(c => c.category === 'dynasty')" 
                :key="color.name"
                class="color-item"
              >
                <div 
                  class="color-swatch" 
                  :style="{ backgroundColor: color.value }"
                ></div>
                <div class="color-info">
                  <span class="color-name">{{ color.name.replace('--dynasty-', '朝代: ') }}</span>
                  <input 
                    type="color" 
                    v-model="color.value" 
                    class="color-picker"
                  />
                  <span class="color-value">{{ color.value }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 字体面板 -->
        <div v-if="activeTab === 'fonts'" class="panel-fonts">
          <div 
            v-for="font in customFonts" 
            :key="font.name"
            class="font-item"
          >
            <label class="font-label">{{ font.name }}</label>
            <input 
              type="text" 
              v-model="font.value" 
              class="font-input"
            />
            <p class="font-preview" :style="{ fontFamily: getFontFamily(font.value) }">
              床前明月光，疑是地上霜。举头望明月，低头思故乡。
            </p>
          </div>
        </div>
        
        <!-- 间距面板 -->
        <div v-if="activeTab === 'spacing'" class="panel-spacing">
          <div 
            v-for="space in customSpacing" 
            :key="space.name"
            class="spacing-item"
          >
            <span class="spacing-name">{{ space.name }}</span>
            <input 
              type="text" 
              v-model="space.value" 
              class="spacing-input"
            />
            <div 
              class="spacing-visual"
              :style="{ width: space.value, height: space.value, backgroundColor: previewStyles['--color-accent'], opacity: 0.6 }"
            ></div>
            <span class="spacing-value">{{ space.value }}</span>
          </div>
        </div>
        
        <!-- 预览面板 -->
        <div v-if="activeTab === 'preview'" class="panel-preview">
          <div class="preview-tabs">
            <button 
              :class="{ active: selectedPreviewItem === 'card' }"
              @click="selectedPreviewItem = 'card'"
            >卡片</button>
            <button 
              :class="{ active: selectedPreviewItem === 'button' }"
              @click="selectedPreviewItem = 'button'"
            >按钮</button>
            <button 
              :class="{ active: selectedPreviewItem === 'typography' }"
              @click="selectedPreviewItem = 'typography'"
            >排版</button>
            <button 
              :class="{ active: selectedPreviewItem === 'list' }"
              @click="selectedPreviewItem = 'list'"
            >列表</button>
          </div>
          
          <div 
            class="preview-area"
            :style="previewStyles"
          >
            <!-- 卡片预览 -->
            <div v-if="selectedPreviewItem === 'card'" class="preview-card">
              <div class="preview-poem-card">
                <div class="poem-header">
                  <span class="dynasty-tag" :style="{ backgroundColor: previewStyles['--dynasty-tang'] }">唐</span>
                  <span class="poem-title">静夜思</span>
                </div>
                <p class="poem-content">
                  床前明月光，<br/>
                  疑是地上霜。<br/>
                  举头望明月，<br/>
                  低头思故乡。
                </p>
                <div class="poem-author">李白</div>
              </div>
            </div>
            
            <!-- 按钮预览 -->
            <div v-if="selectedPreviewItem === 'button'" class="preview-buttons">
              <button class="btn btn-primary">主要按钮</button>
              <button class="btn btn-secondary">次要按钮</button>
              <button class="btn btn-outline">边框按钮</button>
              <button class="btn btn-ghost">幽灵按钮</button>
            </div>
            
            <!-- 排版预览 -->
            <div v-if="selectedPreviewItem === 'typography'" class="preview-typography">
              <h1 :style="{ fontFamily: previewStyles['--font-serif'] }">标题一</h1>
              <h2 :style="{ fontFamily: previewStyles['--font-serif'] }">标题二</h2>
              <h3 :style="{ fontFamily: previewStyles['--font-serif'] }">标题三</h3>
              <p :style="{ fontFamily: previewStyles['--font-sans'] }">正文内容：床前明月光，疑是地上霜。举头望明月，低头思故乡。</p>
              <code :style="{ fontFamily: previewStyles['--font-mono'] }">code: const poem = "静夜思";</code>
            </div>
            
            <!-- 列表预览 -->
            <div v-if="selectedPreviewItem === 'list'" class="preview-list">
              <div class="list-item">
                <span class="list-rank">1</span>
                <span class="list-title">静夜思</span>
                <span class="list-subtitle">李白</span>
              </div>
              <div class="list-item">
                <span class="list-rank">2</span>
                <span class="list-title">春晓</span>
                <span class="list-subtitle">孟浩然</span>
              </div>
              <div class="list-item">
                <span class="list-rank">3</span>
                <span class="list-title">登鹳雀楼</span>
                <span class="list-subtitle">王之涣</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 导出面板 -->
        <div v-if="activeTab === 'export'" class="panel-export">
          <div class="export-actions">
            <button class="btn btn-export" @click="copyToClipboard">
              <CopyOutline />
              复制到剪贴板
            </button>
            <button class="btn btn-export btn-primary" @click="exportFile">
              <DownloadOutline />
              下载 CSS 文件
            </button>
          </div>
          <div class="code-block">
            <pre>{{ generatedCSS }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.design-studio {
  display: flex;
  height: calc(100vh - 64px);
  background: var(--bg-primary);
}

.studio-sidebar {
  width: 220px;
  background: var(--bg-secondary);
  border-right: var(--border-light);
  display: flex;
  flex-direction: column;
  padding: var(--space-4);
}

.studio-logo {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3);
  font-family: var(--font-serif);
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-primary);
  margin-bottom: var(--space-4);
}

.studio-logo :deep(svg) {
  width: 24px;
  height: 24px;
}

.studio-nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  flex: 1;
}

.studio-nav button {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border: none;
  background: transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: var(--text-sm);
  color: var(--color-secondary);
  transition: all var(--duration-fast) var(--ease-out-quart);
}

.studio-nav button:hover {
  background: var(--ink-fog);
  color: var(--color-primary);
}

.studio-nav button.active {
  background: var(--color-accent);
  color: white;
}

.studio-nav button :deep(svg) {
  width: 18px;
  height: 18px;
}

.studio-actions {
  padding-top: var(--space-4);
  border-top: var(--border-light);
}

.action-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-2);
  border: var(--border-medium);
  background: var(--bg-card);
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--color-secondary);
  transition: all var(--duration-fast);
}

.action-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.action-btn :deep(svg) {
  width: 20px;
  height: 20px;
}

.studio-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.studio-header {
  padding: var(--space-4) var(--space-6);
  border-bottom: var(--border-light);
}

.studio-title {
  font-family: var(--font-serif);
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--color-primary);
}

.studio-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6);
}

.panel-colors {
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}

.color-category h3 {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-secondary);
  margin-bottom: var(--space-3);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.color-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: var(--space-3);
}

.color-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2);
  background: var(--bg-card);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}

.color-swatch {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  border: 1px solid var(--ink-fog);
}

.color-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.color-name {
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.color-picker {
  width: 20px;
  height: 20px;
  border: none;
  padding: 0;
  cursor: pointer;
  background: transparent;
}

.color-value {
  font-size: 10px;
  color: var(--color-secondary);
  font-family: var(--font-mono);
}

.panel-fonts {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.font-item {
  padding: var(--space-4);
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.font-label {
  display: block;
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-primary);
  margin-bottom: var(--space-2);
}

.font-input {
  width: 100%;
  padding: var(--space-2) var(--space-3);
  border: var(--border-medium);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-family: var(--font-mono);
  margin-bottom: var(--space-3);
}

.font-preview {
  font-size: var(--text-lg);
  line-height: 1.8;
  color: var(--color-primary);
}

.panel-spacing {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.spacing-item {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-2) var(--space-3);
  background: var(--bg-card);
  border-radius: var(--radius-md);
}

.spacing-name {
  width: 100px;
  font-size: var(--text-sm);
  font-family: var(--font-mono);
  color: var(--color-primary);
}

.spacing-input {
  width: 100px;
  padding: var(--space-1) var(--space-2);
  border: var(--border-medium);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  font-family: var(--font-mono);
}

.spacing-visual {
  min-width: 8px;
  min-height: 8px;
  border-radius: 2px;
}

.spacing-value {
  font-size: var(--text-sm);
  color: var(--color-secondary);
  font-family: var(--font-mono);
  min-width: 60px;
}

.panel-preview {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.preview-tabs {
  display: flex;
  gap: var(--space-2);
}

.preview-tabs button {
  padding: var(--space-2) var(--space-4);
  border: var(--border-medium);
  background: transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: var(--text-sm);
  color: var(--color-secondary);
  transition: all var(--duration-fast);
}

.preview-tabs button:hover {
  border-color: var(--color-accent);
}

.preview-tabs button.active {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: white;
}

.preview-area {
  padding: var(--space-8);
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  min-height: 400px;
}

.preview-card {
  display: flex;
  justify-content: center;
}

.preview-poem-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-lg);
  max-width: 400px;
}

.preview-poem-card .poem-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.dynasty-tag {
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  color: white;
  font-size: var(--text-xs);
  font-weight: 600;
}

.poem-title {
  font-family: var(--font-serif);
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--color-primary);
}

.poem-content {
  font-family: var(--font-serif);
  font-size: var(--text-lg);
  line-height: 2;
  color: var(--color-primary);
  margin-bottom: var(--space-4);
}

.poem-author {
  font-size: var(--text-sm);
  color: var(--color-secondary);
  text-align: right;
}

.preview-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4);
  justify-content: center;
}

.preview-typography {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.preview-typography h1 {
  font-size: var(--text-4xl);
  font-weight: 600;
}

.preview-typography h2 {
  font-size: var(--text-3xl);
  font-weight: 600;
}

.preview-typography h3 {
  font-size: var(--text-2xl);
  font-weight: 600;
}

.preview-typography p {
  font-size: var(--text-base);
  line-height: 1.8;
}

.preview-typography code {
  padding: var(--space-2) var(--space-3);
  background: var(--ink-fog);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
}

.preview-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.panel-export {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.export-actions {
  display: flex;
  gap: var(--space-3);
}

.btn-export {
  flex: 1;
}

@media (max-width: 768px) {
  .design-studio {
    flex-direction: column;
  }
  
  .studio-sidebar {
    width: 100%;
    flex-direction: row;
    align-items: center;
    padding: var(--space-2);
  }
  
  .studio-logo {
    margin-bottom: 0;
    padding: var(--space-2);
  }
  
  .studio-nav {
    flex-direction: row;
    flex: 1;
    justify-content: center;
  }
  
  .studio-actions {
    padding: 0;
    border: none;
  }
  
  .studio-nav button span {
    display: none;
  }
}
</style>
