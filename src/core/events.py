"""
Event System for Decoupling UI and Business Logic
"""

class EventType:
    DOWNLOAD_ADDED = "DOWNLOAD_ADDED"
    DOWNLOAD_START = "DOWNLOAD_START"
    DOWNLOAD_PROGRESS = "DOWNLOAD_PROGRESS"
    DOWNLOAD_COMPLETE = "DOWNLOAD_COMPLETE"
    DOWNLOAD_ERROR = "DOWNLOAD_ERROR"
    DOWNLOAD_CANCELLED = "DOWNLOAD_CANCELLED"
    FETCH_COMPLETE = "FETCH_COMPLETE"
    FETCH_ERROR = "FETCH_ERROR"


class EventEmitter:
    """A simple thread-safe event emitter"""
    _listeners = {}

    @classmethod
    def on(cls, eventType, callback):
        if eventType not in cls._listeners:
            cls._listeners[eventType] = []
        cls._listeners[eventType].append(callback)

    @classmethod
    def emit(cls, eventType, *args, **kwargs):
        if eventType in cls._listeners:
            for callback in cls._listeners[eventType]:
                callback(*args, **kwargs)

    @classmethod
    def off(cls, eventType, callback):
        if eventType in cls._listeners:
            if callback in cls._listeners[eventType]:
                cls._listeners[eventType].remove(callback)
