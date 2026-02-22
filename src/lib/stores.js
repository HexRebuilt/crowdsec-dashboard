import { untrack } from 'svelte';

let status = $state({
  last_poll: null,
  poll_errors: 0,
  poll_interval: 30,
  crowdsec_url: '',
  apprise_mode: 'embedded',
  apprise_api_url: '',
  apprise_configured: false,
  unsecure_mode: false,
  total_bans: 0,
  total_alerts: 0,
  sent_count: 0,
  suppressed_count: 0,
  digest_pending: 0,
  next_digest_in: null,
  cooldowns_tracked: 0,
});

let config = $state({
  notify_on_ban: true,
  notify_on_alert: true,
  alert_threshold: 5,
  ban_threshold: 0,
  notify_cooldown: 3600,
  digest_interval: 0,
  apprise_urls: '',
});

let decisions = $state([]);
let alerts = $state([]);
let events = $state([]);
let cooldowns = $state([]);

let activeTab = $state('decisions');
let eventFilter = $state('');
let searchQuery = $state('');
let isLoading = $state(false);
let error = $state(null);
let toast = $state({ show: false, message: '', type: 'success' });

let appriseStatus = $state({
  mode: 'embedded',
  api_url: '',
  api_reachable: false,
  urls_count: 0,
  config_key: 'crowdsec-dashboard',
});

function showToast(message, type = 'success') {
  toast = { show: true, message, type };
  setTimeout(() => {
    toast = { show: false, message: '', type: 'success' };
  }, 3000);
}

function formatTime(dt) {
  if (!dt) return '—';
  const d = new Date(dt);
  if (isNaN(d)) return dt;
  return d.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function timeAgo(dt) {
  if (!dt) return '—';
  const diff = (Date.now() - new Date(dt)) / 1000;
  if (diff < 5) return 'now';
  if (diff < 60) return `${Math.round(diff)}s`;
  if (diff < 3600) return `${Math.round(diff / 60)}m`;
  if (diff < 86400) return `${Math.round(diff / 3600)}h`;
  return `${Math.round(diff / 86400)}d`;
}

function formatSeconds(s) {
  if (s <= 0) return '0s';
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.round(s / 60)}m`;
  if (s < 86400) return `${Math.round(s / 3600)}h`;
  return `${Math.round(s / 86400)}d`;
}

export {
  status,
  config,
  decisions,
  alerts,
  events,
  cooldowns,
  activeTab,
  eventFilter,
  searchQuery,
  isLoading,
  error,
  toast,
  appriseStatus,
  showToast,
  formatTime,
  timeAgo,
  formatSeconds,
};
