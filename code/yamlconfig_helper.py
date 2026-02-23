"""Default helper functions for working with YAML config files."""

from pathlib import Path
import yaml


def relative_to_absolute_path(config_path: str | Path, path: str | Path) -> Path:
    """Converts a relative path to an absolute path based on the location of the config file.

    Examples
    --------

    path  = ./bin/geckodriver.exe 
    config_path = C:/project/my_tool/config.yaml
    --> absolute path = C:/project/my_tool/bin/geckodriver.exe
     
    """
    return (Path(config_path).parent / path).resolve()

def _resolve_paths_in_dict(data: dict, config_path: str | Path) -> dict:
    """Resolve all values whose key contains 'path' to absolute paths."""
    resolved = {}
    for key, value in data.items():
        if isinstance(value, dict):
            resolved[key] = _resolve_paths_in_dict(value, config_path)
        elif isinstance(value, str) and "path" in key.lower():
            resolved[key] = relative_to_absolute_path(config_path, value)
        else:
            resolved[key] = value
    return resolved


def load_config(config_path: str | Path) -> dict:
    """Load YAML config and automatically resolve all path keys to absolute paths."""
    config_path = Path(config_path)
    with open(config_path, 'r', encoding='utf-8') as f:
        raw = yaml.safe_load(f)
    return _resolve_paths_in_dict(raw, config_path)

