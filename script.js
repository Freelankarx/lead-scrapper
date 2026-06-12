// ============================================
//  FreelancerX Lead Scraper — script.js
// ============================================

// ─── CONFIG ────────────────────────────────
const DEFAULT_API = localStorage.getItem('freelankarx_api') || '';
let API_BASE = DEFAULT_API;
let allLeads = [];
let scrapeAbort = null;
let isScraping = false;

// ─── INIT ────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  spawnParticles();
  animateCounters();
  syncSlider();
  loadApiUrl();
  checkApiStatus();
  initExportOptions();

  // Sync range slider <-> number input
  document.getElementById('leadLimit').addEventListener('input', (e) => {
    document.getElementById('leadLimitNum').value = e.target.value;
  });
  document.getElementById('leadLimitNum').addEventListener('input', (e) => {
    let v = Math.min(1000, Math.max(10, parseInt(e.target.value) || 10));
    document.getElementById('leadLimit').value = v;
    e.target.value = v;
  });
});

// ─── PARTICLES ──────────────────────────
function spawnParticles() {
  const container = document.getElementById('particles');
  for (let i = 0; i < 25; i++) {
    const p = document.createElement('div');
    p.className = 'particle';
    p.style.left = Math.random() * 100 + '%';
    p.style.width = p.style.height = (Math.random() * 2 + 1) + 'px';
    p.style.animationDuration = (Math.random() * 15 + 8) + 's';
    p.style.animationDelay = (Math.random() * 10) + 's';
    p.style.opacity = Math.random() * 0.4;
    container.appendChild(p);
  }
}

// ─── COUNTER ANIMATION ──────────────────
function animateCounters() {
  document.querySelectorAll('.stat-num[data-target]').forEach(el => {
    const target = parseInt(el.dataset.target);
    const step = target / 60;
    let current = 0;
    const timer = setInterval(() => {
      current = Math.min(current + step, target);
      el.textContent = Math.floor(current).toLocaleString();
      if (current >= target) clearInterval(timer);
    }, 30);
  });
}

// ─── SLIDER SYNC ────────────────────────
function syncSlider() {
  const slider = document.getElementById('leadLimit');
  const num = document.getElementById('leadLimitNum');
  const updateSliderTrack = () => {
    const pct = ((slider.value - slider.min) / (slider.max - slider.min)) * 100;
    slider.style.background = `linear-gradient(to right, #D4AF37 ${pct}%, #0a1628 ${pct}%)`;
  };
  slider.addEventListener('input', updateSliderTrack);
  updateSliderTrack();
}

// ─── NICHE SHORTCUTS ────────────────────
function setNiche(val) {
  document.getElementById('nicheInput').value = val;
  document.getElementById('nicheInput').focus();
}

// ─── EXPORT OPTIONS ─────────────────────
function initExportOptions() {
  document.querySelectorAll('.export-option').forEach(opt => {
    opt.addEventListener('click', () => {
      document.querySelectorAll('.export-option').forEach(o => o.classList.remove('selected'));
      opt.classList.add('selected');
    });
  });
}

// ─── API URL ────────────────────────────
function loadApiUrl() {
  const saved = localStorage.getItem('freelankarx_api') || '';
  document.getElementById('apiUrlInput').value = saved;
  API_BASE = saved;
}

function saveApiUrl(val) {
  API_BASE = val.trim().replace(/\/$/, '');
  localStorage.setItem('freelankarx_api', API_BASE);
}

// ─── TEST CONNECTION ─────────────────────
async function testConnection() {
  const url = document.getElementById('apiUrlInput').value.trim().replace(/\/$/, '');
  if (!url) { showToast('Enter your backend URL first', 'warn'); return; }
  API_BASE = url;
  saveApiUrl(url);
  setStatus('connecting');

  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(8000) });
    const data = await res.json();
    if (data.status === 'ok') {
      setStatus('online');
      showToast('✓ Backend connected!', 'success');
    } else { throw new Error('Bad response'); }
  } catch {
    setStatus('offline');
    showToast('Backend not reachable. Check URL or wait for Render spin-up (~30s)', 'error');
  }
}

// ─── STATUS INDICATOR ───────────────────
function setStatus(state) {
  const dot = document.getElementById('statusDot');
  const text = document.getElementById('statusText');
  dot.className = 'status-dot';
  if (state === 'online') { dot.classList.add('online'); text.textContent = 'Online'; }
  else if (state === 'offline') { dot.classList.add('offline'); text.textContent = 'Offline'; }
  else { text.textContent = 'Connecting...'; }
}

async function checkApiStatus() {
  if (!API_BASE) { setStatus('offline'); return; }
  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(5000) });
    const data = await res.json();
    setStatus(data.status === 'ok' ? 'online' : 'offline');
  } catch { setStatus('offline'); }
}

// ─── PROGRESS HELPERS ───────────────────
function setProgress(pct, found, statusText) {
  const circle = document.getElementById('progressCircle');
  const circumference = 408;
  const offset = circumference - (pct / 100) * circumference;
  circle.style.strokeDashoffset = offset;
  document.getElementById('progressPct').textContent = Math.round(pct) + '%';
  document.getElementById('progressFound').textContent = found + ' found';
  document.getElementById('progressStatus').textContent = statusText;
}

function activateStep(stepNum) {
  for (let i = 1; i <= 6; i++) {
    const el = document.getElementById(`step${i}`);
    if (i < stepNum) { el.className = 'p-step done'; el.querySelector('.step-dot').style.background = 'var(--success)'; }
    else if (i === stepNum) { el.className = 'p-step active'; }
    else { el.className = 'p-step'; }
  }
}

function addFeedItem(text, type = 'info') {
  const feed = document.getElementById('feedItems');
  const empty = feed.querySelector('.feed-empty');
  if (empty) empty.remove();

  const item = document.createElement('div');
  item.className = `feed-item ${type}`;
  item.textContent = text;
  feed.appendChild(item);
  feed.scrollTop = feed.scrollHeight;

  // Keep last 40 items
  while (feed.children.length > 40) feed.removeChild(feed.firstChild);
}

// ─── MAIN SCRAPE LAUNCHER ────────────────
async function startScrape() {
  if (isScraping) {
    stopScrape();
    return;
  }

  const niche = document.getElementById('nicheInput').value.trim();
  if (!niche) { showToast('Enter a niche/keyword first!', 'warn'); document.getElementById('nicheInput').focus(); return; }

  if (!API_BASE) {
    showToast('No backend URL set. Enter it in the Docs section below.', 'error');
    document.getElementById('docs').scrollIntoView({ behavior: 'smooth' });
    return;
  }

  const country = document.getElementById('countrySelect').value;
  const location = document.getElementById('locationInput').value.trim();
  const limit = parseInt(document.getElementById('leadLimitNum').value) || 100;
  const filterEmail = document.getElementById('filterEmail').checked;
  const filterWebsite = document.getElementById('filterWebsite').checked;
  const filterPhone = document.getElementById('filterPhone').checked;
  const filterSocial = document.getElementById('filterSocial').checked;
  const exportFormat = document.querySelector('input[name="exportFormat"]:checked')?.value || 'csv';

  isScraping = true;
  allLeads = [];
  clearTable();

  const btn = document.getElementById('launchBtn');
  btn.innerHTML = `<span class="launch-btn-inner"><svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect x="5" y="5" width="10" height="10" rx="2" fill="currentColor"/></svg> Stop Scraping</span><div class="btn-shimmer"></div>`;

  document.getElementById('pulseRing').classList.add('active');
  document.getElementById('feedItems').innerHTML = '';
  setProgress(0, 0, 'Launching...');
  activateStep(1);
  addFeedItem('Scraper initialized', 'info');
  addFeedItem(`Niche: "${niche}" | Country: ${country || 'Any'}`, 'info');
  addFeedItem(`Target: ${limit} leads`, 'info');

  try {
    // Use EventSource for streaming progress, or polling
    await runScrapeWithPolling({
      niche, country, location, limit,
      filter_email: filterEmail,
      filter_website: filterWebsite,
      filter_phone: filterPhone,
      include_social: filterSocial,
      export_format: exportFormat
    });
  } catch (err) {
    if (err.name !== 'AbortError') {
      addFeedItem('Error: ' + err.message, 'warn');
      showToast('Scrape failed: ' + err.message, 'error');
    }
  } finally {
    finishScrape();
  }
}

async function runScrapeWithPolling(params) {
  addFeedItem('Connecting to backend...', 'info');
  activateStep(2);

  // Start job
  const startRes = await fetch(`${API_BASE}/scrape/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
    signal: AbortSignal.timeout(15000)
  });

  if (!startRes.ok) {
    const err = await startRes.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${startRes.status}`);
  }

  const { job_id } = await startRes.json();
  addFeedItem(`Job started: ${job_id}`, 'info');

  // Poll for status
  let done = false;
  let lastCount = 0;

  while (!done && isScraping) {
    await sleep(1500);

    const pollRes = await fetch(`${API_BASE}/scrape/status/${job_id}`, {
      signal: AbortSignal.timeout(10000)
    });

    if (!pollRes.ok) continue;
    const status = await pollRes.json();

    // Update progress
    const pct = status.progress || 0;
    const found = status.found || 0;
    setProgress(pct, found, status.step_label || 'Scraping...');

    if (status.step) activateStep(status.step);

    // Log new leads to feed
    if (status.recent_leads && status.recent_leads.length > lastCount) {
      for (let i = lastCount; i < status.recent_leads.length; i++) {
        const lead = status.recent_leads[i];
        addFeedItem(`✓ ${lead.business_name || 'Unknown'} — ${lead.email || lead.phone || '(no contact)'}`, 'success');
      }
      lastCount = status.recent_leads.length;
    }

    if (status.status === 'done' || status.status === 'error') {
      done = true;
      if (status.leads) {
        allLeads = status.leads;
        renderLeads(allLeads);
      }
      if (status.download_url) {
        handleAutoDownload(`${API_BASE}${status.download_url}`, params.niche, params.export_format);
      }
    }
  }
}

function stopScrape() {
  isScraping = false;
  finishScrape();
  addFeedItem('Scrape stopped by user', 'warn');
}

function finishScrape() {
  isScraping = false;
  const btn = document.getElementById('launchBtn');
  btn.innerHTML = `<span class="launch-btn-inner"><svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M10 2L18 10L10 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M2 10H18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg> Launch Scraper</span><div class="btn-shimmer"></div>`;
  document.getElementById('pulseRing').classList.remove('active');

  if (allLeads.length > 0) {
    setProgress(100, allLeads.length, `Complete — ${allLeads.length} leads`);
    activateStep(7);
    document.getElementById('downloadBtn').disabled = false;
    document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
    showToast(`✓ ${allLeads.length} leads extracted!`, 'success');
  }
}

// ─── RENDER LEADS TABLE ─────────────────
function renderLeads(leads) {
  const tbody = document.getElementById('leadsBody');
  tbody.innerHTML = '';

  const valid = leads.filter(l => l.email).length;
  document.getElementById('totalFound').textContent = `${leads.length} leads found`;
  document.getElementById('validEmails').textContent = `${valid} valid emails`;

  if (!leads.length) {
    tbody.innerHTML = '<tr class="empty-row"><td colspan="9"><div class="empty-state"><div class="empty-icon">😕</div><p>No leads matched your filters. Try a broader niche or country.</p></div></td></tr>';
    return;
  }

  leads.forEach((lead, i) => {
    const score = calcScore(lead);
    const scoreClass = score >= 80 ? 'high' : score >= 50 ? 'mid' : 'low';

    const socials = [];
    if (lead.facebook) socials.push(`<a href="${lead.facebook}" target="_blank" class="social-link" title="Facebook">f</a>`);
    if (lead.instagram) socials.push(`<a href="${lead.instagram}" target="_blank" class="social-link" title="Instagram">ig</a>`);
    if (lead.linkedin) socials.push(`<a href="${lead.linkedin}" target="_blank" class="social-link" title="LinkedIn">in</a>`);
    if (lead.twitter) socials.push(`<a href="${lead.twitter}" target="_blank" class="social-link" title="Twitter">tw</a>`);

    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${i + 1}</td>
      <td title="${lead.business_name || ''}">${truncate(lead.business_name, 28)}</td>
      <td class="lead-email">${lead.email ? `<a href="mailto:${lead.email}" style="color:inherit;text-decoration:none">${truncate(lead.email, 28)}</a>` : '<span style="color:var(--text-muted)">—</span>'}</td>
      <td class="lead-phone">${lead.phone || '<span style="color:var(--text-muted)">—</span>'}</td>
      <td class="lead-website">${lead.website ? `<a href="${lead.website}" target="_blank">${truncate(lead.website.replace(/https?:\/\//,''), 22)}</a>` : '<span style="color:var(--text-muted)">—</span>'}</td>
      <td>${lead.city || '<span style="color:var(--text-muted)">—</span>'}</td>
      <td>${lead.country || '<span style="color:var(--text-muted)">—</span>'}</td>
      <td><div class="social-links">${socials.join('') || '<span style="color:var(--text-muted);font-size:0.75rem">—</span>'}</div></td>
      <td><span class="lead-score score-${scoreClass}">${score}</span></td>
    `;
    tbody.appendChild(row);
  });
}

function calcScore(lead) {
  let score = 0;
  if (lead.business_name) score += 15;
  if (lead.email) score += 30;
  if (lead.phone) score += 20;
  if (lead.website) score += 15;
  if (lead.city || lead.address) score += 10;
  if (lead.facebook || lead.instagram || lead.linkedin || lead.twitter) score += 10;
  return score;
}

function truncate(str, n) {
  if (!str) return '';
  return str.length > n ? str.slice(0, n) + '…' : str;
}

function filterTable(query) {
  const q = query.toLowerCase();
  document.querySelectorAll('#leadsBody tr').forEach(row => {
    row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
}

function clearTable() {
  document.getElementById('leadsBody').innerHTML = '<tr class="empty-row"><td colspan="9"><div class="empty-state"><div class="empty-icon">🎯</div><p>No leads yet. Configure your search above and launch.</p></div></td></tr>';
  document.getElementById('totalFound').textContent = '0 leads found';
  document.getElementById('validEmails').textContent = '0 valid emails';
  document.getElementById('downloadBtn').disabled = true;
  allLeads = [];
}

function clearResults() {
  clearTable();
  setProgress(0, 0, 'Ready to Launch');
  activateStep(0);
  document.getElementById('feedItems').innerHTML = '<div class="feed-empty">Waiting for scrape to start...</div>';
}

// ─── DOWNLOAD ───────────────────────────
async function downloadResults() {
  if (!allLeads.length) return;

  const format = document.querySelector('input[name="exportFormat"]:checked')?.value || 'csv';

  if (format === 'csv' || format === 'all') {
    downloadCSV(allLeads);
  }
  if (format === 'xlsx' || format === 'all') {
    // Request xlsx from backend if available
    if (API_BASE) {
      try {
        const res = await fetch(`${API_BASE}/export/xlsx`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ leads: allLeads })
        });
        if (res.ok) {
          const blob = await res.blob();
          triggerDownload(blob, `freelankarx_leads_${Date.now()}.xlsx`);
          return;
        }
      } catch {}
    }
    downloadCSV(allLeads); // fallback
  }
  if (format === 'docx' || format === 'all') {
    if (API_BASE) {
      try {
        const res = await fetch(`${API_BASE}/export/docx`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ leads: allLeads })
        });
        if (res.ok) {
          const blob = await res.blob();
          triggerDownload(blob, `freelankarx_leads_${Date.now()}.docx`);
        }
      } catch {}
    }
  }
}

function downloadCSV(leads) {
  const headers = ['Business Name','Owner','Email','Phone','Website','Address','City','State','Country','Facebook','Instagram','LinkedIn','Twitter','Score'];
  const rows = leads.map(l => [
    l.business_name, l.owner_name, l.email, l.phone, l.website,
    l.address, l.city, l.state, l.country,
    l.facebook, l.instagram, l.linkedin, l.twitter, calcScore(l)
  ].map(v => `"${(v||'').toString().replace(/"/g,'""')}"`));

  const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  triggerDownload(blob, `freelankarx_leads_${Date.now()}.csv`);
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function handleAutoDownload(url, niche, format) {
  const a = document.createElement('a');
  a.href = url;
  a.download = `freelankarx_${niche.replace(/\s+/g,'_')}_${Date.now()}.${format}`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

// ─── TOAST ──────────────────────────────
function showToast(msg, type = 'info') {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = msg;
  toast.style.cssText = `
    position:fixed; bottom:2rem; right:2rem; z-index:9999;
    background:${type==='success'?'rgba(34,211,160,0.15)':type==='error'?'rgba(240,90,90,0.15)':'rgba(212,175,55,0.15)'};
    border:1px solid ${type==='success'?'var(--success)':type==='error'?'var(--error)':'var(--gold-dim)'};
    color:${type==='success'?'var(--success)':type==='error'?'var(--error)':'var(--gold)'};
    padding:0.85rem 1.5rem; border-radius:10px;
    font-size:0.88rem; font-family:var(--font-mono);
    backdrop-filter:blur(10px);
    animation:slideUp 0.3s ease;
    max-width:360px;
  `;
  document.body.appendChild(toast);

  const style = document.createElement('style');
  style.textContent = `@keyframes slideUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}`;
  document.head.appendChild(style);

  setTimeout(() => { toast.style.opacity = '0'; toast.style.transition = 'opacity 0.3s'; setTimeout(()=>toast.remove(),300); }, 4000);
}

// ─── UTIL ────────────────────────────────
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
