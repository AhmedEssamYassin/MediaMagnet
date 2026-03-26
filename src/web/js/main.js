// Wait for PyWebView to be ready
window.addEventListener('pywebviewready', function() {
    initApp();
});


let currentFetchResult = null;

window.triggerSettingsBrowse = async () => {
    try {
        const currentPath = document.getElementById('settingsDefaultPath').value || '';
        const path = await window.pywebview.api.browseDirectory(currentPath);
        if (path) {
            document.getElementById('settingsDefaultPath').value = path;
            document.getElementById('outputPath').value = path;
        }
    } catch (err) {
        console.error('Failed to open directory natively:', err);
    }
};

function initApp() {
    // Connect elements
    const urlInput = document.getElementById('urlInput');
    const fetchBtn = document.getElementById('fetchBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const browseBtn = document.getElementById('browseBtn');
    const outputPath = document.getElementById('outputPath');
    const themeToggle = document.getElementById('themeToggle');
    const emptyDownloads = document.getElementById('emptyDownloads');
    const globalSettingsModal = document.getElementById('globalSettingsModal');
    // Dismiss skeleton loader with fade
    document.getElementById('initialLoader').style.opacity = '0';
    setTimeout(() => {
        document.getElementById('initialLoader').style.display = 'none';
        document.querySelector('.app-container').style.opacity = '1';
    }, 300);


    window.pywebview.api.getSettings().then(settings => {
        if (settings.defaultPath) {
            outputPath.value = settings.defaultPath;
        }
        if (settings.theme === 'light') {
            document.body.classList.remove('dark-theme');
            document.getElementById('moonIcon').style.display = 'block';
            document.getElementById('sunIcon').style.display = 'none';
        }
        if (settings.maxConcurrent) {
            document.getElementById('maxConcurrentDownloads').value = settings.maxConcurrent;
        }
    }).catch(err => {
        console.error("Failed to load initial settings:", err);
    });


    themeToggle.addEventListener('click', () => {
        const isDark = document.body.classList.toggle('dark-theme');
        document.getElementById('moonIcon').style.display = isDark ? 'none' : 'block';
        document.getElementById('sunIcon').style.display = isDark ? 'block' : 'none';
        window.pywebview.api.saveTheme(isDark ? 'dark' : 'light');
    });


    document.getElementById('globalSettingsBtn').addEventListener('click', () => {
        console.log("Opening App Settings...");
        window.pywebview.api.getSettings().then(settings => {
            if (settings.defaultPath) document.getElementById('settingsDefaultPath').value = settings.defaultPath;
            if (settings.theme) document.getElementById('settingsTheme').value = settings.theme;
            if (settings.maxConcurrent) document.getElementById('maxConcurrentDownloads').value = settings.maxConcurrent;
            if (settings.maxConcurrentParts) document.getElementById('maxConcurrentParts').value = settings.maxConcurrentParts;
            if (settings.language) document.getElementById('settingsLanguage').value = settings.language;
            if (settings.notifications !== undefined) document.getElementById('settingsNotifications').checked = settings.notifications;
            if (settings.rememberPath !== undefined) document.getElementById('settingsAutoPath').checked = settings.rememberPath;
            
            if (settings.defaultFormat) {
                const formatRadio = document.querySelector(`input[name="format"][value="${settings.defaultFormat}"]`);
                if (formatRadio) {
                    formatRadio.checked = true;
                    formatRadio.dispatchEvent(new Event('change'));
                }
            }
            if (settings.defaultQuality) {
                document.getElementById('qualitySelect').value = settings.defaultQuality;
            }
            globalSettingsModal.classList.add('active');
        }).catch(err => {
            console.error("Failed to fetch settings for modal:", err);
            alert("Error loading settings. Please try again.");
        });
    });

    document.getElementById('cancelGlobalSettingsBtn').addEventListener('click', () => {
        globalSettingsModal.classList.remove('active');
    });

    document.getElementById('saveGlobalSettingsBtn').addEventListener('click', () => {
        const maxConc = document.getElementById('maxConcurrentDownloads').value;
        const maxParts = document.getElementById('maxConcurrentParts').value;
        const langCode = document.getElementById('settingsLanguage').value;
        const appTheme = document.getElementById('settingsTheme').value;
        const defaultPath = document.getElementById('settingsDefaultPath').value;
        const noteEnabled = document.getElementById('settingsNotifications').checked;
        const autoPathInfo = document.getElementById('settingsAutoPath').checked;
        
        if(maxConc < 1 || maxConc > 10) {
            alert("Max concurrent downloads must be between 1 and 10.");
            return;
        }
        if(maxParts < 1 || maxParts > 16) {
            alert("Max concurrent parts (per video) must be between 1 and 16.");
            return;
        }
        
        window.pywebview.api.saveSettings(maxConc, maxParts, langCode, noteEnabled, autoPathInfo, appTheme, defaultPath).then(res => {
            if(res.success) {
                // Apply theme visibly right away
                if (appTheme === 'light') {
                    document.body.classList.remove('dark-theme');
                    document.getElementById('moonIcon').style.display = 'block';
                    document.getElementById('sunIcon').style.display = 'none';
                } else {
                    document.body.classList.add('dark-theme');
                    document.getElementById('moonIcon').style.display = 'none';
                    document.getElementById('sunIcon').style.display = 'block';
                }
                globalSettingsModal.classList.remove('active');
            } else {
                alert("Failed to save settings: " + res.error);
            }
        });
    });

    // --- History Modal Logic ---
    const historyModal = document.getElementById('historyModal');
    const historyListContainer = document.getElementById('historyListContainer');
    const emptyHistoryMsg = document.getElementById('emptyHistoryMsg');

    document.getElementById('historyBtn').addEventListener('click', () => {
        loadHistory();
        historyModal.classList.add('active');
    });

    document.getElementById('closeHistoryBtn').addEventListener('click', () => {
        historyModal.classList.remove('active');
    });

    document.getElementById('clearHistoryBtn').addEventListener('click', async () => {
        if(confirm("Are you sure you want to clear your entire download history?")) {
            const res = await window.pywebview.api.clearHistory();
            if(res.success) {
                historyListContainer.innerHTML = '';
                historyListContainer.appendChild(emptyHistoryMsg);
                emptyHistoryMsg.style.display = 'block';
            } else {
                alert("Failed to clear history: " + res.error);
            }
        }
    });

    function loadHistory() {
        window.pywebview.api.getHistory().then(res => {
            if(res.success && res.history) {
                renderHistory(res.history);
            }
        });
    }

    function renderHistory(historyItems) {
        // Clear all except empty msg
        Array.from(historyListContainer.children).forEach(child => {
            if(child.id !== 'emptyHistoryMsg') child.remove();
        });

        if (!historyItems || historyItems.length === 0) {
            emptyHistoryMsg.style.display = 'block';
            return;
        }

        emptyHistoryMsg.style.display = 'none';

        // Sort new to old based on timestamp
        historyItems.sort((a,b) => new Date(b.timestamp) - new Date(a.timestamp));

        historyItems.forEach(item => {
            const card = document.createElement('div');
            card.className = 'history-card';
            
            let dateStr = 'Unknown Date';
            if (item.timestamp) {
                const d = new Date(item.timestamp);
                dateStr = d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            }

            let statusClass = 'status-badge status-completed';
            if(item.status === 'error') statusClass = 'status-badge status-failed';
            if(item.status === 'cancelled') statusClass = 'status-badge status-cancelled';

            card.innerHTML = `
                <img src="${item.thumbnail || ''}" onerror="this.onerror=null; this.src='data:image/svg+xml;utf8,<svg xmlns=\\\'http://www.w3.org/2000/svg\\\' width=\\\'100%\\\' height=\\\'100%\\\'><rect width=\\\'100%\\\' height=\\\'100%\\\' fill=\\\'%23333\\\'/><text x=\\\'50%\\\' y=\\\'50%\\\' fill=\\\'white\\\' font-family=\\\'sans-serif\\\' font-size=\\\'12px\\\' text-anchor=\\\'middle\\\' dy=\\\'.3em\\\'>Video</text></svg>';" class="history-img" alt="thumb">
                <div class="history-info">
                    <div class="history-title" title="${item.title}">${item.title || item.url}</div>
                    <div class="history-meta">
                        <span>🕒 ${dateStr}</span>
                        <span>📦 ${item.formatType || 'Auto'} • ${item.quality || 'Best'}</span>
                        <span class="${statusClass}">${item.status}</span>
                    </div>
                </div>
                <div class="history-actions">
                    <button class="btn icon-button-box" title="Open Folder Location" onclick="window.pywebview.api.openPath('${(item.outputPath || '').replace(/\\/g, '\\\\')}')">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
                    </button>
                    ${item.url && item.url !== 'playlist' ? `<button class="btn icon-button-box" title="Download Again" onclick="window.redownloadFromHistory('${item.url}')">⬇️</button>` : ''}
                    <button class="btn icon-button-box" title="Remove from History" onclick="window.deleteHistoryEntry(${item.index})">🗑️</button>
                </div>
            `;
            historyListContainer.appendChild(card);
        });
    }

    // Global helper for deleting a single history entry
    window.deleteHistoryEntry = async function(index) {
        const res = await window.pywebview.api.removeHistoryEntry(index);
        if (res.success) {
            loadHistory(); // Refresh the list
        } else {
            alert("Failed to remove entry: " + res.error);
        }
    };

    // Global helper for re-downloading from history
    window.redownloadFromHistory = function(url) {
        // Close the history modal
        document.getElementById('historyModal').classList.remove('active');
        // Set the URL
        const input = document.getElementById('urlInput');
        input.value = url;
        // Manually dispatch the input event so fetchBtn gets enabled
        input.dispatchEvent(new Event('input', { bubbles: true }));
        // Small delay to let DOM update, then click fetch
        setTimeout(() => {
            document.getElementById('fetchBtn').click();
        }, 100);
    };

    // --- Preferences Logic ---
    const formatRadios = document.querySelectorAll('input[name="format"]');
    const qualitySelect = document.getElementById('qualitySelect');

    // Fetch version and init update UI
    if (window.pywebview && window.pywebview.api && window.pywebview.api.getAppVersion) {
        window.pywebview.api.getAppVersion().then(ver => {
            console.log("Current App Version:", ver);
            document.getElementById('appVersion').innerText = `Version: ${ver}`;
        }).catch(err => console.error("Failed to fetch version:", err));
    } else {
        console.warn("PyWebView API not ready for version fetch.");
    }

    const checkUpdateBtn = document.getElementById('checkUpdateBtn');
    const installUpdateBtn = document.getElementById('installUpdateBtn');
    const updateStatus = document.getElementById('updateStatus');
    const updateProgressContainer = document.getElementById('updateProgressContainer');
    const updateProgressBar = document.getElementById('updateProgressBar');
    const updatePercent = document.getElementById('updatePercent');
    
    let updateDownloadUrl = null;

    checkUpdateBtn.addEventListener('click', async () => {
        checkUpdateBtn.disabled = true;
        checkUpdateBtn.innerText = 'Checking...';
        updateStatus.innerText = 'Connecting to server...';
        
        try {
            const res = await window.pywebview.api.checkForUpdates();
            if (res.success) {
                if (res.hasUpdate) {
                    updateStatus.innerHTML = `<span style="color: var(--accent); font-weight: 600;">Update Available: v${res.latestVersion}</span>`;
                    updateDownloadUrl = res.downloadUrl;
                    checkUpdateBtn.style.display = 'none';
                    installUpdateBtn.style.display = 'block';
                } else {
                    updateStatus.innerText = 'You are using the latest version.';
                    checkUpdateBtn.innerText = 'Check for Updates';
                    checkUpdateBtn.disabled = false;
                }
            } else {
                updateStatus.innerText = 'Error checking for updates.';
                checkUpdateBtn.disabled = false;
                checkUpdateBtn.innerText = 'Check for Updates';
            }
        } catch (err) {
            updateStatus.innerText = 'Failed to check: ' + err;
            checkUpdateBtn.disabled = false;
            checkUpdateBtn.innerText = 'Check for Updates';
        }
    });

    installUpdateBtn.addEventListener('click', () => {
        if (!updateDownloadUrl) return;
        
        installUpdateBtn.disabled = true;
        installUpdateBtn.innerText = 'Starting...';
        updateProgressContainer.style.display = 'block';
        
        window.pywebview.api.performUpdate(updateDownloadUrl);
    });

    window.addEventListener('update_progress', (e) => {
        const p = e.detail.progress;
        const pct = Math.floor(p * 100);
        updateProgressBar.style.width = pct + '%';
        updatePercent.innerText = pct + '%';
        installUpdateBtn.innerText = 'Downloading...';
    });

    window.addEventListener('update_complete', () => {
        installUpdateBtn.innerText = 'Restarting App...';
        installUpdateBtn.style.background = 'var(--success)';
        updateStatus.innerText = 'Download complete. Launching updater...';
    });

    window.addEventListener('update_error', (e) => {
        alert("Update Error: " + e.detail.error);
        installUpdateBtn.disabled = false;
        installUpdateBtn.innerText = 'Try Again';
        updateStatus.innerText = 'Update failed.';
    });

    // --- Auto Update Toast ---
    const updateToast = document.getElementById('updateToast');
    const viewUpdateBtn = document.getElementById('viewUpdateBtn');
    const closeToastBtn = document.getElementById('closeToastBtn');

    const showUpdateToast = () => {
        updateToast.classList.add('active');
    };

    const hideUpdateToast = () => {
        updateToast.classList.remove('active');
    };

    closeToastBtn.addEventListener('click', hideUpdateToast);
    
    viewUpdateBtn.addEventListener('click', () => {
        hideUpdateToast();
        // Open global settings modal and scroll to update section
        document.getElementById('globalSettingsBtn').click();
        setTimeout(() => {
            document.getElementById('updateSection').scrollIntoView({ behavior: 'smooth' });
        }, 500);
    });

    const autoCheckForUpdates = async () => {
        try {
            const res = await window.pywebview.api.checkForUpdates();
            if (res.success && res.hasUpdate) {
                showUpdateToast();
            }
        } catch (err) {
            console.error("Auto-update check failed:", err);
        }
    };

    // Trigger auto-check after 2 seconds
    setTimeout(autoCheckForUpdates, 2000);

    // Format selection listener

    const savePreferencesToBackend = () => {
        const activeFormat = document.querySelector('input[name="format"]:checked').value;
        const activeQuality = qualitySelect.value;
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.savePreferences(activeFormat, activeQuality);
        }
    };

    formatRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (e.target.value === 'MP3') {
                qualitySelect.disabled = true;
                qualitySelect.parentElement.style.opacity = '0.5';
            } else {
                qualitySelect.disabled = false;
                qualitySelect.parentElement.style.opacity = '1';
            }
            savePreferencesToBackend();
        });
    });
    
    qualitySelect.addEventListener('change', savePreferencesToBackend);

    // URL Input listener
    urlInput.addEventListener('input', () => {
        fetchBtn.disabled = urlInput.value.trim().length === 0;
        downloadBtn.disabled = true;
    });

    // Path Browse
    browseBtn.addEventListener('click', () => {
        window.pywebview.api.browseDirectory(outputPath.value).then(path => {
            if (path) outputPath.value = path;
        });
    });

    // Open Selected OS Folder Location
    const openFolderBtn = document.getElementById('openFolderBtn');
    if (openFolderBtn) {
        openFolderBtn.addEventListener('click', async () => {
            const path = outputPath.value;
            if (path) {
                const res = await window.pywebview.api.openPath(path);
                if (!res.success) {
                    alert('Could not open folder: ' + res.error);
                }
            } else {
                alert('Please select or enter a save location first.');
            }
        });
    }

    // Fetch Button
    fetchBtn.addEventListener('click', async () => {
        const url = urlInput.value.trim();
        if (!url) return;


        fetchBtn.disabled = true;
        fetchBtn.querySelector('.btn-text').style.display = 'none';
        fetchBtn.querySelector('.spinner').style.display = 'block';
        
        document.getElementById('previewEmpty').style.display = 'block';
        document.getElementById('previewContent').style.display = 'none';
        
        try {
            const result = await window.pywebview.api.fetchVideoInfo(url);
            
            if (!result.success) {
                alert('Failed to fetch: ' + result.error);
                return;
            }

            currentFetchResult = result;
            
            if (result.isPlaylist) {
                showPlaylistModal(result.raw);
            } else {
                showVideoPreview({
                    title: result.title,
                    duration: result.duration,
                    thumbnail: result.thumbnail,
                    url: url
                });
            }
        } catch (e) {
            alert('Error: ' + e);
        } finally {
            fetchBtn.disabled = false;
            fetchBtn.querySelector('.btn-text').style.display = 'block';
            fetchBtn.querySelector('.spinner').style.display = 'none';
        }
    });

    // Download Button
    downloadBtn.addEventListener('click', () => {
        if (!currentFetchResult || !outputPath.value) {
            alert("Please fetch a video and select an output path.");
            return;
        }

        const format = document.querySelector('input[name="format"]:checked').value;
        const quality = document.getElementById('qualitySelect').value;
        const path = outputPath.value;

        const finalUrl = currentFetchResult.url || urlInput.value;

        if (currentFetchResult.isPlaylist && currentFetchResult.raw.entries) {
            // Playlist downloads are dispatched as multiple parallel jobs
            const selectedUrls = getSelectedPlaylistUrls();
            window.pywebview.api.startPlaylistDownload(format, quality, path, selectedUrls).then(res => {
                if(!res.success) alert("Failed to start download: " + res.error);
            });
        } else {

            window.pywebview.api.startDownload(finalUrl, format, quality, path).then(res => {
                if(!res.success) alert("Failed to start download: " + res.error);
            });
        }
        

        urlInput.value = '';
        fetchBtn.disabled = true;
        downloadBtn.disabled = true;
        document.getElementById('previewEmpty').style.display = 'block';
        document.getElementById('previewContent').style.display = 'none';
        
        currentFetchResult = null;
    });

    // --- Playlist Modal Logic ---
    const playlistModal = document.getElementById('playlistModal');
    let playlistEntries = [];

    function showPlaylistModal(rawData) {
        playlistEntries = rawData.entries || [];
        document.getElementById('playlistInfo').innerText = `We found ${playlistEntries.length} videos in this playlist.`;
        
        const container = document.getElementById('playlistItems');
        container.innerHTML = '';
        
        playlistEntries.forEach((entry, idx) => {
            if(!entry) return;
            const item = document.createElement('div');
            item.className = 'playlist-item';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.checked = true;
            checkbox.value = entry.url || entry.webpage_url || entry.id;
            checkbox.className = 'playlist-checkbox';
            checkbox.id = 'pl_item_' + idx;
            
            const label = document.createElement('label');
            label.htmlFor = 'pl_item_' + idx;
            label.innerText = entry.title || `Video ${idx+1}`;
            
            item.appendChild(checkbox);
            item.appendChild(label);
            container.appendChild(item);
        });
        
        playlistModal.classList.add('active');
    }

    document.getElementById('selectAllBtn').addEventListener('click', () => {
        document.querySelectorAll('.playlist-checkbox').forEach(cb => cb.checked = true);
    });
    
    document.getElementById('deselectAllBtn').addEventListener('click', () => {
        document.querySelectorAll('.playlist-checkbox').forEach(cb => cb.checked = false);
    });

    document.getElementById('cancelPlaylistBtn').addEventListener('click', () => {
        playlistModal.classList.remove('active');
        currentFetchResult = null;
    });

    document.getElementById('confirmPlaylistBtn').addEventListener('click', () => {
        playlistModal.classList.remove('active');
        const selected = getSelectedPlaylistUrls();
        if (selected.length === 0) {
            alert("No videos selected.");
            return;
        }
        
        // Show first selected in preview just as visual feedback
        const firstSelectedEntry = playlistEntries.find(e => (e.url || e.webpage_url || e.id) === selected[0]);
        if(firstSelectedEntry) {
            showVideoPreview({
                title: "[Playlist] " + (firstSelectedEntry.title || "Selected Videos"),
                duration: "Multiple",
                thumbnail: firstSelectedEntry.thumbnail || "",
                url: null // Handled differently in download loop
            });
        }
    });

    function getSelectedPlaylistUrls() {
        return Array.from(document.querySelectorAll('.playlist-checkbox:checked')).map(cb => cb.value);
    }

    // --- Video Preview ---
    function showVideoPreview(data) {
        document.getElementById('previewEmpty').style.display = 'none';
        document.getElementById('previewContent').style.display = 'flex';
        
        const thumbImg = document.getElementById('thumbnail');
        thumbImg.onerror = function() {
            this.onerror = null;
            this.src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%"><rect width="100%" height="100%" fill="%23333"/><text x="50%" y="50%" fill="white" font-family="sans-serif" text-anchor="middle" dy=".3em">Video</text></svg>';
        };
        thumbImg.src = data.thumbnail || 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%"><rect width="100%" height="100%" fill="%23333"/><text x="50%" y="50%" fill="white" font-family="sans-serif" text-anchor="middle" dy=".3em">Video</text></svg>';
        
        document.getElementById('videoTitle').innerText = data.title;
        document.getElementById('videoDuration').innerText = data.duration;
        
        currentFetchResult.url = data.url; // Ensure we track the URL
        
        if (outputPath.value) {
            downloadBtn.disabled = false;
        }
    }
    
    outputPath.addEventListener('input', () => {
        if(currentFetchResult && outputPath.value) downloadBtn.disabled = false;
        else downloadBtn.disabled = true;
    });

    // ===== Event Listeners from Python =====
    window.addEventListener('download_added', (e) => {
        const job = e.detail;
        createOrUpdateJobCard(job);
    });

    window.addEventListener('download_start', (e) => {
        const job = e.detail;
        createOrUpdateJobCard({
            ...job,
            status: 'Downloading...'
        });
    });

    window.addEventListener('download_progress', (e) => {
        const job = e.detail;
        createOrUpdateJobCard(job);
    });

    window.addEventListener('download_complete', (e) => {
        const job = e.detail;
        createOrUpdateJobCard({
            ...job,
            status: 'Completed',
            progress: 1.0,
            speed: '',
            eta: ''
        });
        setTimeout(() => {
            const card = document.querySelector(`.download-card[data-id="${job.id}"]`);
            if (card) {
                card.style.opacity = '0';
                setTimeout(() => card.remove(), 300);
            }
        }, 5000);
    });

    window.addEventListener('download_error', (e) => {
        const job = e.detail;
        if (!job) return; // Prevent crash when job is null for early-validation fail
        const card = document.querySelector(`.download-card[data-id="${job.id}"]`);
        if (card) {
            card.querySelector('.d-status').innerText = 'Error';
            card.querySelector('.d-status').style.color = 'var(--danger)';
            card.querySelector('.progress-bar-fill').style.background = 'var(--danger)';
            card.querySelector('.download-meta').innerText = job.error || job.errorMsg || 'Failed';
            
            // Hide cancel button on fail
            const btn = card.querySelector('.cancel-job-btn');
            if(btn) btn.style.display = 'none';
        } else {
            alert('Download Error: ' + (job.error || job.errorMsg || 'Unknown Error'));
        }
    });

    // Cancellation UI event delegation
    document.getElementById('downloadsList').addEventListener('click', (e) => {
        if(e.target.classList.contains('cancel-job-btn')) {
            const card = e.target.closest('.download-card');
            if (card) {
                const id = card.dataset.id;
                window.pywebview.api.cancelDownload(id);
                e.target.disabled = true;
                e.target.innerText = 'Stopping...';
            }
        }
    });

    window.addEventListener('download_cancelled', (e) => {
        const job = e.detail;
        const card = document.querySelector(`.download-card[data-id="${job.id}"]`);
        if (card) {
            card.querySelector('.d-status').innerText = 'Cancelled';
            card.querySelector('.d-status').style.color = 'var(--danger)';
            card.querySelector('.progress-bar-fill').style.background = 'var(--danger)';
            card.querySelector('.download-meta').innerText = 'User stop';
            
            const btn = card.querySelector('.cancel-job-btn');
            if(btn) btn.style.display = 'none';
            
            setTimeout(() => {
                card.style.opacity = '0';
                setTimeout(() => card.remove(), 300);
            }, 5000);
        }
    });

    function createOrUpdateJobCard(job) {
        document.getElementById('emptyDownloads').style.display = 'none';
        const list = document.getElementById('downloadsList');
        let card = document.querySelector(`.download-card[data-id="${job.id}"]`);
        
        if (!card) {
            const template = document.getElementById('downloadCardTemplate');
            card = template.content.cloneNode(true).firstElementChild;
            card.dataset.id = job.id;
            list.appendChild(card);
        }

        card.querySelector('.d-title').innerText = job.title || 'Fetching...';
        
        if (job.status) {
            card.querySelector('.d-status').innerText = job.status;
            // Hide cancel button if completed or failed
            if (['Completed', 'Failed', 'Cancelled', 'Error'].includes(job.status)) {
                const btn = card.querySelector('.cancel-job-btn');
                if(btn) btn.style.display = 'none';
            }
        }
        
        const pct = Math.floor((job.progress || 0) * 100);
        card.querySelector('.progress-bar-fill').style.width = pct + '%';
        card.querySelector('.d-percent').innerText = pct + '%';
        
        if (job.speed || job.eta) {
            let text = job.speed || '';
            if (job.eta) text += text ? ` • ETA: ${job.eta}` : `ETA: ${job.eta}`;
            card.querySelector('.d-speed').innerText = text;
        } else if (job.status === 'Downloading...') {
            card.querySelector('.d-speed').innerText = 'Starting...';
        }
    }
}
