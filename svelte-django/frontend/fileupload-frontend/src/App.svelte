<script>
    import { onMount } from 'svelte';
    import axios from 'axios';
    import { currentProject, currentUser, uploadedFiles, selectedFile, currentView, callOffResults, resetState } from './store.js';
    import ProjectSelector from './ProjectSelector.svelte';
    import FileUploader from './FileUploader.svelte';
    import FileViewer from './FileViewer.svelte';
    import ManageDocuments from './ManageDocuments.svelte';
    import OnlineMembers from './OnlineMembers.svelte';
    import CallOffDiscussion from './CallOffDiscussion.svelte';
    import NavBar from './NavBar.svelte';
    import { API_BASE_URL } from './config.js';
  
    let projects = [];
    let users = [];
    let isMenuCollapsed = false;
    let debugInfo = { currentProject: null, currentUser: null, currentView: null, isMenuCollapsed: false };
    let showDebugInfo = false; // Debug window hidden by default
  
    onMount(async () => {
      console.log("App.svelte mounted");
      await fetchProjects();
      await fetchUsers();
      const storedProjectId = localStorage.getItem('selectedProject');
      const storedUsername = localStorage.getItem('selectedUsername');
      if (storedProjectId && storedUsername) {
        await loadProject(storedProjectId);
        await loadUser(storedUsername);
      }
  
      // Add event listener for debug toggle
      window.addEventListener('keydown', toggleDebugInfo);
      return () => {
        window.removeEventListener('keydown', toggleDebugInfo);
      };
    });
  
    function toggleDebugInfo(event) {
      if (event.key === 'd' && event.ctrlKey) {
        showDebugInfo = !showDebugInfo;
      }
    }
  
    async function fetchProjects() {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/projects/`);
        projects = response.data.projects;
      } catch (error) {
        console.error("Error fetching projects:", error);
      }
    }
  
    async function fetchUsers() {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/users/`);
        users = response.data.usernames.map(username => ({ username }));
      } catch (error) {
        console.error("Error fetching users:", error);
      }
    }
  
    async function loadProject(projectId) {
      try {
        const project = projects.find(p => p.id === parseInt(projectId));
        if (project) {
          currentProject.set(project);
          await loadProjectFiles();
        } else {
          console.error("Project not found:", projectId);
          currentProject.set(null);
          localStorage.removeItem('selectedProject');
        }
      } catch (error) {
        console.error("Error loading project:", error);
      }
    }
  
    async function loadUser(username) {
      try {
        const user = users.find(u => u.username === username);
        if (user) {
          currentUser.set(user);
        } else {
          console.error("User not found:", username);
          currentUser.set(null);
          localStorage.removeItem('selectedUsername');
        }
      } catch (error) {
        console.error("Error loading user:", error);
      }
    }
  
    async function handleProjectSelected(event) {
      console.log('Project selected event received:', event.detail);
      const { projectId, username, projectName } = event.detail;
      
      if (!projectId) {
        console.error('Invalid projectId received');
        return;
      }
  
      currentProject.set({ id: projectId, name: projectName });
      currentUser.set({ username });
      localStorage.setItem('selectedProject', projectId);
      localStorage.setItem('selectedUsername', username);
      
      try {
        await createProjectJSON();
        await loadProjectFiles();
        currentView.set('tender-documents');
  
        console.log('Project selection complete. Current project:', $currentProject);
        console.log('Current user:', $currentUser);
        console.log('Current view:', $currentView);
      } catch (error) {
        console.error('Error during project selection:', error);
      }
    }
  
    async function loadProjectFiles() {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/project-files/`, {
          params: { project_id: $currentProject.id }
        });
        uploadedFiles.set(response.data.files);
      } catch (error) {
        console.error('Error loading project files:', error);
      }
    }
  
    async function createProjectJSON() {
      if (!$currentProject || !$currentUser) {
        console.error("Cannot create project JSON: Project or User not selected");
        return;
      }
      try {
        const response = await axios.post(`${API_BASE_URL}/api/create-project-json/`, {
          username: $currentUser.username,
          project_id: $currentProject.id
        });
        console.log("Project JSON created successfully:", response.data);
      } catch (error) {
        console.error('Error creating project JSON:', error);
      }
    }
  
    function handleUploadSuccess() {
      loadProjectFiles();
    }
  
    function toggleMenu() {
      isMenuCollapsed = !isMenuCollapsed;
      console.log('Menu toggled. isMenuCollapsed:', isMenuCollapsed);
    }
  
    function handleLogout() {
      resetState();
      currentProject.set(null);
      currentUser.set(null);
      localStorage.removeItem('selectedProject');
      localStorage.removeItem('selectedUsername');
      console.log('User logged out');
    }
  
    function handleFilesChanged() {
      loadProjectFiles();
    }
  
    async function handleCallOffDiscussion() {
      if (!$currentProject || !$currentUser) {
        console.error("Cannot call off discussion: Project or User not selected");
        return;
      }
      try {
        const response = await axios.post(`${API_BASE_URL}/api/call-off-discussion/`, {
          project_name: $currentProject.name,
          username: $currentUser.username
        });
        callOffResults.set(response.data.results);
      } catch (error) {
        console.error('Error processing call off discussion:', error);
      }
    }
  
    $: {
      debugInfo = {
        currentProject: $currentProject,
        currentUser: $currentUser,
        currentView: $currentView,
        isMenuCollapsed: isMenuCollapsed
      };
      console.log('State updated:', debugInfo);
    }
  
    $: if ($currentView === 'call-off-discussion') {
      handleCallOffDiscussion();
    }
  </script>
  
  <svelte:window on:keydown={toggleDebugInfo}/>
  
  <main class:project-selected={$currentProject}>
    {#if showDebugInfo}
      <pre class="debug-info">DEBUG: {JSON.stringify(debugInfo, null, 2)}</pre>
    {/if}
  
    {#if !$currentProject || !$currentUser}
      <div class="project-selector-container">
        <ProjectSelector API_BASE_URL={API_BASE_URL} on:projectSelected={handleProjectSelected} />
      </div>
    {:else if $currentProject && $currentUser}
      <div class="container">
        <NavBar 
          isCollapsed={isMenuCollapsed} 
          on:toggleMenu={toggleMenu}
          on:logout={handleLogout}
        />
        
        <div class="content">
          <h1>File Explorer - {$currentUser.username}'s Project: {$currentProject.name}</h1>
          
          {#if $currentView === 'tender-documents'}
            <div class="file-explorer">
              <div class="file-controls">
                <FileUploader 
                  API_BASE_URL={API_BASE_URL}
                  projectId={$currentProject.id}
                  username={$currentUser.username}
                  onUploadSuccess={handleUploadSuccess}
                />
                
                <div class="file-selector">
                  <select on:change={(e) => {
                    const file = $uploadedFiles.find(f => f.id === parseInt(e.target.value));
                    selectedFile.set(file);
                  }}>
                    <option value="">Select a file to view</option>
                    {#each $uploadedFiles as file}
                      <option value={file.id}>{file.file.split('/').pop()}</option>
                    {/each}
                  </select>
                </div>
              </div>
              
              <FileViewer 
                API_BASE_URL={API_BASE_URL}
                selectedFile={$selectedFile}
              />
            </div>
          {:else if $currentView === 'manage-documents'}
            <ManageDocuments
              API_BASE_URL={API_BASE_URL}
              projectId={$currentProject.id}
              username={$currentUser.username}
              files={$uploadedFiles}
              onFilesChanged={handleFilesChanged}
            />
          {:else if $currentView === 'call-off-discussion'}
            <CallOffDiscussion 
              projectName={$currentProject.name}
              username={$currentUser.username}
              results={$callOffResults}
            />
          {:else if $currentView === 'bid-writing'}
            <p>Project folder path: {API_BASE_URL}/media/{$currentProject.id}</p>
            <p>Username: {$currentUser.username}</p>
          {:else if $currentView === 'online-members'}
            <OnlineMembers projectName={$currentProject.name} username={$currentUser.username} />
          {/if}
        </div>
      </div>
    {:else}
      <p>Loading...</p>
    {/if}
  </main>
  
  <style>
    :global(body) {
      margin: 0;
      padding: 0;
      font-family: Arial, sans-serif;
      background-color: #f5f5f5;
    }
  
    main {
      height: 100vh;
      display: flex;
    }
  
    .project-selector-container {
      width: 100%;
      max-width: 500px;
      margin: auto;
      padding: 20px;
      background-color: #fff;
      border-radius: 8px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
  
    .container {
      display: flex;
      width: 100%;
      height: 100%;
    }
  
    .content {
      flex: 1;
      padding: 20px;
      overflow-y: auto;
    }
  
    h1 {
      color: #333;
      margin-bottom: 20px;
    }
  
    .file-explorer {
      display: flex;
      flex-direction: column;
      height: calc(100vh - 100px);
    }
  
    .file-controls {
      display: flex;
      justify-content: space-between;
      margin-bottom: 20px;
    }
  
    .file-selector select {
      width: 300px;
      padding: 10px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 1em;
    }
  
    :global(.file-content) {
      flex: 1;
      overflow: auto;
    }
  
    .debug-info {
      position: fixed;
      top: 0;
      right: 0;
      background: rgba(0, 0, 0, 0.8);
      color: white;
      padding: 10px;
      font-size: 12px;
      z-index: 9999;
      max-height: 80vh;
      overflow-y: auto;
    }
  
    @media (max-width: 768px) {
      .container {
        flex-direction: column;
      }
  
      .content {
        padding: 10px;
      }
  
      .file-controls {
        flex-direction: column;
      }
  
      .file-selector select {
        width: 100%;
        margin-top: 10px;
      }
    }
  </style>