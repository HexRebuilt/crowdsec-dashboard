<script>
  import Header from './components/Header.svelte';
  import Stats from './components/Stats.svelte';
  import Tabs from './components/Tabs.svelte';
  import Decisions from './components/Decisions.svelte';
  import Alerts from './components/Alerts.svelte';
  import Timeline from './components/Timeline.svelte';
  import Settings from './components/settings/Index.svelte';
  import Toast from './components/Toast.svelte';
  import { api } from './lib/api.js';
  import {
    status,
    config,
    decisions,
    alerts,
    activeTab,
    isLoading,
    toast,
    appriseStatus,
  } from './lib/stores.js';
  
  let refreshInterval;
  
  async function loadData() {
    isLoading = true;
    try {
      const [statusData, configData, decisionsData, alertsData, appriseData] = await Promise.all([
        api.status(),
        api.config(),
        api.decisions(),
        api.alerts(),
        api.appriseStatus(),
      ]);
      
      status = { ...status, ...statusData };
      config = { ...config, ...configData };
      decisions = decisionsData;
      alerts = alertsData;
      appriseStatus = { ...appriseStatus, ...appriseData };
    } catch (e) {
      console.error('Failed to load data:', e);
    } finally {
      isLoading = false;
    }
  }
  
  $effect(() => {
    loadData();
    refreshInterval = setInterval(loadData, 30000);
    
    return () => {
      if (refreshInterval) clearInterval(refreshInterval);
    };
  });
</script>

<main>
  <Header />
  <Stats />
  <Tabs bind:activeTab />
  
  <div class="content">
    {#if activeTab === 'decisions'}
      <Decisions {decisions} />
    {:else if activeTab === 'alerts'}
      <Alerts {alerts} />
    {:else if activeTab === 'timeline'}
      <Timeline />
    {:else if activeTab === 'settings'}
      <Settings />
    {/if}
  </div>
</main>

{#if toast.show}
  <Toast message={toast.message} type={toast.type} />
{/if}

<style>
  main {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 20px 40px;
  }
  
  .content {
    margin-top: 20px;
  }
</style>
