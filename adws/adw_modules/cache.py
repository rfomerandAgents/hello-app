"""Claude response caching module for ADW workflows.

Provides fingerprint-based caching to avoid redundant Claude API calls.
"""

import hashlib
import json
import os
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CacheConfig:
    """Configuration for Claude response caching."""
    enabled: bool = True
    ttl_seconds: int = 172800  # 48 hours default
    cache_dir: str = "cache"


@dataclass
class CacheEntry:
    """A cached Claude response entry."""
    fingerprint: str
    response_output: str
    response_success: bool
    response_session_id: Optional[str]
    created_at: float
    ttl_seconds: int
    prompt_preview: str  # First 100 chars for debugging
    model: str
    slash_command: Optional[str] = None


def create_fingerprint(
    prompt: str,
    model: str,
    working_dir: Optional[str] = None,
    slash_command: Optional[str] = None,
) -> str:
    """Create MD5 fingerprint for cache key.

    Fingerprint includes:
    - Full prompt text
    - Model name (sonnet vs opus)
    - Working directory (for context)
    - Slash command (for template execution)

    Does NOT include:
    - adw_id (same prompt should cache across ADW instances)
    - agent_name (implementation detail)
    """
    fingerprint_data = {
        "prompt": prompt,
        "model": model,
        "working_dir": working_dir or "",
        "slash_command": slash_command or "",
    }

    # Create deterministic JSON string (sorted keys)
    fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)

    # MD5 hash for compact fingerprint
    return hashlib.md5(fingerprint_str.encode()).hexdigest()


def get_cache_dir(adw_id: str) -> Path:
    """Get cache directory path for an ADW instance."""
    project_root = Path(__file__).parent.parent.parent
    return project_root / "agents" / adw_id / "cache"


def get_cache_path(adw_id: str, fingerprint: str) -> Path:
    """Get full path for a cache file."""
    return get_cache_dir(adw_id) / f"{fingerprint}.json"


def save_cache_entry(adw_id: str, entry: CacheEntry) -> None:
    """Save a cache entry to disk."""
    cache_path = get_cache_path(adw_id, entry.fingerprint)
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    with open(cache_path, "w") as f:
        json.dump({
            "fingerprint": entry.fingerprint,
            "response_output": entry.response_output,
            "response_success": entry.response_success,
            "response_session_id": entry.response_session_id,
            "created_at": entry.created_at,
            "ttl_seconds": entry.ttl_seconds,
            "prompt_preview": entry.prompt_preview,
            "model": entry.model,
            "slash_command": entry.slash_command,
        }, f, indent=2)


def load_cache_entry(adw_id: str, fingerprint: str) -> Optional[CacheEntry]:
    """Load a cache entry if it exists and is not expired."""
    cache_path = get_cache_path(adw_id, fingerprint)

    if not cache_path.exists():
        return None

    try:
        with open(cache_path, "r") as f:
            data = json.load(f)

        entry = CacheEntry(
            fingerprint=data["fingerprint"],
            response_output=data["response_output"],
            response_success=data["response_success"],
            response_session_id=data.get("response_session_id"),
            created_at=data["created_at"],
            ttl_seconds=data["ttl_seconds"],
            prompt_preview=data["prompt_preview"],
            model=data["model"],
            slash_command=data.get("slash_command"),
        )

        # Check TTL expiration
        age = time.time() - entry.created_at
        if age > entry.ttl_seconds:
            cache_path.unlink(missing_ok=True)
            return None

        return entry

    except (json.JSONDecodeError, KeyError):
        cache_path.unlink(missing_ok=True)
        return None


def clear_cache(adw_id: str, max_age_seconds: Optional[int] = None) -> int:
    """Clear cache entries for an ADW instance.

    Args:
        adw_id: The ADW instance ID
        max_age_seconds: If provided, only clear entries older than this.

    Returns:
        Number of entries cleared
    """
    cache_dir = get_cache_dir(adw_id)

    if not cache_dir.exists():
        return 0

    cleared = 0
    current_time = time.time()

    for cache_file in cache_dir.glob("*.json"):
        should_clear = True

        if max_age_seconds is not None:
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                age = current_time - data.get("created_at", 0)
                should_clear = age > max_age_seconds
            except:
                should_clear = True

        if should_clear:
            cache_file.unlink(missing_ok=True)
            cleared += 1

    return cleared


def get_cache_stats(adw_id: str) -> Dict[str, Any]:
    """Get statistics about cache for an ADW instance."""
    cache_dir = get_cache_dir(adw_id)

    if not cache_dir.exists():
        return {"entries": 0, "total_size_bytes": 0, "oldest_entry": None}

    entries = list(cache_dir.glob("*.json"))
    total_size = sum(f.stat().st_size for f in entries)

    oldest = None
    for cache_file in entries:
        try:
            with open(cache_file, "r") as f:
                data = json.load(f)
            created_at = data.get("created_at", 0)
            if oldest is None or created_at < oldest:
                oldest = created_at
        except:
            pass

    return {
        "entries": len(entries),
        "total_size_bytes": total_size,
        "oldest_entry": oldest,
    }
