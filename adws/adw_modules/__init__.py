"""ADW Modules Package (DEPRECATED)

This package is maintained for backwards compatibility.
New code should import from `asw.modules` instead:

    # Old (deprecated):
    from adw_modules.github import fetch_issue
    
    # New (preferred):
    from asw.modules import fetch_issue

The unified `asw.modules` package supports both application (app) 
and infrastructure (io) workflows.
"""
import warnings

warnings.warn(
    "adw_modules is deprecated, use asw.modules instead",
    DeprecationWarning,
    stacklevel=2
)