<script>
  import { onMount } from 'svelte';
  import axios from 'axios';
  import { API_BASE_URL } from './config.js';
  import { setNewUploadsAndFinishProcessing } from './store.js';  // Import the function from the store

  export let projectId;
  export let username;
  export let files;
  export let onFilesChanged;

  let newFiles;
  let isUploading = false;
  let uploadProgress = 0;
  let errorMessage = '';
  let successMessage = '';

  async function handleFileUpload() {
    if (!newFiles || newFiles.length === 0) {
      errorMessage = 'No files selected';
      return;
    }

    if (!projectId || !username) {
      errorMessage = 'Project ID and username are required';
      return;
    }

    isUploading = true;
    errorMessage = '';
    successMessage = '';
    uploadProgress = 0;

    const formData = new FormData();
    formData.append('project_id', projectId);
    formData.append('username', username);

    for (let i = 0; i < newFiles.length; i++) {
      formData.append('files[]', newFiles[i], newFiles[i].name);
    }

    try {
      await axios.post(`${API_BASE_URL}/api/upload/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          uploadProgress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        }
      });

      newFiles = null;
      successMessage = 'Files uploaded successfully';
      setNewUploadsAndFinishProcessing();  // Call this function after successful upload
      onFilesChanged();
    } catch (error) {
      console.error('Upload error:', error);
      errorMessage = error.response?.data?.error || 'An error occurred during upload';
    } finally {
      isUploading = false;
    }
  }

  async function handleFileDelete(fileId) {
    try {
      await axios.delete(`${API_BASE_URL}/api/delete-file/`, {
        params: { file_id: fileId }
      });
      successMessage = 'File deleted successfully';
      onFilesChanged();
    } catch (error) {
      console.error('Delete error:', error);
      errorMessage = error.response?.data?.error || 'An error occurred while deleting the file';
    }
  }
</script>

<div class="manage-documents">
  <h2>Manage Documents</h2>

  <div class="upload-section">
    <input type="file" bind:files={newFiles} multiple>
    <button on:click={handleFileUpload} disabled={isUploading}>Upload Files</button>
  </div>

  {#if isUploading}
    <div class="progress-bar">
      <div class="progress" style="width: {uploadProgress}%"></div>
    </div>
    <p>Uploading... {uploadProgress}%</p>
  {/if}

  {#if errorMessage}
    <p class="error-message">{errorMessage}</p>
  {/if}

  {#if successMessage}
    <p class="success-message">{successMessage}</p>
  {/if}

  <h3>Project Files</h3>
  <ul class="file-list">
    {#each files as file}
      <li>
        <button class="delete-btn" on:click={() => handleFileDelete(file.id)}>Delete</button>
        <span class="file-name">{file.file.split('/').pop()}</span>
      </li>
    {/each}
  </ul>
</div>

<style>
  .manage-documents {
    padding: 20px;
    background-color: #f5f5f5;
    border-radius: 8px;
  }

  h2, h3 {
    color: #333;
  }

  .upload-section {
    margin-bottom: 20px;
  }

  .progress-bar {
    width: 100%;
    background-color: #e0e0e0;
    border-radius: 4px;
    overflow: hidden;
    margin-top: 10px;
  }

  .progress {
    height: 20px;
    background-color: #4CAF50;
    transition: width 0.3s ease-in-out;
  }

  .error-message {
    color: #f44336;
  }

  .success-message {
    color: #4CAF50;
  }

  .file-list {
    list-style-type: none;
    padding: 0;
  }

  .file-list li {
    display: flex;
    align-items: center;
    padding: 10px;
    background-color: #fff;
    margin-bottom: 5px;
    border-radius: 4px;
  }

  .delete-btn {
    padding: 5px 10px;
    background-color: #f44336;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    margin-right: 10px;
  }

  .delete-btn:hover {
    background-color: #d32f2f;
  }

  .file-name {
    flex-grow: 1;
    word-break: break-all;
  }
</style>
