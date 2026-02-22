<script>
  const tabs = [
    { id: 'decisions', label: 'Decisions', icon: 'ban' },
    { id: 'alerts', label: 'Alerts', icon: 'alert' },
    { id: 'timeline', label: 'Timeline', icon: 'timeline' },
    { id: 'settings', label: 'Settings', icon: 'settings' },
  ];
  
  let { activeTab = $bindable() } = $props();
</script>

<div class="tabs">
  {#each tabs as tab}
    <button 
      class="tab" 
      class:active={$activeTab === tab.id}
      onclick={() => activeTab = tab.id}
    >
      {tab.label}
    </button>
  {/each}
</div>

<style>
  .tabs {
    display: flex;
    gap: 4px;
    padding: 4px;
    background: var(--surface);
    border-radius: var(--radius-lg);
    border: 1px solid var(--border-subtle);
    margin-bottom: 20px;
  }
  
  .tab {
    flex: 1;
    padding: 10px 16px;
    font-size: 14px;
    font-weight: 500;
    color: var(--text-secondary);
    border-radius: var(--radius);
    transition: var(--transition);
  }
  
  .tab:hover {
    color: var(--text);
    background: var(--surface2);
  }
  
  .tab.active {
    color: var(--text);
    background: var(--surface3);
  }
</style>
