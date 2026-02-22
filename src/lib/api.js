const API_BASE = '';

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });
  
  if (!res.ok) {
    throw new Error(`API Error: ${res.status}`);
  }
  
  return res.json();
}

export const api = {
  status: () => request('/api/status'),
  config: () => request('/api/config'),
  updateConfig: (data) => request('/api/config', {
    method: 'PATCH',
    body: JSON.stringify(data),
  }),
  
  decisions: (q = '') => request(`/api/decisions${q ? `?q=${encodeURIComponent(q)}` : ''}`),
  alerts: (q = '') => request(`/api/alerts${q ? `?q=${encodeURIComponent(q)}` : ''}`),
  events: (type = '', limit = 80) => {
    const params = new URLSearchParams();
    if (type) params.set('type', type);
    params.set('limit', limit);
    return request(`/api/events?${params}`);
  },
  metrics: () => request('/api/metrics'),
  
  unban: (id) => request(`/api/unban?id=${id}`, { method: 'DELETE' }),
  
  cooldowns: () => request('/api/cooldowns'),
  clearCooldown: (ip) => request(`/api/cooldowns${ip ? `?ip=${encodeURIComponent(ip)}` : ''}`, { method: 'DELETE' }),
  
  testNotify: () => request('/api/test-notify', { method: 'POST' }),
  
  appriseStatus: () => request('/api/apprise/status'),
  appriseUrls: () => request('/api/apprise/urls'),
  setAppriseUrls: (urls) => request('/api/apprise/urls', {
    method: 'POST',
    body: JSON.stringify({ urls }),
  }),
  
  health: () => request('/health'),
};

export default api;
