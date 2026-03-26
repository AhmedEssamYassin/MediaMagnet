"""
Download Job Tracking
"""
import uuid

class DownloadStatus:
    PENDING = "PENDING"
    DOWNLOADING = "DOWNLOADING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class DownloadJob:
    """Represents a single video download task"""
    def __init__(self, url, title, config):
        self.id = str(uuid.uuid4())
        self.url = url
        self.title = title
        self.config = config
        self.status = DownloadStatus.PENDING
        self.progress = 0.0
        self.speed = ""
        self.eta = ""
        self.totalBytes = 0
        self.errorMsg = None
        self.isCancelled = False
        
    def cancel(self):
        self.isCancelled = True
        self.status = DownloadStatus.CANCELLED
