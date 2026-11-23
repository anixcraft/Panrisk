'use strict';
// PancRISK+ Care: patient app (research prototype). All text from users is escaped before display.
const APP_NAME = 'PancRISK+ Care';
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const LANGS = {en: 'English', hi: 'हिन्दी', mr: 'मराठी'};
const DISCLAIMER = 'Research prototype only. This is NOT a medical diagnosis. Please consult a doctor for any health concern.';
let me = null;
let draft = {values: {}, reportId: null, notes: [], filename: null};

function toast(msg, err) {
  const t = $('#toast');
  t.textContent = msg;
  t.className = 'show' + (err ? ' err' : '');
  clearTimeout(toast.t);
  toast.t = setTimeout(() => (t.className = ''), 3500);
}

function errText(d, status) {
  if (!d) return 'Something went wrong (' + status + ').';
  if (typeof d.detail === 'string') return d.detail;
  if (Array.isArray(d.detail)) {
    return d.detail.map((x) => (x.loc || []).slice(-1)[0] + ': ' + x.msg).join('; ');
  }
  return 'Something went wrong (' + status + ').';
}

async function api(path, opts = {}) {
  const init = {credentials: 'same-origin', ...opts};
  if (opts.body && !(opts.body instanceof FormData)) {
    init.headers = {'Content-Type': 'application/json', ...(opts.headers || {})};
    if (typeof opts.body !== 'string') init.body = JSON.stringify(opts.body);
  }
  const r = await fetch('/api' + path, init);
  let d = null;
  try { d = await r.json(); } catch (e) { /* no body */ }
  if (!r.ok) {
    const err = new Error(errText(d, r.status));
    err.status = r.status;
    throw err;
  }
  return d;
}

const fmtSlot = (s) => {
  const [d, t] = s.split(' ');
  const dt = new Date(d + 'T' + t + ':00');
  return dt.toLocaleDateString(undefined, {weekday: 'short', day: 'numeric', month: 'short'}) + ', ' + t;
};
const fmtDate = (s) => new Date(s.replace(' ', 'T') + 'Z').toLocaleDateString(undefined, {day: 'numeric', month: 'short', year: 'numeric'});
const chip = (band, label) => `<span class="chip ${esc(band)}">${esc(label)}</span>`;
const view = (html) => { $('#view').innerHTML = html; window.scrollTo(0, 0); };
const formObj = (form) => Object.fromEntries(new FormData(form).entries());

// ---------- auth ----------
function viewAuth(tab = 'login', newId = null) {
  $('#nav').hidden = true;
  if (newId) {
    view(`<div class="card center"><h2>Welcome 🎉</h2>
      <p>Your Patient ID is</p><div class="idbox">${esc(newId)}</div>
      <p class="muted">Write it down. You need this ID and your password to log in. We cannot recover it for you in this prototype.</p>
      <button class="btn" id="go">Continue</button></div>`);
    $('#go').onclick = () => { location.hash = '#home'; route(); };
    return;
  }
  view(`<div class="banner">${esc(DISCLAIMER)} Please do not enter real patient data in this prototype.</div>
    <div class="tabs"><button data-t="login" class="${tab === 'login' ? 'on' : ''}">Log in</button>
    <button data-t="register" class="${tab === 'register' ? 'on' : ''}">New patient</button></div>
    <div class="card">${tab === 'login' ? `
      <form id="f" autocomplete="on">
        <label>Patient ID</label><input name="patient_code" placeholder="e.g. PT123456" autocapitalize="characters" required>
        <label>Password</label><input name="password" type="password" autocomplete="current-password" required>
        <button class="btn">Log in</button></form>` : `
      <form id="f" autocomplete="off">
        <label>Full name</label><input name="full_name" required minlength="2" maxlength="80">
        <div class="row"><div><label>Age</label><input name="age" type="number" min="18" max="110" required></div>
        <div><label>Sex</label><select name="sex"><option value="F">Female</option><option value="M">Male</option></select></div></div>
        <label>Phone (optional)</label><input name="phone" type="tel" maxlength="20">
        <label>Preferred language for results</label>
        <select name="lang">${Object.entries(LANGS).map(([k, v]) => `<option value="${k}">${v}</option>`).join('')}</select>
        <label>Password (8+ characters)</label><input name="password" type="password" minlength="8" autocomplete="new-password" required>
        <label>Confirm password</label><input name="password2" type="password" minlength="8" autocomplete="new-password" required>
        <p class="muted">This app is for adults (18+).</p>
        <button class="btn">Create my account</button></form>`}</div>`);
  document.querySelectorAll('.tabs button').forEach((b) => (b.onclick = () => viewAuth(b.dataset.t)));
  $('#f').onsubmit = async (e) => {
    e.preventDefault();
    const d = formObj(e.target);
    const btn = e.target.querySelector('button');
    btn.disabled = true;
    try {
      if (tab === 'login') {
        await api('/login', {method: 'POST', body: d});
        me = await api('/me');
        location.hash = '#home';
        route();
      } else {
        if (d.password !== d.password2) throw new Error('Passwords do not match.');
        delete d.password2;
        d.age = Number(d.age);
        const r = await api('/register', {method: 'POST', body: d});
        me = await api('/me');
        viewAuth('login', r.patient_code);
      }
    } catch (err) { toast(err.message, true); btn.disabled = false; }
  };
}

// ---------- home ----------
async function viewHome() {
  const [appts, results] = await Promise.all([api('/appointments'), api('/results')]);
  const next = appts.find((a) => a.upcoming);
  const last = results[0];
  view(`<h2>Hello, ${esc(me.full_name.split(' ')[0])} 👋</h2>
    <div class="banner">${esc(DISCLAIMER)}</div>
    <div class="card"><h3>Your doctor</h3>${me.doctor
      ? `<p><b>${esc(me.doctor.name)}</b><br><span class="muted">${esc(me.doctor.specialty)}</span></p>`
      : `<p class="muted">You have not chosen a doctor yet.</p><a class="btn small" href="#doctors">Choose a doctor</a>`}</div>
    <div class="card"><h3>Next appointment</h3>${next
      ? `<p><b>${esc(fmtSlot(next.slot))}</b><br>${esc(next.doctor)} · <span class="muted">${esc(next.specialty)}</span></p>`
      : `<p class="muted">No upcoming appointments.</p>`}
      <a class="btn small" href="#book">Book a visit</a></div>
    <div class="card"><h3>Latest result</h3>${last
      ? `<p>${chip(last.band, last.band_label)} <span class="muted">${esc(fmtDate(last.created_at))}</span></p>
         <a class="btn small sec" href="#result/${last.id}">View details</a>`
      : `<p class="muted">No results yet.</p>`}
      <a class="btn small" href="#check">Check a report</a></div>`);
}

// ---------- doctors ----------
async function viewDoctors() {
  const docs = await api('/doctors');
  view(`<h2>Doctors</h2><p class="muted">Demo profiles (fictional). Choose your doctor to see them on your home screen.</p>` +
    docs.map((d) => `<div class="card"><h3>${esc(d.name)} ${me.doctor && me.doctor.id === d.id ? '<span class="badge">My doctor</span>' : ''}</h3>
      <p><b>${esc(d.specialty)}</b><br><span class="muted">${esc(d.languages)}</span></p><p class="muted">${esc(d.bio)}</p>
      <button class="btn small ${me.doctor && me.doctor.id === d.id ? 'sec' : ''}" data-pick="${d.id}">${me.doctor && me.doctor.id === d.id ? 'Selected ✓' : 'Select as my doctor'}</button>
      <a class="btn small sec" href="#book/${d.id}">Book</a></div>`).join(''));
  document.querySelectorAll('[data-pick]').forEach((b) => (b.onclick = async () => {
    try { me = await api('/me', {method: 'PATCH', body: {doctor_id: Number(b.dataset.pick)}}); toast('Doctor selected'); viewDoctors(); }
    catch (e) { toast(e.message, true); }
  }));
}

// ---------- appointments ----------
async function viewAppts() {
  const all = await api('/appointments');
  const up = all.filter((a) => a.upcoming);
  const past = all.filter((a) => !a.upcoming).reverse();
  const row = (a, cancel) => `<div class="card"><h3>${esc(fmtSlot(a.slot))}</h3><p>${esc(a.doctor)} · <span class="muted">${esc(a.specialty)}</span></p>
    ${a.reason ? `<p class="muted">Reason: ${esc(a.reason)}</p>` : ''}
    ${a.status === 'cancelled' ? '<span class="chip inconclusive">Cancelled</span>' : ''}
    ${cancel ? `<button class="btn small danger" data-cancel="${a.id}">Cancel</button>` : ''}</div>`;
  view(`<h2>My appointments</h2><a class="btn" href="#book">+ Book a new appointment</a>
    <h3 style="margin-top:18px">Upcoming</h3>${up.length ? up.map((a) => row(a, true)).join('') : '<p class="muted">Nothing booked.</p>'}
    ${past.length ? '<h3 style="margin-top:18px">Past and cancelled</h3>' + past.map((a) => row(a, false)).join('') : ''}`);
  document.querySelectorAll('[data-cancel]').forEach((b) => (b.onclick = async () => {
    if (!confirm('Cancel this appointment?')) return;
    try { await api('/appointments/' + b.dataset.cancel, {method: 'DELETE'}); toast('Appointment cancelled'); viewAppts(); }
    catch (e) { toast(e.message, true); }
  }));
}

async function viewBook(docId) {
  const docs = await api('/doctors');
  const pre = Number(docId) || (me.doctor && me.doctor.id) || docs[0].id;
  const today = new Date();
  const iso = (d) => new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
  const max = new Date(today.getTime() + 14 * 86400000);
  view(`<h2>Book an appointment</h2><div class="card">
    <label>Doctor</label><select id="doc">${docs.map((d) => `<option value="${d.id}" ${d.id === pre ? 'selected' : ''}>${esc(d.name)}, ${esc(d.specialty)}</option>`).join('')}</select>
    <label>Date</label><input id="day" type="date" min="${iso(today)}" max="${iso(max)}" value="${iso(today)}">
    <label>Available times</label><div id="slots" class="slots"></div>
    <label>Reason (optional)</label><input id="reason" maxlength="200" placeholder="e.g. discuss my report">
    <button class="btn" id="confirm" disabled>Confirm appointment</button></div>`);
  let chosen = null;
  const load = async () => {
    chosen = null; $('#confirm').disabled = true;
    const box = $('#slots'); box.innerHTML = '<span class="muted">Loading…</span>';
    try {
      const r = await api(`/slots?doctor_id=${$('#doc').value}&day=${$('#day').value}`);
      box.innerHTML = r.slots.length ? r.slots.map((s) => `<button data-s="${s}">${s.slice(11)}</button>`).join('') : '<span class="muted">No free times that day (Sundays are closed).</span>';
      box.querySelectorAll('button').forEach((b) => (b.onclick = () => {
        box.querySelectorAll('button').forEach((x) => x.classList.remove('on'));
        b.classList.add('on'); chosen = b.dataset.s; $('#confirm').disabled = false;
      }));
    } catch (e) { box.innerHTML = ''; toast(e.message, true); }
  };
  $('#doc').onchange = load; $('#day').onchange = load; load();
  $('#confirm').onclick = async () => {
    try {
      await api('/appointments', {method: 'POST', body: {doctor_id: Number($('#doc').value), slot: chosen, reason: $('#reason').value}});
      toast('Appointment booked ✓'); location.hash = '#appointments';
    } catch (e) { toast(e.message, true); load(); }
  };
}

// ---------- results ----------
async function viewResults() {
  const rs = await api('/results');
  view(`<h2>My results</h2><a class="btn" href="#check">+ Check a new report</a>
    <div class="list" style="margin-top:14px">${rs.length ? rs.map((r) => `<div class="card"><a class="item" href="#result/${r.id}">
      <span>${chip(r.band, r.band_label)}<br><span class="muted">${esc(fmtDate(r.created_at))}</span></span><b>${Math.round(r.probability * 100)}% ›</b></a></div>`).join('')
      : '<p class="muted">No results yet. Upload a report to get your first estimate.</p>'}</div>`);
}

const FIELDS = [
  ['age', 'Age (years)', '1', 18, 110, true], ['creatinine', 'Urine creatinine (mg/ml)', '0.01', 0, 20, true],
  ['LYVE1', 'LYVE1 (ng/ml)', '0.01', 0, 1000, true], ['REG1B', 'REG1B (ng/ml)', '0.01', 0, 5000, true],
  ['TFF1', 'TFF1 (ng/ml)', '0.01', 0, 5000, true], ['plasma_CA19_9', 'Plasma CA19-9 (U/ml), optional', '0.01', 0, 100000, false],
  ['REG1A', 'REG1A (ng/ml), optional', '0.01', 0, 5000, false]];

function checkForm() {
  const v = draft.values;
  const sex = v.sex || me.sex;
  const age = v.age || me.age;
  return `<form id="f">${FIELDS.map(([k, label, step, min, max, req]) => `<label>${esc(label)}</label>
    <input name="${k}" type="number" step="${step}" min="${min}" max="${max}" ${req ? 'required' : ''}
    value="${esc(k === 'age' ? age : (v[k] ?? ''))}">`).join('')}
    <label>Sex</label><select name="sex"><option value="F" ${sex === 'F' ? 'selected' : ''}>Female</option><option value="M" ${sex === 'M' ? 'selected' : ''}>Male</option></select>
    <label style="display:flex;gap:8px;align-items:flex-start;font-weight:400"><input type="checkbox" id="ok" style="width:auto;margin-top:4px" required>
    <span>I understand this is a research prototype estimate and not a medical diagnosis.</span></label>
    <button class="btn">Get my estimate</button></form>`;
}

function viewCheck(mode = 'upload') {
  view(`<h2>Check a report</h2>
    <div class="info">This model was trained on a <b>urinary biomarker panel</b> (creatinine, LYVE1, REG1B, TFF1, optionally CA19-9 and REG1A).
    Routine blood or urine reports usually do <b>not</b> contain LYVE1, REG1B or TFF1. If yours does not, an estimate is not possible.</div>
    <div class="tabs"><button data-m="upload" class="${mode === 'upload' ? 'on' : ''}">Upload report</button>
    <button data-m="manual" class="${mode === 'manual' ? 'on' : ''}">Enter values</button></div>
    <div class="card">${mode === 'upload' ? `<label>Report file (PDF, CSV or TXT, max 5 MB)</label>
      <input id="file" type="file" accept=".pdf,.csv,.txt,application/pdf,text/csv,text/plain">
      <p class="muted">Scanned photos are not supported yet. Text-based PDFs only.</p>
      <div id="notes"></div><div id="formbox"></div>` : checkForm()}</div>`);
  document.querySelectorAll('.tabs button').forEach((b) => (b.onclick = () => { draft = {values: {}, reportId: null, notes: []}; viewCheck(b.dataset.m); }));
  const submit = async (e) => {
    e.preventDefault();
    const d = formObj(e.target);
    const body = {sex: d.sex, report_id: draft.reportId};
    for (const [k, , , , , req] of FIELDS) {
      if (d[k] !== '' && d[k] !== undefined) body[k] = Number(d[k]); else if (req) { toast('Please fill all required values.', true); return; }
    }
    const btn = e.target.querySelector('button'); btn.disabled = true;
    try { const r = await api('/results', {method: 'POST', body}); draft = {values: {}, reportId: null, notes: []}; location.hash = '#result/' + r.id; }
    catch (err) { toast(err.message, true); btn.disabled = false; }
  };
  if (mode === 'manual') { $('#f').onsubmit = submit; return; }
  $('#file').onchange = async (e) => {
    const f = e.target.files[0]; if (!f) return;
    const fd = new FormData(); fd.append('file', f);
    $('#notes').innerHTML = '<p class="muted">Reading your report…</p>';
    try {
      const r = await api('/reports/extract', {method: 'POST', body: fd});
      draft = {values: r.values, reportId: r.report_id, notes: r.notes, filename: r.filename};
      const found = Object.keys(r.values).length;
      $('#notes').innerHTML = `<div class="info">Report: <b>${esc(r.filename)}</b>. ${found ? 'We found the values below. <b>Please check every one against your report, including units.</b>' : ''}
        ${r.notes.map((n) => `<br>${esc(n)}`).join('')}</div>`;
      $('#formbox').innerHTML = checkForm();
      $('#f').onsubmit = submit;
    } catch (err) { $('#notes').innerHTML = ''; toast(err.message, true); }
  };
}

async function viewResult(id, lang) {
  const r = await api(`/results/${id}` + (lang ? '?lang=' + lang : ''));
  const col = {high: 'var(--red)', inconclusive: 'var(--amber)', low: 'var(--green)'}[r.band];
  const pct = Math.round(r.probability * 100);
  view(`<a href="#results" class="muted">‹ All results</a><h2>Your result</h2>
    <div class="banner">${esc(r.disclaimer)}</div>
    <div class="card center"><div class="ring" style="--p:${pct};--c:${col}"><span>${pct}%</span></div>
      <p>${chip(r.band, r.band_label)}</p><p class="muted">Estimated risk score · ${esc(fmtDate(r.created_at))}</p></div>
    <div class="card"><h3>What this means</h3><p>${esc(r.guidance)}</p></div>
    <div class="card"><h3>What to expect next</h3><p>${esc(r.expectation)}</p>
      ${r.band !== 'low' ? '<a class="btn small" href="#book">Book an appointment</a>' : ''}</div>
    <div class="card"><h3>What influenced this result</h3>${r.factors.map((f) => `<p>• ${esc(f.sentence)}</p>`).join('')}
      ${r.warnings.map((w) => `<p class="muted">⚠ ${esc(w)}</p>`).join('')}</div>
    <div class="card"><label>Language</label><select id="lang">${Object.entries(LANGS).map(([k, v]) => `<option value="${k}" ${k === r.lang ? 'selected' : ''}>${v}</option>`).join('')}</select>
      <button class="btn sec" onclick="window.print()">Print / save as PDF</button></div>`);
  $('#lang').onchange = (e) => viewResult(id, e.target.value);
}

// ---------- profile ----------
function viewProfile() {
  view(`<h2>Profile</h2><div class="card"><p><b>${esc(me.full_name)}</b></p>
    <p class="muted">Patient ID: <b>${esc(me.patient_code)}</b><br>Age ${esc(me.age)} · ${me.sex === 'F' ? 'Female' : 'Male'}${me.phone ? '<br>Phone: ' + esc(me.phone) : ''}</p></div>
    <div class="card"><label>Preferred language for results</label>
    <select id="lang">${Object.entries(LANGS).map(([k, v]) => `<option value="${k}" ${k === me.lang ? 'selected' : ''}>${v}</option>`).join('')}</select></div>
    <div class="card"><h3>About</h3><p class="muted">${esc(DISCLAIMER)} Hindi and Marathi text is a draft awaiting native-speaker review. No real patient data should be used.</p></div>
    <button class="btn danger" id="out">Log out</button>`);
  $('#lang').onchange = async (e) => { me = await api('/me', {method: 'PATCH', body: {lang: e.target.value}}); toast('Language saved'); };
  $('#out').onclick = async () => { await api('/logout', {method: 'POST'}); me = null; location.hash = ''; route(); };
}

// ---------- router ----------
const routes = {home: viewHome, doctors: viewDoctors, appointments: viewAppts, book: viewBook, results: viewResults, check: () => viewCheck(), result: viewResult, profile: viewProfile};

async function route() {
  if (!me) { viewAuth(); return; }
  const [name, arg] = (location.hash.slice(1) || 'home').split('/');
  const fn = routes[name] || viewHome;
  $('#nav').hidden = false;
  const active = ['book'].includes(name) ? 'appointments' : ['check', 'result'].includes(name) ? 'results' : name;
  document.querySelectorAll('#nav a').forEach((a) => a.classList.toggle('on', a.dataset.r === active));
  try { await fn(arg); }
  catch (e) {
    if (e.status === 401) { me = null; viewAuth(); toast('Please log in again.', true); } else toast(e.message, true);
  }
}

window.addEventListener('hashchange', route);
(async () => {
  try { me = await api('/me'); } catch (e) { me = null; }
  route();
  if ('serviceWorker' in navigator && (location.protocol === 'https:' || location.hostname === 'localhost')) {
    navigator.serviceWorker.register('/sw.js').catch(() => {});
  }
})();
