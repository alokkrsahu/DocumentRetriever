<script>
import { createEventDispatcher } from 'svelte';
import axios from 'axios';
import { currentProject, currentUser } from './store.js';

export let API_BASE_URL;

const dispatch = createEventDispatcher();

let username = '';
let projectName = '';
let existingProjects = [];
let selectedProject = '';
let error = '';
let loading = false;
let users = [];

async function getUsers() {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/users/`);
    users = response.data.usernames;
  } catch (err) {
    console.error('Error fetching users:', err);
    error = 'Failed to fetch users. Please try again.';
  }
}

async function getExistingProjects() {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/projects/`);
    existingProjects = response.data.projects;
  } catch (err) {
    console.error('Error fetching projects:', err);
    error = 'Failed to fetch existing projects. Please try again.';
  }
}

async function handleSubmit() {
  if (!username) {
    error = 'Please select a username.';
    return;
  }

  if (!projectName && !selectedProject) {
    error = 'Please enter a new project name or select an existing project.';
    return;
  }

  loading = true;
  error = '';

  try {
    console.log('Creating/selecting project...');
    const response = await axios.post(`${API_BASE_URL}/api/projects/`, {
      username,
      project_name: projectName || selectedProject
    });

    console.log('API response:', response.data);

    const projectData = {
      id: response.data.project_id,
      name: projectName || selectedProject
    };

    console.log('Setting currentProject:', projectData);
    currentProject.set(projectData);

    console.log('Setting currentUser:', { username });
    currentUser.set({ username });

    console.log('Dispatching projectSelected event');
    dispatch('projectSelected', {
      username,
      projectName: projectName || selectedProject,
      projectId: response.data.project_id
    });
  } catch (err) {
    console.error('Error creating/selecting project:', err);
    error = 'Failed to create/select project. Please try again.';
  } finally {
    loading = false;
  }
}

getUsers();
getExistingProjects();
</script>


  
  <div class="project-selector">
    <h2>Welcome to File Manager</h2>
    
    <div class="form-group">
      <label for="username">Username:</label>
      <select id="username" bind:value={username}>
        <option value="">Select a user</option>
        {#each users as user}
          <option value={user}>{user}</option>
        {/each}
      </select>
    </div>
    
    <div class="form-group">
      <label for="projectName">New Project Name:</label>
      <input type="text" id="projectName" bind:value={projectName} placeholder="Enter new project name">
    </div>
    
    <h3>Or select an existing project:</h3>
    <div class="form-group">
      <select bind:value={selectedProject}>
        <option value="">Select a project</option>
        {#each existingProjects as project}
          <option value={project.name}>{project.name}</option>
        {/each}
      </select>
    </div>
    
    {#if error}
      <p class="error">{error}</p>
    {/if}
    
    <button class="btn btn-primary" on:click={handleSubmit} disabled={loading}>
      {loading ? 'Loading...' : 'Start'}
    </button>
  </div>
  
  <style>
    .project-selector {
      max-width: 400px;
      margin: 0 auto;
      padding: 20px;
      background-color: #f9f9f9;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    h2, h3 {
      color: #333;
      margin-bottom: 20px;
    }
    
    .form-group {
      margin-bottom: 20px;
    }
    
    label {
      display: block;
      margin-bottom: 5px;
      color: #666;
    }
    
    input, select {
      width: 100%;
      padding: 10px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 16px;
    }
    
    .btn {
      width: 100%;
      padding: 10px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 16px;
      transition: background-color 0.3s;
    }
    
    .btn-primary {
      background-color: #4CAF50;
      color: white;
    }
    
    .btn-primary:hover {
      background-color: #45a049;
    }
    
    .btn:disabled {
      background-color: #ccc;
      cursor: not-allowed;
    }
    
    .error {
      color: #d32f2f;
      margin-top: 10px;
    }
  </style>