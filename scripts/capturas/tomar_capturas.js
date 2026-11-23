const { chromium } = require('playwright');
const BASE = process.env.ODOO_URL || "http://localhost:8069";
async function login(page, u, pw) { await page.goto(BASE + '/web/login'); await page.fill('#login', u); await page.fill('#password', pw); await page.click('button[type=submit]'); await page.waitForURL(/\/odoo/); }
let chatUrl;
async function openAssistant(page) {
  chatUrl = await page.evaluate(async () => { const r = await fetch('/web/dataset/call_kw/chatbot.discuss.service/open_assistant_chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: { model: 'chatbot.discuss.service', method: 'open_assistant_chat', args: [], kwargs: {} } }) }); return (await r.json()).result.url; });
  await page.goto(BASE + chatUrl); await page.waitForSelector('.o-mail-Composer-input'); await page.waitForTimeout(1500);
}
async function ask(page, text, add = 2) {
  const before = await page.locator('.o-mail-Message').count();
  await page.fill('.o-mail-Composer-input', text); await page.keyboard.press('Enter');
  await page.waitForFunction(([n, k]) => document.querySelectorAll('.o-mail-Message').length >= n + k, [before, add], { timeout: 60000 });
  await page.waitForTimeout(1500);
  console.log('>>', text, '\n', (await page.locator('.o-mail-Message').last().innerText()).slice(0, 500), '\n');
}
async function settle(page) { await page.goto(BASE + chatUrl); await page.waitForSelector('.o-mail-Message'); await page.waitForTimeout(3500); }
async function shotChat(page, path) { await settle(page); await page.locator('.o-mail-Discuss-content, .o-mail-Discuss').first().screenshot({ path }); }
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1366, height: 860 }, deviceScaleFactor: 2 });
  const p = await ctx.newPage();
  await login(p, 'admin', 'admin'); await openAssistant(p);
  await ask(p, 'Hola');
  await ask(p, '¿Está pagada la factura INV/2026/00001?');
  await ask(p, '¿Cuánto stock hay de la Cadena transmisión 520?');
  await settle(p); await p.screenshot({ path: 'c1_conversacion.png' });
  await ask(p, '/help', 1); await shotChat(p, 'c2_help.png');
  await ask(p, 'Stock y facturación de la Cadena transmisión 520 este mes');
  await ask(p, '¿Y las ventas de este producto?');
  await ask(p, 'Ventas de la empresa Andina');
  await ask(p, 'Crea una factura para Comercial Andina S.A.');
  await shotChat(p, 'c3_memoria.png');
  await ask(p, 'facturas de Motopartes Ecuador');
  await shotChat(p, 'c4_extenso.png');
  const href = await p.locator('.o-mail-Message').last().locator('a', { hasText: 'Ver todo' }).getAttribute('href');
  console.log('href', href);
  await p.goto(href.startsWith('http') ? href : BASE + href); await p.waitForSelector('.o_list_view, .o_list_renderer'); await p.waitForTimeout(2500); await p.evaluate(() => document.querySelectorAll('.o-mail-ChatWindow, .o-mail-ChatHub').forEach(e => e.remove()));
  await p.screenshot({ path: 'c5_ver_todo.png' });
  await ask2();
  async function ask2() {}
  // Ajustes, permisos, auditoría, métricas
  await p.goto(BASE + '/odoo/action-chatbot_assistant.action_chatbot_config_settings'); await p.waitForSelector('div[name=chatbot_provider]'); await p.waitForTimeout(2500);
  await p.evaluate(() => document.querySelectorAll('.o-mail-ChatWindow, .o-mail-ChatHub').forEach(e => e.remove()));
  await p.screenshot({ path: 'c6_ajustes.png' });
  await p.getByText('Modelo de respaldo', { exact: false }).first().scrollIntoViewIfNeeded();
  await p.evaluate(() => { const el = [...document.querySelectorAll('h2, .o_setting_container h2, div')].find(e => e.textContent.trim().startsWith('Modelo de respaldo') && e.children.length < 3); if (el) el.scrollIntoView({ block: 'start' }); });
  await p.waitForTimeout(1000);
  await p.evaluate(() => document.querySelectorAll('.o-mail-ChatWindow, .o-mail-ChatHub').forEach(e => e.remove()));
  await p.screenshot({ path: 'c6b_respaldo.png' });
  for (const [a, f, sel] of [['action_chatbot_intent_permission', 'c7_permisos.png', '.o_list_renderer'], ['action_chatbot_query_log', 'c8_auditoria.png', '.o_list_renderer'], ['action_chatbot_query_log_metrics', 'c9_metricas.png', '.o_action']]) {
    await p.goto(BASE + '/odoo/action-chatbot_assistant.' + a); await p.waitForSelector(sel); await p.waitForTimeout(3000); await p.evaluate(() => document.querySelectorAll('.o-mail-ChatWindow, .o-mail-ChatHub').forEach(e => e.remove())); await p.screenshot({ path: f });
  }
  // Usuario vendedor sin grupo de Facturación
  const c2 = await b.newContext({ viewport: { width: 1366, height: 860 }, deviceScaleFactor: 2 });
  const q = await c2.newPage();
  await login(q, 'diego.salinas@demo-motos.ec', 'demo'); await openAssistant(q);
  await ask(q, '¿Está pagada la factura INV/2026/00001?');
  await ask(q, '¿Quién es el vendedor de Comercial Andina S.A.?');
  await shotChat(q, 'c10_permiso.png');
  await b.close();
})();
