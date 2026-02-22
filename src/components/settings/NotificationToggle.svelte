<script>
  import { config, appriseStatus } from '../../lib/stores.js';
  import { api } from '../../lib/api.js';
  import { showToast } from '../../lib/stores.js';
  
  async function toggle(key) {
    try {
      const result = await api.updateConfig({ [key]: !$config[key] });
      config = { ...config, ...result.config };
      showToast('Setting updated', 'success');
    } catch (e) {
      showToast('Failed to update', 'error');
    }
  }
  
  async function testNotification() {
    try {
      await api.testNotify();
      showToast('Test notification sent!', 'success');
    } catch (e) {
      showToast('Failed to send notification', 'error');
    }
  }
</script>

<div class="panel">
  <h3>Notifications</h3>
  
  <div class="toggle-row">
    <span class="toggle-label">Notify on Ban</span>
    <button 
      class="toggle {$config.notify_on_ban ? 'on' : ''}" 
      onclick={() => toggle('notify_on_ban')}
      role="switch"
      aria-checked={$config.notify_on_ban}
    >
      <span class="toggle-thumb"></span>
    </button>
  </div>
  
  <div class="toggle-row">
    <span class="toggle-label">Notify on Alert</span>
    <button 
      class="toggle {$config.notify_on_alert ? 'on' : ''}" 
      onclick={() => toggle('notify_on_alert')}
      role="switch"
      aria-checked={$config.notify_on_alert}
    >
      <span class="toggle-thumb"></span>
    </button>
  </div>
  
  <hr />
  
  <div class="status-row">
    <span class="status-label">Apprise Status</span>
    <span class="status-value" class:connected={$appriseStatus.api_reachable || $appriseStatus.urls_count > 0}>
      {#if $appriseStatus.mode === 'api'}
        {#if $appriseStatus.api_reachable}
          <span class="status-dot success"></span> Connected
        {:else}
          <span class="status-dot error"></span> Disconnected
        {/if}
      {:else}
        {#if $appriseStatus.urls_count > 0}
          <span class="status-dot success"></span> Configured
        {:else}
          <span class="status-dot error"></span> Not configured
        {/if}
      {/if}
    </span>
  </div>
  
  <button class="btn btn-primary" onclick={testNotification}>
    Send Test Notification
  </button>
</div>

<style>
  .panel {
    background: var(--surface);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 20px;
  }
  
  h3 {
    font-size: 15px;
    font-weight: 600;
    margin-bottom: 16px;
    color: var(--text);
  }
  
  .toggle-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid var(--border-subtle);
  }
  
  .toggle-row:last-of-type {
    border-bottom: none;
  }
  
  .toggle-label {
    font-size: 14px;
    color: var(--text-secondary);
  }
  
  .toggle {
    position: relative;
    width: 44px;
    height: 26px;
    background: var(--surface3);
    border-radius: 13px;
    border: 1px solid var(--border);
    cursor: pointer;
    transition: var(--transition);
  }
  
  .toggle.on {
    background: var(--accent-muted);
    border-color: var(--accent);
  }
  
  .toggle-thumb {
    position: absolute;
    top: 2px;
    left: 2px;
    width: 20px;
    height: 20px;
    background: var(--text-tertiary);
    border-radius: 50%;
    transition: var(--transition);
  }
  
  .toggle.on .toggle-thumb {
    left: 20px;
    background: var(--accent);
  }
  
  hr {
    border: none;
    border-top: 1px solid var(--border-subtle);
    margin: 16px 0;
  }
  
  .status-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }
  
  .status-label {
    font-size: 13px;
    color: var(--text-tertiary);
  }
  
  .status-value {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    font-weight: 500;
  }
  
  .status-value.connected {
    color: var(--success);
  }
  
  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }
  
  .status-dot.success {
    background: var(--success);
  }
  
  .status-dot.error {
    background: var(--danger);
  }
  
  .btn {
    width: 100%;
    padding: 12px;
    font-size: 14px;
    font-weight: 500;
    border-radius: var(--radius);
    transition: var(--transition);
  }
  
  .btn-primary {
    background: var(--accent);
    color: white;
  }
  
  .btn-primary:hover {
    background: var(--accent-hover);
  }
</style>
