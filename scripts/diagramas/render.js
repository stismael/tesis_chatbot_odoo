// Renderiza cada .mmd de SRC a SVG y PNG (alta resolución) en OUT, con Mermaid y Chromium.
const { chromium } = require('playwright');
const fs = require('fs'); const path = require('path');
const [SRC, OUT] = process.argv.slice(2);
const MERMAID = require.resolve('mermaid/dist/mermaid.min.js');
(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: 3, viewport: { width: 3000, height: 3000 } });
  await page.setContent('<html><body style="margin:0;background:#fff"><div id="c"></div></body></html>');
  await page.addScriptTag({ path: MERMAID });
  await page.evaluate(() => mermaid.initialize({
    startOnLoad: false, theme: 'neutral', securityLevel: 'loose',
    fontFamily: 'Arial, Helvetica, sans-serif', fontSize: 15,
    flowchart: { useMaxWidth: false, htmlLabels: true, curve: 'basis', padding: 12, nodeSpacing: 40, rankSpacing: 55 },
    sequence: { useMaxWidth: false, mirrorActors: false, actorMargin: 25, width: 130, wrap: true, messageFontSize: 14, noteFontSize: 13 },
    er: { useMaxWidth: false, fontSize: 14 }, class: { useMaxWidth: false, htmlLabels: true },
  }));
  for (const f of fs.readdirSync(SRC).filter((x) => x.endsWith('.mmd')).sort()) {
    const code = fs.readFileSync(path.join(SRC, f), 'utf8');
    const name = f.replace('.mmd', '');
    try {
      const svg = await page.evaluate(async ([id, c]) => (await mermaid.render(id, c)).svg, ['g' + name.replace(/\W/g, ''), code]);
      fs.writeFileSync(path.join(OUT, name + '.svg'), svg);
      await page.evaluate((s) => { document.getElementById('c').innerHTML = s; }, svg);
      const el = page.locator('#c svg');
      const box = await el.boundingBox();
      await el.screenshot({ path: path.join(OUT, name + '.png'), omitBackground: false });
      console.log('OK', name, Math.round(box.width) + 'x' + Math.round(box.height));
    } catch (e) { console.log('ERROR', name, String(e).slice(0, 300)); }
  }
  await browser.close();
})();
