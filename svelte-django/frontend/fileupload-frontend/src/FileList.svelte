<script>
  export let files = [];
  export let onFileSelect;

  function handleFileClick(file) {
    onFileSelect(file);
  }

  function getFileName(file) {
    return file.name || file.file.split('/').pop() || 'Unnamed File';
  }
</script>

<div class="file-list">
  <h2>Files</h2>
  {#if files.length === 0}
    <p>No files uploaded yet.</p>
  {:else}
    <ul>
      {#each files as file}
        <li>
          <button on:click={() => handleFileClick(file)}>
            {getFileName(file)}
          </button>
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .file-list {
    background-color: #ffffff;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    max-height: 400px;
    overflow-y: auto;
  }

  h2 {
    margin-top: 0;
    color: #333;
    position: sticky;
    top: 0;
    background-color: #ffffff;
    padding: 10px 0;
    z-index: 1;
  }

  ul {
    list-style-type: none;
    padding: 0;
    margin: 0;
  }

  li {
    margin-bottom: 10px;
  }

  button {
    width: 100%;
    text-align: left;
    padding: 10px;
    background-color: #f0f0f0;
    border: 1px solid #ddd;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  button:hover {
    background-color: #e0e0e0;
  }
</style>
