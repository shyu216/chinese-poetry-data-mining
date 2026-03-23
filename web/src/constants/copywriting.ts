/**
 * Copywriting - 文案配置
 * 
 * 统一管理和维护应用中的所有文案，支持诗意化表达
 */

// 加载状态文案
export const loadingCopy = {
  // 初始化阶段
  initializing: [
    '文脉初启，正在唤醒千年诗魂...',
    '墨香渐起，诗卷缓缓展开...',
    '寻诗之旅，即将启程...',
    '千年文脉，待君品鉴...'
  ],
  
  // 数据加载阶段
  loading: [
    '正在翻阅诗词典藏目录...',
    '正在整理诗人名录档案...',
    '正在汇聚词频统计数据...',
    '正在梳理朝代更迭脉络...',
    '正在采撷千古名句精华...'
  ],
  
  // 完成阶段
  complete: [
    '文脉已通，请君品鉴',
    '诗卷已展，静候知音',
    '千年诗魂，已然苏醒',
    '万首诗词，待君采撷'
  ],
  
  // 错误状态
  error: [
    '文脉暂断，请刷新重试',
    '诗卷难展，稍后再试',
    '墨香暂散，请重新启程'
  ]
}

// 搜索相关文案
export const searchCopy = {
  placeholder: '寻一句诗，觅一位故人...',
  empty: '此处尚无诗词，且去别处寻寻',
  noResults: '未寻得相符诗词，换个词试试？',
  historyTitle: '曾寻',
  hotSearches: '热门',
  searching: '正在寻觅...'
}

// 按钮文案
export const buttonCopy = {
  copy: '誊抄',
  copySuccess: '已誊抄至剪贴板',
  favorite: '收藏',
  unfavorite: '已收藏',
  share: '分享',
  download: '下载',
  view: '品读',
  back: '返回',
  loadMore: '览更多',
  noMore: '—— 已览尽所有诗词 ——'
}

// 页面标题文案
export const pageTitleCopy = {
  home: {
    title: '文脉千秋',
    subtitle: '数字诗学图谱'
  },
  poems: {
    title: '诗词宝库',
    subtitle: '三十三万首，待君采撷'
  },
  authors: {
    title: '高产文人',
    subtitle: '千古风流人物'
  },
  poemDetail: {
    title: '诗词详情',
    subtitle: '品读经典诗词，感受千年文脉'
  },
  authorDetail: {
    title: '诗人详情',
    subtitle: '探寻诗人足迹，领略文心诗魂'
  },
  wordCount: {
    title: '词频统计',
    subtitle: '字字珠玑，词词入画'
  },
  data: {
    title: '数据管理中心',
    subtitle: '管理本地缓存数据，支持离线浏览'
  }
}

// 诗词展示文案
export const poemCopy = {
  untitled: '无题',
  unknownAuthor: '佚名',
  unknownDynasty: '未知朝代',
  sentences: '句',
  characters: '字',
  tags: '标签'
}

// 数据统计文案
export const statsCopy = {
  totalPoems: '首诗词',
  totalAuthors: '位诗人',
  totalWords: '个词条',
  totalDynasties: '个朝代',
  averageLength: '平均句数'
}

// 错误页面文案
export const errorCopy = {
  404: {
    title: '迷途',
    message: '此路不通，且回首页重寻',
    action: '返回首页'
  },
  500: {
    title: '墨尽',
    message: '服务器暂忙，请稍后再试',
    action: '刷新重试'
  }
}

// 功能引导文案
export const guideCopy = {
  firstVisit: {
    title: '欢迎来到文脉千秋',
    steps: [
      '在诗词宝库中寻觅心仪的诗句',
      '在高产文人中探寻千古名家',
      '在词频统计中发现语言之美'
    ]
  },
  searchTip: '输入诗词标题、作者名或关键词，开始寻诗之旅',
  filterTip: '使用筛选器，按朝代、体裁精确定位'
}

// 诗意化随机文案
export const poeticQuotes = [
  '腹有诗书气自华',
  '读书破万卷，下笔如有神',
  '文章千古事，得失寸心知',
  '李杜文章在，光焰万丈长',
  '采菊东篱下，悠然见南山',
  '会当凌绝顶，一览众山小',
  '山重水复疑无路，柳暗花明又一村',
  '问君能有几多愁，恰似一江春水向东流'
]

// 获取随机文案
export const getRandomCopy = (copyArray: string[]): string => {
  const index = Math.floor(Math.random() * copyArray.length)
  return copyArray[index] ?? ''
}

// 获取随机诗意引用
export const getRandomQuote = (): string => {
  const index = Math.floor(Math.random() * poeticQuotes.length)
  return poeticQuotes[index] ?? ''
}
