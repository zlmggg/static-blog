// 数据一致性校验（零依赖，npm run check 调用）。
// 三类检查：
//   1) 死链：config.mts 的 nav/sidebar 链接 + Home.vue 的卡片链接，逐个解析成本地 md 并确认存在
//   2) frontmatter：difficulty 只能是 初级/中级/高级；date 只能是 YYYY-MM-DD
//   3) 占位符：正文出现 待补充/待完善/TODO/FIXME
// 任一问题即退出码非 0（供 CI 拦截）；仅打印不修改任何文件。
import { readFileSync, readdirSync, existsSync, statSync } from 'node:fs'
import path from 'node:path'

const DOCS = path.resolve('docs')
const problems = []
const count = { md: 0, date: 0, category: 0, difficulty: 0 }

// 递归列出 docs 下所有 .md（排除 .vitepress 与构建产物）
function walkMd(dir, acc = []) {
  for (const name of readdirSync(dir)) {
    const p = path.join(dir, name)
    if (statSync(p).isDirectory()) {
      if (name !== '.vitepress') walkMd(p, acc)
    } else if (name.endsWith('.md')) {
      acc.push(p)
    }
  }
  return acc
}

const DIFFS = new Set(['初级', '中级', '高级'])
// 注意：`【】` 不是占位符——它是 ai-prompts.md / ops-templates.md 里「让用户自行替换」的模板约定
const PLACEHOLDERS = ['待补充', '待完善', 'TODO', 'FIXME']
// 占位符检查豁免清单（相对 docs 路径）：这些是「有意保留的待办提示」，不算未完成
const SKIP_PLACEHOLDER = new Set(['projects/homelab.md'])

// 站点内链接 → 本地 md 绝对路径；外链 / 邮件 / 锚点返回 null 由调用方跳过
function resolveLink(link) {
  if (/^(https?:|mailto:|#)/.test(link)) return null
  let rel = link.split('#')[0].replace(/^\/+/, '')
  if (rel === '') return path.join(DOCS, 'index.md')
  if (rel.endsWith('/')) rel += 'index.md'
  else rel += '.md'
  return path.join(DOCS, rel)
}

// 1) 源码里的导航/卡片链接死链检查
function checkSourceLinks() {
  const sources = [
    [path.resolve('docs/.vitepress/config.mts'), /link:\s*'([^']+)'/g],
    [path.resolve('docs/.vitepress/theme/components/Home.vue'), /to:\s*'([^']+)'/g]
  ]
  for (const [file, re] of sources) {
    const code = readFileSync(file, 'utf8')
    for (const m of code.matchAll(re)) {
      const target = resolveLink(m[1])
      if (target && !existsSync(target)) {
        problems.push(`死链：${m[1]}（${path.basename(file)} → 找不到 ${path.relative(process.cwd(), target)}）`)
      }
    }
  }
}

// 2) & 3) frontmatter 与占位符检查
function checkContent() {
  for (const f of walkMd(DOCS)) {
    count.md++
    const text = readFileSync(f, 'utf8')
    const rel = path.relative(DOCS, f).replace(/\\/g, '/')

    const fm = text.match(/^---\n([\s\S]*?)\n---/)
    if (fm) {
      for (const line of fm[1].split('\n')) {
        const kv = line.match(/^([\w-]+):\s*(.*)$/)
        if (!kv) continue
        const val = kv[2].trim().replace(/^["']|["']$/g, '')
        if (kv[1] === 'date') {
          count.date++
          if (val && !/^\d{4}-\d{2}-\d{2}$/.test(val)) {
            problems.push(`date 格式错误：${rel} → "${val}"（应为 YYYY-MM-DD）`)
          }
        } else if (kv[1] === 'category') {
          count.category++
        } else if (kv[1] === 'difficulty') {
          count.difficulty++
          if (val && !DIFFS.has(val)) {
            problems.push(`difficulty 取值错误：${rel} → "${val}"（应为 初级/中级/高级）`)
          }
        }
      }
    }

    if (!SKIP_PLACEHOLDER.has(rel)) {
      for (const p of PLACEHOLDERS) {
        if (text.includes(p)) {
          problems.push(`疑似未完成：${rel} 含 "${p}"`)
          break
        }
      }
    }
  }
}

checkSourceLinks()
checkContent()

// —— 汇总 ——
console.log(`扫描 ${count.md} 篇 md`)
console.log(`  frontmatter：date ${count.date} · category ${count.category} · difficulty ${count.difficulty}`)
if (problems.length === 0) {
  console.log('✅ 校验通过：无死链、无 frontmatter 错误、无占位符残留')
} else {
  console.log(`\n发现 ${problems.length} 个问题：`)
  for (const p of problems) console.log('  ✗ ' + p)
  process.exitCode = 1
}