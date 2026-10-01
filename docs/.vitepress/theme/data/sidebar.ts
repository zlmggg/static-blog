import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { registry } from './registry'
import { pages } from './pages'
import type { Article } from './types'

// docs 根目录：本文件位于 docs/.vitepress/theme/data/sidebar.ts，上三级即 docs/
// 用 import.meta.url 推导，不依赖 cwd。
const docsRoot = fileURLToPath(new URL('../../../', import.meta.url))

/** 规范化：去尾 .html、保证前导 / */
function norm(p: string): string {
  let s = p || ''
  if (s.endsWith('.html')) s = s.slice(0, -'.html'.length)
  if (!s.startsWith('/')) s = '/' + s
  return s
}

// —— 无左栏页面集合：registry 全部 key + 9 个 reference 索引页 + /about ——
const noSidebar = new Set<string>()
for (const e of registry) noSidebar.add(norm(e.key))
for (const r of [
  '/reference/linux-commands',
  '/reference/network-commands',
  '/reference/docker-commands',
  '/reference/kubectl-commands',
  '/reference/git-commands',
  '/reference/cloudnative-commands',
  '/reference/ai-prompts',
  '/reference/ops-templates',
  '/reference/ops-checklists'
]) noSidebar.add(r)
noSidebar.add('/about')

// —— reference 命令详情页映射（Node fs 在配置加载时解析一次，目录 docs/）——
interface RefDetail {
  prefix: string
  indexPath: string
  mdFile: string
  heading: string
  siblings: { text: string; link: string }[]
  backText: string
}

function loadRefDetails(): RefDetail[] {
  const defs: {
    prefix: string
    indexPath: string
    mdFile: string
    linkRe: RegExp
    heading: string
  }[] = [
    { prefix: '/reference/cmd/', indexPath: '/reference/linux-commands', mdFile: 'reference/linux-commands.md', linkRe: /\[([^\]]*)\]\(\.\/cmd\/([^)]+)\)/g, heading: 'Linux 命令' },
    { prefix: '/reference/cmd-net/', indexPath: '/reference/network-commands', mdFile: 'reference/network-commands.md', linkRe: /\[([^\]]*)\]\(\.\/cmd-net\/([^)]+)\)/g, heading: '网络命令' },
    { prefix: '/reference/cmd-docker/', indexPath: '/reference/docker-commands', mdFile: 'reference/docker-commands.md', linkRe: /\[([^\]]*)\]\(\.\/cmd-docker\/([^)]+)\)/g, heading: 'Docker 命令' },
    { prefix: '/reference/cmd-kubectl/', indexPath: '/reference/kubectl-commands', mdFile: 'reference/kubectl-commands.md', linkRe: /\[([^\]]*)\]\(\.\/cmd-kubectl\/([^)]+)\)/g, heading: 'kubectl 命令' },
    { prefix: '/reference/cmd-git/', indexPath: '/reference/git-commands', mdFile: 'reference/git-commands.md', linkRe: /\[([^\]]*)\]\(\.\/cmd-git\/([^)]+)\)/g, heading: 'Git 命令' },
    { prefix: '/reference/cmd-cloudnative/', indexPath: '/reference/cloudnative-commands', mdFile: 'reference/cloudnative-commands.md', linkRe: /\[([^\]]*)\]\(\.\/cmd-cloudnative\/([^)]+)\)/g, heading: '云原生命令' }
  ]

  const out: RefDetail[] = []
  for (const d of defs) {
    let siblings: { text: string; link: string }[] = []
    let backText = '返回'
    try {
      const md = readFileSync(docsRoot + d.mdFile, 'utf-8')
      const h1 = md.match(/^#\s+(.+)$/m)
      backText = '返回' + (h1 ? h1[1].trim() : '')
      const seen = new Set<string>()
      let mm: RegExpExecArray | null
      const re = new RegExp(d.linkRe.source, 'g')
      while ((mm = re.exec(md)) !== null) {
        const label = mm[1].replace(/`+/g, '').trim()
        const link = d.prefix + mm[2]
        if (seen.has(link)) continue
        seen.add(link)
        siblings.push({ text: label || mm[2], link })
      }
    } catch {
      siblings = []
    }
    out.push({ prefix: d.prefix, indexPath: d.indexPath, mdFile: d.mdFile, heading: d.heading, siblings, backText })
  }
  return out
}

const refDetails = loadRefDetails()

/** VitePress 函数式 sidebar */
export function buildSidebar(route: { path: string }): any[] {
  const path = norm(route.path)

  // 1. 首页无左栏
  if (path === '/') return []

  // 2. 聚合页 / 索引页 / about 等无左栏页面
  if (noSidebar.has(path)) return []

  // 3. registry 文章按 link 精确匹配（注册顺序即归属优先级）
  for (const entry of registry) {
    if (entry.inSidebar === false) continue
    const list = pages[entry.key]
    if (!list) continue
    const hit = list.find((a) => norm(a.link) === path)
    if (!hit) continue

    let heading: string
    let siblings: Article[]
    if (entry.scope === 'all') {
      siblings = list
      heading = entry.heading ?? ''
    } else {
      siblings = list.filter((a) => a.group === hit.group)
      heading = (entry.groupHeadings && entry.groupHeadings[hit.group]) ?? ''
    }
    return [
      { text: '← ' + (entry.backLabel ?? `返回${entry.title}`), link: entry.key },
      { text: heading, items: siblings.map((a) => ({ text: a.title, link: a.link })) }
    ]
  }

  // 4. reference 命令详情页（fs 解析结果）
  for (const rd of refDetails) {
    if (path.startsWith(rd.prefix)) {
      return [{ text: '← ' + rd.backText, link: rd.indexPath }, { text: rd.heading, items: rd.siblings }]
    }
  }

  // 5. 兜底
  return []
}

/**
 * 预计算静态 MultiSideBarConfig：VitePress 1.6.4 默认主题不支持函数式 sidebar
 * （SSR 序列化后函数丢失，getSidebar 只处理数组/对象 map）。
 * 在配置加载期（Node 端）复用 buildSidebar({path}) 为每篇文章预算好 items。
 *
 * 文章路径来源：
 *  - registry 中 inSidebar !== false 的各 pages 数据里每条 Article.link；
 *  - refDetails 各 rd.siblings 的 link（6 个 reference 索引解析出的命令详情页）。
 * 只收录 buildSidebar 返回非空数组的路径；key 用 norm() 规范化后的完整文章路径。
 *
 * key 插入顺序：先按 / 段数降序、再按路径长度降序——
 * getSidebar 按段数降序稳定排序后取第一个 startsWith 命中，等长时保留插入顺序，
 * 更长/更具体的路径在前，可消除「同目录一个文件名是另一个前缀」导致的前缀碰撞
 * （如 /reference/cmd/ls 与 /reference/cmd/lsblk-blkid）。
 */
export function buildSidebarMap(): Record<string, any[]> {
  const keys = new Set<string>()

  for (const entry of registry) {
    if (entry.inSidebar === false) continue
    const list = pages[entry.key]
    if (!list) continue
    for (const a of list) keys.add(norm(a.link))
  }
  for (const rd of refDetails) {
    for (const s of rd.siblings) keys.add(norm(s.link))
  }

  const entries: [string, any[]][] = []
  for (const key of keys) {
    const items = buildSidebar({ path: key })
    if (items.length > 0) entries.push([key, items])
  }

  entries.sort((a, b) => {
    const sa = a[0].split('/').length
    const sb = b[0].split('/').length
    if (sb !== sa) return sb - sa
    return b[0].length - a[0].length
  })

  const map: Record<string, any[]> = {}
  for (const [k, v] of entries) map[k] = v
  return map
}
