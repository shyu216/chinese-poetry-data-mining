/**
 * script: 99_web_reachability_tree.cjs
 * stage: P0-分析工具
 * artifact: Web 可达树分析报告
 * purpose: 给定入口文件（默认 App.vue）递归分析前端依赖可达树，并生成 HTML 可视化。
 * inputs:
 * - web/src/App.vue (默认)
 * outputs:
 * - results/web_reachability/reachable_tree.json
 * - results/web_reachability/unreachable_files.json
 * - results/web_reachability/reachability_report.html
 * depends_on:
 * - 无
 * develop_date: 2026-03-25
 * last_modified_date: 2026-03-25
 */

const fs = require('fs');
const path = require('path');

function parseArgs(argv) {
  const args = {
    entry: null,
    srcRoot: null,
    outDir: null,
    includeImporters: 'auto',
  };

  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--entry' && argv[i + 1]) {
      args.entry = argv[++i];
    } else if (a === '--src-root' && argv[i + 1]) {
      args.srcRoot = argv[++i];
    } else if (a === '--out-dir' && argv[i + 1]) {
      args.outDir = argv[++i];
    } else if (a === '--include-importers') {
      args.includeImporters = true;
    } else if (a === '--no-include-importers') {
      args.includeImporters = false;
    }
  }

  return args;
}

function normalizeSlash(p) {
  return p.replace(/\\/g, '/');
}

function normalizeFsPath(p) {
  const abs = path.resolve(p);
  const slash = normalizeSlash(abs);
  // Windows 文件系统通常大小写不敏感，统一为小写避免集合判重错误。
  return process.platform === 'win32' ? slash.toLowerCase() : slash;
}

function safeRead(filePath) {
  try {
    return fs.readFileSync(filePath, 'utf8');
  } catch {
    return '';
  }
}

function listSourceFiles(srcRoot) {
  const out = [];
  const stack = [srcRoot];
  const includeExt = new Set(['.vue', '.ts', '.js', '.tsx', '.jsx', '.mjs', '.cjs']);

  while (stack.length) {
    const dir = stack.pop();
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const e of entries) {
      const full = path.join(dir, e.name);
      if (e.isDirectory()) {
        stack.push(full);
      } else if (includeExt.has(path.extname(e.name))) {
        out.push(normalizeFsPath(full));
      }
    }
  }

  return out;
}

function isPathInside(absPath, root) {
  const rel = path.relative(root, absPath);
  return rel && !rel.startsWith('..') && !path.isAbsolute(rel);
}

function resolveImport(spec, fromFile, srcRoot) {
  let base = null;

  if (spec.startsWith('@/')) {
    base = path.join(srcRoot, spec.slice(2));
  } else if (spec.startsWith('./') || spec.startsWith('../')) {
    base = path.resolve(path.dirname(fromFile), spec);
  } else {
    return null;
  }

  const candidates = [
    base,
    `${base}.ts`,
    `${base}.js`,
    `${base}.vue`,
    `${base}.tsx`,
    `${base}.jsx`,
    path.join(base, 'index.ts'),
    path.join(base, 'index.js'),
    path.join(base, 'index.vue'),
  ];

  // 一些 TS 代码（尤其 generated）会写 .js 扩展名，但源码文件实际是 .ts/.tsx/.vue。
  const ext = path.extname(base);
  if (ext === '.js' || ext === '.mjs' || ext === '.cjs') {
    const withoutExt = base.slice(0, -ext.length);
    candidates.push(`${withoutExt}.ts`);
    candidates.push(`${withoutExt}.tsx`);
    candidates.push(`${withoutExt}.vue`);
  }

  for (const c of candidates) {
    if (fs.existsSync(c) && fs.statSync(c).isFile()) {
      return normalizeFsPath(c);
    }
  }

  return null;
}

function extractImportSpecs(content) {
  const specs = new Set();

  // import ... from '...'; (支持多行 import 列表)
  const reImportFrom = /import\s+(?:type\s+)?[\s\S]*?\s+from\s+[\"']([^\"']+)[\"']/g;
  let m = null;
  while ((m = reImportFrom.exec(content)) !== null) {
    specs.add(m[1]);
  }

  // side-effect import: import '...';
  const reImportOnly = /import\s+[\"']([^\"']+)[\"']/g;
  while ((m = reImportOnly.exec(content)) !== null) {
    specs.add(m[1]);
  }

  // re-export: export { ... } from '...'; / export type { ... } from '...';
  const reExportNamed = /export\s+(?:type\s+)?\{[^}]+\}\s+from\s+[\"']([^\"']+)[\"']/g;
  while ((m = reExportNamed.exec(content)) !== null) {
    specs.add(m[1]);
  }

  // re-export all: export * from '...';
  const reExportAll = /export\s+\*\s+from\s+[\"']([^\"']+)[\"']/g;
  while ((m = reExportAll.exec(content)) !== null) {
    specs.add(m[1]);
  }

  // dynamic import('...')
  const reDynamic = /import\(\s*[\"']([^\"']+)[\"']\s*\)/g;
  while ((m = reDynamic.exec(content)) !== null) {
    specs.add(m[1]);
  }

  return [...specs];
}

function buildGraph(entryAbs, srcRoot, allFiles) {
  const deps = new Map();
  for (const file of allFiles) {
    const content = safeRead(file);
    const specs = extractImportSpecs(content);
    const children = [];

    for (const spec of specs) {
      const resolved = resolveImport(spec, file, srcRoot);
      if (!resolved) continue;
      if (!isPathInside(resolved, srcRoot)) continue;
      children.push(resolved);
    }

    deps.set(file, [...new Set(children)]);
  }

  if (!deps.has(entryAbs)) {
    deps.set(entryAbs, []);
  }

  return deps;
}

function buildReverseGraph(deps) {
  const reverse = new Map();
  for (const [from, children] of deps.entries()) {
    if (!reverse.has(from)) reverse.set(from, []);
    for (const child of children) {
      if (!reverse.has(child)) reverse.set(child, []);
      reverse.get(child).push(from);
    }
  }
  return reverse;
}

function findImporterClosure(entryAbs, deps) {
  const reverse = buildReverseGraph(deps);
  const visited = new Set();
  const queue = [entryAbs];

  while (queue.length) {
    const cur = queue.shift();
    if (visited.has(cur)) continue;
    visited.add(cur);

    const importers = reverse.get(cur) || [];
    for (const imp of importers) {
      if (!visited.has(imp)) queue.push(imp);
    }
  }

  return [...visited];
}

function walkReachableFromRoots(roots, deps, allFiles) {
  const allSet = new Set(allFiles);
  const reachable = new Set();
  const queue = [...roots];

  while (queue.length) {
    const cur = queue.shift();
    if (reachable.has(cur)) continue;
    reachable.add(cur);

    for (const child of deps.get(cur) || []) {
      if (!allSet.has(child)) continue;
      if (!reachable.has(child)) queue.push(child);
    }
  }

  const unreachable = allFiles.filter((f) => !reachable.has(f));
  return { reachable, unreachable };
}

function buildTreeNode(file, deps, stack = new Set()) {
  const rel = normalizeSlash(file);
  if (stack.has(file)) {
    return { name: rel, file, cycle: true, children: [] };
  }

  const nextStack = new Set(stack);
  nextStack.add(file);

  const children = (deps.get(file) || []).map((c) => buildTreeNode(c, deps, nextStack));
  return { name: rel, file, cycle: false, children };
}

function toRel(file, projectRoot) {
  return normalizeSlash(path.relative(projectRoot, file));
}

function escapeHtml(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function countNodes(root) {
  let n = 1;
  for (const c of root.children || []) {
    n += countNodes(c);
  }
  return n;
}

function computeMaxDepth(root, depth = 1) {
  if (!root.children || root.children.length === 0) return depth;
  return Math.max(...root.children.map((c) => computeMaxDepth(c, depth + 1)));
}

function renderReportHtml(payload) {
  const jsonStr = JSON.stringify(payload).replace(/</g, '\\u003c');
  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Web 可达树报告</title>
  <style>
    :root {
      --bg: #0b1020;
      --panel: #131a2e;
      --card: #1b2442;
      --text: #e8eefc;
      --muted: #9fb0da;
      --ok: #40c896;
      --warn: #ffbf5f;
      --link: #8fb3ff;
    }
    body {
      margin: 0;
      background: radial-gradient(1200px 600px at 20% -10%, #243463 0%, var(--bg) 60%);
      color: var(--text);
      font-family: ui-sans-serif, Segoe UI, PingFang SC, Microsoft YaHei, sans-serif;
    }
    .wrap {
      max-width: 1200px;
      margin: 24px auto;
      padding: 0 16px 40px;
    }
    .panel {
      background: color-mix(in srgb, var(--panel) 88%, black);
      border: 1px solid #2e3b67;
      border-radius: 14px;
      padding: 16px;
      box-shadow: 0 10px 30px rgba(0,0,0,.35);
      margin-bottom: 16px;
    }
    h1 { margin: 0 0 8px; font-size: 22px; }
    .meta { color: var(--muted); font-size: 13px; }
    .grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(120px, 1fr));
      gap: 10px;
    }
    .card {
      background: var(--card);
      border: 1px solid #33457f;
      border-radius: 10px;
      padding: 10px;
    }
    .k { color: var(--muted); font-size: 12px; }
    .v { font-size: 20px; font-weight: 700; }
    .ok { color: var(--ok); }
    .warn { color: var(--warn); }
    details { margin: 4px 0 4px 20px; }
    summary {
      cursor: pointer;
      color: var(--link);
      user-select: text;
      word-break: break-all;
    }
    .cycle { color: #ff7e9a; margin-left: 6px; }
    ul { margin: 8px 0; padding-left: 18px; }
    li { margin: 3px 0; }
    code {
      background: #131a30;
      border: 1px solid #2e3d73;
      padding: 1px 6px;
      border-radius: 6px;
      color: #cbd8ff;
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="panel">
      <h1>Web 可达树分析报告</h1>
      <div class="meta">基于入口文件递归解析 import / dynamic import，统计可达与不可达文件。</div>
    </div>

    <div class="panel">
      <div class="grid" id="stats"></div>
    </div>

    <div class="panel">
      <h2>可达树</h2>
      <div id="tree"></div>
    </div>

    <div class="panel">
      <h2>不可达文件</h2>
      <ul id="unreach"></ul>
    </div>
  </div>

  <script>
    const DATA = ${jsonStr};

    function nodeToDetails(node) {
      const hasChildren = node.children && node.children.length > 0;
      const label = node.relPath || node.name;
      const cycle = node.cycle ? '<span class="cycle">(cycle)</span>' : '';
      if (!hasChildren) {
        return '<div style="margin:4px 0 4px 20px;"><code>' + label + '</code>' + cycle + '</div>';
      }
      return '<details open><summary><code>' + label + '</code>' + cycle + '</summary>'
        + node.children.map(nodeToDetails).join('')
        + '</details>';
    }

    const stats = [
      ['总文件数', DATA.stats.totalFiles],
      ['可达文件数', DATA.stats.reachableFiles, 'ok'],
      ['不可达文件数', DATA.stats.unreachableFiles, DATA.stats.unreachableFiles > 0 ? 'warn' : 'ok'],
      ['可达树深度', DATA.stats.maxDepth],
    ];

    document.getElementById('stats').innerHTML = stats
      .map(([k, v, cls]) => '<div class="card"><div class="k">' + k + '</div><div class="v '
        + (cls || '') + '">' + v + '</div></div>')
      .join('');

    document.getElementById('tree').innerHTML = nodeToDetails(DATA.tree);

    const unreach = document.getElementById('unreach');
    if (!DATA.unreachable.length) {
      unreach.innerHTML = '<li>无</li>';
    } else {
      unreach.innerHTML = DATA.unreachable.map((p) => '<li><code>' + p + '</code></li>').join('');
    }
  </script>
</body>
</html>`;
}

function main() {
  const args = parseArgs(process.argv);
  const projectRoot = path.resolve(__dirname, '..');
  const webRoot = path.join(projectRoot, 'web');

  const srcRoot = normalizeFsPath(args.srcRoot || path.join(webRoot, 'src'));
  const entry = normalizeFsPath(args.entry || path.join(srcRoot, 'App.vue'));
  const outDir = path.resolve(args.outDir || path.join(projectRoot, 'results', 'web_reachability'));
  const autoIncludeImporters = path.basename(entry).toLowerCase() === 'app.vue';
  const includeImporters = args.includeImporters === 'auto' ? autoIncludeImporters : !!args.includeImporters;

  if (!fs.existsSync(srcRoot)) {
    console.error(`[error] src-root 不存在: ${srcRoot}`);
    process.exit(1);
  }
  if (!fs.existsSync(entry)) {
    console.error(`[error] entry 不存在: ${entry}`);
    process.exit(1);
  }

  const allFiles = listSourceFiles(srcRoot);
  const deps = buildGraph(entry, srcRoot, allFiles);
  const roots = includeImporters ? findImporterClosure(entry, deps) : [entry];
  const { reachable, unreachable } = walkReachableFromRoots(roots, deps, allFiles);

  const tree = roots.length === 1
    ? buildTreeNode(roots[0], deps)
    : {
      name: '[analysis-roots]',
      file: '[analysis-roots]',
      cycle: false,
      children: roots
        .slice()
        .sort((a, b) => a.localeCompare(b))
        .map((r) => buildTreeNode(r, deps)),
    };

  function patchRelPath(node) {
    if (typeof node.file === 'string' && node.file.startsWith('[')) {
      node.relPath = node.file;
    } else {
      node.relPath = toRel(node.file, projectRoot);
    }
    for (const c of node.children || []) {
      patchRelPath(c);
    }
  }
  patchRelPath(tree);

  const payload = {
    generatedAt: new Date().toISOString(),
    entry: toRel(entry, projectRoot),
    srcRoot: toRel(srcRoot, projectRoot),
    analysisRoots: roots.map((r) => toRel(r, projectRoot)).sort(),
    includeImporters,
    stats: {
      totalFiles: allFiles.length,
      reachableFiles: reachable.size,
      unreachableFiles: unreachable.length,
      treeNodeCount: countNodes(tree),
      maxDepth: computeMaxDepth(tree),
    },
    tree,
    reachable: [...reachable].map((f) => toRel(f, projectRoot)).sort(),
    unreachable: unreachable.map((f) => toRel(f, projectRoot)).sort(),
  };

  fs.mkdirSync(outDir, { recursive: true });

  const jsonPath = path.join(outDir, 'reachable_tree.json');
  const unreachPath = path.join(outDir, 'unreachable_files.json');
  const htmlPath = path.join(outDir, 'reachability_report.html');

  fs.writeFileSync(jsonPath, JSON.stringify(payload, null, 2), 'utf8');
  fs.writeFileSync(unreachPath, JSON.stringify(payload.unreachable, null, 2), 'utf8');
  fs.writeFileSync(htmlPath, renderReportHtml(payload), 'utf8');

  console.log('[ok] 可达树分析完成');
  console.log(`  entry: ${payload.entry}`);
  console.log(`  include importers: ${payload.includeImporters}`);
  console.log(`  analysis roots: ${payload.analysisRoots.length}`);
  console.log(`  total files: ${payload.stats.totalFiles}`);
  console.log(`  reachable: ${payload.stats.reachableFiles}`);
  console.log(`  unreachable: ${payload.stats.unreachableFiles}`);
  console.log(`  tree depth: ${payload.stats.maxDepth}`);
  console.log(`  json: ${normalizeSlash(jsonPath)}`);
  console.log(`  html: ${normalizeSlash(htmlPath)}`);
}

main();
