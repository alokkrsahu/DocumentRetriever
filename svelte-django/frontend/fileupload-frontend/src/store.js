import { writable } from 'svelte/store';

export const currentProject = writable(null);
export const currentUser = writable(null);
export const uploadedFiles = writable([]);
export const selectedFile = writable(null);
export const currentView = writable('tender-documents');
export const callOffResults = writable([]);

// New stores for document processing
export const isProcessingDocuments = writable(false);
export const hasNewUploads = writable(false);

export function resetState() {
    currentProject.set(null);
    currentUser.set(null);
    localStorage.removeItem('selectedProject');
    localStorage.removeItem('selectedUsername');
    isProcessingDocuments.set(false);
    hasNewUploads.set(false);
}

export function startProcessing() {
    isProcessingDocuments.set(true);
    hasNewUploads.set(false);
}

export function finishProcessing() {
    isProcessingDocuments.set(false);
}

export function setNewUploadsAndFinishProcessing() {
    hasNewUploads.set(true);
    isProcessingDocuments.set(false);
}
