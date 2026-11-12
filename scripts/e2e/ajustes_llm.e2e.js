/**
 * Prueba de extremo a extremo de Ajustes del chatbot (Odoo 18 + Chromium con Playwright).
 *
 * Recorre los flujos que tuvieron defectos: probar conexión y actualizar modelos sin guardar,
 * descartar, volver al proveedor original sin pegar la clave, desactivar, clave de otro proveedor
 * y modelo guardado distinto del recomendado. Comprueba el formulario y la configuración guardada.
 *
 * Requisitos (no forma parte de GitHub Actions):
 *   - Postgres en el contenedor "tdb" y Odoo en "odooweb" (puerto 8069, base "web1", admin/admin)
 *     con chatbot_assistant instalado y el módulo de pruebas fake_llm cargado como módulo de
 *     servidor: --addons-path=...,scripts/e2e/fake_llm --load=base,web,chatbot_fake_llm
 *     (simula Gemini y Groq: no se llama a ningún proveedor real).
 *   - node con playwright:  node scripts/e2e/ajustes_llm.e2e.js
 */
const { chromium } = require('playwright');
const { execSync } = require('child_process');
const DIR = __dirname;
const URL = 'http://localhost:8069/odoo/action-chatbot_assistant.action_chatbot_config_settings';
const icp = k => execSync(`docker exec tdb psql -U odoo -d web1 -tAc "select value from ir_config_parameter where key='chatbot_assistant.${k}'"`).toString().trim();
const reset = () => { execSync(`${DIR}/reset_config.sh`); execSync('docker restart odooweb'); for (let i = 0; i < 60; i++) { try { if (execSync('curl -s -o /dev/null -w "%{http_code}" http://localhost:8069/web/login').toString() === '200') return; } catch (e) {} execSync('sleep 2'); } };
let fallos = 0;
const ok = (cond, msg) => { console.log((cond ? '  OK   ' : '  FALLA ') + msg); if (!cond) fallos++; };

async function abrir(p) {
  await p.goto(URL); await p.waitForSelector('div[name=chatbot_provider] select'); await p.waitForTimeout(800);
}
const proveedor = p => p.locator('div[name=chatbot_provider] select').inputValue();
const elegirProveedor = async (p, v) => { await p.selectOption('div[name=chatbot_provider] select', `"${v}"`); await p.waitForTimeout(700); };
const clave = p => p.locator('div[name=chatbot_api_key] input').inputValue();
const modelo = p => p.locator('div[name=chatbot_llm_model_id] input').inputValue();
async function boton(p, name) { await p.click(`button[name=${name}]`); await p.waitForTimeout(1500); }
async function guardar(p) { await p.click('.o_form_button_save'); await p.waitForTimeout(3000); await p.waitForSelector('div[name=chatbot_provider] select'); }

(async () => {
  const b = await chromium.launch();
  const login = async () => {
    const p = await b.newPage({ viewport: { width: 1400, height: 1000 } });
    await p.goto('http://localhost:8069/web/login');
    await p.fill('input[name=login]', 'admin'); await p.fill('input[name=password]', 'admin');
    await p.click('button[type=submit]'); await p.waitForURL(/odoo/); return p;
  };

  console.log('E1. Probar conexión con Groq: el formulario no vuelve a Gemini y el chat no cambia');
  reset(); let p = await login(); await abrir(p);
  await elegirProveedor(p, 'groq');
  ok(await clave(p) === '', 'al cambiar de proveedor la API Key queda vacía');
  await p.fill('div[name=chatbot_api_key] input', 'gsk_NUEVA');
  await boton(p, 'action_chatbot_test_connection');
  ok(await p.locator('.o_notification:has-text("Conexión exitosa")').count() > 0, 'aparece la notificación de conexión exitosa');
  ok(await proveedor(p) === '"groq"', 'el formulario sigue en Groq (antes volvía a Gemini)');
  ok(await clave(p) === 'gsk_NUEVA', 'la API Key escrita se conserva');
  ok((await modelo(p)).includes('llama-3.3-70b-versatile'), 'el modelo sigue siendo el de Groq');
  ok((await p.locator('div[name=chatbot_last_verified]').innerText()).includes('llama-3.3-70b-versatile'), 'el formulario muestra la verificación');
  ok(icp('provider') === 'gemini' && icp('api_key') === 'AIzaCLAVE-GEMINI', 'el chat sigue con Gemini y su clave (no se guardó nada)');

  console.log('E2. Descartar después de probar: no se pierde la clave de Gemini');
  await p.click('.o_form_button_cancel'); await p.waitForTimeout(1500);
  ok(await proveedor(p) === '"gemini"', 'al descartar, Ajustes vuelve a lo guardado (Gemini)');
  ok(icp('provider') === 'gemini' && icp('api_key') === 'AIzaCLAVE-GEMINI', 'la clave de Gemini sigue guardada');

  console.log('E3. Actualizar modelos, elegir uno y Guardar');
  await abrir(p); await elegirProveedor(p, 'groq');
  await p.fill('div[name=chatbot_api_key] input', 'gsk_NUEVA');
  await boton(p, 'action_chatbot_sync_models');
  ok(await p.locator('.o_notification:has-text("Catálogo de modelos actualizado")').count() > 0, 'aparece la notificación del catálogo');
  ok(await proveedor(p) === '"groq"' && await clave(p) === 'gsk_NUEVA', 'el formulario conserva Groq y la clave');
  ok(icp('provider') === 'gemini', 'actualizar modelos no cambia la configuración del chat');
  await p.click('div[name=chatbot_llm_model_id] input'); await p.fill('div[name=chatbot_llm_model_id] input', 'qwen');
  await p.waitForTimeout(1200);
  const opcion = p.locator('.o-autocomplete--dropdown-item:has-text("qwen/qwen3-32b")');
  ok(await opcion.count() > 0, 'el desplegable ofrece el modelo nuevo de Groq');
  ok(await p.locator('.o-autocomplete--dropdown-item:has-text("gemini")').count() === 0, 'el desplegable no ofrece modelos de Gemini');
  await opcion.first().click(); await p.waitForTimeout(700);
  await guardar(p);
  ok(icp('provider') === 'groq' && icp('api_key') === 'gsk_NUEVA' && icp('model') === 'qwen/qwen3-32b', 'al Guardar se aplica Groq, su clave y el modelo elegido');
  ok(icp('last_verified').includes('qwen/qwen3-32b'), 'se registra la verificación del modelo guardado');
  await abrir(p);
  ok(await proveedor(p) === '"groq"' && (await modelo(p)).includes('qwen'), 'al volver a Ajustes se ve lo guardado');

  console.log('E4. Ir a Groq y volver a Gemini sin pegar la clave, cambiar la temperatura y Guardar');
  reset(); await p.close(); p = await login(); await abrir(p);
  await elegirProveedor(p, 'groq'); await elegirProveedor(p, 'gemini');
  await p.fill('div[name=chatbot_temperature] input', '0.2');
  await guardar(p);
  ok(icp('api_key') === 'AIzaCLAVE-GEMINI', 'la API Key guardada no se borra (defecto corregido en el PR #10)');
  ok(icp('provider') === 'gemini', 'el proveedor sigue siendo Gemini');

  console.log('E5. Desactivar el asistente');
  await abrir(p); await p.click('div[name=chatbot_active] input'); await guardar(p);
  ok(icp('active') === 'False', 'queda desactivado');
  await abrir(p);
  ok(!(await p.locator('div[name=chatbot_active] input').isChecked()), 'al volver a Ajustes se ve desactivado');

  console.log('E6. Clave de Gemini con proveedor Groq al probar');
  reset(); await p.close(); p = await login(); await abrir(p);
  await elegirProveedor(p, 'groq'); await p.fill('div[name=chatbot_api_key] input', 'AIzaOTRA');
  await boton(p, 'action_chatbot_test_connection');
  ok(await p.locator('.modal:has-text("parece de Google Gemini")').count() > 0, 'muestra el aviso de clave de otro proveedor');
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  ok(await proveedor(p) === '"groq"' && await clave(p) === 'AIzaOTRA', 'el formulario conserva lo escrito tras el error');
  ok(icp('provider') === 'gemini' && icp('api_key') === 'AIzaCLAVE-GEMINI', 'la configuración del chat no cambia');
  await p.click('.o_form_button_cancel'); await p.waitForTimeout(1500);
  ok(await proveedor(p) === '"gemini"', 'después del error, Descartar recarga normalmente (no queda el reemplazo de un solo uso)');

  console.log('E7. Modelo guardado distinto del recomendado: abrir Ajustes y guardar otro dato');
  reset(); await p.close(); p = await login(); await abrir(p);
  await boton(p, 'action_chatbot_sync_models');
  await p.click('div[name=chatbot_llm_model_id] input'); await p.fill('div[name=chatbot_llm_model_id] input', 'gemini-2.5-pro');
  await p.waitForTimeout(1200); await p.locator('.o-autocomplete--dropdown-item:has-text("gemini-2.5-pro")').first().click();
  await p.waitForTimeout(700); await guardar(p);
  ok(icp('model') === 'gemini-2.5-pro', 'se guarda gemini-2.5-pro');
  await abrir(p);
  ok((await modelo(p)).includes('gemini-2.5-pro'), 'al abrir Ajustes se ve el modelo guardado (antes mostraba el recomendado)');
  ok(await clave(p) === 'AIzaCLAVE-GEMINI', 'al abrir Ajustes la API Key no aparece vacía');
  await p.fill('div[name=chatbot_temperature] input', '0.3'); await guardar(p);
  ok(icp('model') === 'gemini-2.5-pro', 'guardar la temperatura no reemplaza el modelo por el recomendado');
  ok(icp('api_key') === 'AIzaCLAVE-GEMINI', 'ni borra la clave');

  await b.close();
  console.log(fallos ? `\n${fallos} comprobación(es) fallaron` : '\nTodas las comprobaciones pasaron');
  process.exit(fallos ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
