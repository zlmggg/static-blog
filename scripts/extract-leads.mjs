#!/usr/bin/env node
/**
 * extract-leads.mjs —— 提取每篇 md 的「导语」作为聚合页 Article.sub
 *
 * 用法：node scripts/extract-leads.mjs docs/cases/t-*.md docs/guide/expert-*.md
 *
 * 对每篇 md：取首个非标题、非表格、非代码围栏、非 HTML 块的中文段落 / blockquote 文本，
 * 去掉 markdown 符号，截断到约 60 字，输出 JSON：{ "/guide/xxx": "…" }。
 *
 * docs 根目录以本脚本所在工程的 docs/ 为准（scripts/ 的上一级），不依赖 cwd。
 */
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { relative, resolve, sep } from 'node:path'

const docsRoot = fileURLToPath(new URL('../docs/', import.meta.url))

/** md 绝对路径 -> 站内路由（不带 .html，目录页以 / 结尾） */
function mdToRoute(absPath) {
  let rel = relative(docsRoot, absPath).split(sep).join('/')
  if (rel.endsWith('/index.md')) rel = rel.slice(0, -'index.md'.length)
  else if (rel.endsWith('.md')) rel = rel.slice(0, -'.md'.length)
  if (!rel.startsWith('/')) rel = '/' + rel
  return rel
}

/** 去掉 markdown 装饰符号，保留纯文本 */
function stripMd(line) {
  return line
    .replace(/^>\s?/, '')            // blockquote 前缀
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1') // [text](url) -> text
    .replace(/`+/g, '')              // 行内代码反引号
    .replace(/\*\*?/g, '')          // 粗体/斜体
    .replace(/\s+/g, ' ')
    .trim()
}

/** 提取单篇导语 */
function extractLead(md) {
  const lines = md.split(/\r?\n/)
  let inFence = false
  for (const raw of lines) {
    const line = raw.trim()
    if (/^```/.test(line)) { inFence = !inFence; continue }
    if (inFence) continue
    if (!line) continue
    if (/^#/.test(line)) continue            // 标题
    if (/^\|/.test(line)) continue           // 表格
    if (/^(-{3,}|\*{3,}|_{3,})$/.test(line)) continue // 分割线
    if (/^</.test(line)) continue            // HTML 块（nav/script/div…）
    if (/^:{3,}/.test(line)) continue        // 自定义容器围栏（::: tip / ::: details…）
    // 首个合格行：段落或 blockquote
    const text = stripMd(line)
    if (!text) continue
    if (!/[\u4e00-\u9fff]/.test(text)) continue // 只要中文导语
    return text.length > 60 ? text.slice(0, 60) + '…' : text
  }
  return ''
}

const result = {}
for (const arg of process.argv.slice(2)) {
  const abs = resolve(process.cwd(), arg)
  let md
  try {
    md = readFileSync(abs, 'utf-8')
  } catch {
    continue
  }
  result[mdToRoute(abs)] = extractLead(md)
}

process.stdout.write(JSON.stringify(result, null, 2) + '\n')
