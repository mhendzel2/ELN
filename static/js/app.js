// Global state
let currentExperimentId = null;
let experiments = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadExperiments();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // New experiment button
    document.getElementById('newExperimentBtn').addEventListener('click', () => {
        document.getElementById('experimentModal').style.display = 'block';
    });

    // Search
    document.getElementById('searchInput').addEventListener('input', (e) => {
        searchExperiments(e.target.value);
    });

    // Experiment form
    document.getElementById('experimentForm').addEventListener('submit', handleCreateExperiment);

    // Image form
    document.getElementById('imageForm').addEventListener('submit', handleUploadImage);

    // Gel form
    document.getElementById('gelForm').addEventListener('submit', handleUploadGel);

    // Quantification form
    document.getElementById('quantForm').addEventListener('submit', handleAddQuantification);

    // Bioinformatics form
    document.getElementById('bioForm').addEventListener('submit', handleAddBioinformatics);

    // Modal close buttons
    document.querySelectorAll('.modal .close').forEach(btn => {
        btn.addEventListener('click', () => {
            btn.closest('.modal').style.display = 'none';
        });
    });

    // Close modals on outside click
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.style.display = 'none';
        }
    });
}

// Load experiments
async function loadExperiments() {
    try {
        const response = await fetch('/api/experiments');
        experiments = await response.json();
        displayExperiments(experiments);
    } catch (error) {
        console.error('Error loading experiments:', error);
        showError('Failed to load experiments');
    }
}

// Display experiments
function displayExperiments(experimentsList) {
    const container = document.getElementById('experimentsList');
    
    if (experimentsList.length === 0) {
        container.innerHTML = `
            <div class="empty-state" style="grid-column: 1/-1;">
                <i class="fas fa-flask"></i>
                <h3>No experiments yet</h3>
                <p>Create your first experiment to get started</p>
            </div>
        `;
        return;
    }

    container.innerHTML = experimentsList.map(exp => `
        <div class="experiment-card" onclick="loadExperimentDetail(${exp.id})">
            <h3>${escapeHtml(exp.title)}</h3>
            <div class="experiment-meta">
                <div><i class="fas fa-calendar"></i> ${new Date(exp.date).toLocaleDateString()}</div>
                ${exp.researcher ? `<div><i class="fas fa-user"></i> ${escapeHtml(exp.researcher)}</div>` : ''}
            </div>
            ${exp.description ? `<p>${escapeHtml(exp.description.substring(0, 100))}${exp.description.length > 100 ? '...' : ''}</p>` : ''}
            ${exp.tags.length > 0 ? `
                <div class="experiment-tags">
                    ${exp.tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
                </div>
            ` : ''}
        </div>
    `).join('');
}

// Load experiment detail
async function loadExperimentDetail(expId) {
    currentExperimentId = expId;
    
    try {
        const response = await fetch(`/api/experiments/${expId}`);
        const experiment = await response.json();
        
        document.getElementById('experimentsList').style.display = 'none';
        document.getElementById('experimentDetail').style.display = 'block';
        
        displayExperimentDetail(experiment);
    } catch (error) {
        console.error('Error loading experiment detail:', error);
        showError('Failed to load experiment details');
    }
}

// Display experiment detail
function displayExperimentDetail(exp) {
    const container = document.getElementById('experimentDetail');
    
    container.innerHTML = `
        <div class="detail-header">
            <div>
                <h2>${escapeHtml(exp.title)}</h2>
                <div class="experiment-meta" style="margin-top: 10px;">
                    <div><i class="fas fa-calendar"></i> ${new Date(exp.date).toLocaleDateString()}</div>
                    ${exp.researcher ? `<div><i class="fas fa-user"></i> ${escapeHtml(exp.researcher)}</div>` : ''}
                </div>
                ${exp.description ? `<p style="margin-top: 15px;">${escapeHtml(exp.description)}</p>` : ''}
                ${exp.tags.length > 0 ? `
                    <div class="experiment-tags" style="margin-top: 10px;">
                        ${exp.tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
                    </div>
                ` : ''}
            </div>
            <div class="detail-actions">
                <button class="btn btn-secondary btn-small" onclick="backToList()">
                    <i class="fas fa-arrow-left"></i> Back
                </button>
            </div>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="switchTab('images')">
                <i class="fas fa-image"></i> Images (${exp.images.length})
            </button>
            <button class="tab" onclick="switchTab('gels')">
                <i class="fas fa-dna"></i> Gels (${exp.gels.length})
            </button>
            <button class="tab" onclick="switchTab('quantifications')">
                <i class="fas fa-chart-bar"></i> Quantifications (${exp.quantifications.length})
            </button>
            <button class="tab" onclick="switchTab('bioinformatics')">
                <i class="fas fa-code"></i> Bioinformatics (${exp.bioinformatics.length})
            </button>
        </div>

        <div id="images-tab" class="tab-content active">
            <button class="btn btn-primary btn-small" onclick="openImageModal()">
                <i class="fas fa-upload"></i> Upload Image
            </button>
            <div class="images-grid">
                ${exp.images.length > 0 ? exp.images.map(img => `
                    <div class="image-card">
                        <img src="/uploads/${img.filename}" alt="${escapeHtml(img.original_filename)}">
                        <div class="image-info">
                            <h4>${escapeHtml(img.original_filename)}</h4>
                            ${img.image_type ? `<p><strong>Type:</strong> ${escapeHtml(img.image_type)}</p>` : ''}
                            ${img.magnification ? `<p><strong>Magnification:</strong> ${escapeHtml(img.magnification)}</p>` : ''}
                            ${img.notes ? `<p>${escapeHtml(img.notes)}</p>` : ''}
                        </div>
                    </div>
                `).join('') : '<div class="empty-state" style="grid-column: 1/-1;"><p>No images uploaded yet</p></div>'}
            </div>
        </div>

        <div id="gels-tab" class="tab-content">
            <button class="btn btn-primary btn-small" onclick="openGelModal()">
                <i class="fas fa-upload"></i> Upload Gel
            </button>
            <div class="images-grid">
                ${exp.gels.length > 0 ? exp.gels.map(gel => `
                    <div class="image-card">
                        <img src="/uploads/${gel.filename}" alt="${escapeHtml(gel.original_filename)}">
                        <div class="image-info">
                            <h4>${escapeHtml(gel.original_filename)}</h4>
                            ${gel.gel_type ? `<p><strong>Type:</strong> ${escapeHtml(gel.gel_type)}</p>` : ''}
                            ${gel.num_lanes ? `<p><strong>Lanes:</strong> ${gel.num_lanes}</p>` : ''}
                            ${gel.notes ? `<p>${escapeHtml(gel.notes)}</p>` : ''}
                        </div>
                    </div>
                `).join('') : '<div class="empty-state" style="grid-column: 1/-1;"><p>No gels uploaded yet</p></div>'}
            </div>
        </div>

        <div id="quantifications-tab" class="tab-content">
            <button class="btn btn-primary btn-small" onclick="openQuantModal()">
                <i class="fas fa-plus"></i> Add Quantification
            </button>
            ${exp.quantifications.length > 0 ? `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Measurement</th>
                            <th>Value</th>
                            <th>Unit</th>
                            <th>Method</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${exp.quantifications.map(q => `
                            <tr>
                                <td>${escapeHtml(q.measurement_type)}</td>
                                <td>${q.value}</td>
                                <td>${escapeHtml(q.unit || '-')}</td>
                                <td>${escapeHtml(q.method || '-')}</td>
                                <td>${new Date(q.created_date).toLocaleDateString()}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            ` : '<div class="empty-state"><p>No quantifications added yet</p></div>'}
        </div>

        <div id="bioinformatics-tab" class="tab-content">
            <button class="btn btn-primary btn-small" onclick="openBioModal()">
                <i class="fas fa-plus"></i> Add Analysis
            </button>
            ${exp.bioinformatics.length > 0 ? `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Analysis Type</th>
                            <th>Pipeline</th>
                            <th>Summary</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${exp.bioinformatics.map(bio => `
                            <tr>
                                <td>${escapeHtml(bio.analysis_type)}</td>
                                <td>${escapeHtml(bio.pipeline || '-')} ${bio.version ? 'v' + escapeHtml(bio.version) : ''}</td>
                                <td>${escapeHtml(bio.results_summary.substring(0, 100))}...</td>
                                <td>${new Date(bio.created_date).toLocaleDateString()}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            ` : '<div class="empty-state"><p>No analyses added yet</p></div>'}
        </div>
    `;
}

// Switch tabs
function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

// Back to list
function backToList() {
    document.getElementById('experimentsList').style.display = 'grid';
    document.getElementById('experimentDetail').style.display = 'none';
    currentExperimentId = null;
}

// Modal functions
function openImageModal() {
    document.getElementById('imageModal').style.display = 'block';
}

function openGelModal() {
    document.getElementById('gelModal').style.display = 'block';
}

function openQuantModal() {
    document.getElementById('quantModal').style.display = 'block';
}

function openBioModal() {
    document.getElementById('bioModal').style.display = 'block';
}

// Handle create experiment
async function handleCreateExperiment(e) {
    e.preventDefault();
    
    const data = {
        title: document.getElementById('expTitle').value,
        researcher: document.getElementById('expResearcher').value,
        description: document.getElementById('expDescription').value,
        tags: document.getElementById('expTags').value.split(',').map(t => t.trim()).filter(t => t)
    };
    
    try {
        const response = await fetch('/api/experiments', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            document.getElementById('experimentModal').style.display = 'none';
            document.getElementById('experimentForm').reset();
            await loadExperiments();
            showSuccess('Experiment created successfully');
        } else {
            showError('Failed to create experiment');
        }
    } catch (error) {
        console.error('Error creating experiment:', error);
        showError('Failed to create experiment');
    }
}

// Handle upload image
async function handleUploadImage(e) {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append('file', document.getElementById('imageFile').files[0]);
    formData.append('image_type', document.getElementById('imageType').value);
    formData.append('magnification', document.getElementById('imageMagnification').value);
    formData.append('scale_bar', document.getElementById('imageScaleBar').value);
    formData.append('notes', document.getElementById('imageNotes').value);
    
    try {
        const response = await fetch(`/api/experiments/${currentExperimentId}/images`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            document.getElementById('imageModal').style.display = 'none';
            document.getElementById('imageForm').reset();
            await loadExperimentDetail(currentExperimentId);
            showSuccess('Image uploaded successfully');
        } else {
            showError('Failed to upload image');
        }
    } catch (error) {
        console.error('Error uploading image:', error);
        showError('Failed to upload image');
    }
}

// Handle upload gel
async function handleUploadGel(e) {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append('file', document.getElementById('gelFile').files[0]);
    formData.append('gel_type', document.getElementById('gelType').value);
    formData.append('num_lanes', document.getElementById('gelLanes').value);
    formData.append('lane_labels', document.getElementById('gelLabels').value);
    formData.append('marker_info', document.getElementById('gelMarker').value);
    formData.append('notes', document.getElementById('gelNotes').value);
    
    try {
        const response = await fetch(`/api/experiments/${currentExperimentId}/gels`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            document.getElementById('gelModal').style.display = 'none';
            document.getElementById('gelForm').reset();
            await loadExperimentDetail(currentExperimentId);
            showSuccess('Gel uploaded successfully');
        } else {
            showError('Failed to upload gel');
        }
    } catch (error) {
        console.error('Error uploading gel:', error);
        showError('Failed to upload gel');
    }
}

// Handle add quantification
async function handleAddQuantification(e) {
    e.preventDefault();
    
    const data = {
        measurement_type: document.getElementById('quantType').value,
        value: parseFloat(document.getElementById('quantValue').value),
        unit: document.getElementById('quantUnit').value,
        method: document.getElementById('quantMethod').value,
        notes: document.getElementById('quantNotes').value
    };
    
    try {
        const response = await fetch(`/api/experiments/${currentExperimentId}/quantifications`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            document.getElementById('quantModal').style.display = 'none';
            document.getElementById('quantForm').reset();
            await loadExperimentDetail(currentExperimentId);
            showSuccess('Quantification added successfully');
        } else {
            showError('Failed to add quantification');
        }
    } catch (error) {
        console.error('Error adding quantification:', error);
        showError('Failed to add quantification');
    }
}

// Handle add bioinformatics
async function handleAddBioinformatics(e) {
    e.preventDefault();
    
    const data = {
        analysis_type: document.getElementById('bioType').value,
        pipeline: document.getElementById('bioPipeline').value,
        version: document.getElementById('bioVersion').value,
        results_summary: document.getElementById('bioSummary').value,
        notes: document.getElementById('bioNotes').value
    };
    
    try {
        const response = await fetch(`/api/experiments/${currentExperimentId}/bioinformatics`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            document.getElementById('bioModal').style.display = 'none';
            document.getElementById('bioForm').reset();
            await loadExperimentDetail(currentExperimentId);
            showSuccess('Analysis added successfully');
        } else {
            showError('Failed to add analysis');
        }
    } catch (error) {
        console.error('Error adding analysis:', error);
        showError('Failed to add analysis');
    }
}

// Search experiments
async function searchExperiments(query) {
    if (!query) {
        displayExperiments(experiments);
        return;
    }
    
    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const results = await response.json();
        displayExperiments(results);
    } catch (error) {
        console.error('Error searching experiments:', error);
    }
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showSuccess(message) {
    alert(message); // Replace with a better notification system
}

function showError(message) {
    alert(message); // Replace with a better notification system
}
