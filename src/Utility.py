import re
from typing import Dict, Any

def dict_diff(base_options: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
    """Return the difference between base_options and kwargs."""
    params = {}
    for key, value in kwargs.items():
        if key in base_options:
            if isinstance(value, dict):
                params[key] = dict_merge(base_options.get(key, {}), **value)
            else:
                params[key] = value
    return params

def dict_merge(base_options: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
    """Merge kwargs into base_options."""
    params = base_options.copy()
    for key, value in kwargs.items():
        if key in base_options:  # Ensure only keys present in base_options are merged
            if isinstance(value, dict):
                params[key] = dict_merge(params.get(key, {}), **value)
            else:
                params[key] = value
    return params

def slugify(text: str) -> str:
    """Convert a string to a URL-friendly slug."""
    return re.sub(r'[-\s]+', '-', re.sub(r'[^\w\s-]', '', text)).strip().lower()
