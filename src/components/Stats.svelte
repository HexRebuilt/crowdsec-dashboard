<script>
  import { status, timeAgo } from '../lib/stores.js';
  
  const stats = $derived([
    { label: 'Active Bans', value: $status.total_bans, sublabel: 'blocked IPs', color: 'danger' },
    { label: 'Alerts', value: $status.total_alerts, sublabel: 'last 2 hours', color: 'warning' },
    { label: 'Sent', value: $status.sent_count, sublabel: 'notifications', color: 'success' },
    { label: 'Suppressed', value: $status.suppressed_count, sublabel: 'by threshold', color: 'purple' },
    { label: 'Updated', value: timeAgo($status.last_poll), sublabel: $status.poll_errors ? `${$status.poll_errors} errors` : 'polling', color: 'accent' },
  ]);
</script>

<div class="stats-grid">
  {#each stats as stat, i}
    <div class="stat-card" class:stat-danger={stat.color === 'danger'} class:stat-warning={stat.color === 'warning'} class:stat-success={stat.color === 'success'} class:stat-purple={stat.color === 'purple'} class:stat-accent={stat.color === 'accent'}>
      <div class="stat-label">{stat.label}</div>
      <div class="stat-value">{stat.value}</div>
      <div class="stat-sublabel">{stat.sublabel}</div>
    </div>
  {/each}
</div>

<style>
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }
  
  .stat-card {
    background: var(--surface);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 16px 20px;
    position: relative;
    overflow: hidden;
    transition: var(--transition);
  }
  
  .stat-card:hover {
    border-color: var(--border);
  }
  
  .stat-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: var(--accent);
  }
  
  .stat-danger::before { background: var(--danger); }
  .stat-warning::before { background: var(--warning); }
  .stat-success::before { background: var(--success); }
  .stat-purple::before { background: var(--purple); }
  
  .stat-label {
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-tertiary);
    margin-bottom: 8px;
  }
  
  .stat-value {
    font-size: 32px;
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1;
    color: var(--text);
  }
  
  .stat-sublabel {
    font-size: 12px;
    color: var(--text-quaternary);
    margin-top: 6px;
  }
</style>
