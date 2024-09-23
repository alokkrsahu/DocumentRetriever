<script>
  import { onMount } from 'svelte';
  import axios from 'axios';
  import * as XLSX from 'xlsx';
  import JSZip from 'jszip';
  import { API_BASE_URL } from './config.js';
  export let selectedFile;

  let fileContent = '';
  let errorMessage = '';
  let sheets = [];
  let activeSheet = '';
  let workbook = null;
  let isLoading = false;
  let isDarkMode = false;

  $: if (selectedFile) {
    viewFileContent(selectedFile);
  }

  async function viewFileContent(file) {
    if (!file || !file.file) {
      errorMessage = 'Invalid file selected';
      return;
    }

    isLoading = true;
    errorMessage = '';
    fileContent = '';
    sheets = [];
    activeSheet = '';
    workbook = null;
    
    try {
      const response = await axios.get(`${API_BASE_URL}/api/file-content/`, {
        params: { file_path: file.file }
      });
      
      if (response.data.type === 'application/pdf') {
        fileContent = `data:application/pdf;base64,${response.data.content}`;
      } else if (response.data.type.startsWith('image/')) {
        fileContent = `data:${response.data.type};base64,${response.data.content}`;
      } else if (response.data.type === 'text/plain' || response.data.type === 'text/csv') {
        fileContent = enhanceTextContent(response.data.content);
      } else if (response.data.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') {
        workbook = XLSX.read(base64ToArrayBuffer(response.data.content), {type: 'array'});
        sheets = workbook.SheetNames;
        activeSheet = sheets[0];
        fileContent = getSheetHtml(workbook, activeSheet);
      } else if (response.data.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
        const arrayBuffer = base64ToArrayBuffer(response.data.content);
        const result = await window.mammoth.convertToHtml({arrayBuffer: arrayBuffer});
        fileContent = enhanceWordContent(result.value);
      } else if (response.data.type === 'application/vnd.oasis.opendocument.text') {
        fileContent = enhanceOdtContent(await parseOdt(base64ToArrayBuffer(response.data.content)));
      } else if (response.data.message) {
        fileContent = response.data.message;
      } else {
        fileContent = 'Unsupported file type';
      }
    } catch (error) {
      console.error('Error details:', error);
      fileContent = '';
      errorMessage = error.response?.data?.error || error.message || 'Error loading file content';
    } finally {
      isLoading = false;
    }
  }

  function getSheetHtml(workbook, sheetName) {
    const sheet = workbook.Sheets[sheetName];
    const html = XLSX.utils.sheet_to_html(sheet);
    return enhanceExcelHtml(html);
  }

  function enhanceExcelHtml(html) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const table = doc.querySelector('table');
    
    if (table) {
      table.classList.add('excel-table');
      
      // Add header row
      const headerRow = table.rows[0];
      if (headerRow) {
        headerRow.classList.add('header-row');
        Array.from(headerRow.cells).forEach(cell => cell.classList.add('header-cell'));
      }

      // Style other rows
      Array.from(table.rows).slice(1).forEach((row, index) => {
        row.classList.add(index % 2 === 0 ? 'even-row' : 'odd-row');
        Array.from(row.cells).forEach(cell => cell.classList.add('data-cell'));
      });
    }

    return `<div class="excel-container">${doc.body.innerHTML}</div>`;
  }

  function enhanceTextContent(content) {
    return `<div class="text-document">${content.replace(/\n/g, '<br>')}</div>`;
  }

  function enhanceWordContent(content) {
    return `<div class="word-document">${content}</div>`;
  }

  function enhanceOdtContent(content) {
    return `<div class="odt-document">${content}</div>`;
  }

  function changeSheet(sheetName) {
    if (workbook) {
      activeSheet = sheetName;
      fileContent = getSheetHtml(workbook, sheetName);
    }
  }

  function base64ToArrayBuffer(base64) {
    const binaryString = atob(base64);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
  }

  async function parseOdt(arrayBuffer) {
    try {
      const zip = await JSZip.loadAsync(arrayBuffer);
      const contentXml = await zip.file('content.xml').async('text');
      const parser = new DOMParser();
      const xmlDoc = parser.parseFromString(contentXml, 'text/xml');
      const textContent = xmlDoc.getElementsByTagName('text:p');
      return Array.from(textContent).map(p => p.textContent).join('<br>');
    } catch (error) {
      console.error('Error parsing ODT:', error);
      return 'Error: Unable to parse ODT file';
    }
  }

  function getFileTitle(file) {
    return file && file.file ? `File Viewer: ${file.file.split('/').pop()}` : 'No file selected';
  }

  function toggleDarkMode() {
    isDarkMode = !isDarkMode;
  }
</script>

<div class="file-content" class:dark-mode={isDarkMode}>
  <button on:click={toggleDarkMode} class="mode-toggle">
    {isDarkMode ? 'Light Mode' : 'Dark Mode'}
  </button>

  {#if isLoading}
    <div class="loading-spinner"></div>
  {:else if selectedFile}
    <h2>{getFileTitle(selectedFile)}</h2>
    {#if selectedFile.file.endsWith('.pdf') && fileContent}
      <iframe 
        src={fileContent} 
        width="100%" 
        height="100%"
        title={getFileTitle(selectedFile)}
      ></iframe>
    {:else if selectedFile.file.match(/\.(jpg|jpeg|png|gif)$/i) && fileContent}
      <div class="image-viewer">
        <img src={fileContent} alt={selectedFile.name || 'Image'} />
      </div>
    {:else if selectedFile.file.endsWith('.xlsx') && sheets.length > 0}
      <div class="sheet-selector">
        <label for="sheet-select">Select Sheet:</label>
        <select id="sheet-select" on:change={(e) => changeSheet(e.target.value)}>
          {#each sheets as sheet}
            <option value={sheet} selected={sheet === activeSheet}>{sheet}</option>
          {/each}
        </select>
      </div>
      <div class="html-content">{@html fileContent}</div>
    {:else if fileContent.startsWith('<div class="') || fileContent.startsWith('<table')}
      <div class="html-content">{@html fileContent}</div>
    {:else if fileContent.startsWith('Cannot display content')}
      <p>{fileContent}</p>
      <a href={`${API_BASE_URL}/media/${selectedFile.file}`} download class="download-link">Download {selectedFile.name || selectedFile.file.split('/').pop()}</a>
    {:else if fileContent}
      <pre>{fileContent}</pre>
    {:else if errorMessage}
      <p class="error-message">{errorMessage}</p>
    {/if}
  {:else}
    <p>Select a file to view its content.</p>
  {/if}
</div>


<style>
  .file-content {
    width: 100%;
    height: 100%;
    transition: background-color 0.3s, color 0.3s;
    font-family: Arial, sans-serif;
    padding: 20px;
    border-radius: 8px;
    background-color: #ffffff;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    overflow: auto;
    display: flex;
    flex-direction: column;
  }

  .dark-mode {
    background-color: #1e1e1e;
    color: #ffffff;
  }

  .mode-toggle {
    position: absolute;
    top: 10px;
    right: 10px;
    padding: 5px 10px;
    background-color: #f0f0f0;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .dark-mode .mode-toggle {
    background-color: #333;
    color: #fff;
  }

  .loading-spinner {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #3498db;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
    margin: 20px auto;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .image-viewer {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    background-color: #f0f0f0;
    border: 1px solid #ccc;
    border-radius: 4px;
    overflow: auto;
  }

  .image-viewer img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
  }

  iframe {
    border: none;
    flex: 1;
  }

  .html-content {
    flex: 1;
    overflow: auto;
    padding: 20px;
    background-color: #fff;
    border: 1px solid #ccc;
    border-radius: 4px;
  }

  .dark-mode .html-content {
    background-color: #2c2c2c;
    border-color: #444;
  }

  :global(.excel-container) {
    font-family: 'Calibri', sans-serif;
    font-size: 11pt;
  }

  :global(.excel-table) {
    border-collapse: collapse;
    width: 100%;
  }

  :global(.excel-table .header-row) {
    background-color: #f2f2f2;
    font-weight: bold;
  }

  :global(.excel-table .header-cell),
  :global(.excel-table .data-cell) {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
  }

  :global(.excel-table .even-row) {
    background-color: #ffffff;
  }

  :global(.excel-table .odd-row) {
    background-color: #f9f9f9;
  }

  :global(.text-document),
  :global(.word-document),
  :global(.odt-document) {
    font-family: 'Times New Roman', Times, serif;
    font-size: 12pt;
    line-height: 1.5;
    text-align: left;
    padding: 40px;
    background-color: #fff;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
    border-radius: 4px;
  }

  .dark-mode :global(.text-document),
  .dark-mode :global(.word-document),
  .dark-mode :global(.odt-document) {
    background-color: #2c2c2c;
    color: #fff;
  }

  :global(.word-document h1),
  :global(.word-document h2),
  :global(.word-document h3),
  :global(.odt-document h1),
  :global(.odt-document h2),
  :global(.odt-document h3) {
    color: #000;
    margin-top: 20px;
    margin-bottom: 10px;
  }

  .dark-mode :global(.word-document h1),
  .dark-mode :global(.word-document h2),
  .dark-mode :global(.word-document h3),
  .dark-mode :global(.odt-document h1),
  .dark-mode :global(.odt-document h2),
  .dark-mode :global(.odt-document h3) {
    color: #fff;
  }

  .sheet-selector {
    margin-bottom: 15px;
  }

  .sheet-selector label {
    margin-right: 10px;
  }

  .sheet-selector select {
    padding: 5px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background-color: white;
    font-size: 14px;
  }

  .download-link {
    display: inline-block;
    margin-top: 10px;
    padding: 10px 15px;
    background-color: #f0f0f0;
    color: #333;
    text-decoration: none;
    border-radius: 4px;
    transition: background-color 0.3s;
  }

  .download-link:hover {
    background-color: #e0e0e0;
  }

  .error-message {
    color: #d32f2f;
  }

  .dark-mode .download-link {
    background-color: #333;
    color: #fff;
  }

  .dark-mode .download-link:hover {
    background-color: #444;
  }

  h2 {
    margin-top: 0;
    color: #333;
  }

  .dark-mode h2 {
    color: #fff;
  }

  pre {
    white-space: pre-wrap;
    word-wrap: break-word;
    background-color: #f5f5f5;
    padding: 15px;
    border-radius: 4px;
    max-height: 600px;
    overflow-y: auto;
  }

  .dark-mode pre {
    background-color: #2c2c2c;
    color: #f0f0f0;
  }
</style>
