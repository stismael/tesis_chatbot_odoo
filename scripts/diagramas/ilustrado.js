// Genera diagramas ilustrados (estilo «vista general»: íconos, pasos numerados y flechas) a partir de
// especificaciones JSON, y los guarda en PNG (3×) y SVG.
// Uso: node ilustrado.js <carpeta con *.json> <carpeta de salida>
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const si = require('simple-icons');

const TABLER = path.join(path.dirname(require.resolve('simple-icons')), '..', '@tabler', 'icons', 'icons', 'outline');
const STEP = '#5C9E1E';

function icon(ref, color, size) {
  const [kind, name] = ref.split(':');
  if (kind === 'brand') {
    const key = 'si' + name.charAt(0).toUpperCase() + name.slice(1);
    const ic = si[key];
    return `<svg viewBox="0 0 24 24" width="${size}" height="${size}"><path fill="#${ic.hex}" d="${ic.path}"/></svg>`;
  }
  let svg = fs.readFileSync(path.join(TABLER, name + '.svg'), 'utf8');
  svg = svg.replace(/width="24"/, `width="${size}"`).replace(/height="24"/, `height="${size}"`)
    .replace(/stroke="currentColor"/, `stroke="${color || '#0F6CBD'}"`).replace(/stroke-width="2"/, 'stroke-width="1.6"');
  return svg;
}

function esc(t) { return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;'); }

function build(spec) {
  const W = spec.width, H = spec.height;
  const nodes = Object.fromEntries(spec.nodes.map((n) => [n.id, n]));
  const center = (n) => ({ x: n.x, y: n.y });
  let svg = '';
  // Grupos (recuadros con título)
  for (const g of spec.groups || []) {
    svg += `<rect x="${g.x}" y="${g.y}" width="${g.w}" height="${g.h}" rx="14" fill="${g.fill || '#FFFFFF'}" stroke="${g.stroke || '#B9C2CC'}" stroke-width="1.5" ${g.dashed ? 'stroke-dasharray="7 5"' : ''}/>`;
    svg += `<text x="${g.x + 16}" y="${g.y + 28}" font-size="17" font-weight="bold" fill="#3B4754">${esc(g.label)}</text>`;
  }
  // Flechas
  for (const e of spec.edges) {
    const a = center(nodes[e.from]), b = center(nodes[e.to]);
    const dy = e.dy || 0;
    const pts = [{ x: a.x, y: a.y + dy }, ...(e.via || []).map(([x, y]) => ({ x, y })), { x: b.x, y: b.y + dy }];
    // Recorta inicio y fin para no tapar los íconos
    const trim = (p, q, d) => { const dx = q.x - p.x, dy = q.y - p.y, L = Math.hypot(dx, dy) || 1; return { x: p.x + dx / L * d, y: p.y + dy / L * d }; };
    const r = e.trim || 62;
    pts[0] = trim(pts[0], pts[1], r);
    pts[pts.length - 1] = trim(pts[pts.length - 1], pts[pts.length - 2], r);
    const d = pts.map((p, i) => (i ? 'L' : 'M') + p.x.toFixed(1) + ' ' + p.y.toFixed(1)).join(' ');
    const color = e.color || '#4A5560';
    svg += `<path d="${d}" fill="none" stroke="${color}" stroke-width="2.2" ${e.dashed ? 'stroke-dasharray="8 6"' : ''} marker-end="url(#arrow${e.color ? e.color.replace('#', '') : ''})"/>`;
    // Punto medio del tramo más largo para el número y la etiqueta
    let best = 0, mid = pts[0];
    for (let i = 1; i < pts.length; i++) {
      const L = Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y);
      if (L > best) { best = L; mid = { x: (pts[i].x + pts[i - 1].x) / 2, y: (pts[i].y + pts[i - 1].y) / 2 }; }
    }
    const lx = e.labelAt ? e.labelAt[0] : mid.x + (e.labelDx || 0), ly = e.labelAt ? e.labelAt[1] - 30 : mid.y + (e.labelDy || 0);
    if (e.step) {
      const sx = e.stepAt ? e.stepAt[0] : mid.x + (e.stepDx || 0), sy = e.stepAt ? e.stepAt[1] : mid.y + (e.stepDy ?? -34);
      svg += `<circle cx="${sx}" cy="${sy}" r="17" fill="${e.stepColor || STEP}"/><text x="${sx}" y="${sy + 6}" text-anchor="middle" font-size="17" font-weight="bold" fill="#fff">${esc(e.step)}</text>`;
    }
    if (e.label) {
      const lines = e.label.split('\n');
      lines.forEach((t, i) => {
        svg += `<text x="${lx}" y="${ly + 30 + i * 18}" text-anchor="${e.labelAnchor || 'middle'}" font-size="14.5" fill="#3B4754">${esc(t)}</text>`;
      });
    }
  }
  // Nodos: ícono + título + subtítulo
  for (const n of spec.nodes) {
    const size = n.size || 58;
    if (n.box !== false) {
      svg += `<rect x="${n.x - 46}" y="${n.y - 46}" width="92" height="92" rx="18" fill="${n.bg || '#FFFFFF'}" stroke="${n.border || '#D5DBE1'}" stroke-width="1.5"/>`;
    }
    svg += `<g transform="translate(${n.x - size / 2},${n.y - size / 2})">${icon(n.icon, n.color, size)}</g>`;
    if (n.badge) {
      svg += `<g transform="translate(${n.x + 22},${n.y - 58})">${icon(n.badge, n.badgeColor, 30)}</g>`;
    }
    const lines = (n.label || '').split('\n');
    const subs = (n.sub || '').split('\n').filter(Boolean);
    const pos = n.labelPos || 'below';
    const total = lines.length * 20 + subs.length * 17;
    let tx = n.x, ty = n.y + 72, anchor = 'middle';
    if (pos === 'right') { tx = n.x + 60; ty = n.y - total / 2 + 14; anchor = 'start'; }
    if (pos === 'left') { tx = n.x - 60; ty = n.y - total / 2 + 14; anchor = 'end'; }
    if (pos === 'above') { ty = n.y - 58 - total + 14; }
    lines.forEach((t, i) => {
      svg += `<text x="${tx}" y="${ty + i * 20}" text-anchor="${anchor}" font-size="16.5" font-weight="bold" fill="#1F2A36">${esc(t)}</text>`;
    });
    subs.forEach((t, i) => {
      svg += `<text x="${tx}" y="${ty + lines.length * 20 + i * 17}" text-anchor="${anchor}" font-size="13.5" fill="#55636F">${esc(t)}</text>`;
    });
  }
  // Notas (cuadros de texto)
  for (const t of spec.notes || []) {
    const lines = t.text.split('\n');
    const h = 22 + lines.length * 19;
    svg += `<rect x="${t.x}" y="${t.y}" width="${t.w}" height="${h}" rx="10" fill="${t.fill || '#F3F7FB'}" stroke="${t.stroke || '#C9D6E3'}"/>`;
    lines.forEach((l, i) => {
      const bold = l.startsWith('**');
      svg += `<text x="${t.x + 14}" y="${t.y + 24 + i * 19}" font-size="14" ${bold ? 'font-weight="bold"' : ''} fill="#2D3A46">${esc(l.replace(/^\*\*/, ''))}</text>`;
    });
  }
  const markers = ['#4A5560', ...new Set(spec.edges.filter((e) => e.color).map((e) => e.color))].map((c) =>
    `<marker id="arrow${c === '#4A5560' ? '' : c.replace('#', '')}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="${c}"/></marker>`).join('');
  const title = spec.title ? `<text x="30" y="44" font-size="24" font-weight="bold" fill="#1F2A36">${esc(spec.title)}</text>` : '';
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" font-family="Arial, Helvetica, sans-serif">
<defs>${markers}</defs><rect width="${W}" height="${H}" fill="#F7F8FA"/>${title}${svg}</svg>`;
}

(async () => {
  const [SRC, OUT] = process.argv.slice(2);
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  for (const f of fs.readdirSync(SRC).filter((x) => x.endsWith('.json')).sort()) {
    const spec = JSON.parse(fs.readFileSync(path.join(SRC, f), 'utf8'));
    const svg = build(spec);
    const name = f.replace('.json', '');
    fs.writeFileSync(path.join(OUT, name + '.svg'), svg);
    const page = await browser.newPage({ deviceScaleFactor: 3, viewport: { width: spec.width, height: spec.height } });
    await page.setContent(`<html><body style="margin:0">${svg}</body></html>`);
    await page.locator('svg').first().screenshot({ path: path.join(OUT, name + '.png') });
    await page.close();
    console.log('OK', name);
  }
  await browser.close();
})();
