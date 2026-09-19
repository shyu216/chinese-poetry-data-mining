/**
 * 文件: web/src/composables/useTheme.ts
 * 说明: 主题（浅色 / 深色）单例管理。
 *       初始 data-theme 由 index.html 内联脚本在首屏绘制前设定（避免闪烁），
 *       本组合式负责同步响应式状态、切换并持久化到 localStorage。
 *
 * 数据流: index.html 设定 <html data-theme> -> useTheme.syncFromDom() 同步 ->
 *         toggleTheme() 翻转并写回 DOM + localStorage -> 设计系统 CSS 变量自动适配。
 *
 * 复杂度: O(1)，仅维护一个模块级响应式布尔 + DOM 属性读写。
 */
import { ref } from 'vue'

export type ThemeMode = 'light' | 'dark'

const STORAGE_KEY = 'cpdm-theme'

// 模块级单例：保证全应用只有一份主题状态
const isDark = ref<boolean>(false)

function syncFromDom(): void {
  isDark.value = document.documentElement.getAttribute('data-theme') === 'dark'
}

function apply(mode: ThemeMode): void {
  const root = document.documentElement
  root.setAttribute('data-theme', mode)
  root.style.colorScheme = mode
  try {
    localStorage.setItem(STORAGE_KEY, mode)
  } catch {
    /* 隐私模式可能禁用 localStorage，忽略即可 */
  }
  isDark.value = mode === 'dark'
}

function toggleTheme(): void {
  apply(isDark.value ? 'light' : 'dark')
}

export function useTheme() {
  return { isDark, toggleTheme, syncFromDom }
}
