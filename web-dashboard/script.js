// Campus Access Control Dashboard JavaScript

const API_BASE_URL = 'http://localhost:8000';

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupEventListeners();
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);
    
    // Auto-refresh logs every 30 seconds
    setInterval(refreshLogs, 30000);
});

function initializeDashboard() {
    refreshLogs();
    refreshAlerts();
    updateStatistics();
}

function setupEventListeners() {
    const uploadArea = document.getElementById('uploadArea');
    const videoInput = document.getElementById('videoInput');
    
    // Drag and drop functionality
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    
    // File input change
    videoInput.addEventListener('change', handleFileSelect);
}

function updateCurrentTime() {
    const now = new Date();
    const timeString = now.toLocaleString();
    document.getElementById('currentTime').textContent = timeString;
}

// File Upload Handlers
function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        processVideoFile(files[0]);
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        processVideoFile(file);
    }
}

async function processVideoFile(file) {
    // Validate file type
    if (!file.type.startsWith('video/')) {
        showError('Please select a valid video file.');
        return;
    }
    
    // Validate file size (10MB limit)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
        showError('File size must be less than 10MB.');
        return;
    }
    
    try {
        // Show upload progress
        showUploadProgress();
        
        // Create form data
        const formData = new FormData();
        formData.append('video_file', file);
        formData.append('gate_id', 'MAIN_GATE');
        
        // Upload and process video
        const response = await fetch(`${API_BASE_URL}/upload_video`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Hide progress and show results
        hideUploadProgress();
        showProcessingResults(result);
        
        // Refresh logs to show new entry
        setTimeout(refreshLogs, 1000);
        
    } catch (error) {
        console.error('Error processing video:', error);
        hideUploadProgress();
        showError('Failed to process video. Please try again.');
    }
}

function showUploadProgress() {
    document.getElementById('uploadProgress').style.display = 'block';
    document.getElementById('processingStatus').style.display = 'block';
    document.getElementById('resultsDisplay').style.display = 'none';
    
    // Simulate progress (in real implementation, use actual progress)
    let progress = 0;
    const interval = setInterval(() => {
        progress += 10;
        document.getElementById('progressFill').style.width = `${progress}%`;
        document.getElementById('progressText').textContent = `${progress}%`;
        
        if (progress >= 100) {
            clearInterval(interval);
        }
    }, 200);
}

function hideUploadProgress() {
    document.getElementById('uploadProgress').style.display = 'none';
    document.getElementById('processingStatus').style.display = 'none';
}

function showProcessingResults(result) {
    const resultsDisplay = document.getElementById('resultsDisplay');
    
    document.getElementById('detectedPlate').textContent = result.license_plate || 'Not detected';
    document.getElementById('verificationStatus').textContent = result.access_granted ? 'Authorized' : 'Unauthorized';
    document.getElementById('processingTime').textContent = `${result.processing_time || 'N/A'}s`;
    
    // Apply status styling
    const statusElement = document.getElementById('verificationStatus');
    statusElement.className = result.access_granted ? 'result-value status-granted' : 'result-value status-denied';
    
    resultsDisplay.style.display = 'block';
}

// Logs Management
async function refreshLogs() {
    try {
        const response = await fetch(`${API_BASE_URL}/logs?limit=50&offset=0`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayLogs(data.logs || []);
        updateStatistics();
        
    } catch (error) {
        console.error('Error fetching logs:', error);
        showError('Failed to fetch access logs.');
    }
}

function displayLogs(logs) {
    const tbody = document.getElementById('logsTableBody');
    tbody.innerHTML = '';
    
    logs.forEach(log => {
        const row = document.createElement('tr');
        
        const timestamp = new Date(log.timestamp).toLocaleString();
        const statusClass = log.access_granted ? 'status-granted' : 'status-denied';
        const statusText = log.access_granted ? 'Granted' : 'Denied';
        const alertBadge = log.alert_triggered ? '<span class="status-badge alert-badge">Alert</span>' : '';
        
        row.innerHTML = `
            <td>${timestamp}</td>
            <td>${log.gate_id || 'N/A'}</td>
            <td>${log.user_id || 'N/A'}</td>
            <td>${log.license_plate || 'N/A'}</td>
            <td>${log.verification_method || 'N/A'}</td>
            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            <td>${alertBadge}</td>
        `;
        
        tbody.appendChild(row);
    });
}

// Alerts Management
async function refreshAlerts() {
    try {
        const response = await fetch(`${API_BASE_URL}/alerts/recent`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayAlerts(data.alerts || []);
        
    } catch (error) {
        console.error('Error fetching alerts:', error);
    }
}

function displayAlerts(alerts) {
    const alertsList = document.getElementById('alertsList');
    alertsList.innerHTML = '';
    
    if (alerts.length === 0) {
        alertsList.innerHTML = '<p style="color: #64748b; text-align: center; padding: 1rem;">No recent alerts</p>';
        return;
    }
    
    alerts.forEach(alert => {
        const alertItem = document.createElement('div');
        alertItem.className = `alert-item ${alert.resolved ? 'resolved' : ''}`;
        
        const timestamp = new Date(alert.created_at).toLocaleString();
        const icon = alert.resolved ? 'fa-check-circle' : 'fa-exclamation-triangle';
        
        alertItem.innerHTML = `
            <i class="fas ${icon}"></i>
            <div style="flex: 1;">
                <div style="font-weight: 500;">${alert.message}</div>
                <div style="font-size: 0.8rem; color: #64748b;">${timestamp} - Gate: ${alert.gate_id}</div>
            </div>
        `;
        
        alertsList.appendChild(alertItem);
    });
}

// Statistics
function updateStatistics() {
    // This would typically fetch real statistics from the API
    // For now, we'll calculate from the current logs
    const logs = Array.from(document.querySelectorAll('#logsTableBody tr'));
    
    const total = logs.length;
    const granted = logs.filter(row => row.querySelector('.status-granted')).length;
    const denied = total - granted;
    const alerts = logs.filter(row => row.querySelector('.alert-badge')).length;
    
    document.getElementById('totalAccess').textContent = total;
    document.getElementById('grantedAccess').textContent = granted;
    document.getElementById('deniedAccess').textContent = denied;
    document.getElementById('activeAlerts').textContent = alerts;
}

// Filtering
function filterLogs() {
    const filterType = document.getElementById('filterType').value;
    const rows = document.querySelectorAll('#logsTableBody tr');
    
    rows.forEach(row => {
        let show = true;
        
        switch (filterType) {
            case 'granted':
                show = row.querySelector('.status-granted') !== null;
                break;
            case 'denied':
                show = row.querySelector('.status-denied') !== null;
                break;
            case 'alerts':
                show = row.querySelector('.alert-badge') !== null;
                break;
            default:
                show = true;
        }
        
        row.style.display = show ? '' : 'none';
    });
}

// Error Handling
function showError(message) {
    // Create a simple error notification
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #fee2e2;
        color: #991b1b;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ef4444;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        z-index: 1000;
        max-width: 300px;
    `;
    errorDiv.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <i class="fas fa-exclamation-circle"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(errorDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.parentNode.removeChild(errorDiv);
        }
    }, 5000);
}