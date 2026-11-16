/**
 * Prueba e2e de resultados extensos en el chat (vista previa, «Ver todo» y CSV).
 * Requiere Odoo con la base generada por chatbot_test_data y el módulo chatbot_fake_llm cargado
 * (--load=base,web,chatbot_fake_llm). Uso: BASE=http://localhost:8070 SHOTS=carpeta node resultados_extensos.e2e.js
 */
const { chromium } = require('playwright');
const fs = require('fs');

const BASE = process.env.BASE || 'http://localhost:8070';
const SHOTS = process.env.SHOTS || '.';
let ok = 0, fail = 0;
const check = (cond, label) => { cond ? ok++ : fail++; console.log(`${cond ? 'OK   ' : 'FALLA'} ${label}`); };

async function login(page, user, password) {
  await page.goto(`${BASE}/web/login`);
  await page.fill('#login', user);
  await page.fill('#password', password);
  await page.click('button[type=submit]');
  await page.waitForURL(/\/odoo/);
}

async function openAssistant(page) {
  const url = await page.evaluate(async () => {
    const res = await fetch('/web/dataset/call_kw/chatbot.discuss.service/open_assistant_chat', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: {
        model: 'chatbot.discuss.service', method: 'open_assistant_chat', args: [], kwargs: {} } }),
    });
    return (await res.json()).result.url;
  });
  await page.goto(BASE + url);
  await page.waitForSelector('.o-mail-Composer-input');
}

async function ask(page, text) {
  const before = await page.locator('.o-mail-Message').count();
  await page.fill('.o-mail-Composer-input', text);
  await page.keyboard.press('Enter');
  await page.waitForFunction((n) => document.querySelectorAll('.o-mail-Message').length >= n + 2, before, { timeout: 30000 });
  await page.waitForTimeout(800);
  return page.locator('.o-mail-Message').last();
}

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, acceptDownloads: true });
  const page = await context.newPage();
  await login(page, 'admin', 'admin');
  await openAssistant(page);

  // R1: facturas de un cliente con 12 facturas → vista previa de 5, «Ver todo (12)» y CSV.
  let msg = await ask(page, 'facturas de Motopartes Ecuador');
  let text = await msg.innerText();
  check(/Facturas de "Motopartes Ecuador S\.A\.": 12/.test(text), 'R1 resumen con total de facturas');
  check((text.match(/^- /gm) || []).length === 5, 'R1 el chat muestra solo 5 facturas');
  check(text.includes('Mostrando 5 de 12 facturas'), 'R1 indica que muestra 5 de 12');
  check(await msg.locator('a', { hasText: 'Ver todo (12)' }).count() === 1, 'R1 enlace «Ver todo (12)»');
  check(await msg.locator('a', { hasText: 'Descargar CSV' }).count() === 1, 'R1 enlace «Descargar CSV»');
  await page.screenshot({ path: `${SHOTS}/r1_chat_facturas.png` });

  // R2: descarga del CSV.
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    msg.locator('a', { hasText: 'Descargar CSV' }).click(),
  ]);
  const csvPath = `${SHOTS}/r2_facturas.csv`;
  await download.saveAs(csvPath);
  const csv = fs.readFileSync(csvPath, 'utf8').replace(/^﻿/, '').trim().split('\n');
  check(download.suggestedFilename().endsWith('.csv'), `R2 archivo ${download.suggestedFilename()}`);
  check(csv[0].startsWith('Factura,Cliente,Fecha,Vencimiento,Total,Saldo pendiente,Estado de pago'), 'R2 encabezados autorizados');
  check(csv.length === 13, `R2 CSV con 12 filas (tiene ${csv.length - 1})`);

  // R3: «Ver todo» abre la lista nativa con los 12 registros.
  await msg.locator('a', { hasText: 'Ver todo (12)' }).click();
  await page.waitForSelector('.o_list_view', { timeout: 15000 });
  await page.waitForTimeout(800);
  const rows = await page.locator('.o_list_view tbody tr.o_data_row').count();
  const title = await page.locator('.o_breadcrumb').innerText();
  check(rows === 12, `R3 la lista muestra 12 facturas (muestra ${rows})`);
  check(title.includes('Facturas de Motopartes Ecuador S.A.'), 'R3 título de la lista');
  await page.screenshot({ path: `${SHOTS}/r3_ver_todo_facturas.png` });

  // R4: ventas por producto con muchas líneas (lista).
  await openAssistant(page);
  msg = await ask(page, 'lista las ventas del FIL-M01');
  text = await msg.innerText();
  check(/Mostrando 5 de 38 líneas de pedido/.test(text), 'R4 vista previa de 5 de 38 líneas');
  check(await msg.locator('a', { hasText: 'Ver todo (38)' }).count() === 1, 'R4 enlace «Ver todo (38)»');
  await page.screenshot({ path: `${SHOTS}/r4_chat_ventas_producto.png` });
  await msg.locator('a', { hasText: 'Ver todo (38)' }).click();
  await page.waitForSelector('.o_list_view', { timeout: 15000 });
  await page.waitForTimeout(800);
  const pager = await page.locator('.o_pager_counter').innerText().catch(() => '');
  check(/38/.test(pager), `R4 la lista de líneas de pedido tiene 38 registros (${pager.trim()})`);

  // R5: resumen de ventas por cliente (sin listar) también ofrece «Ver todo».
  await openAssistant(page);
  msg = await ask(page, 'ventas de Jessica');
  text = await msg.innerText();
  check(/19 pedido\(s\) confirmado\(s\)/.test(text), 'R5 resumen de 19 pedidos');
  check(await msg.locator('a', { hasText: 'Ver todo (19)' }).count() === 1, 'R5 enlace «Ver todo (19)»');

  // R6: resultado corto → sin enlaces.
  msg = await ask(page, 'facturas de Comercial Andina');
  check(await msg.locator('a', { hasText: 'Ver todo' }).count() === 0, 'R6 5 facturas o menos: sin «Ver todo»');
  check(await msg.locator('a', { hasText: 'Descargar CSV' }).count() === 0, 'R6 sin CSV');

  // R7: stock y facturación → «Ver todo» con las facturas del producto.
  msg = await ask(page, 'stock y facturación del FIL-M01');
  check(await msg.locator('a', { hasText: /Ver todo \(\d+\)/ }).count() === 1, 'R7 enlace a las facturas del producto');
  await page.screenshot({ path: `${SHOTS}/r7_chat_stock_facturacion.png` });

  // R8: otro usuario no puede descargar el CSV ni abrir el resultado de la consulta de admin.
  const href = await page.locator('a', { hasText: 'Descargar CSV' }).first().getAttribute('href');
  const other = await browser.newContext();
  const page2 = await other.newPage();
  await login(page2, 'otro.e2e', 'otro.e2e12345');
  const res = await page2.request.get(BASE + href);
  check(res.status() === 404, `R8 otro usuario recibe 404 al descargar (${res.status()})`);
  const openHref = await page.locator('a', { hasText: /Ver todo/ }).first().getAttribute('href');
  await page2.goto(BASE + openHref);
  await page2.waitForTimeout(3000);
  check(await page2.locator('.o_list_view tbody tr.o_data_row').count() === 0, 'R8 otro usuario no ve los registros');
  check(await page2.getByText('pertenece a la consulta de otro usuario').count() === 1, 'R8 mensaje claro al otro usuario');
  await page2.screenshot({ path: `${SHOTS}/r8_otro_usuario.png` });

  // R9: un usuario normal (sin ser administrador del chatbot) abre «Ver todo» y descarga su CSV.
  await openAssistant(page2);
  msg = await ask(page2, 'facturas de Motopartes Ecuador');
  await msg.locator('a', { hasText: 'Ver todo (12)' }).click();
  await page2.waitForSelector('.o_list_view', { timeout: 15000 });
  await page2.waitForTimeout(800);
  check(await page2.locator('.o_list_view tbody tr.o_data_row').count() === 12, 'R9 usuario normal ve sus 12 facturas');
  await page2.goBack();
  await page2.waitForSelector('.o-mail-Message');
  const ownCsv = await page2.locator('a', { hasText: 'Descargar CSV' }).last().getAttribute('href');
  const ownRes = await page2.request.get(BASE + ownCsv);
  check(ownRes.status() === 200, `R9 usuario normal descarga su CSV (${ownRes.status()})`);

  await browser.close();
  console.log(`\n${ok} OK / ${fail} FALLA`);
  process.exit(fail ? 1 : 0);
})();
