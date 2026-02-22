<script>
  let { message, type = 'success' } = $props();
</script>

<div class="toast toast-{type}" role="alert">
  <span class="toast-icon">
    {#if type === 'success'}
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="20 6 9 17 4 12"/>
      </svg>
    {:else}
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <line x1="15" y1="9" x2="9" y2="15"/>
        <line x1="9" y1="9" x2="15" y2="15"/>
      </svg>
    {/if}
  </span>
  <span class="toast-message">{message}</span>
</div>

<style>
  .toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 16px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    font-size: 14px;
    font-weight: 500;
    box-shadow: var(--shadow-lg);
    animation: slideUp 0.2s ease-out;
    z-index: 1000;
  }
  
  .toast-success {
    border-color: var(--success);
  }
  
  .toast-success .toast-icon {
    color: var(--success);
  }
  
  .toast-error {
    border-color: var(--danger);
  }
  
  .toast-error .toast-icon {
    color: var(--danger);
  }
  
  .toast-icon {
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .toast-message {
    color: var(--text);
  }
</style>
