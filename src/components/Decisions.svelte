<script>
  import { api } from '../lib/api.js';
  import { showToast, formatTime } from '../lib/stores.js';
  
  let { decisions } = $props();
  let searchQuery = $state('');
  
  let filteredDecisions = $derived(
    searchQuery 
      ? decisions.filter(d => 
          JSON.stringify(d).toLowerCase().includes(searchQuery.toLowerCase())
        )
      : decisions
  );
  
  async function unban(id) {
    if (!confirm(`Unban decision #${id}?`)) return;
    try {
      const result = await api.unban(id);
      if (result.ok) {
        showToast('IP unbanned successfully', 'success');
      } else {
        showToast('Failed to unban', 'error');
      }
    } catch (e) {
      showToast('Failed to unban', 'error');
    }
  }
  
  function getTypeClass(type) {
    switch (type) {
      case 'ban': return 'danger';
      case 'captcha': return 'warning';
      default: return 'default';
    }
  }
</script>

<div class="panel">
  <div class="panel-header">
    <input 
      type="text" 
      class="search-input" 
      placeholder="Search IP, scenario, type..."
      bind:value={searchQuery}
    />
    <span class="count">{filteredDecisions.length} bans</span>
  </div>
  
  <div class="table-container">
    {#if filteredDecisions.length === 0}
      <div class="empty">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M9 12l2 2 4-4"/>
          <circle cx="12" cy="12" r="10"/>
        </svg>
        <p>No active bans</p>
      </div>
    {:else}
      <table>
        <thead>
          <tr>
            <th>IP / Value</th>
            <th>Scenario</th>
            <th>Type</th>
            <th>Origin</th>
            <th>Expires</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {#each filteredDecisions as d}
            <tr>
              <td class="ip">{d.value || '?'}</td>
              <td class="scenario">{d.scenario || '—'}</td>
              <td>
                <span class="badge badge-{getTypeClass(d.type)}">{d.type || '—'}</span>
              </td>
              <td class="dim">{d.origin || '—'}</td>
              <td class="dim">{formatTime(d.until)}</td>
              <td>
                <button class="btn btn-sm btn-danger" onclick={() => unban(d.id)}>Unban</button>
              </td>
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
  
  .count {
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
  
  .badge {
    display: inline-block;
    padding: 4px 8px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    border-radius: var(--radius-sm);
  }
  
  .badge-danger {
    background: var(--danger-muted);
    color: var(--danger);
  }
  
  .badge-warning {
    background: var(--warning-muted);
    color: var(--warning);
  }
  
  .badge-default {
    background: var(--accent-muted);
    color: var(--accent);
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
  
  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 6px 12px;
    font-size: 12px;
    font-weight: 500;
    border-radius: var(--radius-sm);
    transition: var(--transition);
  }
  
  .btn-sm {
    padding: 4px 10px;
    font-size: 11px;
  }
  
  .btn-danger {
    background: var(--danger-muted);
    color: var(--danger);
  }
  
  .btn-danger:hover {
    background: var(--danger);
    color: white;
  }
</style>
