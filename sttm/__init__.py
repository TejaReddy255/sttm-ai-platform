"""AI-Assisted Source-to-Target Mapping platform.

The :mod:`sttm` package contains the domain, application,
orchestration, infrastructure, validation, and compiler
components of the STTM platform.
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version

try:
    __version__ = package_version("sttm-ai-platform")
except PackageNotFoundError:
    # The package may be imported directly from the source tree
    # before it has been installed by pip.
    __version__ = "0.1.0"

__all__ = ["__version__"]