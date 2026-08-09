"""Application configuration package.

This package contains strongly typed application settings used
across the STTM platform.
"""

from .settings import Settings, get_settings

__all__ = [
    "Settings",
    "get_settings",
]