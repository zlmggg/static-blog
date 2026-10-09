<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vitepress'

const router = useRouter()

// 面经卡片链接：面经已并入主站，直接走站内路径
const INTERVIEW_TO = '/interview/'

const termBody = ref<HTMLElement | null>(null)
let alive = true
let reduceMotion = false
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))

/* ---------------- 终端脚本数据 ---------------- */
type Out = [string, string]
const SCRIPTS: { cmd: string; out: Out[] }[] = [
  {
    cmd: 'kubectl get pods -n sre',
    out: [
      ['t-out', 'NAME            READY  STATUS   RESTARTS'],
      ['t-ok', 'nginx-7d9f      1/1    Running  0'],
      ['t-ok', 'netdata-6b4c    1/1    Running  0']
    ]
  },
  {
    cmd: 'df -h /data',
    out: [
      ['t-out', 'Filesystem  Size  Used  Avail Use% Mounted on'],
      ['t-info', '/dev/vdb1    20G  2.1G   17G  11% /data']
    ]
  },
  {
    cmd: 'uptime',
    out: [['t-cyan', ' 14:55:01 up 36 days,  load average: 0.08, 0.05, 0.02']]
  },
  {
    cmd: 'systemctl is-active docker nginx',
    out: [
      ['t-ok', 'active'],
      ['t-ok', 'active']
    ]
  }
]

async function typeCmd(text: string) {
  const body = termBody.value
  if (!body) return
  const line = document.createElement('div')
  line.className = 'ln'
  line.innerHTML =
    '<span class="t-prompt">$ </span><span class="t-cmd"></span><span class="t-cursor"></span>'
  const target = line.querySelector('.t-cmd') as HTMLElement
  body.appendChild(line)
  body.scrollTop = body.scrollHeight
  for (const ch of text) {
    if (!alive) break
    target.textContent += ch
    await sleep(38 + Math.random() * 46)
  }
  line.querySelector('.t-cursor')?.remove()
  body.scrollTop = body.scrollHeight
}

function addOut(cls: string, text: string) {
  const body = termBody.value
  if (!body) return
  const line = document.createElement('div')
  line.className = 'ln ' + cls
  line.textContent = text
  body.appendChild(line)
  body.scrollTop = body.scrollHeight
}

function staticTerm() {
  const body = termBody.value
  if (!body) return
  body.innerHTML = ''
  SCRIPTS.forEach((s) => {
    const l = document.createElement('div')
    l.className = 'ln'
    l.innerHTML =
      '<span class="t-prompt">$ </span><span class="t-cmd"></span>'
    ;(l.querySelector('.t-cmd') as HTMLElement).textContent = s.cmd
    body.appendChild(l)
    s.out.forEach((o) => addOut(o[0], o[1]))
  })
}

async function runTerm() {
  if (reduceMotion) {
    staticTerm()
    return
  }
  while (alive) {
    const body = termBody.value
    if (!body) {
      await sleep(200)
      continue
    }
    body.innerHTML = ''
    body.scrollTop = 0
    for (let i = 0; i < SCRIPTS.length && alive; i++) {
      const s = SCRIPTS[i]
      await typeCmd(s.cmd)
      await sleep(340)
      for (let j = 0; j < s.out.length && alive; j++) {
        addOut(s.out[j][0], s.out[j][1])
        await sleep(100)
      }
      await sleep(560)
    }
    await sleep(1500)
  }
}

/* ---------------- 卡片数据 ---------------- */
interface Feat {
  t: string
  d: string
  g: string
  i: string
  to: string
}
const FEATS: Feat[] = [
  {
    t: '操作指南',
    d: 'Linux 系统、服务部署、容器编排、监控日志与自动化 IaC，原理配合完整操作。',
    g: '浏览指南',
    i: '<circle cx="12" cy="12" r="9"/><path d="m15.5 8.5-2 5-5 2 2-5z"/>',
    to: '/guide/linux'
  },
  {
    t: '命令速查',
    d: 'Linux、网络、Docker、kubectl 常用命令按场景分类汇总，翻到即用。',
    g: '查看速查',
    i: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="m7 9 3 3-3 3M13 15h4"/>',
    to: '/reference/linux-commands'
  },
  {
    t: '故障排障',
    d: '典型故障场景与排障记录：从现象、定位、根因到解决，练一套可复用的排查套路。',
    g: '查看案例',
    i: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M12 8v4M12 16h.01"/>',
    to: '/cases/troubleshooting'
  },
  {
    t: 'DevOps 与平台工程',
    d: 'CI/CD、GitOps、制品库与平台化实践，打通从代码到生产的完整链路。',
    g: '进入专题',
    i: '<line x1="6" y1="3" x2="6" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/>',
    to: '/guide/devops'
  },
  {
    t: '智能运维与 AI',
    d: 'AIOps、可观测性、LLM 与 Agent 在运维场景的最新前沿实践。',
    g: '了解前沿',
    i: '<rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 1v3M15 1v3M1 9h3M1 14h3M20 9h3M20 14h3M9 20v3M15 20v3"/>',
    to: '/guide/aiops'
  },
  {
    t: '运维手记与职业思考',
    d: '值班经历、行业看法、就业心得与成长方向，一个“活生生”的工程师视角。',
    g: '阅读手记',
    i: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
    to: '/guide/career'
  },
  {
    t: '面试专区',
    d: 'Linux、网络、容器、云原生高频面试与场景题，公开可查、随时翻阅。',
    g: '进入面试',
    i: '<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>',
    to: INTERVIEW_TO
  },
  {
    t: '架构设计实战',
    d: '网站、微服务、银行、游戏等多架构方案：服务器选型、服务编排与上线风险。',
    g: '查看方案',
    i: '<rect x="3" y="4" width="18" height="6" rx="1"/><rect x="3" y="14" width="18" height="6" rx="1"/><path d="M7 7h.01M7 17h.01"/>',
    to: '/guide/architecture'
  },
  {
    t: '实战脚本与自动化',
    d: '巡检、备份、批量操作与告警脚本集，拿来即用，减少重复手工劳动。',
    g: '获取脚本',
    i: '<path d="M13 2 3 14h9l-1 8 10-12h-9z"/>',
    to: '/guide/automation'
  }
]

/* ---------------- 我的项目（首页特色条） ---------------- */
interface Pj {
  t: string
  d: string
  tags: string
  to: string
}
const PROJECTS: Pj[] = [
  {
    t: '禾光知寒站点',
    d: '你正在看的知识库：自定义主题、Mermaid 集成、容器化部署并开源。',
    tags: 'VitePress · Vue · Docker',
    to: '/projects/site-blog'
  },
  {
    t: '阿里云个人站点部署',
    d: 'ECS 挂数据盘，Docker Compose 跑 Nginx 与 Netdata，主机加固。',
    tags: '阿里云 · Docker · Nginx',
    to: '/projects/aliyun-deploy'
  },
  {
    t: '家庭实验室 Homelab',
    d: '双路 E5 + 128G ECC，部署 OpenStack / KVM，把云平台在真机练一遍。',
    tags: 'X99 · OpenStack · KVM',
    to: '/projects/homelab'
  }
]

function onCardMove(e: MouseEvent) {
  const card = e.currentTarget as HTMLElement
  const r = card.getBoundingClientRect()
  card.style.setProperty('--mx', e.clientX - r.left + 'px')
  card.style.setProperty('--my', e.clientY - r.top + 'px')
}

function go(to: string) {
  if (to.startsWith('http')) {
    window.location.href = to
  } else {
    router.go(to)
  }
}

/* ---------------- 搜索 ---------------- */
function openSearch() {
  const ev = new KeyboardEvent('keydown', {
    key: 'k',
    ctrlKey: true,
    metaKey: true,
    bubbles: true
  })
  window.dispatchEvent(ev)
}

/* ---------------- 数字滚动 ---------------- */
function animateCount(el: HTMLElement) {
  const target = Number(el.dataset.count)
  const suffix = el.dataset.suffix || ''
  const start = performance.now()
  const dur = 1400
  function step(now: number) {
    const p = Math.min((now - start) / dur, 1)
    const eased = 1 - Math.pow(1 - p, 3)
    el.textContent = Math.round(target * eased) + suffix
    if (p < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}

let io: IntersectionObserver | null = null

onMounted(() => {
  reduceMotion = window.matchMedia(
    '(prefers-reduced-motion: reduce)'
  ).matches
  runTerm()

  io = new IntersectionObserver(
    (entries) => {
      entries.forEach((en) => {
        if (!en.isIntersecting) return
        const el = en.target as HTMLElement
        el.classList.add('in')
        const n = (el.hasAttribute('data-count')
          ? el
          : el.querySelector('[data-count]')) as HTMLElement | null
        if (n && !n.dataset.done) {
          n.dataset.done = '1'
          animateCount(n)
        }
        io?.unobserve(el)
      })
    },
    { threshold: 0.25 }
  )
  document
    .querySelectorAll('.home-root .reveal')
    .forEach((el) => io?.observe(el))
})

onBeforeUnmount(() => {
  alive = false
  io?.disconnect()
})
</script>

<template>
  <div class="home-root">
    <!-- 背景统一由全局 Layout 的 .bg-fx 提供，这里不再重复渲染 -->

    <!-- Hero -->
    <header class="hero">
      <div class="home-wrap hero-grid">
        <div class="reveal hero-left">
          <span class="badge">
            <span class="dot"></span>持续更新中 · 已沉淀 325+ 篇笔记
          </span>
          <h1>
            随时可查的<br />
            <span class="gradient-text">SRE 运维手册</span>
          </h1>
          <p class="lead">
            Linux 系统、服务部署、容器编排、云原生与排障训练——原理铺垫配合完整操作，学过忘了也能迅速接上，翻到即用。
          </p>
          <div class="hero-actions">
            <button class="btn btn-primary" @click="go('/guide/linux')">
              浏览知识库
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2.2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path d="M5 12h14M13 6l6 6-6 6" />
              </svg>
            </button>
            <button class="btn btn-ghost" @click="go('/reference/linux-commands')">
              命令速查
            </button>
            <button class="btn btn-ghost" @click="go('/cases/troubleshooting')">
              排障记录
            </button>
          </div>
        </div>
        <div class="reveal hero-right">
          <div class="term">
            <div class="term-header">
              <span class="tl r"></span>
              <span class="tl y"></span>
              <span class="tl g"></span>
              <span class="tt">root@sresec:~</span>
            </div>
            <div ref="termBody" class="term-body"></div>
          </div>
        </div>
      </div>
    </header>

    <!-- 数据条 -->
    <section class="stats">
      <div class="home-wrap stats-grid">
        <div class="stat reveal">
          <div class="num" data-count="325" data-suffix="+">0</div>
          <div class="lbl">技术文档</div>
        </div>
        <div class="stat reveal">
          <div class="num" data-count="129" data-suffix="">0</div>
          <div class="lbl">命令详解</div>
        </div>
        <div class="stat reveal">
          <div class="num" data-count="50" data-suffix="">0</div>
          <div class="lbl">排障案例</div>
        </div>
        <div class="stat reveal">
          <div class="num" data-count="24" data-suffix="">0</div>
          <div class="lbl">知识专题</div>
        </div>
      </div>
    </section>

    <!-- 我的项目 -->
    <section class="projects">
      <div class="home-wrap">
        <div class="section-head reveal">
          <h2>我的项目</h2>
          <p>
            真实动手做过的东西，从搭环境到上线——<a class="pj-more" href="/projects/">查看全部</a>
          </p>
        </div>
        <div class="pj-grid">
          <div
            v-for="p in PROJECTS"
            :key="p.t"
            class="pj reveal"
            @click="go(p.to)"
          >
            <h3>{{ p.t }}</h3>
            <p>{{ p.d }}</p>
            <span class="pj-tags">{{ p.tags }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 搜索条 -->
    <section class="search-section">
      <div class="home-wrap">
        <div class="search-hero reveal">
          <div class="search-box" @click="openSearch">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#9a9ab0"
              stroke-width="2"
              stroke-linecap="round"
            >
              <circle cx="11" cy="11" r="7" />
              <path d="m21 21-4.3-4.3" />
            </svg>
            <span class="ph">搜索命令、服务、故障案例…</span>
            <span class="key">Ctrl K</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 卡片 -->
    <section class="section" id="features">
      <div class="home-wrap">
        <div class="section-head reveal">
          <h2>一个“活生生”的高级运维站点</h2>
          <p>从基础到高级，从排障到前沿，按分类快速找到你要的内容</p>
        </div>
        <div class="feat-grid">
          <div
            v-for="f in FEATS"
            :key="f.t"
            class="feat reveal"
            @mousemove="onCardMove"
            @click="go(f.to)"
          >
            <div class="ic">
              <svg
                width="22"
                height="22"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                v-html="f.i"
              ></svg>
            </div>
            <h3>{{ f.t }}</h3>
            <p>{{ f.d }}</p>
            <span class="go">
              {{ f.g }}
              <svg
                width="15"
                height="15"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2.2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path d="M5 12h14M13 6l6 6-6 6" />
              </svg>
            </span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<!-- 非 scoped：明暗 token + 终端动态 DOM 样式（.home-root 命名空间，不污染他页） -->
<style>
html.dark .home-root {
  --bg: #08080d;
  --surface: rgba(255, 255, 255, 0.035);
  --surface-2: rgba(255, 255, 255, 0.06);
  --border: rgba(255, 255, 255, 0.09);
  --border-strong: rgba(255, 255, 255, 0.16);
  --text: #ececf3;
  --muted: #9a9ab0;
  --term-bg: #0b0f16;
  --term-header: #141a23;
  --shadow: 0 24px 60px -24px rgba(0, 0, 0, 0.8);
}
html:not(.dark) .home-root {
  --surface: rgba(255, 255, 255, 0.6);
  --surface-2: rgba(255, 255, 255, 0.92);
  --border: rgba(30, 35, 70, 0.09);
  --border-strong: rgba(30, 35, 70, 0.16);
  --text: #181b28;
  --muted: #585e76;
  --term-bg: #1e293b;
  --term-header: #1b2638;
  --shadow: 0 22px 52px -26px rgba(55, 65, 140, 0.32);
}
.home-root {
  position: relative;
  color: var(--text);
}

/* 容器：宽度对齐 1580 */
.home-root .home-wrap {
  position: relative;
  z-index: 1;
  max-width: var(--vp-layout-max-width);
  margin: 0 auto;
  padding-left: clamp(24px, 4vw, 48px);
  padding-right: clamp(24px, 4vw, 48px);
}

/* Hero */
.home-root .hero {
  padding: calc(var(--vp-nav-height) + 56px) 0 40px;
}
.home-root .hero-grid {
  display: grid;
  grid-template-columns: 0.9fr 1.1fr;
  gap: 56px;
  align-items: center;
}
.home-root .badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--muted);
  border: 1px solid var(--border);
  background: var(--surface);
  padding: 6px 14px;
  border-radius: 999px;
  margin-bottom: 22px;
}
.home-root .badge .dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--brand-3);
  box-shadow: 0 0 10px var(--brand-3);
}
.home-root .hero h1 {
  font-family: var(--vp-font-family-base);
  font-size: clamp(34px, 4.4vw, 56px);
  line-height: 1.08;
  letter-spacing: -0.02em;
  font-weight: 700;
}
.home-root .gradient-text {
  background: linear-gradient(
    110deg,
    var(--brand-1),
    var(--brand-2) 55%,
    var(--brand-3)
  );
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
html:not(.dark) .home-root .gradient-text {
  background: linear-gradient(110deg, #4f46e5, #7c3aed 58%, #0284c7);
  -webkit-background-clip: text;
  background-clip: text;
}
.home-root .lead {
  margin-top: 18px;
  font-size: 17px;
  color: var(--muted);
  max-width: 500px;
}
.home-root .hero-actions {
  display: flex;
  gap: 14px;
  margin-top: 32px;
  flex-wrap: wrap;
}
.home-root .btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 13px 24px;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid transparent;
  transition: 0.22s;
  font-family: var(--vp-font-family-base);
}
.home-root .btn-primary {
  background: linear-gradient(135deg, var(--brand-1), var(--brand-2));
  color: #fff;
  box-shadow: 0 12px 28px -12px var(--brand-1);
}
.home-root .btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 18px 34px -12px var(--brand-1);
}
.home-root .btn-ghost {
  background: var(--surface);
  border-color: var(--border);
  color: var(--text);
  backdrop-filter: blur(8px);
}
.home-root .btn-ghost:hover {
  background: var(--surface-2);
  transform: translateY(-2px);
}

/* 终端外壳 */
.home-root .term {
  background: var(--term-bg);
  border: 1px solid var(--border-strong);
  border-radius: 14px;
  box-shadow: var(--shadow);
  overflow: hidden;
  transform: rotate(0.4deg);
  max-width: 580px;
  width: 100%;
  justify-self: end;
}
.home-root .term-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--term-header);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.home-root .term-header .tl {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}
.home-root .tl.r {
  background: #ff5f57;
}
.home-root .tl.y {
  background: #febc2e;
}
.home-root .tl.g {
  background: #28c840;
}
.home-root .term-header .tt {
  margin-left: auto;
  font-family: var(--vp-font-family-mono);
  font-size: 12px;
  color: #6b7280;
}
.home-root .term-body {
  font-family: var(--vp-font-family-mono);
  font-size: 13.5px;
  line-height: 1.75;
  padding: 18px 18px 20px;
  height: 300px;
  overflow: hidden;
}
html:not(.dark) .home-root .term {
  border-color: #334155;
}
html:not(.dark) .home-root .term-header {
  border-bottom-color: rgba(255, 255, 255, 0.07);
}

/* 终端动态行（JS 创建） */
.home-root .term-body .ln {
  white-space: pre;
}
.home-root .term-body .t-prompt {
  color: #9ca3af;
}
.home-root .term-body .t-cmd {
  color: #e5e7eb;
}
.home-root .term-body .t-out {
  color: #7d8590;
}
.home-root .term-body .t-ok {
  color: #3fb950;
}
.home-root .term-body .t-info {
  color: #58a6ff;
}
.home-root .term-body .t-warn {
  color: #d29922;
}
.home-root .term-body .t-cyan {
  color: #39c5cf;
}
.home-root .term-body .t-cursor {
  display: inline-block;
  width: 8px;
  height: 16px;
  background: #e5e7eb;
  vertical-align: -3px;
  animation: home-blink 1s steps(1) infinite;
}
@keyframes home-blink {
  50% {
    opacity: 0;
  }
}

/* 数据条 */
.home-root .stats {
  padding: 36px 0;
}
.home-root .stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
}
.home-root .stat {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 26px 22px;
  text-align: center;
  transition: 0.25s;
  backdrop-filter: blur(14px) saturate(160%);
}
.home-root .stat:hover {
  border-color: var(--border-strong);
  transform: translateY(-3px);
}
.home-root .stat .num {
  font-family: var(--vp-font-family-base);
  font-size: 38px;
  font-weight: 700;
  letter-spacing: -0.02em;
}
.home-root .stat .lbl {
  margin-top: 6px;
  font-size: 14px;
  color: var(--muted);
}

/* 搜索条 */
.home-root .search-section {
  padding-top: 8px;
}
.home-root .search-hero {
  max-width: 600px;
  margin: 8px auto 0;
}
.home-root .search-box {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 15px 20px;
  cursor: pointer;
  transition: 0.25s;
  backdrop-filter: blur(14px) saturate(160%);
}
.home-root .search-box:hover {
  border-color: var(--brand-1);
  background: var(--surface-2);
}
.home-root .search-box .key {
  margin-left: auto;
  font-family: var(--vp-font-family-mono);
  font-size: 12px;
  color: var(--muted);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 2px 8px;
}
.home-root .search-box .ph {
  color: var(--muted);
  font-size: 15px;
}

/* 卡片 */
.home-root .section {
  padding: 56px 0 64px;
}
.home-root .section-head {
  text-align: center;
  margin-bottom: 44px;
}
.home-root .section-head h2 {
  font-family: var(--vp-font-family-base);
  font-size: clamp(26px, 3vw, 36px);
  font-weight: 700;
  letter-spacing: -0.02em;
}
.home-root .section-head p {
  margin-top: 10px;
  color: var(--muted);
}
.home-root .feat-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}
.home-root .feat {
  position: relative;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 28px 26px;
  transition: 0.28s;
  overflow: hidden;
  cursor: pointer;
  backdrop-filter: blur(14px) saturate(160%);
}
.home-root .feat::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  opacity: 0;
  transition: 0.3s;
  background: radial-gradient(
    420px circle at var(--mx, 50%) var(--my, 0%),
    color-mix(in srgb, var(--brand-1) 14%, transparent),
    transparent 60%
  );
}
.home-root .feat:hover {
  transform: translateY(-5px);
  border-color: var(--border-strong);
  box-shadow: var(--shadow);
}
.home-root .feat:hover::before {
  opacity: 1;
}
.home-root .feat .ic {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  margin-bottom: 16px;
  background: color-mix(in srgb, var(--brand-1) 16%, transparent);
  color: var(--brand-2);
}
.home-root .feat h3 {
  font-family: var(--vp-font-family-base);
  font-size: 18px;
  font-weight: 600;
}
.home-root .feat p {
  margin-top: 8px;
  font-size: 14px;
  color: var(--muted);
}
.home-root .feat .go {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 16px;
  font-size: 14px;
  font-weight: 500;
  color: var(--brand-2);
}
.home-root .feat .go svg {
  transition: 0.2s;
}
.home-root .feat:hover .go svg {
  transform: translateX(4px);
}

/* 我的项目特色条 */
.home-root .projects {
  padding: 56px 0 24px;
}
.home-root .pj-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}
.home-root .pj {
  position: relative;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px 26px;
  cursor: pointer;
  overflow: hidden;
  backdrop-filter: blur(14px) saturate(160%);
  transition: 0.28s;
}
.home-root .pj:hover {
  transform: translateY(-4px);
  border-color: var(--border-strong);
  box-shadow: var(--shadow);
}
.home-root .pj h3 {
  font-size: 17px;
  font-weight: 600;
}
.home-root .pj p {
  margin-top: 8px;
  font-size: 14px;
  color: var(--muted);
}
.home-root .pj-tags {
  display: inline-block;
  margin-top: 14px;
  font-family: var(--vp-font-family-mono);
  font-size: 12px;
  color: var(--brand-2);
}
.home-root .pj-more {
  color: var(--brand-2);
  font-weight: 500;
}

/* 入场动效 */
.home-root .reveal {
  opacity: 0;
  transform: translateY(22px);
  transition: opacity 0.7s ease, transform 0.7s ease;
}
.home-root .reveal.in {
  opacity: 1;
  transform: none;
}

/* 响应式 */
@media (max-width: 920px) {
  .home-root .hero-grid {
    grid-template-columns: 1fr;
    gap: 40px;
  }
  .home-root .feat-grid,
  .home-root .pj-grid {
    grid-template-columns: 1fr 1fr;
  }
  .home-root .stats-grid {
    grid-template-columns: 1fr 1fr;
  }
  .home-root .term {
    justify-self: center;
    margin: 0 auto;
  }
}
@media (max-width: 560px) {
  .home-root .feat-grid,
  .home-root .pj-grid {
    grid-template-columns: 1fr;
  }
  .home-root .hero {
    padding: calc(var(--vp-nav-height) + 24px) 0 24px;
  }
  .home-root .term-body {
    height: 260px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .home-root .reveal {
    opacity: 1;
    transform: none;
  }
  .home-root .term {
    transform: none;
  }
}
</style>
