// Smart Campus Access Control - Frontend JavaScript
// Connects to FastAPI backend for OCR video processing

class OCRDashboard {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000/api';
        this.stats = {
            successCount: 0,
            failedCount: 0,
            totalProcessingTime: 0,
            processedVideos: 0
        };
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadStats();
        this.loadRecentActivity();
    }

    setupEventListeners() {
        const uploadArea = document.getElementById('uploadArea');
        const videoInput = document.getElementById('videoInput');

        // File input change
        videoInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileUpload(e.target.files[0]);
            }
        });

        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileUpload(files[0]);
            }
        });
    }

    async handleFileUpload(file) {
        // Validate file
        if (!this.validateFile(file)) {
            return;
        }

        // Show processing status
        this.showProcessingStatus();

        try {
            // Upload and process video
            const result = await this.uploadVideo(file);
            
            // Show results
            this.showResults(result);
            
            // Update stats
            this.updateStats(result);
            
            // Add to activity
            this.addActivity(result);
            
            // Show success toast
            this.showToast('Video processed successfully!', 'success');
            
        } catch (error) {
            console.error('Upload error:', error);
            this.showError(error.message);
            this.showToast('Failed to process video', 'error');
        }
    }

    validateFile(file) {
        // Check file type
        const allowedTypes = ['video/mp4', 'video/avi', 'video/mov'];
        if (!allowedTypes.includes(file.type)) {
            this.showToast('Please upload a valid video file (MP4, AVI, MOV)', 'error');
            return false;
        }

        // Check file size (10MB limit)
        const maxSize = 10 * 1024 * 1024; // 10MB
        if (file.size > maxSize) {
            this.showToast('File size must be less than 10MB', 'error');
            return false;
        }

        return true;
    }

    async uploadVideo(file) {
        const formData = new FormData();
        formData.append('video_file', file);
        formData.append('gate_id', 'WEB_DASHBOARD');

        const response = await fetch(`${this.apiBaseUrl}/vehicles/upload_video`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Upload failed');
        }

        return await response.json();
    }

    showProcessingStatus() {
        document.getElementById('uploadArea').style.display = 'none';
        document.getElementById('resultContainer').style.display = 'none';
        document.getElementById('processingStatus').style.display = 'block';

        // Animate progress bar
        this.animateProgress();
    }

    animateProgress() {
        const progressFill = document.getElementById('progressFill');
        const processingMessage = document.getElementById('processingMessage');
        
        const messages = [
            'Uploading video...',
            'Extracting frames...',
            'Analyzing with OCR...',
            'Processing license plate...',
            'Verifying against database...'
        ];

        let progress = 0;
        let messageIndex = 0;

        const interval = setInterval(() => {
            progress += Math.random() * 15 + 5;
            
            if (progress > 100) {
                progress = 100;
                clearInterval(interval);
            }

            progressFill.style.width = `${progress}%`;

            // Update message
            if (messageIndex < messages.length - 1 && progress > (messageIndex + 1) * 20) {
                messageIndex++;
                processingMessage.textContent = messages[messageIndex];
            }
        }, 300);
    }

    showResults(result) {
        document.getElementById('processingStatus').style.display = 'none';
        document.getElementById('resultContainer').style.display = 'block';

        // Update result icon and title
        const resultIcon = document.getElementById('resultIcon');
        const resultTitle = document.getElementById('resultTitle');
        
        if (result.ocr_results && result.ocr_results.license_plate) {
            resultIcon.innerHTML = '<i class="fas fa-check-circle"></i>';
            resultIcon.className = 'result-icon success';
            resultTitle.textContent = 'License Plate Detected';
        } else {
            resultIcon.innerHTML = '<i class="fas fa-times-circle"></i>';
            resultIcon.className = 'result-icon error';
            resultTitle.textContent = 'No License Plate Found';
        }

        // Update result values
        document.getElementById('licensePlate').textContent = 
            result.ocr_results?.license_plate || 'Not detected';
        
        document.getElementById('confidence').textContent = 
            result.ocr_results?.confidence ? `${(result.ocr_results.confidence * 100).toFixed(1)}%` : 'N/A';
        
        document.getElementById('accessStatus').textContent = 
            result.verification?.access_granted ? 'Access Granted' : 'Access Denied';
        
        document.getElementById('processingTime').textContent = 
            result.processing_time ? `${result.processing_time.toFixed(1)}s` : 'N/A';

        // Style access status
        const accessStatusElement = document.getElementById('accessStatus');
        if (result.verification?.access_granted) {
            accessStatusElement.style.color = 'var(--success-color)';
        } else {
            accessStatusElement.style.color = 'var(--danger-color)';
        }
    }

    showError(message) {
        document.getElementById('processingStatus').style.display = 'none';
        document.getElementById('resultContainer').style.display = 'block';

        const resultIcon = document.getElementById('resultIcon');
        const resultTitle = document.getElementById('resultTitle');
        
        resultIcon.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
        resultIcon.className = 'result-icon error';
        resultTitle.textContent = 'Processing Failed';

        // Clear result values
        document.getElementById('licensePlate').textContent = 'Error';
        document.getElementById('confidence').textContent = 'N/A';
        document.getElementById('accessStatus').textContent = 'Failed';
        document.getElementById('processingTime').textContent = 'N/A';
    }

    updateStats(result) {
        if (result.ocr_results?.license_plate) {
            this.stats.successCount++;
        } else {
            this.stats.failedCount++;
        }

        if (result.processing_time) {
            this.stats.totalProcessingTime += result.processing_time;
            this.stats.processedVideos++;
        }

        // Update UI
        document.getElementById('successCount').textContent = this.stats.successCount;
        document.getElementById('failedCount').textContent = this.stats.failedCount;
        
        const avgTime = this.stats.processedVideos > 0 ? 
            (this.stats.totalProcessingTime / this.stats.processedVideos).toFixed(1) : 0;
        document.getElementById('avgTime').textContent = `${avgTime}s`;
    }

    addActivity(result) {
        const activityList = document.getElementById('activityList');
        const activityItem = document.createElement('div');
        activityItem.className = 'activity-item';

        const isSuccess = result.ocr_results?.license_plate;
        const iconClass = isSuccess ? 'success' : 'warning';
        const iconSymbol = isSuccess ? 'fas fa-check' : 'fas fa-exclamation';
        const statusClass = result.verification?.access_granted ? 'granted' : 'denied';
        const statusText = result.verification?.access_granted ? 'Access Granted' : 'Access Denied';

        activityItem.innerHTML = `
            <div class="activity-icon ${iconClass}">
                <i class="${iconSymbol}"></i>
            </div>
            <div class="activity-content">
                <div class="activity-title">
                    ${isSuccess ? `License plate detected: ${result.ocr_results.license_plate}` : 'No license plate detected'}
                </div>
                <div class="activity-time">Just now</div>
            </div>
            <div class="activity-status ${statusClass}">${statusText}</div>
        `;

        // Add to top of list
        activityList.insertBefore(activityItem, activityList.firstChild);

        // Remove old items (keep only 5)
        while (activityList.children.length > 5) {
            activityList.removeChild(activityList.lastChild);
        }
    }

    loadStats() {
        // Load stats from localStorage or API
        const savedStats = localStorage.getItem('ocrDashboardStats');
        if (savedStats) {
            this.stats = { ...this.stats, ...JSON.parse(savedStats) };
            this.updateStatsDisplay();
        }
    }

    updateStatsDisplay() {
        document.getElementById('successCount').textContent = this.stats.successCount;
        document.getElementById('failedCount').textContent = this.stats.failedCount;
        
        const avgTime = this.stats.processedVideos > 0 ? 
            (this.stats.totalProcessingTime / this.stats.processedVideos).toFixed(1) : 0;
        document.getElementById('avgTime').textContent = `${avgTime}s`;
    }

    saveStats() {
        localStorage.setItem('ocrDashboardStats', JSON.stringify(this.stats));
    }

    loadRecentActivity() {
        // This would typically load from an API
        // For now, we'll use the existing sample data
    }

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'times-circle' : 'info-circle'}"></i>
                <span>${message}</span>
            </div>
        `;

        toastContainer.appendChild(toast);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }

    // Save stats when page unloads
    beforeUnload() {
        this.saveStats();
    }
}

// Global functions for HTML onclick handlers
function resetUpload() {
    document.getElementById('uploadArea').style.display = 'block';
    document.getElementById('processingStatus').style.display = 'none';
    document.getElementById('resultContainer').style.display = 'none';
    document.getElementById('videoInput').value = '';
}

function viewDetails() {
    // This could open a modal with more detailed information
    dashboard.showToast('Detailed view coming soon!', 'info');
}

function loadRecentActivity() {
    dashboard.loadRecentActivity();
    dashboard.showToast('Activity refreshed', 'success');
}

// Initialize dashboard when page loads
let dashboard;

document.addEventListener('DOMContentLoaded', () => {
    dashboard = new OCRDashboard();
    
    // Save stats before page unload
    window.addEventListener('beforeunload', () => {
        dashboard.beforeUnload();
    });
});

// API Health Check
async function checkAPIHealth() {
    try {
        const response = await fetch('http://localhost:8000/health');
        if (response.ok) {
            document.querySelector('.status-indicator').className = 'status-indicator online';
            document.querySelector('.header-info span:last-child').textContent = 'System Online';
        } else {
            throw new Error('API not responding');
        }
    } catch (error) {
        document.querySelector('.status-indicator').className = 'status-indicator offline';
        document.querySelector('.header-info span:last-child').textContent = 'System Offline';
        console.error('API health check failed:', error);
    }
}

// Check API health every 30 seconds
setInterval(checkAPIHealth, 30000);
checkAPIHealth(); // Initial check