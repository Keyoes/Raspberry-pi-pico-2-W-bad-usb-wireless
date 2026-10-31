// Drives the real web page in a headless browser against mock_device.py.
//
//   python3 tests/ui/mock_device.py &
//   node tests/ui/ui_test.js
//
// Needs Playwright and a Chromium. Optional: the Python suite under tests/
// covers the firmware logic and needs neither. This one covers the page,
// and is worth having -- it is what caught the boot animation wiping
// command output and destroying .terminal-bg-effect.

const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  const errors = [];
  // A refused script name legitimately answers 4xx, and the browser logs
  // that as a console error. Only unexpected ones should fail the run.
  page.on('console', m => {
    if (m.type() !== 'error') return;
    if (/status of 4\d\d/.test(m.text())) return;
    errors.push(m.text());
  });
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));

  let failures = 0;
  const ok = (label, cond) => {
    if (!cond) failures++;
    console.log(`  ${cond ? 'PASS' : 'FAIL'}  ${label}`);
  };

  await page.goto('http://127.0.0.1:8111/', { waitUntil: 'networkidle' });
  console.log('=== pagina incarcata ===');
  ok('butonul CHECK exista',   await page.locator('button:text-is("CHECK")').count() === 1);
  ok('butonul DRY RUN exista', await page.locator('button:text-is("DRY RUN")').count() === 1);
  ok('randul de biblioteca exista', await page.locator('.library-row').count() === 1);

  const status = page.locator('#status');

  // --- CHECK pe un script cu bug-ul cunoscut ---
  await page.fill('#script', 'STRING hi\nCTRL ALT DELETE\nBOGUS_CMD\nDELAY abc');
  await page.click('button:text-is("CHECK")');
  await page.waitForFunction(() => document.getElementById('status').innerText.includes('problem'));
  let text = await status.innerText();
  console.log('=== CHECK ===');
  ok('raporteaza 3 probleme', text.includes('3 problem'));
  ok('prinde capcana cu spatii', text.includes('only CTRL is sent'));
  ok('sugereaza forma corecta', text.includes('CTRL+ALT+DELETE'));
  ok('prinde comanda necunoscuta', text.includes('BOGUS_CMD'));
  ok('prinde DELAY nenumeric', text.includes('not a number'));

  // --- escaparea HTML ---
  await page.fill('#script', 'STRING x\n<img src=x onerror="window.__xss=1">');
  await page.click('button:text-is("CHECK")');
  await page.waitForTimeout(400);
  ok('nu executa HTML din script', await page.evaluate(() => window.__xss === undefined));

  // --- DRY RUN ---
  await page.fill('#script', 'REM note\nSTRING hello\nDELAY 500\nCTRL+ALT+DELETE');
  await page.click('button:text-is("DRY RUN")');
  await page.waitForFunction(() => document.getElementById('status').innerText.includes('Would do'));
  text = await status.innerText();
  console.log('=== DRY RUN ===');
  ok('descrie tastarea',  text.includes("type 'hello'"));
  ok('descrie asteptarea', text.includes('wait 500 ms'));
  ok('descrie combinatia', text.includes('press CTRL'));

  // --- biblioteca ---
  console.log('=== BIBLIOTECA ===');
  await page.fill('#script', 'STRING saved payload\n');
  await page.fill('#script-name', 'demo-1');
  await page.click('button:text-is("SAVE")');
  await page.waitForFunction(() => document.getElementById('status').innerText.includes('Saved as'));
  await page.waitForTimeout(300);
  ok('apare in dropdown', (await page.locator('#script-list option').allTextContents()).includes('demo-1'));

  await page.click('button:text-is("LOAD")');
  await page.waitForFunction(() => document.getElementById('status').innerText.includes('active script'));
  ok('devine scriptul activ', (await status.innerText()).includes('demo-1'));

  // nume periculos refuzat, si eroarea ajunge la utilizator
  await page.fill('#script-name', '../boot.py');
  await page.click('button:text-is("SAVE")');
  await page.waitForFunction(() => document.getElementById('status').innerText.startsWith('Error'));
  ok('refuza ../boot.py cu mesaj clar', (await status.innerText()).includes('dot'));

  // nume gol
  await page.fill('#script-name', '   ');
  await page.click('button:text-is("DELETE")');
  await page.waitForTimeout(300);
  ok('cere un nume cand e gol', (await status.innerText()).includes('name it first') ||
                                (await status.innerText()).includes('Give the script a name'));

  await page.fill('#script-name', 'demo-1');
  await page.click('button:text-is("DELETE")');
  await page.waitForFunction(() => document.getElementById('status').innerText.includes('Deleted'));
  await page.waitForTimeout(300);
  ok('dispare din dropdown', !(await page.locator('#script-list option').allTextContents()).includes('demo-1'));


  console.log(`\n${failures} failure(s), ${errors.length} unexpected console error(s)`);
  errors.forEach(e => console.log('  ' + e));
  await browser.close();
  process.exit(failures || errors.length ? 1 : 0);
})();
