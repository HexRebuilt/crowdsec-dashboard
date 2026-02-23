const state = {
  status: {},
  config: {},
  decisions: [],
  alerts: [],
  appriseStatus: {},
  decisionsPage: 1,
  decisionsPerPage: 50,
  decisionsSearch: '',
  alertsSearch: '',
  currentPeriod: 'all',
  charts: {},
  auth: {
    enabled: false,
    method: null,
    authenticated: false,
    username: null,
    auth0Domain: null,
    auth0ClientId: null,
    auth0AuthorizeUrl: null,
    auth0TokenUrl: null,
    appUrl: null,
    passwordChangeAvailable: false
  }
};

function getTheme() {
  return localStorage.getItem('theme') || 'dark';
}

function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
  updateThemeIcons(theme);
}

function toggleTheme() {
  const current = getTheme();
  const next = current === 'dark' ? 'light' : 'dark';
  setTheme(next);
}

function updateThemeIcons(theme) {
  const sunIcons = document.querySelectorAll('.icon-sun');
  const moonIcons = document.querySelectorAll('.icon-moon');
  sunIcons.forEach(el => el.classList.toggle('hidden', theme === 'light'));
  moonIcons.forEach(el => el.classList.toggle('hidden', theme === 'dark'));
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    credentials: 'include',
    ...options
  });
  if (res.status === 401) {
    showLoginPage();
    throw new Error('Unauthorized');
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || `HTTP ${res.status}`);
  }
  return res.json();
}

function showToast(message, type = 'success') {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.className = `toast ${type}`;
  setTimeout(() => toast.classList.add('hidden'), 3000);
}

function timeAgo(isoString) {
  if (!isoString) return '—';
  const seconds = Math.floor((Date.now() - new Date(isoString).getTime()) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function showLoginPage() {
  document.getElementById('login-page').classList.remove('hidden');
  document.getElementById('app').classList.add('hidden');
  document.getElementById('login-error').classList.add('hidden');
  document.getElementById('username').value = '';
  document.getElementById('password').value = '';
  
  if (state.auth.method === 'auth0') {
    document.getElementById('login-form').classList.add('hidden');
    document.getElementById('sso-section').classList.remove('hidden');
  } else {
    document.getElementById('login-form').classList.remove('hidden');
    document.getElementById('username').focus();
  }
}

function showApp() {
  document.getElementById('login-page').classList.add('hidden');
  document.getElementById('app').classList.remove('hidden');
}

function setLoading(loading) {
  const btn = document.getElementById('login-btn');
  const text = btn.querySelector('.btn-text');
  const spinner = btn.querySelector('.btn-spinner');
  btn.disabled = loading;
  text.textContent = loading ? 'Signing in...' : 'Sign In';
  spinner.classList.toggle('hidden', !loading);
}

async function handleLogin(e) {
  e.preventDefault();
  const username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value;
  const errorEl = document.getElementById('login-error');
  
  if (!username || !password) {
    errorEl.textContent = 'Please enter username and password';
    errorEl.classList.remove('hidden');
    return;
  }
  
  setLoading(true);
  errorEl.classList.add('hidden');
  
  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ username, password })
    });
    
    const data = await res.json();
    
    if (!res.ok) {
      throw new Error(data.error || 'Login failed');
    }
    
    state.auth.authenticated = true;
    state.auth.username = data.username;
    showApp();
    document.getElementById('user-badge').textContent = data.username;
    await initApp();
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.classList.remove('hidden');
  } finally {
    setLoading(false);
  }
}

async function handleSSOLogin() {
  const clientId = state.auth.auth0ClientId;
  const authorizeUrl = state.auth.auth0AuthorizeUrl;
  
  if (!clientId) {
    showToast('SSO not configured', 'error');
    return;
  }
  
  const appUrl = state.auth.appUrl || window.location.origin;
  const redirectUri = encodeURIComponent(appUrl + '/callback');
  const stateParam = btoa(Math.random().toString());
  sessionStorage.setItem('auth0_state', stateParam);
  
  let authUrl;
  if (authorizeUrl) {
    authUrl = `${authorizeUrl}?` +
      `response_type=code&` +
      `client_id=${clientId}&` +
      `redirect_uri=${redirectUri}&` +
      `scope=openid%20profile%20email&` +
      `state=${stateParam}`;
  } else {
    const domain = state.auth.auth0Domain;
    authUrl = `https://${domain}/authorize?` +
      `response_type=code&` +
      `client_id=${clientId}&` +
      `redirect_uri=${redirectUri}&` +
      `scope=openid%20profile%20email&` +
      `state=${stateParam}`;
  }
  
  window.location.href = authUrl;
}

async function handleAuth0Callback(code) {
  const appUrl = state.auth.appUrl || window.location.origin;
  const redirectUri = appUrl + '/callback';
  
  if (code) {
    const urlParams = new URLSearchParams(window.location.search);
    const stateParam = urlParams.get('state');
    
    const savedState = sessionStorage.getItem('auth0_state');
    if (savedState && savedState !== stateParam) {
      showToast('Invalid state parameter', 'error');
      return false;
    }
    
    sessionStorage.removeItem('auth0_state');
    
    try {
      const res = await fetch('/api/auth/callback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ code: code, redirect_uri: redirectUri })
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.error || 'Login failed');
      }
      
      state.auth.authenticated = true;
      state.auth.username = data.username;
      window.history.replaceState({}, document.title, window.location.pathname);
      showApp();
      document.getElementById('user-badge').textContent = data.username;
      await initApp();
      return true;
    } catch (e) {
      showToast(e.message, 'error');
      return false;
    }
  }
  
  const hash = window.location.hash.substring(1);
  const params = new URLSearchParams(hash);
  const accessToken = params.get('access_token');
  const stateParam = params.get('state');
  
  if (!accessToken) return false;
  
  const savedState = sessionStorage.getItem('auth0_state');
  if (savedState && savedState !== stateParam) {
    showToast('Invalid state parameter', 'error');
    return false;
  }
  
  sessionStorage.removeItem('auth0_state');
  
  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ access_token: accessToken })
    });
    
    const data = await res.json();
    
    if (!res.ok) {
      throw new Error(data.error || 'Login failed');
    }
    
    state.auth.authenticated = true;
    state.auth.username = data.username;
    window.history.replaceState({}, document.title, window.location.pathname);
    showApp();
    document.getElementById('user-badge').textContent = data.username;
    await initApp();
    return true;
  } catch (e) {
    showToast(e.message, 'error');
    return false;
  }
}

async function handleLogout() {
  try {
    await fetch('/api/auth/logout', {
      method: 'POST',
      credentials: 'include'
    });
  } catch (e) {}
  state.auth.authenticated = false;
  state.auth.username = null;
  showLoginPage();
}

async function checkAuth() {
  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get('code');
  
  if (code) {
    const handled = await handleAuth0Callback(code);
    if (!handled) {
      window.location.href = '/';
    }
    return;
  }
  
  if (window.location.hash.includes('access_token')) {
    const handled = await handleAuth0Callback();
    if (!handled) {
      window.location.href = '/';
    }
    return;
  }
  
  try {
    const status = await fetch('/api/auth/status', { credentials: 'include' }).then(r => r.json());
    state.auth.enabled = status.enabled;
    state.auth.method = status.method;
    state.auth.auth0Domain = status.auth0_domain;
    state.auth.auth0ClientId = status.auth0_client_id;
    state.auth.auth0AuthorizeUrl = status.auth0_authorize_url;
    state.auth.auth0TokenUrl = status.auth0_token_url;
    state.auth.appUrl = status.app_url;
    state.auth.passwordChangeAvailable = status.password_change_available;
    
    if (status.method === 'auth0' || (status.auth0_domain && status.auth0_client_id)) {
      document.getElementById('sso-section').classList.remove('hidden');
    }
    
    updateAuthMethodSelect();
    
    if (!status.enabled) {
      showApp();
      await initApp();
      return;
    }
    
    try {
      const check = await api('/api/auth/check');
      state.auth.authenticated = true;
      state.auth.username = check.username;
      showApp();
      document.getElementById('user-badge').textContent = check.username;
      await initApp();
    } catch (e) {
      showLoginPage();
    }
  } catch (e) {
    showApp();
    await initApp();
  }
}

function updateAuthMethodSelect() {
  const content = document.getElementById('auth-method-content');
  
  if (!state.auth.enabled) {
    content.innerHTML = `
      <div class="status-line">
        <span class="status-label">Status</span>
        <span class="status-value">Disabled</span>
      </div>
      <p class="settings-note">Authentication is not configured. Set AUTH_USERNAME and AUTH_PASSWORD or AUTH0_* variables to enable.</p>
    `;
    return;
  }
  
  if (state.auth.method === 'auth0') {
    const domain = state.auth.auth0Domain || '';
    const displayDomain = domain.includes('://') ? domain : `https://${domain}`;
    content.innerHTML = `
      <div class="status-line">
        <span class="status-label">Current Method</span>
        <span class="status-value connected">SSO (OIDC)</span>
      </div>
      <div class="status-line">
        <span class="status-label">Provider</span>
        <span class="status-value code" style="word-break: break-all; font-size: 12px;">${displayDomain}</span>
      </div>
      <div class="status-line">
        <span class="status-label">Client ID</span>
        <span class="status-value code">${state.auth.auth0ClientId || '—'}</span>
      </div>
      <div class="status-line">
        <span class="status-label">App URL</span>
        <span class="status-value code">${state.auth.appUrl || window.location.origin}</span>
      </div>
    `;
  } else {
    content.innerHTML = `
      <div class="status-line">
        <span class="status-label">Current Method</span>
        <span class="status-value connected">Username / Password</span>
      </div>
      <div class="status-line">
        <span class="status-label">Username</span>
        <span class="status-value">${state.auth.username || '—'}</span>
      </div>
      <p class="settings-note">To switch to SSO, configure AUTH0_DOMAIN, AUTH0_CLIENT_ID, and AUTH0_CLIENT_SECRET environment variables.</p>
    `;
  }
}

async function loadStatus() {
  try {
    state.status = await api('/api/status');
    updateStatusUI();
  } catch (e) {
    console.error('Failed to load status:', e);
  }
}

async function loadConfig() {
  try {
    state.config = await api('/api/config');
    updateConfigUI();
  } catch (e) {
    console.error('Failed to load config:', e);
  }
}

async function loadDecisions() {
  try {
    const q = state.decisionsSearch;
    state.decisions = await api(`/api/decisions${q ? '?q=' + encodeURIComponent(q) : ''}`);
    updateDecisionsUI();
  } catch (e) {
    console.error('Failed to load decisions:', e);
  }
}

async function loadAlerts() {
  try {
    const q = state.alertsSearch;
    state.alerts = await api(`/api/alerts${q ? '?q=' + encodeURIComponent(q) : ''}`);
    updateAlertsUI();
  } catch (e) {
    console.error('Failed to load alerts:', e);
  }
}

async function loadAppriseStatus() {
  try {
    state.appriseStatus = await api('/api/apprise/status');
    updateAppriseUI();
  } catch (e) {
    console.error('Failed to load apprise status:', e);
  }
}

async function loadAppriseUrls() {
  try {
    const data = await api('/api/apprise/urls');
    document.getElementById('apprise-urls').value = data.urls || '';
  } catch (e) {
    console.error('Failed to load apprise urls:', e);
  }
}

async function loadAuthProviderSettings() {
  try {
    const data = await api('/api/auth/config');
    updateAuthSettingsUI(data);
  } catch (e) {
    console.error('Failed to load auth config:', e);
  }
}

function updateAuthSettingsUI(data) {
  const authContent = document.getElementById('auth-content');
  if (!state.auth.enabled) {
    document.getElementById('auth-settings').style.display = 'none';
    return;
  }
  document.getElementById('auth-settings').style.display = 'block';
  
  if (state.auth.method === 'credentials' && state.auth.passwordChangeAvailable) {
    authContent.innerHTML = `
      <div class="status-line">
        <span class="status-label">Logged in as</span>
        <span class="status-value">${state.auth.username}</span>
      </div>
      <div class="status-line">
        <span class="status-label">Username</span>
        <span class="status-value code">${data.credentials?.username || '—'}</span>
      </div>
      <button id="change-password-btn" class="btn btn-secondary" style="margin-top:12px">Change Password</button>
    `;
    document.getElementById('change-password-btn').addEventListener('click', openPasswordModal);
  } else if (state.auth.method === 'auth0') {
    authContent.innerHTML = `
      <div class="status-line">
        <span class="status-label">Logged in as</span>
        <span class="status-value">${state.auth.username}</span>
      </div>
      <p class="settings-note">Account managed by SSO provider.</p>
    `;
  } else {
    authContent.innerHTML = `
      <div class="status-line">
        <span class="status-label">Method</span>
        <span class="status-value">Username/Password</span>
      </div>
    `;
  }
}

function openPasswordModal() {
  document.getElementById('password-modal').classList.remove('hidden');
  document.getElementById('current-password').value = '';
  document.getElementById('new-password').value = '';
  document.getElementById('confirm-password').value = '';
  document.getElementById('password-error').classList.add('hidden');
}

function closePasswordModal() {
  document.getElementById('password-modal').classList.add('hidden');
}

async function handlePasswordChange(e) {
  e.preventDefault();
  const currentPassword = document.getElementById('current-password').value;
  const newPassword = document.getElementById('new-password').value;
  const confirmPassword = document.getElementById('confirm-password').value;
  const errorEl = document.getElementById('password-error');
  
  if (newPassword !== confirmPassword) {
    errorEl.textContent = 'Passwords do not match';
    errorEl.classList.remove('hidden');
    return;
  }
  
  if (newPassword.length < 8) {
    errorEl.textContent = 'Password must be at least 8 characters';
    errorEl.classList.remove('hidden');
    return;
  }
  
  try {
    await api('/api/auth/password', {
      method: 'POST',
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
    });
    showToast('Password changed successfully');
    closePasswordModal();
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.classList.remove('hidden');
  }
}

function updateStatusUI() {
  const s = state.status;
  const dot = document.querySelector('.status-dot');
  const text = document.querySelector('.status-text');
  
  dot.className = 'status-dot';
  if (s.poll_errors > 3) {
    dot.classList.add('error');
    text.textContent = 'Error';
  } else if (s.poll_errors > 0) {
    dot.classList.add('warning');
    text.textContent = 'Warning';
  } else {
    text.textContent = 'Online';
  }
  
  document.getElementById('decisions-count').textContent = s.total_bans || 0;
  document.getElementById('alerts-count').textContent = s.total_alerts || 0;
  
  document.getElementById('connection-status').innerHTML = `
    <div class="status-line">
      <span class="status-label">CrowdSec URL</span>
      <span class="status-value code">${s.crowdsec_url || '—'}</span>
    </div>
    <div class="status-line">
      <span class="status-label">Apprise Mode</span>
      <span class="status-value">${s.apprise_mode || '—'}</span>
    </div>
    <div class="status-line">
      <span class="status-label">Apprise Configured</span>
      <span class="status-value ${s.apprise_configured ? 'connected' : 'error'}">${s.apprise_configured ? 'Yes' : 'No'}</span>
    </div>
    <div class="status-line">
      <span class="status-label">Poll Interval</span>
      <span class="status-value">${s.poll_interval}s</span>
    </div>
  `;
  
  document.getElementById('stats-content').innerHTML = `
    <div class="status-line">
      <span class="status-label">Active Bans</span>
      <span class="status-value">${s.total_bans || 0}</span>
    </div>
    <div class="status-line">
      <span class="status-label">Alerts</span>
      <span class="status-value">${s.total_alerts || 0}</span>
    </div>
    <div class="status-line">
      <span class="status-label">Notifications Sent</span>
      <span class="status-value">${s.sent_count || 0}</span>
    </div>
    <div class="status-line">
      <span class="status-label">Suppressed</span>
      <span class="status-value">${s.suppressed_count || 0}</span>
    </div>
  `;
}

function updateConfigUI() {
  const c = state.config;
  document.getElementById('notify-ban').checked = c.notify_on_ban;
  document.getElementById('notify-alert').checked = c.notify_on_alert;
  document.getElementById('alert-threshold').value = c.alert_threshold;
  document.getElementById('ban-threshold').value = c.ban_threshold;
  document.getElementById('notify-cooldown').value = c.notify_cooldown;
}

function updateDecisionsUI() {
  const tbody = document.getElementById('decisions-body');
  const start = (state.decisionsPage - 1) * state.decisionsPerPage;
  const end = start + state.decisionsPerPage;
  const page = state.decisions.slice(start, end);
  
  if (page.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--text-muted);padding:40px">No active bans</td></tr>';
    document.getElementById('decisions-pagination').innerHTML = '';
    return;
  }
  
  tbody.innerHTML = page.map(d => `
    <tr>
      <td class="ip-cell">${d.ip || '—'}</td>
      <td><span class="type-${d.type || 'ban'}">${d.type || 'ban'}</span></td>
      <td>${d.scenario || '—'}</td>
      <td>${d.origin || '—'}</td>
      <td>${d.duration || '—'}</td>
      <td><button class="btn btn-danger btn-sm" onclick="deleteDecision('${d.ip}')">Delete</button></td>
    </tr>
  `).join('');
  
  updatePagination();
}

function updatePagination() {
  const total = state.decisions.length;
  const pages = Math.ceil(total / state.decisionsPerPage);
  const container = document.getElementById('decisions-pagination');
  
  if (pages <= 1) {
    container.innerHTML = '';
    return;
  }
  
  let html = '';
  for (let i = 1; i <= pages; i++) {
    html += `<button class="${i === state.decisionsPage ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
  }
  container.innerHTML = html;
}

function goToPage(page) {
  state.decisionsPage = page;
  updateDecisionsUI();
}

function updateAlertsUI() {
  const tbody = document.getElementById('alerts-body');
  
  if (state.alerts.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--text-muted);padding:40px">No alerts</td></tr>';
    return;
  }
  
  tbody.innerHTML = state.alerts.slice(0, 100).map(a => `
    <tr>
      <td class="ip-cell">${(a.source || {}).ip || '—'}</td>
      <td>${a.scenario || '—'}</td>
      <td>${a.events_count || 0}</td>
      <td>${(a.message || '').substring(0, 60)}${a.message && a.message.length > 60 ? '...' : ''}</td>
      <td>${timeAgo(a.created_at)}</td>
    </tr>
  `).join('');
}

function updateAppriseUI() {
  const s = state.appriseStatus;
  document.getElementById('apprise-status').innerHTML = `
    <div class="status-line">
      <span class="status-label">Mode</span>
      <span class="status-value">${s.mode || '—'}</span>
    </div>
    <div class="status-line">
      <span class="status-label">Configured</span>
      <span class="status-value ${s.configured ? 'connected' : 'error'}">${s.configured ? 'Yes' : 'No'}</span>
    </div>
  `;
}

async function saveConfig() {
  const config = {
    notify_on_ban: document.getElementById('notify-ban').checked,
    notify_on_alert: document.getElementById('notify-alert').checked,
    alert_threshold: parseInt(document.getElementById('alert-threshold').value) || 0,
    ban_threshold: parseInt(document.getElementById('ban-threshold').value) || 0,
    notify_cooldown: parseInt(document.getElementById('notify-cooldown').value) || 0
  };
  
  try {
    await api('/api/config', { method: 'POST', body: JSON.stringify(config) });
    showToast('Settings saved');
  } catch (e) {
    showToast('Failed to save settings', 'error');
  }
}

async function testNotification() {
  try {
    await api('/api/test-notify', { method: 'POST' });
    showToast('Test notification sent');
  } catch (e) {
    showToast('Failed to send notification', 'error');
  }
}

async function saveAppriseUrls() {
  const urls = document.getElementById('apprise-urls').value;
  try {
    await api('/api/apprise/urls', { method: 'POST', body: JSON.stringify({ urls }) });
    showToast('Apprise URLs saved');
    loadAppriseStatus();
  } catch (e) {
    showToast('Failed to save URLs', 'error');
  }
}

async function deleteDecision(ip) {
  if (!confirm(`Delete decision for ${ip}?`)) return;
  try {
    await api(`/api/decisions/${ip}`, { method: 'DELETE' });
    showToast('Decision deleted');
    loadDecisions();
  } catch (e) {
    showToast('Failed to delete decision', 'error');
  }
}

async function loadStatistics() {
  try {
    const stats = await api(`/api/statistics?period=${state.currentPeriod}`);
    updateCharts(stats);
    document.getElementById('stat-bans').textContent = stats.decisions.total;
    document.getElementById('stat-alerts').textContent = stats.alerts.total;
    document.getElementById('stat-sent').textContent = state.status.sent_count || 0;
    document.getElementById('stat-suppressed').textContent = state.status.suppressed_count || 0;
  } catch (e) {
    console.error('Failed to load statistics:', e);
  }
}

function updateCharts(stats) {
  const colors = ['#3b82f6', '#22c55e', '#ef4444', '#eab308', '#a855f7', '#ec4899', '#14b8a6', '#f97316'];
  
  if (state.charts.scenarios) {
    state.charts.scenarios.destroy();
  }
  
  const scenarioData = stats.decisions.by_scenario;
  const labels = Object.keys(scenarioData);
  const values = Object.values(scenarioData);
  
  if (labels.length === 0) return;
  
  const ctx = document.getElementById('chart-scenarios').getContext('2d');
  state.charts.scenarios = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: colors.slice(0, labels.length),
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      cutout: '65%'
    }
  });
  
  const legend = document.getElementById('legend-scenarios');
  legend.innerHTML = labels.map((label, i) => `
    <div class="legend-item">
      <span class="legend-color" style="background:${colors[i % colors.length]}"></span>
      <span class="legend-label">${label}</span>
      <span class="legend-value">${values[i]}</span>
    </div>
  `).join('');
}

function setupTabs() {
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById(`tab-${tab.dataset.tab}`).classList.add('active');
    });
  });
}

function setupTimeFilter() {
  document.querySelectorAll('.time-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.time-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.currentPeriod = btn.dataset.period;
      loadStatistics();
    });
  });
}

function setupSearch() {
  document.getElementById('decisions-search').addEventListener('input', e => {
    state.decisionsSearch = e.target.value;
    state.decisionsPage = 1;
    loadDecisions();
  });
  
  document.getElementById('alerts-search').addEventListener('input', e => {
    state.alertsSearch = e.target.value;
    loadAlerts();
  });
}

async function initApp() {
  setupTabs();
  setupTimeFilter();
  setupSearch();
  
  await Promise.all([
    loadStatus(),
    loadConfig(),
    loadDecisions(),
    loadAlerts(),
    loadAppriseStatus(),
    loadAppriseUrls(),
    loadAuthProviderSettings()
  ]);
  
  await loadStatistics();
  
  setInterval(loadStatus, 30000);
  setInterval(() => {
    loadDecisions();
    loadAlerts();
  }, 30000);
  
  setInterval(loadStatistics, 86400000);
}

document.addEventListener('DOMContentLoaded', () => {
  setTheme(getTheme());
  
  document.getElementById('login-form').addEventListener('submit', handleLogin);
  document.getElementById('logout-btn').addEventListener('click', handleLogout);
  document.getElementById('theme-toggle-btn').addEventListener('click', toggleTheme);
  document.getElementById('theme-toggle-header').addEventListener('click', toggleTheme);
  document.getElementById('save-config').addEventListener('click', saveConfig);
  document.getElementById('test-notify').addEventListener('click', testNotification);
  document.getElementById('save-apprise').addEventListener('click', saveAppriseUrls);
  document.getElementById('password-form').addEventListener('submit', handlePasswordChange);
  document.getElementById('close-password-modal').addEventListener('click', closePasswordModal);
  document.getElementById('cancel-password').addEventListener('click', closePasswordModal);
  
  document.getElementById('sso-btn').addEventListener('click', handleSSOLogin);
  
  document.getElementById('refresh-chart').addEventListener('click', loadStatistics);
  
  checkAuth();
});
