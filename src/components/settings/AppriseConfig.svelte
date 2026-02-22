<script>
  import { config, appriseStatus } from '../../lib/stores.js';
  import { api } from '../../lib/api.js';
  import { showToast } from '../../lib/stores.js';
  
  let urls = $state($config.apprise_urls || '');
  
  async function saveUrls() {
    try {
      const result = await api.setAppriseUrls(urls);
      if (result.mode === 'api') {
        showToast('URLs saved to Apprise API', 'success');
      } else {
        config = { ...config, apprise_urls: urls };
        showToast('URLs saved (in-memory)', 'success');
      }
    } catch (e) {
      showToast('Failed to save URLs', 'error');
    }
  }
  
  const urlExamples = [
    { service: 'Telegram', url: 'tgram://TOKEN/CHAT_ID' },
    { service: 'Discord', url: 'discord://ID/TOKEN' },
    { service: 'Gotify', url: 'gotify://host/TOKEN' },
    { service: 'ntfy', url: 'ntfy://host/TOPIC' },
    { service: 'Slack', url: 'slack://TOKEN/CHANNEL' },
    { service: 'Email', url: 'mailto://user:pass@host' },
  ];
</script>

<div class="panel">
  <h3>Apprise URLs</h3>
  
  <div class="mode-indicator">
    <span class="mode-label">Mode:</span>
    <span class="mode-value">
      {#if $appriseStatus.mode === 'api'}
        <span class="badge badge-api">API</span>
        <span class="mode-note">URLs persist in Apprise API</span>
      {:else}
        <span class="badge badge-embedded">Embedded</span>
        <span class="mode-note">URLs reset on restart</span>
      {/if}
    </span>
  </div>
  
  <div class="form-group">
    <label class="form-label">URLs (comma-separated)</label>
    <textarea 
      class="textarea" 
      bind:value={urls} 
      placeholder="tgram://TOKEN/CHAT_ID,gotify://host/TOKEN"
      rows="3"
    ></textarea>
  </div>
  
  <button class="btn btn-primary" onclick={saveUrls}>Save URLs</button>
  
  <div class="url-examples">
    <p class="examples-title">Common URL formats:</p>
    <div class="examples-grid">
      {#each urlExamples as example}
        <div class="example">
          <span class="example-service">{example.service}</span>
          <code class="example-url">{example.url}</code>
        </div>
      {/each}
    </div>
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
  
  .mode-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
    padding: 10px 14px;
    background: var(--surface2);
    border-radius: var(--radius);
  }
  
  .mode-label {
    font-size: 12px;
    color: var(--text-tertiary);
  }
  
  .mode-value {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .badge {
    font-size: 11px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: var(--radius-sm);
  }
  
  .badge-api {
    background: var(--purple-muted);
    color: var(--purple);
  }
  
  .badge-embedded {
    background: var(--accent-muted);
    color: var(--accent);
  }
  
  .mode-note {
    font-size: 11px;
    color: var(--text-quaternary);
  }
  
  .form-group {
    margin-bottom: 16px;
  }
  
  .form-label {
    display: block;
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-tertiary);
    margin-bottom: 8px;
  }
  
  .textarea {
    width: 100%;
    padding: 12px;
    background: var(--bg);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius);
    color: var(--text);
    font-family: var(--font-mono);
    font-size: 13px;
    resize: vertical;
    outline: none;
    transition: var(--transition);
  }
  
  .textarea:focus {
    border-color: var(--accent);
  }
  
  .textarea::placeholder {
    color: var(--text-quaternary);
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
  
  .url-examples {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid var(--border-subtle);
  }
  
  .examples-title {
    font-size: 12px;
    font-weight: 500;
    color: var(--text-tertiary);
    margin-bottom: 10px;
  }
  
  .examples-grid {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  
  .example {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 12px;
  }
  
  .example-service {
    min-width: 70px;
    color: var(--text-secondary);
  }
  
  .example-url {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--accent);
    background: var(--accent-muted);
    padding: 2px 6px;
    border-radius: 4px;
  }
</style>
