<script>
  import NotificationToggle from './NotificationToggle.svelte';
  import Thresholds from './Thresholds.svelte';
  import CooldownDigest from './CooldownDigest.svelte';
  import ConnectionOverride from './ConnectionOverride.svelte';
  import AppriseConfig from './AppriseConfig.svelte';
  import CooldownList from './CooldownList.svelte';
</script>

<div class="settings-grid">
  <NotificationToggle />
  <Thresholds />
  <CooldownDigest />
  <ConnectionOverride />
  <AppriseConfig />
  <CooldownList />
</div>

<style>
  .settings-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 20px;
  }
</style>
