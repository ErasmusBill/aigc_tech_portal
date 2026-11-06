import json
import logging
from typing import Any, Callable, Optional
from django.core.cache import cache

logger = logging.getLogger("platform_core.cache")

def get_namespace_version(namespace: str) -> int:
    """Get the current version number for a cache namespace."""
    key = f"version:{namespace}"
    v = cache.get(key)
    if v is None:
        cache.set(key, 1, timeout=None)
        return 1
    try:
        return int(v)
    except (ValueError, TypeError):
        cache.set(key, 1, timeout=None)
        return 1

def bump_namespace_version(namespace: str) -> int:
    """Increment the version number for a namespace, invalidating all related cached queries."""
    key = f"version:{namespace}"
    try:
        new_v = cache.incr(key)
    except Exception:
        # Fallback if incr fails on uninitialized key or cache backend
        current = cache.get(key) or 1
        new_v = int(current) + 1
        cache.set(key, new_v, timeout=None)
    return new_v

def record_namespace(workspace_key: str, record_type: str) -> str:
    return f"records:{workspace_key}:{record_type}"

def user_namespace(org_id: str = "") -> str:
    return f"users:{org_id}" if org_id else "users:all"

def attendance_namespace() -> str:
    return "attendance:all"

def files_namespace(org_id: str = "") -> str:
    return f"files:{org_id}" if org_id else "files:all"

# ================= Cache Invalidation =================

def invalidate_workspace(workspace_key: str = "t4f-global") -> None:
    """Invalidate workspace state and dependent caches."""
    cache.delete(f"workspace:state:{workspace_key}")
    bump_namespace_version(f"workspace:{workspace_key}")
    invalidate_system_stats()

def invalidate_records(record_type: str, workspace_key: str = "t4f-global") -> None:
    """Invalidate cached queries for a given record type."""
    bump_namespace_version(record_namespace(workspace_key, record_type))
    # Also invalidate workspace state since records are reflected in workspace
    cache.delete(f"workspace:state:{workspace_key}")
    invalidate_system_stats()

def invalidate_all_records(workspace_key: str = "t4f-global") -> None:
    """Invalidate all record caches for a workspace."""
    bump_namespace_version(f"records_all:{workspace_key}")
    cache.delete(f"workspace:state:{workspace_key}")
    invalidate_system_stats()

def invalidate_users(org_id: str = "") -> None:
    """Invalidate user listing caches."""
    bump_namespace_version("users:all")
    if org_id:
        bump_namespace_version(f"users:{org_id}")
    invalidate_system_stats()

def invalidate_attendance() -> None:
    """Invalidate attendance caches."""
    bump_namespace_version(attendance_namespace())
    invalidate_records("attendanceEvents", "t4f-global")

def invalidate_files(org_id: str = "") -> None:
    """Invalidate file listing caches."""
    bump_namespace_version("files:all")
    if org_id:
        bump_namespace_version(f"files:{org_id}")

def invalidate_system_stats() -> None:
    """Invalidate system stats cache."""
    cache.delete("system:stats")

# ================= Cached Retrieval Helpers =================

def get_or_set_cache(key: str, producer: Callable[[], Any], timeout: int = 300) -> Any:
    """Read-through cache helper: returns cached value or executes producer and caches result."""
    cached = cache.get(key)
    if cached is not None:
        return cached
    result = producer()
    cache.set(key, result, timeout=timeout)
    return result
