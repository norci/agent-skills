"""akcli - akshare CLI wrapper"""

__version__ = "0.2.0"

from .cli import call_api, list_apis, get_info

__all__ = ["call_api", "list_apis", "get_info"]
