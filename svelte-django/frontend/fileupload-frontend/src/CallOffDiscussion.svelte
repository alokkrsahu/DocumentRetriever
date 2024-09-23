<script>
import { onMount } from 'svelte';
import axios from 'axios';
import { isProcessingDocuments, hasNewUploads, startProcessing, finishProcessing } from './store.js';
import { API_BASE_URL } from './config.js';

export let projectName = '';
export let username = '';

let error = null;
let processingStatus = '';
let isProcessing = false;
let processedLocation = null;
let analysisResults = null;

// Parameters for analyser.py
let minFrequency = 1;
let topMClauses = 3;
let minThreshold = 10;
let topNDocs = 5;

// Slider ranges
let maxFrequency = 1;
let maxClauses = 1;
let maxThreshold = 100;
let maxDocs = 1;

$: filteredResults = filterResults(analysisResults, minFrequency, topMClauses, minThreshold, topNDocs);

onMount(() => {
    console.log("CallOffDiscussion mounted with:", { projectName, username });
    checkProcessingStatus();
});

async function callOffDiscussion(action) {
    console.log(`Calling off discussion with:`, { projectName, username, action, minFrequency, topMClauses, minThreshold, topNDocs });
    if (!projectName || !username) {
        error = "Project name or username is missing";
        return;
    }

    isProcessing = true;
    error = null;

    try {
        const response = await axios.post(`${API_BASE_URL}/api/call-off-discussion/`, {
            project_name: projectName,
            username: username,
            action: action,
            min_frequency: minFrequency,
            top_m_clauses: topMClauses,
            min_threshold: minThreshold,
            top_n_docs: topNDocs
        });

        console.log('Response:', response.data);
        
        if (response.data.status === 'processing') {
            processingStatus = 'Document processing started. This may take a while.';
            startProcessing();
        } else if (response.data.status === 'completed') {
            processedLocation = response.data.processed_location;
            processingStatus = 'Call off discussion is ready.';
            if (action === 'call_off') {
                analysisResults = response.data.results;
                initializeSliderRanges(analysisResults);
            }
            finishProcessing();
        } else if (response.data.status === 'not_ready') {
            processingStatus = 'Files are not processed yet. Please process documents first.';
            finishProcessing();
        }
    } catch (err) {
        console.error('Error:', err.response ? err.response.data : err.message);
        error = err.response ? err.response.data.error : err.message;
        finishProcessing();
    } finally {
        isProcessing = false;
    }
}

async function checkProcessingStatus() {
    try {
        const response = await axios.get(`${API_BASE_URL}/api/check-processing-status/`, {
            params: { project_name: projectName }
        });

        if (response.data.status === 'completed') {
            processedLocation = response.data.processed_location;
            processingStatus = 'Call off discussion is ready.';
            finishProcessing();
        } else {
            processingStatus = 'Documents are not processed yet.';
        }
    } catch (err) {
        console.error('Error checking status:', err.response ? err.response.data : err.message);
        error = err.response ? err.response.data.error : err.message;
    }
}

function processDocuments() {
    callOffDiscussion('process_docs');
}

function displayResults() {
    callOffDiscussion('call_off');
}

function initializeSliderRanges(results) {
    if (!results) return;

    maxFrequency = Math.max(...Object.values(results).map(doc => doc.frequency));
    maxClauses = Math.max(...Object.values(results).map(doc => Object.keys(doc.clause_ids).length));
    maxDocs = Object.keys(results).length;

    // Only update the sliders if they're outside the new ranges
    minFrequency = Math.min(minFrequency, maxFrequency);
    topMClauses = Math.min(topMClauses, maxClauses);
    topNDocs = Math.min(topNDocs, maxDocs);
}



function filterResults(results, minFreq, topM, minThresh, topN) {
    if (!results) return null;

    const filteredDocs = Object.entries(results)
        .filter(([_, doc]) => doc.frequency >= minFreq)
        .sort((a, b) => b[1].frequency - a[1].frequency)
        .slice(0, topN);

    return Object.fromEntries(filteredDocs.map(([docId, doc]) => {
        const filteredClauses = Object.entries(doc.clause_ids)
            .filter(([_, clause]) => 
                Object.values(clause).some(score => 
                    typeof score === 'number' && score >= minThresh
                )
            )
            .sort((a, b) => 
                Math.max(...Object.values(b[1]).filter(v => typeof v === 'number')) -
                Math.max(...Object.values(a[1]).filter(v => typeof v === 'number'))
            )
            .slice(0, topM);

        return [docId, {
            ...doc,
            clause_ids: Object.fromEntries(filteredClauses)
        }];
    }));
}

$: {
    if (analysisResults) {
        initializeSliderRanges(analysisResults);
    }
}
</script>

<div class="call-off-discussion">
<h2>Call Off Discussion for {projectName}</h2>

<div class="parameter-sliders">
    <h3>Analysis Parameters</h3>
    <div class="slider-container">
        <label for="minFrequency">Minimum Frequency: {minFrequency}</label>
        <input type="range" id="minFrequency" bind:value={minFrequency} min="1" max={maxFrequency} step="1">
    </div>
    <div class="slider-container">
        <label for="topMClauses">Top M Clauses: {topMClauses}</label>
        <input type="range" id="topMClauses" bind:value={topMClauses} min="1" max={maxClauses} step="1">
    </div>
    <div class="slider-container">
        <label for="minThreshold">Minimum Threshold: {minThreshold}</label>
        <input type="range" id="minThreshold" bind:value={minThreshold} min="0" max={maxThreshold} step="1">
    </div>
    <div class="slider-container">
        <label for="topNDocs">Top N Documents: {topNDocs}</label>
        <input type="range" id="topNDocs" bind:value={topNDocs} min="1" max={maxDocs} step="1">
    </div>
</div>

<div class="button-container">
    <button on:click={processDocuments} disabled={$isProcessingDocuments || !$hasNewUploads}>Process Documents</button>
    <button on:click={displayResults} disabled={isProcessing}>Call Off Discussion</button>
</div>

{#if $isProcessingDocuments}
    <div class="processing-status">
        <p>Processing... Please wait.</p>
        <div class="progress-bar"></div>
    </div>
{/if}

{#if processingStatus}
    <p class="status-message">{processingStatus}</p>
{/if}

{#if error}
    <p class="error">{error}</p>
{/if}

{#if processedLocation}
    <p>Processed documents are available at: {processedLocation}</p>
{/if}

{#if filteredResults}
<div class="analysis-results">
    <h3>Analysis Results</h3>
    {#each Object.entries(filteredResults) as [docId, doc]}
        <div class="document">
            <h4>Document ID: {docId}</h4>
            <p><strong>Source:</strong> {doc.document_source}</p>
            <p><strong>Frequency:</strong> {doc.frequency}</p>
            <details>
                <summary>Document Text</summary>
                <p class="document-text">{doc.document_text}</p>
            </details>
            <details>
                <summary>Matching Clauses</summary>
                {#each Object.entries(doc.clause_ids) as [clauseId, clause]}
                    <div class="clause">
                        <h5>Clause ID: {clauseId}</h5>
                        <p class="clause-text">{clause.clause_text}</p>
                        <ul>
                            {#each Object.entries(clause).filter(([key, value]) => key !== 'clause_text' && typeof value === 'number') as [method, score]}
                                <li>{method}: {score.toFixed(2)}</li>
                            {/each}
                        </ul>
                    </div>
                {/each}
            </details>
        </div>
    {/each}
</div>
{/if}
</div>


<style>
    .call-off-discussion {
        font-family: 'Roboto', Arial, sans-serif;
        max-width: 1200px;
        margin: 0 auto;
        padding: 2em;
        background-color: #ffffff;
        color: #333333;
        position: relative;
    }

    h2, h3, h4, h5, h6 {
        color: #222222;
    }

    .parameter-sliders {
        background-color: #f6f6f6;
        padding: 1.5em;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 2em;
    }

    .parameter-sliders h3 {
        margin-top: 0;
        margin-bottom: 1em;
        color: #d32f2f;
    }

    .slider-container {
        margin-bottom: 1em;
    }

    .slider-container label {
        display: block;
        margin-bottom: 0.5em;
        font-weight: 500;
    }

    input[type="range"] {
        width: 100%;
        -webkit-appearance: none;
        background: #e0e0e0;
        outline: none;
        border-radius: 15px;
        height: 6px;
        margin-top: 0.5em;
    }

    input[type="range"]::-webkit-slider-thumb {
        -webkit-appearance: none;
        appearance: none;
        width: 18px;
        height: 18px;
        background: #d32f2f;
        cursor: pointer;
        border-radius: 50%;
    }

    input[type="range"]::-moz-range-thumb {
        width: 18px;
        height: 18px;
        background: #d32f2f;
        cursor: pointer;
        border-radius: 50%;
        border: none;
    }

    .button-container {
        display: flex;
        gap: 1em;
        margin-bottom: 1em;
    }

    button {
        background-color: #d32f2f;
        color: white;
        border: none;
        padding: 0.75em 1.5em;
        font-size: 1em;
        cursor: pointer;
        border-radius: 4px;
        transition: background-color 0.3s ease;
    }

    button:hover {
        background-color: #b71c1c;
    }

    button:disabled {
        background-color: #e0e0e0;
        color: #9e9e9e;
        cursor: not-allowed;
    }

    .processing-status {
        background-color: #e3f2fd;
        padding: 1em;
        border-radius: 4px;
        margin-top: 1em;
    }

    .progress-bar {
        width: 100%;
        height: 4px;
        background-color: #bbdefb;
        margin-top: 1em;
        position: relative;
        overflow: hidden;
    }

    .progress-bar::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 50%;
        height: 100%;
        background-color: #2196f3;
        animation: progress 2s linear infinite;
    }

    @keyframes progress {
        0% { left: -50%; }
        100% { left: 100%; }
    }

    .status-message {
        margin-top: 1em;
        font-weight: 500;
    }

    .error {
        color: #d32f2f;
        font-weight: bold;
    }

    .analysis-results {
        margin-top: 2em;
    }

    .document {
        background-color: #f6f6f6;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1.5em;
        margin-bottom: 1.5em;
    }

    .document h4 {
        margin-top: 0;
        color: #d32f2f;
    }

    .document-text {
        max-height: 200px;
        overflow-y: auto;
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 1em;
        font-size: 0.9em;
        border-radius: 4px;
    }

    .clause {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        padding: 1em;
        margin-top: 1em;
    }

    .clause h6 {
        margin-top: 0;
        color: #d32f2f;
    }

    .clause-text {
        font-style: italic;
        color: #555555;
        margin-bottom: 0.5em;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 1em;
    }

    th, td {
        text-align: left;
        padding: 0.75em;
        border-bottom: 1px solid #e0e0e0;
    }

    th {
        background-color: #f6f6f6;
        font-weight: bold;
        color: #d32f2f;
    }

    tr:last-child td {
        border-bottom: none;
    }
</style>