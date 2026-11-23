// Start the server first (new empty DB):  APP_DB=/tmp/ui.db python -m uvicorn app.server:app --port 8766
// then:  npm install  &&  node ui_test.js
const {JSDOM, VirtualConsole} = require('jsdom');
const fs = require('fs');
const base = 'http://127.0.0.1:8766';
let cookie = '';
async function cfetch(url, opts = {}) {
  const headers = {...(opts.headers || {})};
  if (cookie) headers.cookie = cookie;
  const r = await fetch(new URL(url, base), {method: opts.method || 'GET', headers, body: opts.body});
  for (const c of (r.headers.getSetCookie ? r.headers.getSetCookie() : [])) {
    cookie = /max-age=0/i.test(c) ? '' : c.split(';')[0];
  }
  return r;
}
const errors = [];
const vc = new VirtualConsole();
vc.on('jsdomError', (e) => { if (!/not implemented/i.test(e.message)) errors.push('jsdom: ' + e.message); });
vc.on('error', (e) => errors.push('console.error: ' + e));
const html = fs.readFileSync(require('path').join(__dirname, '..', 'app', 'static', 'index.html') + '', 'utf8');
const dom = new JSDOM(html, {url: base + '/', runScripts: 'dangerously', resources: 'usable', pretendToBeVisual: true, virtualConsole: vc,
  beforeParse(w) { w.fetch = cfetch; w.scrollTo = () => {}; w.confirm = () => true; }});
const w = dom.window, d = w.document;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function until(fn, what, ms = 6000) {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) { try { const v = fn(); if (v) return v; } catch (e) {} await sleep(50); }
  throw new Error('TIMEOUT waiting for: ' + what + '\nVIEW: ' + d.querySelector('#view').textContent.slice(0, 300));
}
const $ = (s) => d.querySelector(s);
const set = (sel, v) => { const el = $(sel); el.value = v; el.dispatchEvent(new w.Event('input', {bubbles: true})); el.dispatchEvent(new w.Event('change', {bubbles: true})); };
const submit = (sel) => $(sel).dispatchEvent(new w.Event('submit', {cancelable: true, bubbles: true}));
const ok = (m) => console.log('PASS  ' + m);
(async () => {
  await until(() => $('.tabs'), 'login screen'); ok('login screen shown when logged out');
  d.querySelector('[data-t=register]').click();
  await until(() => $('input[name=full_name]'), 'register form');
  set('input[name=full_name]', 'Priya Test'); set('input[name=age]', '52'); set('select[name=sex]', 'F');
  set('select[name=lang]', 'en'); set('input[name=password]', 'secret-pass-1'); set('input[name=password2]', 'secret-pass-1');
  submit('#f');
  const id = (await until(() => $('.idbox') && $('.idbox').textContent.startsWith('PT') && $('.idbox').textContent, 'patient id')).trim();
  ok('registered, got Patient ID ' + id);
  $('#go').click();
  await until(() => /Hello, Priya/.test($('#view').textContent), 'home'); ok('home dashboard after registration');

  w.location.hash = '#doctors';
  await until(() => d.querySelector('[data-pick]'), 'doctor list');
  d.querySelector('[data-pick]').click();
  await until(() => $('.badge') && /My doctor/.test($('.badge').textContent), 'doctor selected'); ok('doctor selected');

  w.location.hash = '#book';
  await until(() => $('#day'), 'book screen');
  const pad = (n) => String(n).padStart(2, '0');
  for (let i = 1; i <= 3; i++) {
    const dt = new Date(Date.now() + i * 86400000);
    if (dt.getDay() !== 0) { set('#day', `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())}`); break; }
  }
  await until(() => d.querySelector('#slots button'), 'slots');
  d.querySelector('#slots button').click();
  $('#confirm').click();
  await until(() => w.location.hash === '#appointments' && d.querySelector('[data-cancel]'), 'appointment listed'); ok('appointment booked and listed');

  w.location.hash = '#check';
  await until(() => d.querySelector('[data-m=manual]'), 'check screen');
  d.querySelector('[data-m=manual]').click();
  await until(() => $('input[name=LYVE1]'), 'manual form');
  const vals = {age: 68, creatinine: 0.4, LYVE1: 8, REG1B: 150, TFF1: 1500, plasma_CA19_9: 400, REG1A: 900};
  for (const [k, v] of Object.entries(vals)) set(`input[name=${k}]`, v);
  set('select[name=sex]', 'M'); $('#ok').checked = true;
  submit('#f');
  await until(() => w.location.hash.startsWith('#result/') && $('.ring span'), 'result screen');
  const pct = $('.ring span').textContent;
  if (!/Higher risk/.test($('#view').textContent)) throw new Error('unexpected band: ' + $('#view').textContent.slice(0, 200));
  ok('result shown: ' + pct + ', Higher risk signal, expectation + factors present: ' + (/What to expect next/.test($('#view').textContent) && /increasing the estimated risk/.test($('#view').textContent)));
  set('#lang', 'hi');
  await until(() => /अधिक जोखिम/.test($('#view').textContent), 'hindi result'); ok('result switched to Hindi');

  w.location.hash = '#profile';
  await until(() => $('#out'), 'profile'); $('#out').click();
  await until(() => $('.tabs') && !$('#nav').hidden === false, 'logged out'); ok('logout returns to login screen, nav hidden');

  // log back in with the Patient ID
  set('input[name=patient_code]', id.toLowerCase()); set('input[name=password]', 'secret-pass-1'); submit('#f');
  await until(() => /Hello, Priya/.test($('#view').textContent), 'login again'); ok('login with Patient ID + password works');
  w.location.hash = '#results';
  await until(() => /Higher risk/.test($('#view').textContent), 'results history'); ok('result history saved');
  if (errors.length) { console.log('ERRORS:', errors); process.exit(1); }
  console.log('ALL UI CHECKS PASSED'); process.exit(0);
})().catch((e) => { console.log('FAIL ', e.message); if (errors.length) console.log(errors); process.exit(1); });
