"""
Controller for coordinating downloads, managing job state, and bridging services.
"""

import threading
from concurrent.futures import ThreadPoolExecutor
from .download_manager import DownloadManager
from ..data_models import DownloadConfig, PlaylistInfo
from ..services import HistoryService
from ..services import DesktopNotifier
from ..utils.file_utils import sanitizeFilename
from .events import EventEmitter, EventType
from .download_job import DownloadJob, DownloadStatus

class DownloadController:
    """Coordinates download operations and manages state"""
    
    def __init__(self):
        self.videoInfo = None
        self.historyService = HistoryService()
        self.notifier = DesktopNotifier()
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.jobs = {} # dictionary mapping jobId to DownloadJob instance
    
    def fetchVideoInfo(self, url, onSuccess=None, onError=None, onComplete=None):
        """Fetch video information in a background thread"""
        def fetchThread():
            try:
                self.videoInfo = DownloadManager.getVideoInfo(url)
                if onSuccess: onSuccess(self.videoInfo)
                EventEmitter.emit(EventType.FETCH_COMPLETE, self.videoInfo)
            except Exception as e:
                if onError: onError(str(e))
                EventEmitter.emit(EventType.FETCH_ERROR, str(e))
            finally:
                if onComplete: onComplete()
        
        self.executor.submit(fetchThread)
    
    def startDownload(self, config, selectedVideos=None, mainTitle=None):
        """
        Start download in a background thread pool
        
        Args:
            config: DownloadConfig object
            selectedVideos: List of URLs to download (if playlist). If None, downloads all.
            mainTitle: Optional main title for single video
        """
        try:
            config.validate()
        except ValueError as e:
            EventEmitter.emit(EventType.DOWNLOAD_ERROR, None, str(e))
            return
        
        if isinstance(self.videoInfo, PlaylistInfo):
            playlistInfo: PlaylistInfo = self.videoInfo
            videosToDownload = playlistInfo.videos
            if selectedVideos:
                videosToDownload = [v for v in videosToDownload if v['url'] in selectedVideos]
                
            for video in videosToDownload:
                sanTitle = sanitizeFilename(video['title'])
                job = DownloadJob(url=video['url'], title=sanTitle, config=config)
                self._submitJob(job)
        else:
            if self.videoInfo:
                originalTitle = mainTitle if mainTitle else self.videoInfo.title
                sanTitle = sanitizeFilename(originalTitle)
                job = DownloadJob(url=config.url, title=sanTitle, config=config)
                self._submitJob(job)
            
    def _submitJob(self, job: DownloadJob):
        self.jobs[job.id] = job
        EventEmitter.emit(EventType.DOWNLOAD_ADDED, job)
        self.executor.submit(self._downloadWorker, job)
        
    def _downloadWorker(self, job: DownloadJob):
        job.status = DownloadStatus.DOWNLOADING
        EventEmitter.emit(EventType.DOWNLOAD_START, job)
        
        def progressCallback(d):
            if job.isCancelled:
                raise Exception("Download cancelled by user")
            if d['status'] == 'downloading':
                try:
                    # yt-dlp specific progress parsing
                    total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                    downloaded = d.get('downloaded_bytes', 0)
                    if total > 0:
                        job.progress = downloaded / total
                    
                    job.totalBytes = total
                    
                    speed_bps = d.get('speed', 0)
                    if speed_bps:
                        if speed_bps > 1024 * 1024:
                            job.speed = f"{speed_bps / (1024 * 1024):.1f} MB/s"
                        elif speed_bps > 1024:
                            job.speed = f"{speed_bps / 1024:.1f} KB/s"
                        else:
                            job.speed = f"{int(speed_bps)} B/s"
                    else:
                        job.speed = ""

                    eta_sec = d.get('eta', 0)
                    if eta_sec:
                        mins, secs = divmod(eta_sec, 60)
                        hours, mins = divmod(mins, 60)
                        if hours > 0:
                            job.eta = f"{int(hours)}h {int(mins)}m"
                        elif mins > 0:
                            job.eta = f"{int(mins)}m {int(secs)}s"
                        else:
                            job.eta = f"{int(secs)}s"
                    else:
                        job.eta = ""

                    if total > 0 or speed_bps or eta_sec:
                        EventEmitter.emit(EventType.DOWNLOAD_PROGRESS, job)
                except Exception:
                    pass

        try:
            DownloadManager.downloadVideo(
                job.url,
                job.config.outputPath,
                job.config.quality,
                job.config.formatType,
                progressCallback,
                title=job.title
            )
            job.status = DownloadStatus.COMPLETED
            job.progress = 1.0
            self.historyService.addEntry(job.title, job.url, job.config.outputPath, "Completed")
            EventEmitter.emit(EventType.DOWNLOAD_COMPLETE, job)
            self.notifier.sendNotification("Download Complete", f"Finished downloading: {job.title}")
        except Exception as e:
            if "cancelled by user" in str(e) or job.isCancelled:
                job.status = DownloadStatus.CANCELLED
                EventEmitter.emit(EventType.DOWNLOAD_CANCELLED, job)
            else:
                job.status = DownloadStatus.FAILED
                job.errorMsg = str(e)
                self.notifier.sendNotification("Download Failed", f"Error downloading: {job.title}")
                EventEmitter.emit(EventType.DOWNLOAD_ERROR, job, str(e))
    
    def cancelJob(self, jobId):
        if jobId in self.jobs:
            self.jobs[jobId].cancel()
    
    def getVideoInfo(self):
        """Get currently loaded video info"""
        return self.videoInfo
    
    def isDownloadInProgress(self):
        """Check if any download is currently in progress"""
        return any(job.status == DownloadStatus.DOWNLOADING for job in self.jobs.values())
    
    def getHistory(self):
        """Get download history"""
        return self.historyService.getHistory()
    
    def removeHistoryEntry(self, index: int):
        """Remove a single entry from the history"""
        self.historyService.removeEntry(index)

    def clearHistory(self):
        """Clear the entire download history"""
        self.historyService.clearHistory()