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
  auth: {
    enabled: false,
    method: null,
    authenticated: false,
    username: null,
    auth0Domain: null,
    auth0ClientId: null,
    passwordChangeAvailable: false
  }
};

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    credentials: 'include',
    ...options
  });
  if (res.status === 401) {
    const data = await res.json().catch(() => ({}));
    if (state.auth.enabled) {
      showLogin();
    }
    throw new Error('Unauthorized');
  }
  if (!res.ok) throw new Error(`API Error: ${res.status}`);
  return res.json();
}

function showToast(message, type = 'success') {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.className = `toast ${type}`;
  setTimeout(() => toast.classList.add('hidden'), 3000);
}

function formatTime(isoString) {
  if (!isoString) return '—';
  const d = new Date(isoString);
  return d.toLocaleString();
}

function timeAgo(isoString) {
  if (!isoString) return '—';
  const diff = (Date.now() - new Date(isoString)) / 1000;
  if (diff < 60) return `${Math.round(diff)}s ago`;
  if (diff < 3600) return `${Math.round(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.round(diff / 3600)}h ago`;
  return `${Math.round(diff / 86400)}d ago`;
}

function showLogin() {
  document.getElementById('login-overlay').classList.remove('hidden');
  document.getElementById('main-container').classList.add('blur');
  document.getElementById('login-loading').classList.add('hidden');
  document.getElementById('login-content').classList.remove('hidden');
}

function hideLogin() {
  document.getElementById('login-overlay').classList.add('hidden');
  document.getElementById('main-container').classList.remove('blur');
}

function updateAuthUI() {
  const loginForm = document.getElementById('login-form');
  const auth0Login = document.getElementById('auth0-login');
  const logoutBtn = document.getElementById('logout-btn');
  const userInfo = document.getElementById('user-info');

  if (state.auth.method === 'auth0') {
    loginForm.classList.add('hidden');
    auth0Login.classList.remove('hidden');
  } else if (state.auth.method === 'credentials') {
    loginForm.classList.remove('hidden');
    auth0Login.classList.add('hidden');
  } else {
    loginForm.classList.remove('hidden');
    auth0Login.classList.add('hidden');
  }

  if (state.auth.authenticated) {
    logoutBtn.classList.remove('hidden');
    userInfo.textContent = state.auth.username;
    userInfo.classList.remove('hidden');
  } else {
    logoutBtn.classList.add('hidden');
    userInfo.classList.add('hidden');
  }

  updateAuthSettingsUI();
}

function updateAuthSettingsUI() {
  const authCard = document.getElementById('auth-settings-card');
  const authContent = document.getElementById('auth-settings-content');

  if (!state.auth.enabled) {
    authCard.style.display = 'none';
    return;
  }

  authCard.style.display = 'block';

  if (state.auth.method === 'auth0') {
    authContent.innerHTML = `
      <div class="status-line">
        <span class="status-label">Method</span>
        <span class="status-value">Auth0</span>
      </div>
      <div class="status-line">
        <span class="status-label">Domain</span>
        <span class="status-value">${state.auth.auth0Domain}</span>
      </div>
      <p class="settings-note">Authentication is managed by Auth0. Password changes are disabled.</p>
    `;
  } else if (state.auth.method === 'credentials' && state.auth.passwordChangeAvailable) {
    authContent.innerHTML = `
      <div class="status-line">
        <span class="status-label">Method</span>
        <span class="status-value">Username/Password</span>
      </div>
      <div class="status-line">
        <span class="status-label">Logged in as</span>
        <span class="status-value">${state.auth.username}</span>
      </div>
      <button id="change-password-btn" class="btn btn-secondary" style="margin-top: 12px;">Change Password</button>
    `;
    document.getElementById('change-password-btn').addEventListener('click', openPasswordModal);
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

async function changePassword(currentPassword, newPassword) {
  try {
    const res = await api('/api/auth/password', {
      method: 'POST',
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword
      })
    });
    showToast('Password changed successfully');
    closePasswordModal();
  } catch (e) {
    const errorEl = document.getElementById('password-error');
    errorEl.textContent = e.message;
    errorEl.classList.remove('hidden');
  }
}

async function checkAuthStatus() {
  try {
    const status = await fetch('/api/auth/status', { credentials: 'include' }).then(r => r.json());
    state.auth.enabled = status.enabled;
    state.auth.method = status.method;
    state.auth.auth0Domain = status.auth0_domain;
    state.auth.auth0ClientId = status.auth0_client_id;
    state.auth.passwordChangeAvailable = status.password_change_available;

    if (!status.enabled) {
      hideLogin();
      return true;
    }

    try {
      const check = await api('/api/auth/check');
      state.auth.authenticated = true;
      state.auth.username = check.username;
      hideLogin();
      return true;
    } catch (e) {
      showLogin();
      updateAuthUI();
      return false;
    }
  } catch (e) {
    console.error('Failed to check auth status:', e);
    hideLogin();
    return true;
  }
}

async function loginWithCredentials(username, password) {
  document.getElementById('login-loading').classList.remove('hidden');
  document.getElementById('login-content').classList.add('hidden');

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
    hideLogin();
    updateAuthSettingsUI();
    initApp();
  } catch (e) {
    const errorEl = document.getElementById('login-error');
    errorEl.textContent = e.message;
    errorEl.classList.remove('hidden');
    document.getElementById('login-loading').classList.add('hidden');
    document.getElementById('login-content').classList.remove('hidden');
  }
}

async function loginWithAuth0() {
  const domain = state.auth.auth0Domain;
  const clientId = state.auth.auth0ClientId;
  const redirectUri = encodeURIComponent(window.location.origin + '/callback');

  const stateParam = btoa(Math.random().toString());
  sessionStorage.setItem('auth0_state', stateParam);

  const authUrl = `https://${domain}/authorize?` +
    `response_type=token&` +
    `client_id=${clientId}&` +
    `redirect_uri=${redirectUri}&` +
    `scope=openid%20profile%20email&` +
    `state=${stateParam}`;

  window.location.href = authUrl;
}

async function handleAuth0Callback() {
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

  document.getElementById('login-loading').classList.remove('hidden');
  document.getElementById('login-content').classList.add('hidden');

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
    hideLogin();
    updateAuthSettingsUI();
    initApp();
    return true;
  } catch (e) {
    const errorEl = document.getElementById('login-error');
    errorEl.textContent = e.message;
    errorEl.classList.remove('hidden');
    document.getElementById('login-loading').classList.add('hidden');
    document.getElementById('login-content').classList.remove('hidden');
    return false;
  }
}

async function logout() {
  try {
    await fetch('/api/auth/logout', {
      method: 'POST',
      credentials: 'include'
    });
  } catch (e) {
    console.error('Logout error:', e);
  }

  state.auth.authenticated = false;
  state.auth.username = null;
  showLogin();
  updateAuthUI();
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

function updateStatusUI() {
  const s = state.status;
  const indicator = document.getElementById('status-indicator');
  const statusText = document.getElementById('status-text');
  const lastPoll = document.getElementById('last-poll');
  const decisionsCount = document.getElementById('decisions-count');
  const alertsCount = document.getElementById('alerts-count');

  indicator.className = 'status-dot';
  if (s.poll_errors > 3) {
    indicator.classList.add('error');
    statusText.textContent = 'Error';
  } else if (s.poll_errors > 0) {
    indicator.classList.add('warning');
    statusText.textContent = 'Warning';
  } else {
    statusText.textContent = 'Online';
  }

  lastPoll.textContent = s.last_poll ? `Last poll: ${timeAgo(s.last_poll)}` : '';
  decisionsCount.textContent = s.total_bans || 0;
  alertsCount.textContent = s.total_alerts || 0;

  const connectionStatus = document.getElementById('connection-status');
  connectionStatus.innerHTML = `
    <div class="status-line">
      <span class="status-label">CrowdSec URL</span>
      <span class="status-value">${s.crowdsec_url || '—'}</span>
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

  const stats = document.getElementById('stats');
  stats.innerHTML = `
    <div class="stat-item">
      <div class="stat-value">${s.total_bans || 0}</div>
      <div class="stat-label">Active Bans</div>
    </div>
    <div class="stat-item">
      <div class="stat-value">${s.total_alerts || 0}</div>
      <div class="stat-label">Alerts</div>
    </div>
    <div class="stat-item">
      <div class="stat-value">${s.sent_count || 0}</div>
      <div class="stat-label">Sent</div>
    </div>
    <div class="stat-item">
      <div class="stat-value">${s.suppressed_count || 0}</div>
      <div class="stat-label">Suppressed</div>
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
  const decisions = state.decisions;
  const start = (state.decisionsPage - 1) * state.decisionsPerPage;
  const end = start + state.decisionsPerPage;
  const pageDecisions = decisions.slice(start, end);

  if (pageDecisions.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No decisions found</td></tr>';
  } else {
    tbody.innerHTML = pageDecisions.map(d => `
      <tr>
        <td class="ip-cell">${d.value || '?'}</td>
        <td>
          <span class="type-${d.type || 'ban'} decision-tooltip" 
                data-tooltip="${getTypeDescription(d.type)}">${d.type || 'ban'}</span>
        </td>
        <td>
          <span class="decision-tooltip" data-tooltip="${getScenarioDescription(d.scenario)}">${d.scenario || '?'}</span>
        </td>
        <td>
          <span class="decision-tooltip" data-tooltip="${getOriginDescription(d.origin)}">${d.origin || '?'}</span>
        </td>
        <td>${d.duration || '?'}</td>
        <td>
          <button class="btn btn-sm btn-danger" onclick="unban('${d.id}')">Unban</button>
        </td>
      </tr>
    `).join('');
  }

  setupTooltips();
  updatePagination();
}

function getTypeDescription(type) {
  const descriptions = {
    'ban': 'This IP is completely blocked from accessing your server.',
    'captcha': 'This IP must solve a CAPTCHA challenge before accessing your server.',
    'throttle': 'This IP has restricted access speed to prevent abuse.'
  };
  return descriptions[type] || `Action type: ${type}`;
}

function getScenarioDescription(scenario) {
  if (!scenario) return 'No scenario information available';
  
  const descriptions = {
    'crowdsecurity/ssh-bf': 'SSH brute-force attack detected - multiple failed login attempts',
    'crowdsecurity/ssh-slow-bf': 'Slow SSH brute-force attack - distributed failed login attempts',
    'crowdsecurity/http-bf-wordpress_wplogin': 'WordPress login brute-force attack',
    'crowdsecurity/http-bf-generic': 'HTTP brute-force attack detected',
    'crowdsecurity/http-path-traversal-probing': 'Path traversal attack - attempting to access restricted files',
    'crowdsecurity/http-xss-probing': 'XSS attack probing - attempting to inject malicious scripts',
    'crowdsecurity/http-sqli-probing': 'SQL injection probing - attempting to manipulate database queries',
    'crowdsecurity/http-crawl-non_statics': 'Aggressive web crawling detected',
    'crowdsecurity/http-generic-bf': 'Generic HTTP brute-force attack'
  };
  
  return descriptions[scenario] || `Security scenario: ${scenario}`;
}

function getOriginDescription(origin) {
  if (!origin) return 'Origin not specified';
  
  const descriptions = {
    'crowdsec': 'Automated decision by CrowdSec based on detected behavior patterns.',
    'cscli': 'Manual decision added via CrowdSec CLI tool.',
    'lists': 'Decision from external blocklist subscription.',
    'caas': 'Decision from CrowdSec Crowd Conservation API.'
  };
  
  return descriptions[origin.toLowerCase()] || `Decision source: ${origin}`;
}

function updatePagination() {
  const pagination = document.getElementById('decisions-pagination');
  const totalPages = Math.ceil(state.decisions.length / state.decisionsPerPage);

  if (totalPages <= 1) {
    pagination.innerHTML = '';
    return;
  }

  let html = '';
  const maxVisible = 5;
  let startPage = Math.max(1, state.decisionsPage - Math.floor(maxVisible / 2));
  let endPage = Math.min(totalPages, startPage + maxVisible - 1);

  if (endPage - startPage + 1 < maxVisible) {
    startPage = Math.max(1, endPage - maxVisible + 1);
  }

  if (startPage > 1) {
    html += `<button onclick="goToPage(1)">1</button>`;
    if (startPage > 2) html += `<span>...</span>`;
  }

  for (let i = startPage; i <= endPage; i++) {
    html += `<button class="${i === state.decisionsPage ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
  }

  if (endPage < totalPages) {
    if (endPage < totalPages - 1) html += `<span>...</span>`;
    html += `<button onclick="goToPage(${totalPages})">${totalPages}</button>`;
  }

  pagination.innerHTML = html;
}

function goToPage(page) {
  state.decisionsPage = page;
  updateDecisionsUI();
}

function updateAlertsUI() {
  const tbody = document.getElementById('alerts-body');
  const alerts = state.alerts;

  if (alerts.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No alerts found</td></tr>';
  } else {
    tbody.innerHTML = alerts.slice(0, 100).map(a => `
      <tr>
        <td class="ip-cell">${a.source?.ip || '?'}</td>
        <td>${a.scenario || '?'}</td>
        <td>${a.events_count || 0}</td>
        <td>${(a.message || '').substring(0, 60)}${a.message && a.message.length > 60 ? '...' : ''}</td>
        <td>${timeAgo(a.created_at)}</td>
      </tr>
    `).join('');
  }
}

function updateAppriseUI() {
  const status = document.getElementById('apprise-status');
  const s = state.appriseStatus;

  status.innerHTML = `
    <span class="status-label">Mode:</span>
    <span class="status-value">${s.mode || '—'}</span>
    ${s.mode === 'api' ? `<span class="status-label">API URL:</span><span class="status-value">${s.api_url || '—'}</span>` : ''}
  `;
}

async function unban(decisionId) {
  if (!confirm('Are you sure you want to remove this ban?')) return;
  try {
    await api(`/api/unban?id=${decisionId}`, { method: 'DELETE' });
    showToast('Ban removed successfully');
    await loadDecisions();
    await loadStatus();
  } catch (e) {
    showToast('Failed to remove ban', 'error');
  }
}

async function saveConfig() {
  try {
    const config = {
      notify_on_ban: document.getElementById('notify-ban').checked,
      notify_on_alert: document.getElementById('notify-alert').checked,
      alert_threshold: parseInt(document.getElementById('alert-threshold').value) || 0,
      ban_threshold: parseInt(document.getElementById('ban-threshold').value) || 0,
      notify_cooldown: parseInt(document.getElementById('notify-cooldown').value) || 0
    };
    await api('/api/config', {
      method: 'PATCH',
      body: JSON.stringify(config)
    });
    showToast('Settings saved');
    await loadConfig();
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
  try {
    const urls = document.getElementById('apprise-urls').value
      .split('\n')
      .map(u => u.trim())
      .filter(u => u);
    await api('/api/apprise/urls', {
      method: 'POST',
      body: JSON.stringify({ urls })
    });
    showToast('Apprise URLs saved');
    await loadAppriseStatus();
  } catch (e) {
    showToast('Failed to save URLs', 'error');
  }
}

async function loadAppriseUrls() {
  try {
    const data = await api('/api/apprise/urls');
    document.getElementById('apprise-urls').value = (data.urls || []).join('\n');
  } catch (e) {
    console.error('Failed to load apprise URLs:', e);
  }
}

function setupTabs() {
  const tabs = document.querySelectorAll('.tab');
  const contents = document.querySelectorAll('.tab-content');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetId = tab.dataset.tab;

      tabs.forEach(t => t.classList.remove('active'));
      contents.forEach(c => c.classList.remove('active'));

      tab.classList.add('active');
      document.getElementById(`tab-${targetId}`).classList.add('active');
    });
  });
}

function setupSearch() {
  let decisionsTimeout, alertsTimeout;

  document.getElementById('decisions-search').addEventListener('input', (e) => {
    clearTimeout(decisionsTimeout);
    decisionsTimeout = setTimeout(() => {
      state.decisionsSearch = e.target.value;
      state.decisionsPage = 1;
      loadDecisions();
    }, 300);
  });

  document.getElementById('alerts-search').addEventListener('input', (e) => {
    clearTimeout(alertsTimeout);
    alertsTimeout = setTimeout(() => {
      state.alertsSearch = e.target.value;
      loadAlerts();
    }, 300);
  });
}

function setupTooltips() {
  const tooltip = document.getElementById('tooltip');
  
  document.querySelectorAll('.decision-tooltip, .tooltip-trigger').forEach(el => {
    el.addEventListener('mouseenter', (e) => {
      const text = el.dataset.tooltip;
      if (!text) return;
      
      tooltip.textContent = text;
      tooltip.classList.remove('hidden');
      
      const rect = el.getBoundingClientRect();
      let top = rect.bottom + 8;
      let left = rect.left;
      
      if (left + tooltip.offsetWidth > window.innerWidth) {
        left = window.innerWidth - tooltip.offsetWidth - 16;
      }
      
      if (top + tooltip.offsetHeight > window.innerHeight) {
        top = rect.top - tooltip.offsetHeight - 8;
      }
      
      tooltip.style.top = `${top}px`;
      tooltip.style.left = `${left}px`;
    });
    
    el.addEventListener('mouseleave', () => {
      tooltip.classList.add('hidden');
    });
  });
}

function setupAuthHandlers() {
  document.getElementById('login-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    loginWithCredentials(username, password);
  });

  document.getElementById('auth0-btn').addEventListener('click', (e) => {
    e.preventDefault();
    loginWithAuth0();
  });

  document.getElementById('logout-btn').addEventListener('click', logout);

  document.getElementById('password-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const currentPassword = document.getElementById('current-password').value;
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;

    if (newPassword !== confirmPassword) {
      const errorEl = document.getElementById('password-error');
      errorEl.textContent = 'New passwords do not match';
      errorEl.classList.remove('hidden');
      return;
    }

    if (newPassword.length < 8) {
      const errorEl = document.getElementById('password-error');
      errorEl.textContent = 'New password must be at least 8 characters';
      errorEl.classList.remove('hidden');
      return;
    }

    changePassword(currentPassword, newPassword);
  });
}

async function initApp() {
  setupTabs();
  setupSearch();
  setupTooltips();

  document.getElementById('save-config').addEventListener('click', saveConfig);
  document.getElementById('test-notify').addEventListener('click', testNotification);
  document.getElementById('save-apprise').addEventListener('click', saveAppriseUrls);

  await Promise.all([
    loadStatus(),
    loadConfig(),
    loadDecisions(),
    loadAlerts(),
    loadAppriseStatus(),
    loadAppriseUrls()
  ]);

  setInterval(loadStatus, 30000);
  setInterval(() => {
    loadDecisions();
    loadAlerts();
  }, 30000);
}

async function init() {
  setupAuthHandlers();

  if (window.location.pathname === '/callback' || window.location.hash.includes('access_token')) {
    const handled = await handleAuth0Callback();
    if (!handled) {
      window.location.href = '/';
    }
    return;
  }

  const authenticated = await checkAuthStatus();
  updateAuthUI();

  if (authenticated || !state.auth.enabled) {
    initApp();
  }
}

document.addEventListener('DOMContentLoaded', init);
