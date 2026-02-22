<script>
  import { cooldowns, formatSeconds } from '../../lib/stores.js';
  import { api } from '../../lib/api.js';
  import { showToast } from '../../lib/stores.js';
  
  async function loadCooldowns() {
    try {
      cooldowns = await api.cooldowns();
    } catch (e) {
      console.error('Failed to load cooldowns:', e);
    }
  }
  
  async function clearCooldown(ip) {
    try {
      await api.clearCooldown(ip);
      await loadCooldowns();
      showToast(`Cooldown cleared for ${ip}`, 'success');
    } catch (e) {
      showToast('Failed to clear cooldown', 'error');
    }
  }
  
  async function clearAll() {
    try {
      await api.clearCooldown();
      await loadCooldowns();
      showToast('All cooldowns cleared', 'success');
    } catch (e) {
      showToast('Failed to clear cooldowns', 'error');
    }
  }
  
  $effect(() => {
    loadCooldowns();
  });
</script>

<div class="panel">
  <div class="panel-header">
    <h3>IP Cooldowns</h3>
    <button class="btn-clear" onclick={clearAll} disabled={$cooldowns.length === 0}>
      Clear All
    </button>
  </div>
  
  <div class="cooldown-list">
    {#if $cooldowns.length === 0}
      <div class="empty">
        <p>No IPs in cooldown</p>
      </div>
    {:else}
      {#each $cooldowns as cd}
        <div class="cooldown-item">
          <span class="cooldown-ip">{cd.ip}</span>
          <span class="cooldown-time">{formatSeconds(cd.remaining_seconds)}</span>
          <button class="btn-remove" onclick={() => clearCooldown(cd.ip)}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      {/each}
    {/if}
  </div>
  
  <p class="count">{$cooldowns.length} IP{$cooldowns.length !== 1 ? 's' : ''} in cooldown</p>
</div>

<style>
  .panel {
    background: var(--surface);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 20px;
  }
  
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }
  
  h3 {
    font-size: 15px;
    font-weight: 600;
    color: var(--text);
    margin: 0;
  }
  
  .btn-clear {
    font-size: 12px;
    font-weight: 500;
    padding: 6px 12px;
    background: var(--danger-muted);
    color: var(--danger);
    border-radius: var(--radius-sm);
    transition: var(--transition);
  }
  
  .btn-clear:hover:not(:disabled) {
    background: var(--danger);
    color: white;
  }
  
  .btn-clear:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .cooldown-list {
    max-height: 200px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  
  .empty {
    padding: 20px;
    text-align: center;
    color: var(--text-tertiary);
    font-size: 13px;
  }
  
  .cooldown-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    background: var(--surface2);
    border-radius: var(--radius);
    border: 1px solid var(--border-subtle);
  }
  
  .cooldown-ip {
    flex: 1;
    font-family: var(--font-mono);
    font-size: 13px;
    font-weight: 500;
    color: var(--accent);
  }
  
  .cooldown-time {
    font-size: 12px;
    color: var(--text-tertiary);
  }
  
  .btn-remove {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    color: var(--text-tertiary);
    border-radius: var(--radius-sm);
    transition: var(--transition);
  }
  
  .btn-remove:hover {
    background: var(--danger-muted);
    color: var(--danger);
  }
  
  .count {
    font-size: 12px;
    color: var(--text-quaternary);
    margin-top: 12px;
    margin-bottom: 0;
  }
</style>
