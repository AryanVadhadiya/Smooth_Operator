"""
Threat_Ops.ai - Ingest Service Storage
Simple JSON file storage for demo purposes
"""

import json
import os
from datetime import datetime
from typing import List, Optional
from pathlib import Path
import asyncio
from threading import Lock

# Storage file path
STORAGE_DIR = Path(__file__).parent / "data"
EVENTS_FILE = STORAGE_DIR / "events.json"

# Thread-safe lock for file operations
_file_lock = Lock()

# In-memory event counter
_event_count = 0


def init_storage() -> None:
    """Initialize storage directory and file"""
    global _event_count

    STORAGE_DIR.mkdir(exist_ok=True)

    if not EVENTS_FILE.exists():
        with open(EVENTS_FILE, 'w') as f:
            json.dump([], f)
        _event_count = 0
    else:
        # Count existing events
        try:
            with open(EVENTS_FILE, 'r') as f:
                events = json.load(f)
                _event_count = len(events)
        except (json.JSONDecodeError, FileNotFoundError):
            _event_count = 0


def store_event(event: dict) -> bool:
    """
    Store a single event to the JSON file.
    Returns True on success, False on failure.
    """
    global _event_count

    try:
        with _file_lock:
            # Read existing events
            events = []
            if EVENTS_FILE.exists():
                try:
                    with open(EVENTS_FILE, 'r') as f:
                        events = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    events = []

            # Append new event
            events.append(event)

            # Keep only last 1000 events (demo safety)
            if len(events) > 1000:
                events = events[-1000:]

            # Write back
            with open(EVENTS_FILE, 'w') as f:
                json.dump(events, f, indent=2, default=str)

            _event_count = len(events)
            return True

    except Exception as e:
        print(f"Storage error: {e}")
        return False


def get_events(limit: int = 100, offset: int = 0) -> List[dict]:
    """Get stored events with pagination"""
    try:
        with _file_lock:
            if not EVENTS_FILE.exists():
                return []

            with open(EVENTS_FILE, 'r') as f:
                events = json.load(f)

            # Return newest first
            events.reverse()
            return events[offset:offset + limit]

    except (json.JSONDecodeError, FileNotFoundError):
        return []


def get_event_count() -> int:
    """Get total number of stored events"""
    return _event_count


def clear_events() -> bool:
    """Clear all stored events (for testing)"""
    global _event_count

    try:
        with _file_lock:
            with open(EVENTS_FILE, 'w') as f:
                json.dump([], f)
            _event_count = 0
            return True
    except Exception as e:
        print(f"Clear error: {e}")
        return False
