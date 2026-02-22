<script>
  import { status, isLoading, appriseStatus } from '../lib/stores.js';
  import { api } from '../lib/api.js';
  import { showToast } from '../lib/stores.js';
  
  async function testNotification() {
    try {
      await api.testNotify();
      showToast('Test notification sent!', 'success');
    } catch (e) {
      showToast('Failed to send notification', 'error');
    }
  }
  
  async function refresh() {
    window.location.reload();
  }
</script>

<header>
  <div class="logo">
    <div class="logo-icon">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      </svg>
    </div>
    <span class="logo-text">CrowdSec Dashboard</span>
  </div>
  
  <div class="header-actions">
    <div class="status-indicator">
      <span class="status-dot" class:connected={!$status.poll_errors} class:error={$status.poll_errors > 3}></span>
      <span class="status-text">{#if $status.poll_errors > 3}Error{:else if $status.poll_errors > 0}Warning{:else}Online{/if}</span>
    </div>
    
    {#if $appriseStatus.mode === 'api'}
      <span class="badge badge-api">API Mode</span>
    {/if}
    
    <button class="btn btn-ghost" onclick={testNotification} title="Send test notification">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
        <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
      </svg>
    </button>
    
    <button class="btn btn-ghost" onclick={refresh} title="Refresh" class:spinning={$isLoading}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M23 4v6h-6"/>
        <path d="M1 20v-6h6"/>
        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
      </svg>
    </button>
  </div>
</header>

<style>
  header {
    position: sticky;
    top: 0;
    z-index: 100;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 0;
    background: rgba(9, 11, 15, 0.8);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid var(--border-subtle);
  }
  
  .logo {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .logo-icon {
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, var(--accent), var(--purple));
    border-radius: var(--radius);
    color: white;
  }
  
  .logo-text {
    font-size: 17px;
    font-weight: 600;
    letter-spacing: -0.02em;
  }
  
  .header-actions {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .status-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    background: var(--surface);
    border-radius: var(--radius);
    border: 1px solid var(--border-subtle);
  }
  
  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--success);
  }
  
  .status-dot.error {
    background: var(--danger);
  }
  
  .status-text {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-secondary);
  }
  
  .badge {
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-radius: var(--radius-sm);
  }
  
  .badge-api {
    background: var(--purple-muted);
    color: var(--purple);
  }
  
  .btn {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 8px;
    border-radius: var(--radius);
    transition: var(--transition);
    color: var(--text-secondary);
  }
  
  .btn-ghost:hover {
    background: var(--surface);
    color: var(--text);
  }
  
  .btn.spinning svg {
    animation: spin 1s linear infinite;
  }
</style>
