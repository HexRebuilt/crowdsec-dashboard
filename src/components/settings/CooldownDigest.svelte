<script>
  import { config, formatSeconds } from '../../lib/stores.js';
  import { api } from '../../lib/api.js';
  import { showToast } from '../../lib/stores.js';
  
  let cooldown = $state($config.notify_cooldown);
  let digest = $state($config.digest_interval);
  
  async function save() {
    try {
      const result = await api.updateConfig({
        notify_cooldown: parseInt(cooldown) || 0,
        digest_interval: parseInt(digest) || 0,
      });
      config = { ...config, ...result.config };
      showToast('Timing settings saved', 'success');
    } catch (e) {
      showToast('Failed to save', 'error');
    }
  }
</script>

<div class="panel">
  <h3>Cooldown & Digest</h3>
  
  <div class="form-group">
    <div class="form-label">
      <span>IP Cooldown</span>
      <span class="current">{$config.notify_cooldown === 0 ? 'Off' : formatSeconds($config.notify_cooldown)}</span>
    </div>
    <input 
      type="number" 
      class="input" 
      bind:value={cooldown} 
      min="0" 
      placeholder="3600"
    />
    <p class="hint">Don't re-notify same IP for N seconds. Set to 0 to disable.</p>
  </div>
  
  <div class="form-group">
    <div class="form-label">
      <span>Digest Interval</span>
      <span class="current">{$config.digest_interval === 0 ? 'Immediate' : formatSeconds($config.digest_interval)}</span>
    </div>
    <input 
      type="number" 
      class="input" 
      bind:value={digest} 
      min="0" 
      placeholder="0"
    />
    <p class="hint">Batch notifications and send summary every N seconds. 0 = immediate.</p>
  </div>
  
  <button class="btn btn-secondary" onclick={save}>Save Timing</button>
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
  
  .form-group {
    margin-bottom: 16px;
  }
  
  .form-label {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-tertiary);
  }
  
  .current {
    font-size: 13px;
    text-transform: none;
    letter-spacing: 0;
    color: var(--purple);
    font-weight: 600;
  }
  
  .input {
    width: 100%;
    padding: 10px 14px;
    background: var(--bg);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius);
    color: var(--text);
    font-size: 14px;
    outline: none;
    transition: var(--transition);
  }
  
  .input:focus {
    border-color: var(--accent);
  }
  
  .hint {
    font-size: 12px;
    color: var(--text-quaternary);
    margin-top: 6px;
    line-height: 1.5;
  }
  
  .btn {
    width: 100%;
    padding: 12px;
    font-size: 14px;
    font-weight: 500;
    border-radius: var(--radius);
    transition: var(--transition);
  }
  
  .btn-secondary {
    background: var(--surface2);
    color: var(--text);
    border: 1px solid var(--border-subtle);
  }
  
  .btn-secondary:hover {
    background: var(--surface3);
    border-color: var(--border);
  }
</style>
