const state = {
  status: {},
  config: {},
  configLoaded: false,
  decisions: [],
  appriseStatus: {},
  decisionsPage: 1,
  decisionsPerPage: 50,
  decisionsSearch: '',
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

const SCENARIO_DESCRIPTIONS = {
  "http-crawl": "Automated bot crawling your website to find vulnerabilities",
  "http-sql-injection": "SQL injection attack attempt - attacker tries to inject malicious SQL code",
  "http-xss": "Cross-site scripting (XSS) attack - attempts to inject malicious scripts",
  "http-csrf": "Cross-site request forgery attempt",
  "http-probing": "Probing attack - scanning for open ports or vulnerabilities",
  "http-backdoor": "Backdoor access attempt - trying to establish unauthorized access",
  "http-bruteforce": "Brute force attack - repeated login attempts to guess passwords",
  "ssh-bruteforce": "SSH brute force attack - repeated attempts to guess SSH credentials",
  "ssh-probing": "SSH probing - scanning for SSH vulnerabilities",
  "ftp-bruteforce": "FTP brute force attack - guessing FTP credentials",
  "smtp-bruteforce": "SMTP brute force - attempting to send spam or hack email accounts",
  "pop3-bruteforce": "POP3 brute force attack on email retrieval",
  "imap-bruteforce": "IMAP brute force attack on email access",
  "http-irc-bounce": "Attempt to use HTTP proxy as IRC bounce",
  "http-misc": "Miscellaneous HTTP attack",
  "tls-invalid-client_hello": "Invalid TLS client hello - potential scanning or attack",
  "http-wordpress": "WordPress specific attack or vulnerability probe",
  "http-joomla": "Joomla CMS specific attack",
  "http-drupal": "Drupal CMS specific attack",
  "http-magento": "Magento e-commerce platform attack",
  "httpnginx": "Nginx-specific attack attempt",
  "httpapache": "Apache web server attack attempt",
  "http-cowboy": "Cowboy web framework attack",
  "http-openresty": "OpenResty web platform attack",
  "ssl-cert": "SSL certificate issue or mismatch",
  "ssl-known-good": "Known safe SSL certificate",
  "tls-scan": "TLS/SSL vulnerability scanning",
  "iprep": "IP reputation based blocking - IP has bad reputation",
  "crowdsecurity/http-crawl": "CrowdSec HTTP crawling detection",
  "crowdsecurity/http-sensitive-files": "Access to sensitive files detected",
  "crowdsecurity/path-traversal": "Path traversal attack attempt",
  "crowdsecurity/404-recon": "Reconnaissance via repeated 404 errors",
  "crowdsecurity/admin-panel": "Admin panel access attempt",
  "crowdsecurity/database-probe": "Database vulnerability probing",
  "crowdsecurity/login-s的法": "Brute force login attempt",
};

function showTooltip(e, text) {
  let tooltip = document.getElementById('scenario-tooltip');
  if (!tooltip) {
    tooltip = document.createElement('div');
    tooltip.id = 'scenario-tooltip';
    tooltip.style.cssText = 'position:fixed;background:#333;color:#fff;padding:8px 12px;border-radius:4px;font-size:12px;z-index:9999;max-width:300px;pointer-events:none;display:none;';
    document.body.appendChild(tooltip);
  }
  tooltip.textContent = text;
  tooltip.style.display = 'block';
  tooltip.style.left = (e.pageX + 10) + 'px';
  tooltip.style.top = (e.pageY + 10) + 'px';
}

function hideTooltip() {
  const tooltip = document.getElementById('scenario-tooltip');
  if (tooltip) tooltip.style.display = 'none';
}

function getScenarioDescription(scenario) {
  if (!scenario) return 'Unknown scenario';
  return SCENARIO_DESCRIPTIONS[scenario] || `Security event: ${scenario}`;
}

function getSystemTheme() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function getTheme() {
  const saved = localStorage.getItem('theme');
  if (saved && saved !== 'auto') return saved;
  return getSystemTheme();
}

function setTheme(theme) {
  if (theme === 'auto') {
    localStorage.removeItem('theme');
    theme = getSystemTheme();
  } else {
    localStorage.setItem('theme', theme);
  }
  document.documentElement.setAttribute('data-theme', theme);
  updateThemeIcons(theme);
}

function initThemeListener() {
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  mediaQuery.addEventListener('change', e => {
    const saved = localStorage.getItem('theme');
    if (!saved || saved === 'auto') {
      setTheme(e.matches ? 'dark' : 'light');
    }
  });
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
    console.warn('API 401:', path);
    if (!options.allowAuthFailure) {
      showLoginPage();
    }
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
  console.log('showLoginPage called, auth method:', state.auth.method);
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
  console.log('showApp called');
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
  sessionStorage.setItem('auth0_app_url', appUrl);
  
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
  const appUrl = sessionStorage.getItem('auth0_app_url') || state.auth.appUrl || window.location.origin;
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
    sessionStorage.removeItem('auth0_app_url');
    
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
      
      console.log('Login successful, username:', data.username);
      state.auth.authenticated = true;
      state.auth.username = data.username;
      window.history.replaceState({}, document.title, window.location.pathname);
      showApp();
      document.getElementById('user-badge').textContent = data.username;
      console.log('Calling initApp...');
      await initApp();
      console.log('initApp complete');
      return true;
    } catch (e) {
      console.error('Login failed:', e);
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
  
  // Get fresh auth status to determine login method
  try {
    const status = await fetch('/api/auth/status', { credentials: 'include' }).then(r => r.json());
    state.auth.method = status.method;
    state.auth.auth0Domain = status.auth0_domain;
    state.auth.auth0ClientId = status.auth0_client_id;
    state.auth.auth0AuthorizeUrl = status.auth0_authorize_url;
  } catch (e) {}
  
  showLoginPage();
}

async function checkAuth() {
  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get('code');
  
  if (code) {
    await handleAuth0Callback(code);
    return;
  }
  
  if (window.location.hash.includes('access_token')) {
    await handleAuth0Callback();
    return;
  }
  
  // Set defaults first — ensures state is always initialized
  state.auth.enabled = false;
  state.auth.method = null;
  state.auth.auth0Domain = null;
  state.auth.auth0ClientId = null;
  state.auth.auth0AuthorizeUrl = null;
  state.auth.auth0TokenUrl = null;
  state.auth.appUrl = null;
  state.auth.passwordChangeAvailable = false;
  
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
  } catch (e) {
    console.error('Failed to load auth status:', e);
  }
  
  updateAuthMethodSelect();
  
  if (state.auth.enabled) {
    try {
      const check = await api('/api/auth/check');
      state.auth.authenticated = true;
      state.auth.username = check.username;
      showApp();
      document.getElementById('user-badge').textContent = check.username;
    } catch (e) {
      showLoginPage();
    }
  } else {
    showApp();
  }
  
  await initApp();
}

function updateAuthMethodSelect() {
  const card = document.getElementById('auth-method-settings');
  
  if (!state.auth.enabled) {
    card.style.display = 'block';
    const content = document.getElementById('auth-method-content');
    content.innerHTML = `
      <div class="status-line">
        <span class="status-label">Status</span>
        <span class="status-value">Disabled</span>
      </div>
      <p class="settings-note">Authentication is not configured. Set AUTH_USERNAME and AUTH_PASSWORD or AUTH0_* variables to enable.</p>
    `;
    return;
  }
  
  card.style.display = 'block';
  const content = document.getElementById('auth-method-content');
  
  if (state.auth.method === 'auth0') {
    content.innerHTML = `
      <div class="status-line">
        <span class="status-label">Method</span>
        <span class="status-value connected">External SSO (Auth0/Authentik)</span>
      </div>
      <div class="status-line">
        <span class="status-label">Provider</span>
        <span class="status-value">${state.auth.auth0Domain || 'External'}</span>
      </div>
      <p class="settings-note">SSO is configured via environment variables.</p>
    `;
    return;
  }
  
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

async function loadStatus() {
  try {
    state.status = await api('/api/status', { allowAuthFailure: true });
    updateStatusUI();
  } catch (e) {
    console.error('Failed to load status:', e);
  }
}

async function loadConfig() {
  try {
    state.config = await api('/api/config', { allowAuthFailure: true });
    state.configLoaded = true;
    updateConfigUI();
  } catch (e) {
    console.error('Failed to load config:', e);
  }
}

async function loadDecisions() {
  try {
    const q = state.decisionsSearch;
    state.decisions = await api(`/api/decisions${q ? '?q=' + encodeURIComponent(q) : ''}`, { allowAuthFailure: true });
    updateDecisionsUI();
  } catch (e) {
    console.error('Failed to load decisions:', e);
  }
}

async function loadAppriseStatus() {
  try {
    state.appriseStatus = await api('/api/apprise/status', { allowAuthFailure: true });
    updateAppriseUI();
  } catch (e) {
    console.error('Failed to load apprise status:', e);
  }
}

async function loadAppriseUrls() {
  try {
    const data = await api('/api/apprise/urls', { allowAuthFailure: true });
    document.getElementById('apprise-urls').value = data.urls || '';
  } catch (e) {
    console.error('Failed to load apprise urls:', e);
  }
}

async function loadAuthProviderSettings() {
  try {
    const data = await api('/api/auth/config', { allowAuthFailure: true });
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
  
  const decisionsCountEl = document.getElementById('decisions-count');
  if (decisionsCountEl) decisionsCountEl.textContent = s.total_bans || 0;
  
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
  document.getElementById('alert-threshold').value = c.alert_threshold || 10;
  document.getElementById('ban-threshold').value = c.ban_threshold || 50;
  document.getElementById('notify-cooldown').value = c.notify_cooldown ?? 3600;
  
  // Rate-based thresholds
  document.getElementById('events-per-minute').value = c.events_per_minute_threshold || 100;
  document.getElementById('events-per-hour').value = c.events_per_hour_threshold || 1000;
  document.getElementById('events-per-day').value = c.events_per_day_threshold || 10000;
}

function updateDecisionsUI() {
  const tbody = document.getElementById('decisions-body');
  const start = (state.decisionsPage - 1) * state.decisionsPerPage;
  const end = start + state.decisionsPerPage;
  const page = state.decisions.slice(start, end);
  
  if (page.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--text-muted);padding:40px">No active bans</td></tr>';
    document.getElementById('decisions-pagination').innerHTML = '';
    return;
  }
  
  tbody.innerHTML = page.map(d => `
    <tr>
      <td class="ip-cell">${d.ip || '—'}</td>
      <td onmouseover="showTooltip(event, getScenarioDescription('${d.scenario || ''}'))" onmouseout="hideTooltip()">${d.scenario || '—'}</td>
      <td>${timeAgo(d.created_at)}</td>
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
  
  html += `<button onclick="goToPage(1)" ${state.decisionsPage === 1 ? 'disabled' : ''} title="First page">«</button>`;
  html += `<button onclick="goToPage(${state.decisionsPage - 1})" ${state.decisionsPage === 1 ? 'disabled' : ''} title="Previous page">‹</button>`;
  
  const rangeStart = Math.max(1, state.decisionsPage - 2);
  const rangeEnd = Math.min(pages, state.decisionsPage + 2);
  
  if (rangeStart > 1) {
    html += `<button onclick="goToPage(1)">1</button>`;
    if (rangeStart > 2) {
      html += `<span class="page-ellipsis">…</span>`;
    }
  }
  
  for (let i = rangeStart; i <= rangeEnd; i++) {
    html += `<button class="${i === state.decisionsPage ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
  }
  
  if (rangeEnd < pages) {
    if (rangeEnd < pages - 1) {
      html += `<span class="page-ellipsis">…</span>`;
    }
    html += `<button onclick="goToPage(${pages})">${pages}</button>`;
  }
  
  html += `<button onclick="goToPage(${state.decisionsPage + 1})" ${state.decisionsPage === pages ? 'disabled' : ''} title="Next page">›</button>`;
  html += `<button onclick="goToPage(${pages})" ${state.decisionsPage === pages ? 'disabled' : ''} title="Last page">»</button>`;
  
  container.innerHTML = html;
}

function initResizableColumns() {
  const tables = document.querySelectorAll('table');
  tables.forEach(table => {
    const ths = table.querySelectorAll('th');
    ths.forEach((th, index) => {
      if (index === ths.length - 1) return;
      
      th.addEventListener('mousedown', (e) => {
        if (e.offsetX < th.offsetWidth - 10) return;
        
        const startX = e.clientX;
        const startWidth = th.offsetWidth;
        
        th.classList.add('resizing');
        
        const onMouseMove = (e) => {
          const newWidth = Math.max(50, startWidth + (e.clientX - startX));
          th.style.width = newWidth + 'px';
        };
        
        const onMouseUp = () => {
          th.classList.remove('resizing');
          document.removeEventListener('mousemove', onMouseMove);
          document.removeEventListener('mouseup', onMouseUp);
        };
        
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
      });
    });
  });
}

function goToPage(page) {
  state.decisionsPage = page;
  updateDecisionsUI();
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
    ${s.urls_count !== undefined ? `
    <div class="status-line">
      <span class="status-label">URLs</span>
      <span class="status-value">${s.urls_count}</span>
    </div>
    ` : ''}
  `;
}

async function saveConfig() {
  const config = {
    notify_on_ban: document.getElementById('notify-ban').checked,
    notify_on_alert: document.getElementById('notify-alert').checked,
    alert_threshold: parseInt(document.getElementById('alert-threshold').value) || 0,
    ban_threshold: parseInt(document.getElementById('ban-threshold').value) || 0,
    notify_cooldown: parseInt(document.getElementById('notify-cooldown').value) || 3600,
    events_per_minute_threshold: parseInt(document.getElementById('events-per-minute').value) || 100,
    events_per_hour_threshold: parseInt(document.getElementById('events-per-hour').value) || 1000,
    events_per_day_threshold: parseInt(document.getElementById('events-per-day').value) || 10000,
  };
  
  try {
    await api('/api/config', { method: 'PATCH', body: JSON.stringify(config) });
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
    const stats = await api('/api/statistics', { allowAuthFailure: true });
    updateCharts(stats);
    document.getElementById('stat-bans').textContent = stats.decisions.total;
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
    state.charts.scenarios = null;
  }
  
  const scenarioData = stats.decisions.by_scenario;
  const labels = Object.keys(scenarioData);
  const values = Object.values(scenarioData);
  
  const ctx = document.getElementById('chart-scenarios').getContext('2d');
  const legend = document.getElementById('legend-scenarios');
  
  if (labels.length === 0) {
    legend.innerHTML = '<div style="color:var(--text-muted);text-align:center;padding:20px">No data for this period</div>';
    return;
  }
  
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
  
  legend.innerHTML = labels.map((label, i) => `
    <div class="legend-item" onmouseover="showTooltip(event, getScenarioDescription('${label}'))" onmouseout="hideTooltip()">
      <span class="legend-color" style="background:${colors[i % colors.length]}"></span>
      <span class="legend-label">${label}</span>
      <span class="legend-value">${values[i]}</span>
    </div>
  `).join('');
}

function setupTabs() {
  // Navigation is now link-based for dedicated pages
  // This function is kept for backward compatibility but does nothing
  // since each page has its own init function
}

function initDashboard() {
  setupSearch();
  initResizableColumns();
  
  loadStatus();
  loadConfig().then(() => {
    loadDecisions();
    loadStatistics();
  });
  loadAppriseStatus();
  loadAppriseUrls();
  loadAuthProviderSettings();
  
  setInterval(loadStatus, 30000);
  setInterval(loadDecisions, 30000);
  setInterval(loadStatistics, 86400000);
  
  document.getElementById('refresh-chart')?.addEventListener('click', loadStatistics);
}

function initAlarms() {
  loadStatus();
  loadConfig();
  loadAlarms();
  
  setInterval(loadStatus, 30000);
  setInterval(loadAlarms, 30000);
  
  document.getElementById('refresh-alarms')?.addEventListener('click', loadAlarms);
  document.getElementById('alarm-severity-filter')?.addEventListener('change', loadAlarms);
}

async function initSettings() {
  await loadConfig();
  loadStatus();
  loadAppriseStatus();
  loadAppriseUrls();
  loadAuthProviderSettings();
  loadStatistics();
  
  setInterval(loadStatus, 30000);
  setInterval(loadStatistics, 86400000);
  
  document.getElementById('save-config')?.addEventListener('click', saveConfig);
  document.getElementById('test-notify')?.addEventListener('click', testNotification);
  document.getElementById('save-apprise')?.addEventListener('click', saveAppriseUrls);
}

function setupSearch() {
  document.getElementById('decisions-search').addEventListener('input', e => {
    state.decisionsSearch = e.target.value;
    state.decisionsPage = 1;
    loadDecisions();
  });
}

function setupAutoRefresh() {
  // Auto-refresh is handled by setInterval in initApp
}

async function initApp() {
  setupSearch();
  setupAutoRefresh();
  initResizableColumns();
  
  // Sequential load to avoid race conditions — auth/apprise must load after status
  await loadStatus();
  await loadConfig();
  await loadDecisions();
  await loadAppriseStatus();
  await loadAppriseUrls();
  await loadAuthProviderSettings();
  await loadStatistics();
  
  setInterval(loadStatus, 30000);
  setInterval(() => {
    loadDecisions();
    loadAlarms();
  }, 30000);
  
  setInterval(loadStatistics, 86400000);
}

async function loadAlarms() {
  try {
    const severity = document.getElementById('alarm-severity-filter')?.value || '';
    const url = severity ? `/api/alarms?severity=${severity}` : '/api/alarms';
    const data = await api(url, { allowAuthFailure: true });
    
    renderAlarms(data);
    updateAlarmsBadge(data);
  } catch (e) {
    console.error('Failed to load alarms:', e);
  }
}

async function dismissAlarm(type) {
  try {
    await api(`/api/alarms/${type}/dismiss`, { method: 'POST' });
    showToast('Alarm dismissed');
    loadAlarms();
  } catch (e) {
    showToast('Failed to dismiss alarm', 'error');
  }
}

function renderAlarms(data) {
  const container = document.getElementById('alarms-container');
  const emptyState = document.getElementById('alarms-empty');
  
  if (!data.alarms || data.alarms.length === 0) {
    if (emptyState) emptyState.style.display = 'flex';
    document.getElementById('alarms-count').textContent = '';
    return;
  }
  
  if (emptyState) emptyState.style.display = 'none';
  
  let html = '';
  for (const alarm of data.alarms) {
    const severityClass = alarm.severity?.value || alarm.severity || 'info';
    const severityLabel = severityClass.toUpperCase();
    const icon = getAlarmIcon(alarm.type);
    const newBadge = alarm.is_new ? '<span class="badge badge-new" style="margin-left:8px">NEW</span>' : '';
    const dismissBtn = `<button class="btn btn-sm btn-secondary alarm-dismiss" data-type="${alarm.type}" style="margin-left:8px">Dismiss</button>`;
    
    html += `
      <div class="alarm-card alarm-${severityClass}">
        <div class="alarm-header">
          <div class="alarm-icon">${icon}</div>
          <div class="alarm-title">
            <span class="alarm-type">${formatAlarmType(alarm.type)}</span>
            ${newBadge}
            <span class="alarm-badge badge-${severityClass}">${severityLabel}</span>
          </div>
          <div class="alarm-count">${alarm.count}</div>
          ${dismissBtn}
        </div>
        <div class="alarm-message">${alarm.message}</div>
        <div class="alarm-details">${renderAlarmDetails(alarm)}</div>
      </div>
    `;
  }
  
  container.innerHTML = html;
  document.getElementById('alarms-count').textContent = `(${data.total})`;
}

function getAlarmIcon(type) {
  const icons = {
    'new_attack_source': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    'manual_review': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    'whitelist_expiry': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
    'failed_login_pattern': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 9.9-1"/></svg>',
    'api_connection_error': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 15l-6-6-6 6"/></svg>',
    'geo_anomaly': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
    'rate_limit_warning': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>',
  };
  return icons[type] || icons['new_attack_source'];
}

function formatAlarmType(type) {
  const names = {
    'new_attack_source': 'New Attack Sources',
    'manual_review': 'Manual Review Needed',
    'whitelist_expiry': 'Whitelist Expiring',
    'failed_login_pattern': 'Failed Login Pattern',
    'api_connection_error': 'API Connection Error',
    'geo_anomaly': 'Geo Anomaly',
    'rate_limit_warning': 'Rate Limit Warning',
  };
  return names[type] || type;
}

function renderAlarmDetails(alarm) {
  if (!alarm.ips && !alarm.alerts && !alarm.errors && !alarm.countries && !alarm.warnings && !alarm.entries) {
    return '';
  }
  
  let details = '<div class="alarm-data">';
  
  if (alarm.ips && alarm.ips.length > 0) {
    details += '<div class="alarm-data-row"><strong>IPs:</strong> ' + alarm.ips.slice(0, 5).join(', ') + (alarm.ips.length > 5 ? '...' : '') + '</div>';
  }
  
  if (alarm.countries && alarm.countries.length > 0) {
    details += '<div class="alarm-data-row"><strong>Countries:</strong> ' + alarm.countries.join(', ') + '</div>';
  }
  
  if (alarm.entries && alarm.entries.length > 0) {
    for (const entry of alarm.entries.slice(0, 3)) {
      details += `<div class="alarm-data-row"><strong>${entry.ip}</strong> - Expires: ${entry.expires || 'unknown'}</div>`;
    }
  }
  
  details += '</div>';
  return details;
}

function updateAlarmsBadge(data) {
  const badge = document.getElementById('alarms-badge');
  if (!badge) return;
  
  const newCount = data.alarms ? data.alarms.filter(a => a.is_new).length : 0;
  
  if (newCount > 0) {
    badge.textContent = newCount;
    badge.style.display = 'inline';
    badge.className = 'badge badge-new';
  } else if (data.critical_count > 0) {
    badge.textContent = data.critical_count;
    badge.style.display = 'inline';
    badge.className = 'badge badge-critical';
  } else if (data.warning_count > 0) {
    badge.textContent = data.warning_count;
    badge.style.display = 'inline';
    badge.className = 'badge badge-warning';
  } else if (data.info_count > 0) {
    badge.textContent = data.info_count;
    badge.style.display = 'inline';
    badge.className = 'badge badge-info';
  } else {
    badge.style.display = 'none';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initThemeListener();
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
  
  document.addEventListener('click', (e) => {
    if (e.target.classList.contains('alarm-dismiss')) {
      const type = e.target.dataset.type;
      if (type && confirm('Dismiss this alarm?')) {
        dismissAlarm(type);
      }
    }
  });
  
  checkAuth();
});
