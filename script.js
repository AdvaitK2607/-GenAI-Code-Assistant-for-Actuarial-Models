const API_BASE = "http://127.0.0.1:5000";

// DOM Elements
const evaluateBtn = document.getElementById("evaluateBtn");
const clearBtn = document.getElementById("clearBtn");
const formatBtn = document.getElementById("formatBtn");
const exportBtn = document.getElementById("exportBtn");
const promptTextarea = document.getElementById("prompt");
const fileInput = document.getElementById("fileInput");
const fileList = document.getElementById("fileList");
const charCount = document.querySelector('.char-count');
const loading = document.getElementById("loading");

const tabs = document.querySelectorAll(".tab");
const tabContents = document.querySelectorAll(".tab-content");

// Tab functionality
tabs.forEach(tab => {
    tab.addEventListener("click", () => {
        tabs.forEach(t => t.classList.remove("active"));
        tab.classList.add("active");

        tabContents.forEach(tc => tc.classList.remove("active"));
        document.getElementById(tab.dataset.tab).classList.add("active");
    });
});

// Character count update
promptTextarea.addEventListener('input', () => {
    const count = promptTextarea.value.length;
    charCount.textContent = ${count} characters;
});

// File input handling
fileInput.addEventListener('change', () => {
    fileList.innerHTML = '';
    Array.from(fileInput.files).forEach(file => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <i class="fas fa-file"></i>
            <span>${file.name}</span>
            <i class="fas fa-times" style="cursor: pointer; margin-left: 8px;" 
               onclick="removeFile('${file.name}')"></i>
        `;
        fileList.appendChild(fileItem);
    });
});

// Remove file function
window.removeFile = (fileName) => {
    const dt = new DataTransfer();
    const files = fileInput.files;

    for (let i = 0; i < files.length; i++) {
        if (files[i].name !== fileName) {
            dt.items.add(files[i]);
        }
    }

    fileInput.files = dt.files;
    fileInput.dispatchEvent(new Event('change'));
};

// Format button functionality
formatBtn.addEventListener('click', () => {
    const prompt = promptTextarea.value;
    if (prompt.trim()) {
        // Simple formatting - in a real app, you might use a code formatter library
        promptTextarea.value = prompt
            .replace(/\n\s*\n/g, '\n\n') // Normalize line breaks
            .replace(/^\s+|\s+$/g, ''); // Trim whitespace
    }
});

// Export button functionality
exportBtn.addEventListener('click', () => {
    const activeTab = document.querySelector('.tab.active').dataset.tab;
    const content = document.getElementById(activeTab).innerHTML;

    if (!content.trim()) {
        alert('No content to export');
        return;
    }

    const blob = new Blob([content], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = analysis-${activeTab}-${new Date().toISOString().split('T')[0]}.html;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
});

// Main analysis function
evaluateBtn.onclick = async () => {
    const prompt = promptTextarea.value.trim();
    const model = document.getElementById("modelSelect").value;
    const files = fileInput.files;

    if (!prompt) {
        showNotification('Please enter a prompt!', 'error');
        return;
    }

    const fd = new FormData();
    fd.append("prompt", prompt);
    fd.append("model", model);
    for (const f of files) fd.append("files", f);

    loading.classList.remove("hidden");
    evaluateBtn.disabled = true;

    try {
        const res = await fetch(${API_BASE}/analyze, {
            method: "POST",
            body: fd
        });

        if (!res.ok) {
            throw new Error(Server responded with ${res.status});
        }

        const data = await res.json();

        if (data.error) {
            showNotification(data.error, 'error');
            document.getElementById("explanation").innerText = data.error;
            return;
        }

        const sections = data.content.split(/### /g);
        document.getElementById("explanation").innerHTML =
            marked.parse(sections.find(s => s.startsWith("Explanation")) || "No explanation provided.");
        document.getElementById("code").innerHTML =
            marked.parse(sections.find(s => s.startsWith("Code")) || "No code found.");
        document.getElementById("complexity").innerHTML =
            marked.parse(sections.find(s => s.startsWith("Time & Space Complexity")) || "No analysis found.");

        updateHistory(prompt);
        showNotification('Analysis completed successfully!', 'success');

    } catch (err) {
        console.error('Analysis error:', err);
        showNotification('Error: ' + err.message, 'error');
    } finally {
        loading.classList.add("hidden");
        evaluateBtn.disabled = false;
    }
};

// Clear button functionality
clearBtn.onclick = () => {
    promptTextarea.value = "";
    fileInput.value = "";
    fileList.innerHTML = "";
    charCount.textContent = "0 characters";
    document.querySelectorAll(".tab-content").forEach(c => c.innerHTML = "");
};

// History functionality
function updateHistory(entry) {
    const historyList = document.getElementById("historyList");
    const emptyMsg = historyList.querySelector('.history-empty');

    if (emptyMsg) {
        emptyMsg.remove();
    }

    // Check if entry already exists
    const existingEntries = Array.from(historyList.children);
    const existing = existingEntries.find(item =>
        item.textContent.includes(entry.slice(0, 50))
    );

    if (existing) {
        historyList.removeChild(existing);
    }

    const item = document.createElement("div");
    item.textContent = entry.slice(0, 60) + (entry.length > 60 ? "..." : "");
    item.title = entry;

    item.addEventListener("click", () => {
        promptTextarea.value = entry;
        charCount.textContent = ${entry.length} characters;
    });

    historyList.prepend(item);

    // Keep only last 10 items
    if (historyList.children.length > 10) {
        historyList.removeChild(historyList.lastChild);
    }
}

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = notification notification-${type};
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation' : 'info'}-circle"></i>
        <span>${message}</span>
    `;

    // Add styles if not already added
    if (!document.querySelector('#notification-styles')) {
        const styles = document.createElement('style');
        styles.id = 'notification-styles';
        styles.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 12px 20px;
                border-radius: 8px;
                color: white;
                font-weight: 500;
                z-index: 1000;
                display: flex;
                align-items: center;
                gap: 10px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                transform: translateX(400px);
                transition: transform 0.3s ease;
            }
            .notification-success { background: var(--success); }
            .notification-error { background: var(--error); }
            .notification-info { background: var(--primary); }
            .notification.show { transform: translateX(0); }
        `;
        document.head.appendChild(styles);
    }

    document.body.appendChild(notification);

    setTimeout(() => notification.classList.add('show'), 100);
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    // Load any saved history from localStorage
    const savedHistory = JSON.parse(localStorage.getItem('analysisHistory') || '[]');
    savedHistory.forEach(entry => updateHistory(entry));

    // Add keyboard shortcut (Ctrl+Enter to analyze)
    promptTextarea.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            evaluateBtn.click();
        }
    });
});

// Save history to localStorage when page unloads
window.addEventListener('beforeunload', () => {
    const historyItems = Array.from(document.querySelectorAll('#historyList div'))
        .map(item => item.title || item.textContent)
        .filter(text => text && !text.includes('No analyses yet'));

    localStorage.setItem('analysisHistory', JSON.stringify(historyItems));
});
