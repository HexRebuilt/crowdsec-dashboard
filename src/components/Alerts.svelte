<script>
  import { config, formatTime } from '../lib/stores.js';
  
  let { alerts } = $props();
  let searchQuery = $state('');
  
  let filteredAlerts = $derived(
    searchQuery 
      ? alerts.filter(a => 
          JSON.stringify(a).toLowerCase().includes(searchQuery.toLowerCase())
        )
      : alerts
  );
  
  function getSourceIp(alert) {
    return alert.source?.ip || alert.source?.value || '?';
  }
</script>

<div class="panel">
  <div class="panel-header">
    <input 
      type="text" 
      class="search-input" 
      placeholder="Search IP, scenario..."
      bind:value={searchQuery}
    />
    <span class="count">{filteredAlerts.length} alerts</span>
  </div>
  
  <div class="table-container">
    {#if filteredAlerts.length === 0}
      <div class="empty">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
          <polyline points="22 4 12 14.01 9 11.01"/>
        </svg>
        <p>No alerts in last 2 hours</p>
      </div>
    {:else}
      <table>
        <thead>
          <tr>
            <th>#ID</th>
            <th>Source IP</th>
            <th>Scenario</th>
            <th>Events</th>
            <th>Machine</th>
            <th>When</th>
          </tr>
        </thead>
        <tbody>
          {#each filteredAlerts as a}
            {@const ip = getSourceIp(a)}
            {@const count = a.events_count || 0}
            {@const threshold = $config.alert_threshold}
            {@const belowThreshold = threshold > 0 && count < threshold}
            <tr class:dimmed={belowThreshold}>
              <td class="dim">#{a.id}</td>
              <td class="ip">{ip}</td>
              <td class="scenario">{a.scenario || '—'}</td>
              <td>
                <span class="count" class:warning={count > 20} class:dim={belowThreshold}>
                  {count}
                  {#if belowThreshold}
                    <span class="threshold-note">(&lt; {threshold})</span>
                  {/if}
                </span>
              </td>
              <td class="dim">{(a.machine_id || '').split('.')[0]}</td>
              <td class="dim">{formatTime(a.start_at)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
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
    gap: 12px;
    padding: 16px;
    border-bottom: 1px solid var(--border-subtle);
  }
  
  .search-input {
    flex: 1;
    padding: 10px 14px;
    background: var(--bg);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius);
    color: var(--text);
    font-size: 14px;
    outline: none;
    transition: var(--transition);
  }
  
  .search-input:focus {
    border-color: var(--accent);
  }
  
  .search-input::placeholder {
    color: var(--text-quaternary);
  }
  
  .count-label {
    font-size: 13px;
    color: var(--text-tertiary);
    white-space: nowrap;
  }
  
  .table-container {
    overflow-x: auto;
  }
  
  table {
    width: 100%;
    border-collapse: collapse;
  }
  
  th {
    text-align: left;
    padding: 12px 16px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-tertiary);
    background: var(--surface2);
    border-bottom: 1px solid var(--border-subtle);
  }
  
  td {
    padding: 12px 16px;
    font-size: 13px;
    border-bottom: 1px solid var(--border-subtle);
    vertical-align: middle;
  }
  
  tr:last-child td {
    border-bottom: none;
  }
  
  tr:hover td {
    background: rgba(255, 255, 255, 0.02);
  }
  
  tr.dimmed {
    opacity: 0.5;
  }
  
  .ip {
    font-family: var(--font-mono);
    font-weight: 600;
    color: var(--accent);
  }
  
  .scenario {
    color: var(--warning);
  }
  
  .dim {
    color: var(--text-tertiary);
  }
  
  .count {
    font-weight: 600;
    color: var(--warning);
  }
  
  .count.warning {
    color: var(--danger);
  }
  
  .count.dim {
    color: var(--text-tertiary);
  }
  
  .threshold-note {
    font-size: 11px;
    font-weight: 400;
    margin-left: 4px;
    color: var(--text-quaternary);
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
