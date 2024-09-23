<script>
import axios from 'axios';
import { setNewUploadsAndFinishProcessing } from './store.js';

export let API_BASE_URL;
export let projectId;
export let username;
export let onUploadSuccess;

let files;
let uploadStatus = '';
let errorMessage = '';
let uploadProgress = 0;
let isUploading = false;

async function handleSubmit() {
  if (!files || files.length === 0) {
    uploadStatus = 'No files selected';
    return;
  }
  
  isUploading = true;
  uploadStatus = '';
  errorMessage = '';
  uploadProgress = 0;
  
  const formData = new FormData();
  formData.append('project_id', projectId);
  formData.append('username', username);
  
  for (let i = 0; i < files.length; i++) {
    formData.append('files[]', files[i], files[i].webkitRelativePath || files[i].name);
  }

  try {
    const response = await axios.post(`${API_BASE_URL}/api/upload/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        uploadProgress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
      }
    });
    
    uploadStatus = 'Files uploaded successfully';
    onUploadSuccess(response.data.files);
    setNewUploadsAndFinishProcessing(); // Set new uploads and finish processing
    files = null;
  } catch (error) {
    console.error('Upload error:', error);
    errorMessage = error.response?.data?.error || 'An error occurred during upload';
  } finally {
    isUploading = false;
  }
}
</script>

<div class="file-uploader">
  <h3>Upload Files</h3>
  <div class="upload-controls">
    <label for="file-upload" class="custom-file-upload">
      Choose Files or Folder
    </label>
    <input 
      id="file-upload" 
      type="file" 
      bind:files 
      webkitdirectory directory multiple
      disabled={isUploading}
    >
    <button 
      on:click={handleSubmit} 
      class="upload-button" 
      disabled={isUploading || !files}
    >
      Upload
    </button>
  </div>

  {#if isUploading}
    <div class="progress-bar">
      <div class="progress" style="width: {uploadProgress}%"></div>
    </div>
    <p class="status-message">Uploading... {uploadProgress}%</p>
  {:else if uploadStatus}
    <p class="status-message">{uploadStatus}</p>
  {/if}

  {#if errorMessage}
    <p class="error-message">{errorMessage}</p>
  {/if}
</div>

<style>
  .file-uploader {
    background-color: #f9f9f9;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
  }

  h3 {
    margin-top: 0;
    color: #333;
  }

  .upload-controls {
    display: flex;
    gap: 10px;
    margin-bottom: 15px;
  }

  .custom-file-upload {
    flex: 1;
    display: inline-block;
    padding: 10px;
    cursor: pointer;
    background-color: #4CAF50;
    color: white;
    border-radius: 4px;
    text-align: center;
    transition: background-color 0.3s;
  }

  .custom-file-upload:hover {
    background-color: #45a049;
  }

  input[type="file"] {
    display: none;
  }

  .upload-button {
    padding: 10px 20px;
    background-color: #008CBA;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s;
  }

  .upload-button:hover {
    background-color: #007B9A;
  }

  .upload-button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
  }

  .progress-bar {
    width: 100%;
    background-color: #f0f0f0;
    border-radius: 4px;
    margin-top: 10px;
    overflow: hidden;
  }

  .progress {
    height: 20px;
    background-color: #4CAF50;
    transition: width 0.3s ease-in-out;
  }

  .status-message {
    margin-top: 10px;
    color: #4CAF50;
  }

  .error-message {
    margin-top: 10px;
    color: #f44336;
  }
</style>
