const { chromium } = require('playwright');
const BASE = process.env.ODOO_URL || "http://localhost:8069";
async function login(page, u, pw) { await page.goto(BASE + '/web/login'); await page.fill('#login', u); await page.fill('#password', pw); await page.click('button[type=submit]'); await page.waitForURL(/\/odoo/); }
async function openChat(page) {
  const url = await page.evaluate(async () => { const r = await fetch('/web/dataset/call_kw/chatbot.discuss.service/open_assistant_chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: { model: 'chatbot.discuss.service', method: 'open_assistant_chat', args: [], kwargs: {} } }) }); return (await r.json()).result.url; });
  await page.goto(BASE + url); await page.waitForSelector('.o-mail-Message'); await page.waitForTimeout(3000);
}
// Recorta desde el mensaje que contiene `a` hasta el que contiene `z` (índices de aparición), incluyendo el ancho del hilo.
async function clip(page, a, z, path, opts = {}) {
  await page.evaluate((t) => { const m = [...document.querySelectorAll('.o-mail-Message')].find(x => x.innerText.includes(t)); m.scrollIntoView({ block: 'start' }); }, a);
  await page.waitForTimeout(700);
  const box = await page.evaluate(([a, z]) => {
    const ms = [...document.querySelectorAll('.o-mail-Message')];
    const i = ms.findIndex(x => x.innerText.includes(a)); let j = -1; ms.forEach((x, k) => { if (k >= i && x.innerText.includes(z) && j < 0) j = k; });
    const r1 = ms[i].getBoundingClientRect(), r2 = ms[j].getBoundingClientRect(); const th = document.querySelector('.o-mail-Thread').getBoundingClientRect();
    return { x: th.x, y: r1.y - 6, width: th.width, height: r2.bottom - r1.y + 12 };
  }, [a, z]);
  if (opts.top) { box.height += box.y; box.y = 0; box.x = 0; box.width = 1366; }
  await page.screenshot({ path, clip: box });
  console.log(path, JSON.stringify(box));
}
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1366, height: 1500 }, deviceScaleFactor: 2 });
  const p = await ctx.newPage(); await login(p, 'admin', 'admin'); await openChat(p);
  await clip(p, 'Hola, soy el', 'tiene 161 Unidades', 'f_chat.png', { top: true });
  await clip(p, 'Consultas que puedo responder', 'Consultas que puedo responder', 'f_help.png');
  await clip(p, 'Stock y facturación de la Cadena', 'No puedo crear facturas', 'f_memoria.png');
  await clip(p, 'facturas de Motopartes Ecuador', 'Mostrando 5 de 12', 'f_extenso.png');
  const ctx2 = await b.newContext({ viewport: { width: 1366, height: 1500 }, deviceScaleFactor: 2 });
  const q = await ctx2.newPage(); await login(q, 'diego.salinas@demo-motos.ec', 'demo'); await openChat(q);
  await clip(q, '¿Está pagada la factura INV/2026/00001?', 'andrea.villafuerte', 'f_permiso.png');
  await b.close();
})();
