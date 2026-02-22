<script>
  import { status, appriseStatus } from '../../lib/stores.js';
  import { api } from '../../lib/api.js';
  import { showToast } from '../../lib/stores.js';
  
  let testingCrowdsec = $state(false);
  let testingApprise = $state(false);
  let crowdsecLatency = $state(null);
  let appriseLatency = $state(null);
  
  async function testCrowdsec() {
    testingCrowdsec = true;
    crowdsecLatency = null;
    const start = Date.now();
    try {
      await api.status();
      crowdsecLatency = Date.now() - start;
      showToast('CrowdSec connected', 'success');
    } catch (e) {
      showToast('CrowdSec connection failed', 'error');
    }
    testingCrowdsec = false;
  }
  
  async function testApprise() {
    testingApprise = true;
    appriseLatency = null;
    const start = Date.now();
    try {
      await api.appriseStatus();
      appriseLatency = Date.now() - start;
      showToast('Apprise connected', 'success');
    } catch (e) {
      showToast('Apprise connection failed', 'error');
    }
    testingApprise = false;
  }
</script>

<div class="panel">
  <h3>Connections</h3>
  
  <div class="connection-group">
    <div class="connection-header">
      <span class="connection-label">CrowdSec LAPI</span>
      <span class="connection-status" class:connected={crowdsecLatency !== null}>
        {#if crowdsecLatency !== null}
          <span class="status-dot success"></span> {crowdsecLatency}ms
        {:else}
          <span class="status-dot"></span> Not tested
        {/if}
      </span>
    </div>
    <div class="connection-url">
      <code>{$status.crowdsec_url}</code>
    </div>
    <button class="btn btn-sm" onclick={testCrowdsec} disabled={testingCrowdsec}>
      {#if testingCrowdsec}
        <span class="spinner"></span>
      {:else}
        Test
      {/if}
    </button>
  </div>
  
  <hr />
  
  <div class="connection-group">
    <div class="connection-header">
      <span class="connection-label">Apprise</span>
      <span class="connection-status" class:connected={appriseLatency !== null}>
        {#if $appriseStatus.mode === 'api'}
          {#if appriseLatency !== null}
            <span class="status-dot success"></span> {appriseLatency}ms
          {:else}
            <span class="status-dot"></span> Not tested
          {/if}
        {:else}
          <span class="badge-embedded">Embedded</span>
        {/if}
      </span>
    </div>
    
    {#if $appriseStatus.mode === 'api'}
      <div class="connection-url">
        <code>{$appriseStatus.api_url}</code>
      </div>
      <div class="connection-detail">
        <span class="detail-label">Config Key:</span>
        <code>{$appriseStatus.config_key}</code>
      </div>
      <button class="btn btn-sm" onclick={testApprise} disabled={testingApprise}>
        {#if testingApprise}
          <span class="spinner"></span>
        {:else}
          Test
        {/if}
      </button>
    {:else}
      <p class="embedded-note">
        Using embedded Apprise library. URLs are stored in memory.
      </p>
    {/if}
  </div>
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
  
  .connection-group {
    margin-bottom: 8px;
  }
  
  .connection-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }
  
  .connection-label {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-secondary);
  }
  
  .connection-status {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: var(--text-tertiary);
  }
  
  .connection-status.connected {
    color: var(--success);
  }
  
  .connection-url {
    background: var(--bg);
    padding: 10px 14px;
    border-radius: var(--radius);
    border: 1px solid var(--border-subtle);
    margin-bottom: 8px;
  }
  
  .connection-url code {
    font-family: var(--font-mono);
    font-size: 13px;
    color: var(--text);
  }
  
  .connection-detail {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    font-size: 12px;
  }
  
  .detail-label {
    color: var(--text-tertiary);
  }
  
  .connection-detail code {
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--purple);
    background: var(--purple-muted);
    padding: 2px 6px;
    border-radius: 4px;
  }
  
  .status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--text-quaternary);
  }
  
  .status-dot.success {
    background: var(--success);
  }
  
  .badge-embedded {
    font-size: 11px;
    font-weight: 600;
    padding: 3px 8px;
    background: var(--surface3);
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
  }
  
  .embedded-note {
    font-size: 12px;
    color: var(--text-tertiary);
    padding: 10px;
    background: var(--surface2);
    border-radius: var(--radius);
    border: 1px dashed var(--border-subtle);
  }
  
  hr {
    border: none;
    border-top: 1px solid var(--border-subtle);
    margin: 16px 0;
  }
  
  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
    border-radius: var(--radius);
    transition: var(--transition);
    background: var(--surface2);
    color: var(--text-secondary);
    border: 1px solid var(--border-subtle);
  }
  
  .btn:hover:not(:disabled) {
    background: var(--surface3);
    color: var(--text);
  }
  
  .btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  .btn-sm {
    padding: 6px 12px;
    font-size: 12px;
  }
  
  .spinner {
    width: 12px;
    height: 12px;
    border: 2px solid var(--text-tertiary);
    border-top-color: transparent;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
</style>
