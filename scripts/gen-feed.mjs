// 构建后生成 RSS 2.0 订阅源（零依赖）。
// 扫描带 frontmatter「date」的内容文章：排障案例(cases/t-*)、项目文章(projects/*)，
// 以及将来补了 date 的指南(guide/*，自动排除聚合页)；按日期倒序取最新 MAX 篇。
import { readFileSync, writeFileSync, readdirSync, mkdirSync } from 'node:fs'
import path from 'node:path'

const DOCS = path.resolve('docs')
const DIST = path.join(DOCS, '.vitepress', 'dist')
const SITE = 'https://www.sresec.com'
const MAX = 20

// guide 下这些是聚合页（导航/索引），不是具体文章，不进订阅
const GUIDE_INDEX = new Set([
  'linux', 'services', 'data', 'monitor', 'container', 'automation',
  'devops', 'aiops', 'architecture', 'blog', 'opsdev', 'career'
])

function listMd(dir) {
  return readdirSync(dir)
    .filter((f) => f.endsWith('.md'))
    .map((f) => path.join(dir, f))
}

const candidates = [
  ...listMd(path.join(DOCS, 'cases')).filter((f) =>
    /^t-[^/]+\.md$/.test(path.basename(f))
  ),
  ...listMd(path.join(DOCS, 'projects')).filter(
    (f) => path.basename(f) !== 'index.md'
  ),
  ...listMd(path.join(DOCS, 'guide')).filter(
    (f) => !GUIDE_INDEX.has(path.basename(f, '.md'))
  )
]

// 解析 frontmatter（取 date）与第一个 H1（取标题）
function parseArticle(md) {
  const fm = {}
  const fmMatch = md.match(/^---\n([\s\S]*?)\n---/)
  if (fmMatch) {
    for (const line of fmMatch[1].split('\n')) {
      const kv = line.match(/^([\w-]+):\s*(.*)$/)
      if (kv) fm[kv[1]] = kv[2].trim()
    }
  }
  const h1 = md.match(/^#\s+(.+)$/m)
  return { date: fm.date, title: h1 ? h1[1].trim() : '' }
}

function esc(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

const items = candidates
  .map((f) => {
    const { date, title } = parseArticle(readFileSync(f, 'utf8'))
    if (!date) return null // 没有日期的文章暂不进订阅
    const url =
      SITE +
      '/' +
      path.relative(DOCS, f).replace(/\\/g, '/').replace(/\.md$/, '.html')
    return { title, date, url }
  })
  .filter(Boolean)
  .sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0))
  .slice(0, MAX)

const rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>禾光知寒 · SRE Notes</title>
<link>${SITE}/</link>
<description>一个 SRE 的成长档案：排障案例与实战项目更新</description>
<language>zh-CN</language>
${items
  .map(
    (i) => `  <item>
    <title>${esc(i.title)}</title>
    <link>${i.url}</link>
    <guid isPermaLink="true">${i.url}</guid>
    <pubDate>${new Date(i.date + 'T00:00:00+08:00').toUTCString()}</pubDate>
  </item>`
  )
  .join('\n')}
</channel>
</rss>
`

mkdirSync(DIST, { recursive: true })
writeFileSync(path.join(DIST, 'feed.xml'), rss)
console.log(`feed.xml 已生成：${items.length} 篇`)
