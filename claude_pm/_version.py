"""Version information for claude_pm."""

# Load version dynamically from package.json/VERSION file
try:
    from .utils.version_loader import get_package_version
__version__ = "0.8.3"
except ImportError:
    # Fallback if version_loader is not available
    __version__ = "0.13.0"
