"""
Persistent download history storage using a JSON file.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict

class HistoryService:
    """Manages download history"""

    def __init__(self, historyFile: str = "history.json"):
        self.historyFile = Path.home() / ".video_downloader" / historyFile
        self.historyFile.parent.mkdir(parents=True, exist_ok=True)
        self.history = self._loadHistory()

    def _loadHistory(self) -> List[Dict]:
        if not self.historyFile.exists():
            return []
        with open(self.historyFile, "r") as f:
            return json.load(f)

    def _saveHistory(self):
        with open(self.historyFile, "w") as f:
            json.dump(self.history, f, indent=4)

    def addEntry(self, title: str, url: str, path: str, status: str, thumbnail: str = ""):
        entry = {
            "title": title,
            "url": url,
            "path": path,
            "status": status,
            "thumbnail": thumbnail,
            "timestamp": datetime.now().isoformat()
        }
        self.history.insert(0, entry)
        self._saveHistory()

    def getHistory(self) -> List[Dict]:
        return self.history

    def removeEntry(self, index: int):
        """Remove a single entry from the history"""
        if 0 <= index < len(self.history):
            del self.history[index]
            self._saveHistory()

    def clearHistory(self):
        """Clear the entire download history"""
        self.history = []
        self._saveHistory()