"""NonPDF — PDF pentesting framework.

Maintained by Anonymous-beta (chinedu).
"""

__version__ = "0.1.0-beta"
__author__ = "Anonymous-beta (chinedu)"
__brand__ = "NonPDF"
__creator__ = "Anonymous-beta (chinedu)"

# Importing the payloads package registers every vector with the global
# registry. This must run before the CLI/TUI touch the registry.
from nonpdf import payloads as _payloads  # noqa: F401,E402