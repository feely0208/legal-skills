/**
 * 深鲸诉讼可视化 · 渲染器 v2（纯 Node，无第三方依赖）
 *
 * 输入：案件 JSON（schema 见 skills/legal-litigation-viz/SKILL.md）
 * 输出：单文件 HTML（内联 CSS/JS/SVG），可交互、可打印、离线可用。
 *
 * v2 相比 v1：
 *  - 左侧目录 + 顶部页签，五个视图（时间轴/关系图/证据矩阵/争点/缺口）
 *  - 时间轴按年分组、关键/有证据/无证据筛选、关键词搜索
 *  - 关系图曲线边、悬停高亮、缩放
 *  - 证据矩阵：事实覆盖率、零证据事实标红、首列吸附
 *  - 打印时自动展开全部视图
 */

const ESC = (s) => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

const SIDE = {
  plaintiff: { label: '原告 / 申请人视角', accent: '#2563eb', tint: '#eff6ff', name: '原告' },
  defendant: { label: '被告 / 被申请人视角', accent: '#c2410c', tint: '#fff7ed', name: '被告' },
  neutral: { label: '中立梳理', accent: '#475569', tint: '#f8fafc', name: '中立' },
};

const SIG_MAP = { red: '🔴', yellow: '🟡', white: '⚪', '🔴': '🔴', '🟡': '🟡', '⚪': '⚪' };
const SIG_CLASS = { '🔴': 'sig-red', '🟡': 'sig-yellow', '⚪': 'sig-white' };
const KIND = {
  contract: { icon: '📄', label: '合同' }, payment: { icon: '💰', label: '款项' },
  court: { icon: '⚖️', label: '诉讼' }, notice: { icon: '✉️', label: '通知/催告' },
  injury: { icon: '🩺', label: '损害' }, other: { icon: '•', label: '其他' },
};

function norm(data) {
  const d = data && typeof data === 'object' ? data : {};
  const arr = (x) => (Array.isArray(x) ? x : []);
  return {
    title: String(d.title || '案件梳理'),
    caseNo: String(d.caseNo || ''),
    court: String(d.court || ''),
    hearingDate: String(d.hearingDate || ''),
    side: SIDE[d.side] ? d.side : 'neutral',
    summary: String(d.summary || ''),
    parties: arr(d.parties),
    events: arr(d.events).filter((e) => e && (e.date || e.fact)),
    relations: arr(d.relations).filter((r) => r && r.from && r.to),
    facts: arr(d.facts),
    evidence: arr(d.evidence),
    issues: arr(d.issues),
    gaps: arr(d.gaps),
  };
}

function dateKey(e) {
  const s = String(e.date || '');
  const m = s.match(/(\d{4})[-年./]?(\d{1,2})?[-月./]?(\d{1,2})?/);
  if (!m) return '9999-99-99';
  return `${m[1]}-${String(m[2] || '99').padStart(2, '0')}-${String(m[3] || '99').padStart(2, '0')}`;
}

function coverage(d) {
  if (!d.facts.length) return null;
  const covered = d.facts.filter((f) => d.evidence.some((e) => (Array.isArray(e.proves) ? e.proves : []).includes(f.id)));
  return { covered: covered.length, total: d.facts.length, pct: Math.round((covered.length / d.facts.length) * 100) };
}

function stats(d) {
  const cov = coverage(d);
  const red = d.events.filter((e) => (SIG_MAP[e.significance] || SIG_MAP[e.sig]) === '🔴').length;
  const noEv = d.events.filter((e) => !(Array.isArray(e.evidence) ? e.evidence.length : e.evidence)).length;
  return [
    ['事件', d.events.length], ['关键事件', red], ['证据', d.evidence.length],
    ['待证事实', d.facts.length], ['争点', d.issues.length],
    ['事实覆盖', cov ? cov.pct + '%' : '—'], ['无证据事件', noEv],
  ];
}

function timeline(d) {
  const events = [...d.events].sort((a, b) => dateKey(a).localeCompare(dateKey(b)));
  if (!events.length) return `<div class="empty">还没有事件。events 里每条至少要有 date 和 fact。</div>`;
  const years = [...new Set(events.map((e) => String(e.date || '').slice(0, 4) || '时间待定'))];
  const body = years.map((y) => {
    const rows = events.filter((e) => (String(e.date || '').slice(0, 4) || '时间待定') === y).map((e) => {
      const sig = SIG_MAP[e.significance] || SIG_MAP[e.sig] || '⚪';
      const ev = Array.isArray(e.evidence) ? e.evidence : (e.evidence ? [e.evidence] : []);
      const kind = KIND[e.kind] || KIND.other;
      return `<li class="tl-item ${SIG_CLASS[sig] || 'sig-white'}" data-sig="${sig}" data-hasev="${ev.length ? 1 : 0}" data-text="${ESC((e.fact || '') + ' ' + (e.actor || '') + ' ' + ev.join(' '))}">
        <div class="tl-date">${ESC(e.date || '时间待定')}</div>
        <div class="tl-body">
          <div class="tl-fact"><span class="sig-badge" title="重要性">${sig}</span><span class="kind" title="${ESC(kind.label)}">${kind.icon}</span>${ESC(e.fact || '')}</div>
          <div class="tl-meta">${e.actor ? `<span class="who">${ESC(e.actor)}</span>` : ''}${ev.length ? ev.map((x) => `<span class="ev">${ESC(x)}</span>`).join('') : '<span class="noev">无证据</span>'}${e.note ? `<span class="note">${ESC(e.note)}</span>` : ''}</div>
        </div>
      </li>`;
    }).join('');
    return `<div class="tl-year" data-year="${ESC(y)}"><div class="tl-year-label">${ESC(y)}<span>${rows.split('tl-item').length - 1} 条</span></div><ol class="tl">${rows}</ol></div>`;
  }).join('');
  return `<div class="toolbar">
      <div class="chips" id="tl-chips">
        <button class="chip on" data-f="all">全部</button>
        <button class="chip" data-f="red">🔴 关键</button>
        <button class="chip" data-f="yellow">🟡 辅助</button>
        <button class="chip" data-f="ev">有证据</button>
        <button class="chip" data-f="noev">无证据</button>
      </div>
      <input class="search" id="tl-search" placeholder="搜事件/主体/证据编号…">
    </div>${body}<div class="empty" id="tl-empty" style="display:none">没有匹配的事件。</div>`;
}

function relations(d) {
  const nodes = [];
  const push = (id, label, role) => { if (id && !nodes.find((n) => n.id === id)) nodes.push({ id, label: label || id, role: role || '' }); };
  d.parties.forEach((p) => push(p.id || p.name, p.name || p.id, p.role));
  d.relations.forEach((r) => { push(r.from, r.fromLabel || r.from); push(r.to, r.toLabel || r.to); });
  if (!nodes.length) return `<div class="empty">还没有当事人或法律关系。至少给 parties 和 relations。</div>`;
  const W = 900;
  const H = nodes.length <= 2 ? 280 : Math.max(380, Math.min(560, 200 + nodes.length * 34));
  const cx = W / 2, cy = H / 2, rx = W / 2 - 180, ry = H / 2 - 100;
  const pos = {};
  if (nodes.length === 1) pos[nodes[0].id] = { x: cx, y: cy };
  else if (nodes.length === 2) { pos[nodes[0].id] = { x: 230, y: cy }; pos[nodes[1].id] = { x: W - 230, y: cy }; }
  else nodes.forEach((n, i) => { const a = (Math.PI * 2 * i) / nodes.length - Math.PI / 2; pos[n.id] = { x: cx + rx * Math.cos(a), y: cy + ry * Math.sin(a) }; });

  const colorOf = (role) => /原告|申请|债权|受害/.test(role) ? '#2563eb' : /被告|被申请|债务|侵权/.test(role) ? '#c2410c' : '#475569';
  const edges = d.relations.map((r, i) => {
    const a = pos[r.from], b = pos[r.to]; if (!a || !b) return '';
    const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
    const dx = b.x - a.x, dy = b.y - a.y, len = Math.hypot(dx, dy) || 1;
    const qx = mx + (dy / len) * 26, qy = my - (dx / len) * 26;
    const label = ESC(r.label || '');
    const w = Math.max(76, label.length * 14);
    return `<g class="edge" data-from="${ESC(r.from)}" data-to="${ESC(r.to)}">
      <path d="M${a.x} ${a.y} Q${qx} ${qy} ${b.x} ${b.y}" marker-end="url(#arrow)"/>
      <rect x="${qx - w / 2}" y="${qy - 14}" width="${w}" height="26" rx="7" class="edge-bg"/>
      <text x="${qx}" y="${qy + 4}" text-anchor="middle" class="edge-label">${label}</text></g>`;
  }).join('');
  const circles = nodes.map((n) => {
    const p = pos[n.id]; const w = Math.max(104, n.label.length * 15 + 30);
    return `<g class="node" data-id="${ESC(n.id)}"><rect x="${p.x - w / 2}" y="${p.y - 24}" width="${w}" height="48" rx="12" class="node-bg" stroke="${colorOf(n.role)}"/>
      <text x="${p.x}" y="${p.y - 3}" text-anchor="middle" class="node-name">${ESC(n.label)}</text>
      <text x="${p.x}" y="${p.y + 15}" text-anchor="middle" class="node-role" fill="${colorOf(n.role)}">${ESC(n.role)}</text></g>`;
  }).join('');
  return `<div class="graph-toolbar"><button class="mini" data-zoom="in">放大</button><button class="mini" data-zoom="out">缩小</button><button class="mini" data-zoom="reset">复位</button><span class="hint">悬停节点可高亮相关关系；滚轮也可缩放（按住 Ctrl）。</span></div>
    <div class="graph-wrap"><svg viewBox="0 0 ${W} ${H}" class="rel" id="rel-svg" role="img" aria-label="法律关系图">
      <defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#94a3b8"/></marker></defs>
      ${edges}${circles}</svg></div>
    <div class="legend"><span><i style="background:#2563eb"></i>原告/债权/受害</span><span><i style="background:#c2410c"></i>被告/债务/侵权</span><span><i style="background:#475569"></i>其他</span></div>`;
}

function evidenceMatrix(d) {
  if (!d.evidence.length) return `<div class="empty">还没有证据。evidence 里每条给 id、name、proves（对应 facts 的 id）。</div>`;
  const facts = d.facts;
  if (!facts.length) {
    return `<table class="m"><thead><tr><th>编号</th><th>证据</th><th>证明目的</th><th>状态</th></tr></thead><tbody>${d.evidence.map((e) => `<tr><td>${ESC(e.id || '')}</td><td>${ESC(e.name || '')}</td><td>${ESC(e.purpose || '')}</td><td>${ESC(e.status || '待补')}</td></tr>`).join('')}</tbody></table>`;
  }
  const count = {}; facts.forEach((f) => { count[f.id] = d.evidence.filter((e) => (Array.isArray(e.proves) ? e.proves : []).includes(f.id)).length; });
  const head = facts.map((f) => `<th class="${count[f.id] ? '' : 'gap-col'}" title="${ESC(f.text || f.id)}"><span class="fid">${ESC(f.id || '')}</span><span class="ftext">${ESC(f.text || '')}</span><span class="fcount ${count[f.id] ? '' : 'zero'}">${count[f.id] ? count[f.id] + ' 份' : '0 份'}</span></th>`).join('');
  const rows = d.evidence.map((e) => {
    const proves = new Set(Array.isArray(e.proves) ? e.proves : []);
    const cells = facts.map((f) => proves.has(f.id) ? '<td class="yes">✓</td>' : '<td class="no">—</td>').join('');
    return `<tr><td class="sticky">${ESC(e.id || '')}</td><td class="sticky2">${ESC(e.name || '')}</td>${cells}<td>${ESC(e.status || '待补')}</td></tr>`;
  }).join('');
  const cov = coverage(d);
  return `<div class="cov"><div class="cov-bar"><i style="width:${cov.pct}%"></i></div><span>事实覆盖 ${cov.covered}/${cov.total}（${cov.pct}%）</span></div>
    <div class="table-wrap"><table class="m matrix"><thead><tr><th class="sticky">证据</th><th class="sticky2">名称</th>${head}<th>状态</th></tr></thead><tbody>${rows}</tbody></table></div>
    <p class="hint">✓ = 该证据用于证明该事实；— = 未对应。红色列 = 还没有任何证据支撑的事实（缺口）。</p>`;
}

function issues(d) {
  if (!d.issues.length) return `<div class="empty">还没有争点。issues 里每条给 point、ours、theirs、evidence。</div>`;
  return `<div class="issues">${d.issues.map((x, i) => {
    const ev = Array.isArray(x.evidence) ? x.evidence : (x.evidence ? [x.evidence] : []);
    return `<article class="issue">
      <div class="issue-h"><span class="idx">${i + 1}</span><h3>${ESC(x.point || '')}</h3>${x.status ? `<span class="pill">${ESC(x.status)}</span>` : ''}</div>
      <div class="vs"><div class="side ours"><b>我方</b><p>${ESC(x.ours || '—')}</p></div><div class="side theirs"><b>对方</b><p>${ESC(x.theirs || '—')}</p></div></div>
      <div class="issue-f">${ev.length ? '对应证据：' + ev.map((e) => `<span class="ev">${ESC(e)}</span>`).join('') : '<span class="noev">未绑定证据</span>'}${x.tip ? `<div class="tip">准备提示：${ESC(x.tip)}</div>` : ''}</div>
    </article>`;
  }).join('')}</div>`;
}

function gaps(d) {
  if (!d.gaps.length) return `<div class="empty">没有记录缺口。如果材料确实完整，可以留空；否则这正是最该写的一节。</div>`;
  return `<ul class="gaps">${d.gaps.map((g) => {
    const t = typeof g === 'string' ? g : (g.text || '');
    const owner = typeof g === 'object' && g.owner ? `<span class="gap-meta">负责：${ESC(g.owner)}</span>` : '';
    const due = typeof g === 'object' && g.due ? `<span class="gap-meta">截止：${ESC(g.due)}</span>` : '';
    return `<li><span class="gap-dot">!</span><div><p>${ESC(t)}</p>${owner}${due}</div></li>`;
  }).join('')}</ul>`;
}

export function normalize(data) { return norm(data); }

export function renderHtml(input) {
  const d = norm(input);
  const side = SIDE[d.side];
  const now = new Date();
  const stamp = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
  const st = stats(d);
  return `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${ESC(d.title)} · 诉讼可视化</title>
<style>
  :root{--accent:${side.accent};--tint:${side.tint};--ink:#0f172a;--muted:#64748b;--line:#e2e8f0;--bg:#f5f7fb;--card:#fff}
  *{box-sizing:border-box}
  html{scroll-behavior:smooth}
  body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,"PingFang SC","Microsoft YaHei",Segoe UI,sans-serif;line-height:1.65;font-size:15px}
  a{color:inherit}
  .layout{display:grid;grid-template-columns:210px minmax(0,1fr);max-width:1280px;margin:0 auto;gap:0}
  /* 侧栏 */
  aside{position:sticky;top:0;height:100vh;padding:26px 14px 26px 22px;border-right:1px solid var(--line);background:rgba(255,255,255,.75);backdrop-filter:blur(8px);display:flex;flex-direction:column;gap:18px}
  .brand{display:flex;align-items:center;gap:8px;font-weight:700;font-size:15px;color:var(--accent)}
  .brand i{width:9px;height:9px;border-radius:50%;background:var(--accent);display:inline-block}
  .nav{display:flex;flex-direction:column;gap:4px}
  .nav button{display:flex;align-items:center;gap:9px;border:0;background:transparent;text-align:left;padding:9px 10px;border-radius:9px;font-size:13.5px;color:var(--muted);cursor:pointer}
  .nav button .n{width:18px;height:18px;border-radius:5px;background:#eef2f7;display:grid;place-items:center;font-size:11px;color:#64748b}
  .nav button:hover{background:#eef2f7;color:var(--ink)}
  .nav button.on{background:var(--tint);color:var(--accent);font-weight:600}
  .nav button.on .n{background:var(--accent);color:#fff}
  .side-foot{margin-top:auto;font-size:11.5px;color:#94a3b8;line-height:1.7}
  /* 主体 */
  main{padding:34px 40px 80px;min-width:0}
  header.hero{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:24px 26px;margin-bottom:18px;border-top:4px solid var(--accent)}
  .chip-side{display:inline-block;background:var(--tint);color:var(--accent);border-radius:999px;padding:2px 11px;font-size:12px;font-weight:600;margin-right:8px}
  .meta{color:var(--muted);font-size:12.5px}
  h1{font-size:27px;margin:8px 0 6px;letter-spacing:.2px}
  .summary{color:#334155;font-size:14px;margin-top:8px}
  .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(92px,1fr));gap:10px;margin-top:18px}
  .stat{background:var(--bg);border:1px solid var(--line);border-radius:11px;padding:9px 12px}
  .stat b{display:block;font-size:19px;color:var(--accent)}
  .stat span{font-size:11.5px;color:var(--muted)}
  /* 视图 */
  .panel{display:none}.panel.on{display:block}
  .card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px 22px;margin-bottom:16px}
  .card h2{font-size:17px;margin:0 0 4px;display:flex;align-items:center;gap:8px}
  .card h2 small{font-weight:400;color:var(--muted);font-size:12px}
  .sub{color:var(--muted);font-size:12.5px;margin:0 0 14px}
  .empty{color:#94a3b8;font-size:14px;padding:16px 0}
  .hint{color:#64748b;font-size:12.5px;margin:10px 0 0}
  /* 工具条 */
  .toolbar{display:flex;gap:10px;align-items:center;justify-content:space-between;flex-wrap:wrap;margin-bottom:14px}
  .chips{display:flex;gap:7px;flex-wrap:wrap}
  .chip{border:1px solid var(--line);background:#fff;color:var(--muted);font-size:12.5px;padding:6px 12px;border-radius:999px;cursor:pointer}
  .chip.on{background:var(--accent);border-color:var(--accent);color:#fff}
  .search{border:1px solid var(--line);border-radius:9px;padding:7px 12px;font-size:13px;min-width:220px;outline:none}
  .search:focus{border-color:var(--accent)}
  /* 时间轴 */
  .tl-year{margin-bottom:20px}
  .tl-year-label{font-size:13px;font-weight:700;color:var(--accent);display:flex;gap:8px;align-items:baseline;margin:0 0 8px;padding-left:4px}
  .tl-year-label span{font-weight:400;color:var(--muted);font-size:11.5px}
  .tl{list-style:none;margin:0;padding:0;position:relative}
  .tl:before{content:"";position:absolute;left:118px;top:8px;bottom:8px;width:2px;background:var(--line)}
  .tl-item{display:grid;grid-template-columns:104px 1fr;gap:30px;padding:9px 0;position:relative;border-radius:10px}
  .tl-item:hover{background:rgba(37,99,235,.04)}
  .tl-date{font-weight:600;font-size:12.5px;color:#334155;position:relative;text-align:right;padding-right:20px;align-self:center}
  .tl-date:after{content:"";position:absolute;right:-5px;top:50%;transform:translateY(-50%);width:10px;height:10px;border-radius:50%;background:#cbd5e1;box-shadow:0 0 0 3px #fff;z-index:1}
  .sig-red .tl-date:after{background:#ef4444}.sig-yellow .tl-date:after{background:#f59e0b}.sig-white .tl-date:after{background:#94a3b8}
  .tl-body{padding-left:10px}
  .tl-fact{font-size:14.5px}
  .sig-red .tl-fact{font-weight:600}
  .tl-meta{color:var(--muted);font-size:12px;margin-top:4px;display:flex;gap:6px;flex-wrap:wrap;align-items:center}
  .kind{opacity:.75;margin-right:6px}.sig-badge{margin-right:5px;font-size:12px}
  .who{background:#eef2f7;border-radius:5px;padding:0 6px}
  .ev{display:inline-block;background:#eef2f7;border-radius:5px;padding:0 6px;font-size:12px}
  .noev{color:#dc2626;font-size:12px}
  .note{color:#94a3b8}
  .tl-sig{font-size:13px}
  /* 关系图 */
  .graph-toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:10px}
  .mini{border:1px solid var(--line);background:#fff;border-radius:8px;padding:5px 12px;font-size:12.5px;cursor:pointer;color:#475569}
  .mini:hover{border-color:var(--accent);color:var(--accent)}
  .graph-wrap{overflow:hidden;border:1px solid var(--line);border-radius:12px;background:linear-gradient(180deg,#fbfdff,#f4f8ff)}
  .rel{width:100%;height:auto;display:block;transition:transform .18s ease}
  .node-bg{fill:#fff;stroke-width:2.2;filter:drop-shadow(0 2px 3px rgba(15,23,42,.06))}
  .node-name{font-size:13.5px;font-weight:700;fill:#0f172a}
  .node-role{font-size:11.5px}
  .edge path{fill:none;stroke:#94a3b8;stroke-width:1.6}
  .edge-bg{fill:#fff;stroke:var(--line)}
  .edge-label{font-size:11.5px;fill:#475569}
  .node.dim,.edge.dim{opacity:.18}
  .legend{display:flex;gap:18px;color:var(--muted);font-size:12px;margin-top:10px;flex-wrap:wrap}
  .legend i{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px}
  /* 表 */
  .table-wrap{overflow:auto;border:1px solid var(--line);border-radius:12px;max-height:70vh}
  table.m{width:100%;border-collapse:separate;border-spacing:0;font-size:13px}
  table.m th,table.m td{border-bottom:1px solid var(--line);padding:9px 10px;text-align:left;vertical-align:top}
  table.m th{background:#f8fafc;font-size:12px;color:#475569;font-weight:600;position:sticky;top:0;z-index:2}
  table.m th .fid{display:block;font-weight:700;color:#334155}
  table.m th .ftext{display:block;font-weight:400;color:#64748b;font-size:11px;max-width:150px;white-space:normal}
  table.m th .fcount{display:inline-block;margin-top:4px;font-size:10.5px;background:#eef2f7;border-radius:999px;padding:0 6px;color:#64748b}
  table.m th .fcount.zero{background:#fee2e2;color:#b91c1c}
  table.m th.gap-col{background:#fff5f5}
  table.m td.yes{text-align:center;color:#16a34a;font-weight:700;background:#f0fdf4}
  table.m td.no{text-align:center;color:#e2e8f0}
  table.m td.sticky,table.m th.sticky{position:sticky;left:0;background:#fff;z-index:3}
  table.m th.sticky{background:#f8fafc;z-index:4}
  table.m td.sticky2,table.m th.sticky2{position:sticky;left:52px;background:#fff;z-index:3;min-width:120px}
  table.m th.sticky2{background:#f8fafc;z-index:4}
  .cov{display:flex;align-items:center;gap:12px;margin-bottom:12px;font-size:12.5px;color:var(--muted)}
  .cov-bar{flex:1;height:8px;background:#eef2f7;border-radius:99px;overflow:hidden;max-width:320px}
  .cov-bar i{display:block;height:100%;background:linear-gradient(90deg,var(--accent),#22d3ee)}
  /* 争点 */
  .issues{display:grid;gap:12px}
  .issue{border:1px solid var(--line);border-radius:14px;padding:16px 18px;background:#fff}
  .issue-h{display:flex;align-items:center;gap:9px;margin-bottom:10px}
  .issue-h h3{margin:0;font-size:15px}
  .issue-h .idx{width:22px;height:22px;border-radius:7px;background:var(--tint);color:var(--accent);display:grid;place-items:center;font-size:12px;font-weight:700}
  .pill{font-size:11px;border:1px solid var(--line);border-radius:999px;padding:1px 9px;color:var(--muted)}
  .vs{display:grid;grid-template-columns:1fr 1fr;gap:12px}
  .side{border-radius:10px;padding:10px 12px;font-size:13px}
  .side b{font-size:11.5px;letter-spacing:.05em}
  .side p{margin:4px 0 0;color:#334155}
  .ours{background:#eff6ff}.theirs{background:#fff7ed}
  .ours b{color:#2563eb}.theirs b{color:#c2410c}
  .issue-f{margin-top:10px;font-size:12.5px;color:var(--muted)}
  .tip{margin-top:6px;color:#475569}
  /* 缺口 */
  .gaps{list-style:none;margin:0;padding:0;display:grid;gap:9px}
  .gaps li{display:flex;gap:11px;background:#fff7ed;border:1px solid #fed7aa;border-radius:11px;padding:11px 14px;font-size:13.5px}
  .gap-dot{width:20px;height:20px;border-radius:50%;background:#fb923c;color:#fff;font-weight:700;display:grid;place-items:center;font-size:12px;flex:none}
  .gaps p{margin:0}
  .gap-meta{font-size:11.5px;color:#9a3412;margin-right:10px}
  footer{margin-top:26px;color:#94a3b8;font-size:12px;border-top:1px solid var(--line);padding-top:14px}
  .print-btn{border:1px solid var(--line);background:#fff;border-radius:9px;padding:7px 14px;font-size:12.5px;cursor:pointer;color:#475569}
  .print-btn:hover{border-color:var(--accent);color:var(--accent)}
  .topbar{display:flex;justify-content:flex-end;gap:8px;margin-bottom:10px}
  @media (max-width:900px){
    .layout{grid-template-columns:1fr}
    aside{position:static;height:auto;border-right:0;border-bottom:1px solid var(--line);flex-direction:row;align-items:center;flex-wrap:wrap;padding:12px 16px}
    .nav{flex-direction:row;overflow:auto;flex:1}
    .nav button{white-space:nowrap}
    .side-foot{display:none}
    main{padding:18px 16px 60px}
    .tl-item{grid-template-columns:84px 1fr;gap:16px}
    .tl:before{left:96px}
    .tl-date{padding-right:16px;font-size:11.5px}
    .vs{grid-template-columns:1fr}
  }
  @media print{
    aside,.topbar,.toolbar,.graph-toolbar{display:none!important}
    .layout{display:block;max-width:none}
    main{padding:0}
    .panel{display:block!important;break-inside:avoid}
    .card{box-shadow:none;break-inside:avoid}
    .table-wrap{max-height:none;overflow:visible}
    body{background:#fff}
    @page{margin:12mm}
  }
</style></head><body><div class="layout">
<aside>
  <div class="brand"><i></i>诉讼可视化</div>
  <nav class="nav" id="nav">
    <button class="on" data-tab="timeline"><span class="n">1</span>时间轴</button>
    <button data-tab="relations"><span class="n">2</span>法律关系</button>
    <button data-tab="evidence"><span class="n">3</span>证据矩阵</button>
    <button data-tab="issues"><span class="n">4</span>争点对照</button>
    <button data-tab="gaps"><span class="n">5</span>证据缺口</button>
  </nav>
  <div class="side-foot">只用你给的材料，不补事实。<br>打印时自动展开全部视图。</div>
</aside>
<main>
  <div class="topbar"><button class="print-btn" onclick="window.print()">打印 / 导出 PDF</button></div>
  <header class="hero">
    <div class="meta"><span class="chip-side">${ESC(side.label)}</span>${d.caseNo ? '案号：' + ESC(d.caseNo) : ''}${d.court ? ' · ' + ESC(d.court) : ''}${d.hearingDate ? ' · 开庭：' + ESC(d.hearingDate) : ''}</div>
    <h1>${ESC(d.title)}</h1>
    ${d.summary ? `<div class="summary">${ESC(d.summary)}</div>` : ''}
    <div class="stats">${st.map(([k, v]) => `<div class="stat"><b>${ESC(v)}</b><span>${ESC(k)}</span></div>`).join('')}</div>
  </header>
  <section class="panel on" id="panel-timeline"><div class="card"><h2>时间轴 <small>按日期排序，红色为关键事件</small></h2>${timeline(d)}</div></section>
  <section class="panel" id="panel-relations"><div class="card"><h2>法律关系 <small>颜色区分立场，箭头表示关系指向</small></h2>${relations(d)}</div></section>
  <section class="panel" id="panel-evidence"><div class="card"><h2>证据矩阵 <small>每份证据能证明哪个待证事实</small></h2>${evidenceMatrix(d)}</div></section>
  <section class="panel" id="panel-issues"><div class="card"><h2>争点对照 <small>主张 vs 抗辩 vs 证据</small></h2>${issues(d)}</div></section>
  <section class="panel" id="panel-gaps"><div class="card"><h2>证据缺口 <small>开庭前最该补的东西</small></h2>${gaps(d)}</div></section>
  <footer>生成于 ${stamp} · 深鲸诉讼可视化 · 本图根据输入材料整理，不构成法律意见；提交前须由承办律师核对原始材料。</footer>
</main></div>
<script>
(function(){
  var nav=document.getElementById('nav');
  function show(t){document.querySelectorAll('.panel').forEach(function(p){p.classList.toggle('on',p.id==='panel-'+t)});
    nav.querySelectorAll('button').forEach(function(b){b.classList.toggle('on',b.getAttribute('data-tab')===t)});
    if(history.replaceState)history.replaceState(null,'','#'+t);}
  nav.addEventListener('click',function(e){var b=e.target.closest('button');if(b)show(b.getAttribute('data-tab'))});
  var h=location.hash.slice(1); if(h&&document.getElementById('panel-'+h))show(h);

  // 时间轴筛选
  var chips=document.getElementById('tl-chips'), search=document.getElementById('tl-search');
  if(chips){
    var filter='all';
    function apply(){
      var q=(search&&search.value||'').trim().toLowerCase(), n=0;
      document.querySelectorAll('.tl-item').forEach(function(li){
        var sig=li.getAttribute('data-sig'), has=li.getAttribute('data-hasev')==='1', txt=li.getAttribute('data-text').toLowerCase();
        var ok=(filter==='all')||(filter==='red'&&sig==='🔴')||(filter==='yellow'&&sig==='🟡')||(filter==='ev'&&has)||(filter==='noev'&&!has);
        if(q) ok=ok&&txt.indexOf(q)>=0;
        li.style.display=ok?'':'none'; if(ok)n++;
      });
      document.querySelectorAll('.tl-year').forEach(function(y){
        var vis=y.querySelectorAll('.tl-item:not([style*="display: none"])').length;
        y.style.display=vis?'':'none';
      });
      var em=document.getElementById('tl-empty'); if(em)em.style.display=n?'none':'';
    }
    chips.addEventListener('click',function(e){var b=e.target.closest('.chip');if(!b)return;
      chips.querySelectorAll('.chip').forEach(function(x){x.classList.remove('on')});b.classList.add('on');filter=b.getAttribute('data-f');apply();});
    if(search)search.addEventListener('input',apply);
  }

  // 关系图悬停 + 缩放
  var svg=document.getElementById('rel-svg');
  if(svg){
    var nodes=svg.querySelectorAll('.node'), edges=svg.querySelectorAll('.edge');
    nodes.forEach(function(n){
      n.addEventListener('mouseenter',function(){
        var id=n.getAttribute('data-id');
        nodes.forEach(function(x){x.classList.toggle('dim',x!==n&&x.getAttribute('data-id')!==id)});
        edges.forEach(function(e){var f=e.getAttribute('data-from'),t=e.getAttribute('data-to');e.classList.toggle('dim',f!==id&&t!==id)});
      });
      n.addEventListener('mouseleave',function(){nodes.forEach(function(x){x.classList.remove('dim')});edges.forEach(function(e){e.classList.remove('dim')})});
    });
    var scale=1, wrap=svg.parentElement;
    function set(z){scale=Math.max(.6,Math.min(2.5,z));svg.style.transform='scale('+scale+')';svg.style.transformOrigin='center top';}
    document.querySelectorAll('[data-zoom]').forEach(function(b){b.addEventListener('click',function(){
      var z=b.getAttribute('data-zoom'); if(z==='in')set(scale+.15); else if(z==='out')set(scale-.15); else set(1);});});
    wrap.addEventListener('wheel',function(e){if(!e.ctrlKey)return;e.preventDefault();set(scale+(e.deltaY<0?.08:-.08));},{passive:false});
  }
})();
</script>
</body></html>`;
}
