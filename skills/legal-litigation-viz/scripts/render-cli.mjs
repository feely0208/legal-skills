#!/usr/bin/env node
/** 诉讼可视化 · 离线渲染：case.json → 单文件 HTML（无依赖） */
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { renderHtml } from './render.mjs';

const [input, ...rest] = process.argv.slice(2);
if (!input || input === '--help' || input === '-h') {
  console.log('用法：node render-cli.mjs <case.json> [-o 输出.html]');
  process.exit(input ? 0 : 2);
}
const i = rest.indexOf('-o');
const out = i >= 0 ? rest[i + 1] : join(process.cwd(), '诉讼可视化.html');
const data = JSON.parse(readFileSync(input, 'utf8'));
writeFileSync(out, renderHtml(data), 'utf8');
console.log('已生成：' + out);
