<script>
  import { config } from '../../lib/stores.js';
  import { api } from '../../lib/api.js';
  import { showToast } from '../../lib/stores.js';
  
  let alertThreshold = $state($config.alert_threshold);
  let banThreshold = $state($config.ban_threshold);
  
  async function save() {
    try {
      const result = await api.updateConfig({
        alert_threshold: parseInt(alertThreshold) || 0,
        ban_threshold: parseInt(banThreshold) || 0,
      });
      config = { ...config, ...result.config };
      showToast('Thresholds saved', 'success');
    } catch (e) {
      showToast('Failed to save', 'error');
    }
  }
</script>

<div class="panel">
  <h3>Thresholds</h3>
  
  <div class="form-group">
    <div class="form-label">
      <span>Alert Threshold</span>
      <span class="current">{$config.alert_threshold === 0 ? 'Always' : `≥ ${$config.alert_threshold}`}</span>
    </div>
    <input 
      type="number" 
      class="input" 
      bind:value={alertThreshold} 
      min="0" 
      placeholder="5"
    />
    <p class="hint">Notify only when event count ≥ N. Set to 0 to always notify.</p>
  </div>
  
  <div class="form-group">
    <div class="form-label">
      <span>Ban Threshold</span>
      <span class="current">{$config.ban_threshold === 0 ? 'Always' : `≥ ${$config.ban_threshold}`}</span>
    </div>
    <input 
      type="number" 
      class="input" 
      bind:value={banThreshold} 
      min="0" 
      placeholder="0"
    />
    <p class="hint">Notify ban only if associated alert had ≥ N events.</p>
  </div>
  
  <button class="btn btn-secondary" onclick={save}>Save Thresholds</button>
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
    color: var(--accent);
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
