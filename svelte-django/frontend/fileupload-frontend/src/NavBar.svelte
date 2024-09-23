<script>
  import { createEventDispatcher } from 'svelte';
  import { currentView } from './store.js';

  export let isCollapsed = false;
  const dispatch = createEventDispatcher();

  function setView(view) {
      currentView.set(view);
  }

  function handleLogout() {
      dispatch('logout');
  }
</script>

<nav class:collapsed={isCollapsed}>
  <button on:click={() => dispatch('toggleMenu')} class="toggle-btn">
      {isCollapsed ? '≡' : '×'}
  </button>
  <ul>
      {#each ['tender-documents', 'manage-documents', 'call-off-discussion', 'bid-writing', 'online-members'] as view}
          <li>
              <button on:click={() => setView(view)} class:active={$currentView === view}>
                  {#if !isCollapsed}<span>{view.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}</span>{/if}
              </button>
          </li>
      {/each}
  </ul>
  <button on:click={handleLogout} class="logout-btn">
      {#if !isCollapsed}<span>Logout</span>{/if}
  </button>
</nav>

<style>
  nav {
      width: 250px;
      background-color: #333;
      color: white;
      transition: width 0.3s;
      overflow: hidden;
      display: flex;
      flex-direction: column;
  }

  nav.collapsed {
      width: 60px;
  }

  .toggle-btn {
      width: 100%;
      padding: 15px;
      background: none;
      border: none;
      color: white;
      font-size: 24px;
      cursor: pointer;
      text-align: left;
  }

  ul {
      list-style-type: none;
      padding: 0;
      margin: 0;
      flex-grow: 1;
  }

  li {
      padding: 0;
  }

  button {
      display: flex;
      align-items: center;
      justify-content: flex-start;
      width: 100%;
      padding: 15px;
      background: none;
      border: none;
      color: white;
      cursor: pointer;
      text-align: left;
      font-size: 16px;
      transition: background-color 0.3s;
  }

  button:hover,
  button.active {
      background-color: #444;
  }

  .logout-btn {
      width: 100%;
      padding: 15px;
      background: #d32f2f;
      border: none;
      color: white;
      cursor: pointer;
      text-align: center;
      font-size: 16px;
      transition: background-color 0.3s;
  }

  .logout-btn:hover {
      background-color: #b71c1c;
  }

  @media (max-width: 768px) {
      nav {
          width: 100%;
          height: auto;
      }

      nav.collapsed {
          height: 60px;
      }
  }
</style>
