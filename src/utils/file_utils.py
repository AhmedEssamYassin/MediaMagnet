# pyre-ignore-all-errors
import re
import unicodedata

"""
The Windows file system has a traditional maximum path length (MAX_PATH) of 260 characters. 
This limit must contain the entire file path, including the drive letter (e.g., C:\\\\), all folder names, 
the filename itself, and the file extension (e.g., .mp4).
"""

def sanitizeFilename(filename, max_length=200):
    """
    Sanitize filename for Windows compatibility
    - Remove invalid characters
    - Remove bidirectional text markers
    - Strip emojis and special Unicode
    - Limit length
    """
    # Remove bidirectional text markers and other control characters
    filename = ''.join(char for char in filename if unicodedata.category(char)[0] != 'C')
    
    # Remove emojis and other special symbols
    filename = re.sub(r'[^\w\s\-_.]', '', filename, flags=re.UNICODE)
    
    # Replace multiple spaces/underscores with single space
    filename = re.sub(r'[\s_]+', ' ', filename)
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Limit length (leave room for extension and path)
    if len(filename) > max_length:
        filename = filename[:max_length]
        
    # Fallback to generic name if empty
    if not filename:
        filename = "video"
        
    return filename

def getFfmpegPath():
    import sys
    import os
    
    ffmpegExe = "ffmpeg.exe" if os.name == 'nt' else "ffmpeg"
    
    if getattr(sys, 'frozen', False):
        path1 = os.path.join(sys._MEIPASS, ffmpegExe)
        path2 = os.path.join(sys._MEIPASS, "assets", ffmpegExe)
        if os.path.exists(path1): return path1
        if os.path.exists(path2): return path2
    else:
        # We assume file_utils is in src/utils folder
        projectRoot = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        possiblePath = os.path.join(projectRoot, "assets", ffmpegExe)
        if os.path.exists(possiblePath):
            return possiblePath
            
    return "ffmpeg" # Fallback to global PATH