<script>
  import { api } from '../lib/api.js';
  import { events, eventFilter, timeAgo } from '../lib/stores.js';
  
  let filters = [
    { id: '', label: 'All' },
    { id: 'ban', label: 'Ban' },
    { id: 'alert', label: 'Alert' },
    { id: 'suppressed', label: 'Suppressed' },
  ];
  
  async function loadEvents() {
    try {
      const data = await api.events($eventFilter);
      events = data;
    } catch (e) {
      console.error('Failed to load events:', e);
    }
  }
  
  $effect(() => {
    loadEvents();
  });
</script>

<div class="panel">
  <div class="panel-header">
    <div class="filters">
      {#each filters as filter}
        <button 
          class="filter-btn" 
          class:active={$eventFilter === filter.id}
          onclick={() => eventFilter = filter.id}
        >
          {filter.label}
        </button>
      {/each}
    </div>
    <button class="btn btn-ghost" onclick={loadEvents}>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M23 4v6h-6"/>
        <path d="M1 20v-6h6"/>
        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
      </svg>
    </button>
  </div>
  
  <div class="timeline">
    {#if $events.length === 0}
      <div class="empty">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="10"/>
          <polyline points="12 6 12 12 16 14"/>
        </svg>
        <p>No events yet</p>
      </div>
    {:else}
      {#each $events as event}
        <div class="event event-{event.type}">
          <span class="event-time">{timeAgo(event.time)}</span>
          <span class="event-message">{event.msg}</span>
        </div>
      {/each}
    {/if}
  </div>
</div>

<style>
  .panel {
    background: var(--surface);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    overflow: hidden;
  }
  
  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 16px;
    border-bottom: 1px solid var(--border-subtle);
  }
  
  .filters {
    display: flex;
    gap: 4px;
  }
  
  .filter-btn {
    padding: 6px 12px;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-secondary);
    background: var(--surface2);
    border-radius: var(--radius-sm);
    transition: var(--transition);
  }
  
  .filter-btn:hover {
    color: var(--text);
    background: var(--surface3);
  }
  
  .filter-btn.active {
    color: var(--text);
    background: var(--accent-muted);
  }
  
  .btn-ghost {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 8px;
    color: var(--text-secondary);
    border-radius: var(--radius);
    transition: var(--transition);
  }
  
  .btn-ghost:hover {
    background: var(--surface2);
    color: var(--text);
  }
  
  .timeline {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 600px;
    overflow-y: auto;
  }
  
  .event {
    display: flex;
    gap: 12px;
    padding: 12px 14px;
    background: var(--surface2);
    border-radius: var(--radius);
    border-left: 3px solid var(--text-tertiary);
    font-size: 13px;
    animation: slideUp 0.2s ease-out;
  }
  
  .event-ban {
    border-left-color: var(--danger);
  }
  
  .event-alert {
    border-left-color: var(--warning);
  }
  
  .event-unban {
    border-left-color: var(--success);
  }
  
  .event-suppressed {
    border-left-color: var(--text-quaternary);
    opacity: 0.6;
  }
  
  .event-time {
    font-size: 11px;
    font-weight: 500;
    color: var(--text-quaternary);
    white-space: nowrap;
    min-width: 50px;
    padding-top: 2px;
  }
  
  .event-message {
    flex: 1;
    color: var(--text-secondary);
  }
  
  .empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 20px;
    color: var(--text-tertiary);
  }
  
  .empty svg {
    margin-bottom: 16px;
    opacity: 0.5;
  }
  
  .empty p {
    font-size: 15px;
  }
</style>
