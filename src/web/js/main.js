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

    document.getElementById('clearHistoryBtn').addEventListener('click', () => {
        showConfirmDialog(
            'Clear Download History',
            'This will permanently delete your entire download history. This action cannot be undone.',
            async () => {
                const res = await window.pywebview.api.clearHistory();
                if(res.success) {
                    historyListContainer.innerHTML = '';
                    historyListContainer.appendChild(emptyHistoryMsg);
                    emptyHistoryMsg.style.display = 'block';
                }
            }
        );
    });

    function showConfirmDialog(title, message, onConfirm) {
        const dialog = document.getElementById('confirmDialog');
        document.getElementById('confirmDialogTitle').innerText = title;
        document.getElementById('confirmDialogMessage').innerText = message;
        dialog.classList.add('active');
        
        const confirmBtn = document.getElementById('confirmDialogConfirm');
        const cancelBtn = document.getElementById('confirmDialogCancel');
        
        // Clone and replace to remove old listeners
        const newConfirm = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirm, confirmBtn);
        const newCancel = cancelBtn.cloneNode(true);
        cancelBtn.parentNode.replaceChild(newCancel, cancelBtn);
        
        newConfirm.addEventListener('click', () => {
            dialog.classList.remove('active');
            onConfirm();
        });
        newCancel.addEventListener('click', () => {
            dialog.classList.remove('active');
        });
    }

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
                    <button class="icon-button" title="Open Folder Location" onclick="window.pywebview.api.openPath('${(item.outputPath || '').replace(/\\/g, '\\\\')}')">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
                    </button>
                    ${item.url && item.url !== 'playlist' ? `<button class="icon-button" title="Download Again" onclick="window.redownloadFromHistory('${item.url}')"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg></button>` : ''}
                    <button class="icon-button" style="color: var(--danger);" title="Remove from History" onclick="window.deleteHistoryEntry(${item.index})">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                    </button>
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

    // Downloads Modal logic
    const activeDownloadsBtn = document.getElementById('activeDownloadsBtn');
    const downloadsModal = document.getElementById('downloadsModal');
    if (activeDownloadsBtn) {
        activeDownloadsBtn.addEventListener('click', () => {
            downloadsModal.classList.add('active');
        });
    }

    function updateDownloadsBadge() {
        const badge = document.getElementById('activeDownloadsBadge');
        const minibar = document.getElementById('activeDownloadsMiniBar');
        const minibarText = document.getElementById('minibarText');
        
        if (!badge) return;
        
        let activeCount = 0;
        document.querySelectorAll('.download-card').forEach(card => {
            const status = card.querySelector('.d-status').innerText;
            if (!['Completed', 'Failed', 'Cancelled', 'Error'].includes(status)) {
                activeCount++;
            }
        });

        if (activeCount > 0) {
            badge.style.display = 'flex';
            badge.innerText = activeCount;
            if(minibar) {
                minibar.style.display = 'flex';
                minibarText.innerText = activeCount === 1 ? '1 download in progress...' : `${activeCount} downloads in progress...`;
            }
        } else {
            badge.style.display = 'none';
            if(minibar) minibar.style.display = 'none';
        }
        
        // Also update empty state inside modal
        const emptyState = document.getElementById('emptyDownloads');
        const totalCount = document.querySelectorAll('.download-card').length;
        if (emptyState) {
            emptyState.style.display = totalCount === 0 ? 'block' : 'none';
        }
    }
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
            if (e.target.value.toLowerCase() === 'mp3') {
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

    urlInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            if (urlInput.value.trim().length > 0 && !fetchBtn.disabled) {
                fetchBtn.click();
            }
        }
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

        currentFetchResult = null;


        fetchBtn.disabled = true;
        fetchBtn.querySelector('.btn-text').style.display = 'none';
        fetchBtn.querySelector('.spinner').style.display = 'block';
        
        document.getElementById('previewEmpty').style.display = 'flex';
        document.getElementById('previewPlaylist').style.display = 'none';
        
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
        document.getElementById('previewEmpty').style.display = 'flex';
        document.getElementById('previewPlaylist').style.display = 'none';
        
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
            label.className = 'playlist-item-content';
            
            let thumbHtml = '';
            if (entry.thumbnail) {
                thumbHtml = `<div class="pl-thumb-wrapper"><img src="${entry.thumbnail}" class="pl-thumb"><span class="pl-duration">${entry.duration || ''}</span></div>`;
            } else {
                thumbHtml = `<div class="pl-thumb-wrapper empty-thumb"><span class="pl-duration">${entry.duration || ''}</span></div>`;
            }
            
            label.innerHTML = `
                ${thumbHtml}
                <div class="pl-details">
                    <div class="pl-title">${entry.title || `Video ${idx+1}`}</div>
                </div>
            `;
            
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
        
        const selectedEntries = playlistEntries.filter(e => selected.includes(e.url || e.webpage_url || e.id));
        
        document.getElementById('previewEmpty').style.display = 'none';
        const plContainer = document.getElementById('previewPlaylist');
        plContainer.style.display = 'flex';
        
        document.getElementById('previewPlaylistTitle').innerText = `Selected Videos (${selectedEntries.length})`;
        
        const container = document.getElementById('previewPlaylistItems');
        container.innerHTML = '';
        
        selectedEntries.forEach((entry, idx) => {
            const item = document.createElement('div');
            item.className = 'playlist-item';
            
            let thumbHtml = '';
            if (entry.thumbnail) {
                thumbHtml = `<div class="pl-thumb-wrapper" style="width: 80px; height: 45px;"><img src="${entry.thumbnail}" class="pl-thumb"><span class="pl-duration" style="font-size:0.6rem;">${entry.duration || ''}</span></div>`;
            } else {
                thumbHtml = `<div class="pl-thumb-wrapper empty-thumb" style="width: 80px; height: 45px;"><span class="pl-duration" style="font-size:0.6rem;">${entry.duration || ''}</span></div>`;
            }
            
            item.innerHTML = `
                <div class="playlist-item-content">
                    ${thumbHtml}
                    <div class="pl-details">
                        <div class="pl-title" style="font-size: 0.85rem;">${entry.title || `Video ${idx+1}`}</div>
                    </div>
                </div>
            `;
            container.appendChild(item);
        });
        
        if (outputPath.value) {
            downloadBtn.disabled = false;
        }
    });

    function getSelectedPlaylistUrls() {
        return Array.from(document.querySelectorAll('.playlist-checkbox:checked')).map(cb => cb.value);
    }

    // --- Video Preview ---
    function showVideoPreview(data) {
        document.getElementById('previewEmpty').style.display = 'none';
        const plContainer = document.getElementById('previewPlaylist');
        plContainer.style.display = 'flex';
        
        document.getElementById('previewPlaylistTitle').innerText = `Selected Video`;
        
        const container = document.getElementById('previewPlaylistItems');
        container.innerHTML = '';
        
        const item = document.createElement('div');
        item.className = 'playlist-item';
        
        let thumbHtml = '';
        if (data.thumbnail) {
            thumbHtml = `<div class="pl-thumb-wrapper" style="width: 80px; height: 45px;"><img src="${data.thumbnail}" class="pl-thumb"><span class="pl-duration" style="font-size:0.6rem;">${data.duration || ''}</span></div>`;
        } else {
            thumbHtml = `<div class="pl-thumb-wrapper empty-thumb" style="width: 80px; height: 45px;"><span class="pl-duration" style="font-size:0.6rem;">${data.duration || ''}</span></div>`;
        }
        
        item.innerHTML = `
            <div class="playlist-item-content">
                ${thumbHtml}
                <div class="pl-details">
                    <div class="pl-title" style="font-size: 0.95rem;">${data.title}</div>
                </div>
            </div>
        `;
        container.appendChild(item);
        
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
            
            setTimeout(() => {
                card.style.opacity = '0';
                setTimeout(() => {
                    card.remove();
                    updateDownloadsBadge();
                }, 300);
            }, 8000);
        } else {
            alert('Download Error: ' + (job.error || job.errorMsg || 'Unknown Error'));
        }
    });

    // Cancellation UI event delegation
    document.getElementById('downloadsList').addEventListener('click', (e) => {
        const cancelBtn = e.target.closest('.cancel-job-btn');
        if(cancelBtn) {
            const card = cancelBtn.closest('.download-card');
            if (card) {
                const id = card.dataset.id;
                window.pywebview.api.cancelDownload(id);
                cancelBtn.disabled = true;
                cancelBtn.innerHTML = '<span style="font-size:10px;">Stop...</span>';
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
                setTimeout(() => {
                    card.remove();
                    updateDownloadsBadge();
                }, 300);
            }, 5000);
        }
    });

    function createOrUpdateJobCard(job) {
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
        
        if (job.totalBytes) {
            const mb = (job.totalBytes / (1024 * 1024)).toFixed(1);
            card.querySelector('.d-size').innerText = `${mb} MB`;
            card.querySelector('.d-size').style.display = 'inline';
        } else {
            card.querySelector('.d-size').style.display = 'none';
        }
        
        if (job.speed) {
            card.querySelector('.d-speed').innerText = job.speed;
            card.querySelector('.d-speed').style.display = 'inline';
        } else if (job.status === 'Downloading...') {
            card.querySelector('.d-speed').innerText = 'Starting...';
            card.querySelector('.d-speed').style.display = 'inline';
        } else {
            card.querySelector('.d-speed').style.display = 'none';
        }
        
        if (job.eta) {
            card.querySelector('.d-eta').innerText = `ETA: ${job.eta}`;
            card.querySelector('.d-eta').style.display = 'inline';
        } else {
            card.querySelector('.d-eta').style.display = 'none';
        }
        
        updateDownloadsBadge();
    }
}

// ===== Custom Context Menu for Input Fields =====
// pywebview suppresses the native browser right-click menu,
// so we provide Cut/Copy/Paste/Select All for text inputs.
(function() {
    const ctxMenu = document.getElementById("ctxMenu");
    if (!ctxMenu) return;

    let targetInput = null;

    // Show on right-click over input/textarea elements
    document.addEventListener("contextmenu", function(e) {
        const el = e.target;
        if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
            e.preventDefault();
            targetInput = el;

            // Position menu at cursor
            ctxMenu.style.left = e.clientX + "px";
            ctxMenu.style.top = e.clientY + "px";
            ctxMenu.classList.add("visible");

            // Enable/disable cut based on readonly
            const cutItem = ctxMenu.querySelector('[data-action="cut"]');
            if (el.readOnly) {
                cutItem.classList.add("disabled");
            } else {
                cutItem.classList.remove("disabled");
            }
        } else {
            ctxMenu.classList.remove("visible");
        }
    });

    // Hide when clicking anywhere else
    document.addEventListener("click", function() {
        ctxMenu.classList.remove("visible");
    });

    // Handle menu item clicks
    ctxMenu.addEventListener("click", async function(e) {
        const action = e.target.closest(".ctx-menu-item")?.dataset.action;
        if (!action || !targetInput) return;

        targetInput.focus();

        switch (action) {
            case "cut":
                if (!targetInput.readOnly) {
                    document.execCommand("cut");
                }
                break;
            case "copy":
                document.execCommand("copy");
                break;
            case "paste":
                try {
                    const text = await window.pywebview.api.getClipboard();
                    if (text) {
                        // Insert at cursor position instead of replacing everything
                        const start = targetInput.selectionStart;
                        const end = targetInput.selectionEnd;
                        const current = targetInput.value;
                        targetInput.value = current.slice(0, start) + text + current.slice(end);
                        targetInput.selectionStart = targetInput.selectionEnd = start + text.length;
                        targetInput.dispatchEvent(new Event("input", { bubbles: true }));
                    }
                } catch (err) {
                    console.error("Paste failed:", err);
                }
                break;
            case "selectall":
                targetInput.select();
                break;
        }

        ctxMenu.classList.remove("visible");
    });
})();
