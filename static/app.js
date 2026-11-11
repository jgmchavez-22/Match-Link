// MatchLink Company Name Templater JS Logic

// DOM Elements
const elements = {
    // Section sections
    inputSection: document.getElementById('step-input'),
    loadingSection: document.getElementById('step-loading'),
    resultsSection: document.getElementById('step-results'),

    // Inputs & zones
    toggleFile: document.getElementById('toggle-file'),
    toggleText: document.getElementById('toggle-text'),
    zoneFile: document.getElementById('zone-file'),
    zoneText: document.getElementById('zone-text'),
    inputFileElement: document.getElementById('input-file-element'),
    infoFile: document.getElementById('info-file'),
    txtArea: document.getElementById('txt-area'),
    configBox: document.getElementById('config-box'),
    selectCompanyCol: document.getElementById('select-company-col'),
    chkDedup: document.getElementById('chk-dedup'),

    // Buttons
    btnGenerate: document.getElementById('btn-generate'),
    btnRestart: document.getElementById('btn-restart'),
    btnDownload: document.getElementById('btn-download'),

    // Result metrics
    metricTotal: document.getElementById('metric-total'),
    resultsDesc: document.getElementById('results-desc')
};

// Global App State
let appState = {
    file: null,
    inputMode: 'file', // 'file' or 'text'
    headers: [],
    currentDownloadId: null,
    exportFormat: 'excel'
};

document.addEventListener('DOMContentLoaded', () => {
    setupDragAndDrop();
    setupEventListeners();
});

// Setup Drag & Drop Handlers
function setupDragAndDrop() {
    const zone = elements.zoneFile;
    const input = elements.inputFileElement;

    zone.addEventListener('click', () => input.click());

    input.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        zone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            zone.classList.add('border-color-active');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        zone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            zone.classList.remove('border-color-active');
        }, false);
    });

    zone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        if (dt.files.length > 0) {
            handleFileSelect(dt.files[0]);
        }
    });
}

// Handle selected file
async function handleFileSelect(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    const allowed = ['csv', 'xlsx', 'xls', 'txt'];
    if (!allowed.includes(ext)) {
        alert("Please upload a spreadsheet (Excel/CSV) or plain text (TXT) file.");
        return;
    }

    appState.file = file;
    elements.zoneFile.classList.add('active');
    elements.infoFile.textContent = `${file.name} (${formatBytes(file.size)})`;

    // Process file headers if CSV/Excel
    if (ext === 'csv' || ext === 'xlsx' || ext === 'xls') {
        await parseFileHeaders(file);
    } else {
        // Plain text file doesn't need column headers mapping
        elements.configBox.classList.add('hidden');
        elements.btnGenerate.disabled = false;
    }
}

// Helper to format bytes
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Parse headers on backend
async function parseFileHeaders(file) {
    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/parse-headers', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Failed to analyze headers.");
        }

        const data = await response.json();
        appState.headers = data.headers;

        populateColumnSelector(data.headers);
        elements.configBox.classList.remove('hidden');
        elements.btnGenerate.disabled = false;
    } catch (e) {
        alert(`Error parsing file: ${e.message}`);
        resetFileInput();
    }
}

// Populate column selector dropdown
function populateColumnSelector(headers) {
    elements.selectCompanyCol.innerHTML = '<option value="">-- Select Column --</option>';
    headers.forEach(h => {
        elements.selectCompanyCol.innerHTML += `<option value="${h}">${h}</option>`;
    });

    // Auto-match name columns
    const keywords = ['company', 'name', 'firm', 'organization', 'client', 'vendor', 'entity'];
    let bestMatch = headers.find(h => {
        const lh = h.toLowerCase();
        return keywords.some(kw => lh.includes(kw));
    });
    if (!bestMatch) {
        bestMatch = headers.find(h => h.toLowerCase() === 'name');
    }

    if (bestMatch) {
        elements.selectCompanyCol.value = bestMatch;
    }
}

// Reset file input
function resetFileInput() {
    appState.file = null;
    appState.headers = [];
    elements.inputFileElement.value = '';
    elements.zoneFile.classList.remove('active');
    elements.infoFile.textContent = 'No file selected (Supports CSV, XLSX, XLS, TXT)';
    elements.configBox.classList.add('hidden');
    elements.btnGenerate.disabled = true;
}

// Convert text area to a file blob
function handleTextAreaInput() {
    if (appState.inputMode !== 'text') return;
    const text = elements.txtArea.value.trim();
    if (text.length > 0) {
        const blob = new Blob([text], { type: 'text/plain' });
        appState.file = new File([blob], 'pasted_companies.txt', { type: 'text/plain' });
        elements.btnGenerate.disabled = false;
    } else {
        appState.file = null;
        elements.btnGenerate.disabled = true;
    }
}

// Setup listeners
function setupEventListeners() {
    // Mode toggles
    elements.toggleFile.addEventListener('click', () => {
        appState.inputMode = 'file';
        elements.toggleFile.classList.add('active');
        elements.toggleText.classList.remove('active');
        elements.zoneFile.classList.remove('hidden');
        elements.zoneText.classList.add('hidden');
        resetFileInput();
    });

    elements.toggleText.addEventListener('click', () => {
        appState.inputMode = 'text';
        elements.toggleText.classList.add('active');
        elements.toggleFile.classList.remove('active');
        elements.zoneText.classList.remove('hidden');
        elements.zoneFile.classList.add('hidden');
        elements.configBox.classList.add('hidden');
        handleTextAreaInput();
    });

    elements.txtArea.addEventListener('input', handleTextAreaInput);

    // Run action
    elements.btnGenerate.addEventListener('click', async () => {
        let companyCol = "Company Name"; // Default for text area / txt files
        if (appState.inputMode === 'file' && appState.headers.length > 0) {
            companyCol = elements.selectCompanyCol.value;
            if (!companyCol) {
                alert("Please select the column containing company names.");
                return;
            }
        }

        // Move to loading screen
        elements.inputSection.classList.add('hidden');
        elements.loadingSection.classList.remove('hidden');

        try {
            const format = document.querySelector('input[name="export-format"]:checked').value;
            appState.exportFormat = format;

            const dedup = elements.chkDedup.checked;

            const formData = new FormData();
            formData.append('file', appState.file);
            formData.append('company_col', companyCol);
            formData.append('export_format', format);
            formData.append('deduplicate', dedup);

            const response = await fetch('/api/template', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || "Failed to process template.");
            }

            const data = await response.json();
            appState.currentDownloadId = data.download_id;

            // Transition to success results card
            elements.loadingSection.classList.add('hidden');
            elements.resultsSection.classList.remove('hidden');
            elements.resultsSection.classList.add('animate-slide-up');

            elements.metricTotal.textContent = data.total_records.toLocaleString();
            elements.resultsDesc.textContent = `Standardized 'Cleaned Name (exact match, no spaces/chars)', 'by Left 25 Characters', 'by Left 15 Characters', and 'by Left 10 Characters' columns successfully appended.`;
            
            if (format === 'csv') {
                elements.btnDownload.innerHTML = `<i class="fa-solid fa-file-csv"></i> <span>Download CSV Dataset</span>`;
                elements.btnDownload.className = 'btn btn-success';
            } else {
                elements.btnDownload.innerHTML = `<i class="fa-solid fa-file-excel"></i> <span>Download Excel Workbook</span>`;
                elements.btnDownload.className = 'btn btn-success';
            }

        } catch (e) {
            alert(`Error: ${e.message}`);
            elements.loadingSection.classList.add('hidden');
            elements.inputSection.classList.remove('hidden');
        }
    });

    // Download action
    elements.btnDownload.addEventListener('click', () => {
        if (!appState.currentDownloadId) return;
        window.open(`/api/download/${appState.currentDownloadId}`, '_blank');
    });

    // Start over action
    elements.btnRestart.addEventListener('click', () => {
        appState.file = null;
        appState.headers = [];
        appState.currentDownloadId = null;
        appState.inputMode = 'file';

        elements.inputFileElement.value = '';
        elements.txtArea.value = '';
        elements.selectCompanyCol.innerHTML = '';
        elements.zoneFile.classList.remove('active');
        elements.infoFile.textContent = 'No file selected (Supports CSV, XLSX, XLS, TXT)';

        elements.toggleFile.classList.add('active');
        elements.toggleText.classList.remove('active');
        elements.zoneFile.classList.remove('hidden');
        elements.zoneText.classList.add('hidden');
        elements.configBox.classList.add('hidden');
        elements.btnGenerate.disabled = true;

        elements.resultsSection.classList.add('hidden');
        elements.inputSection.classList.remove('hidden');
        elements.inputSection.classList.add('animate-slide-up');
    });
}
