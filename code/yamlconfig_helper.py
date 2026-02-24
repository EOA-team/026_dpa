"""Default helper functions for working with YAML config files."""

from pathlib import Path
import yaml


def relative_to_absolute_path( path: str | Path, base_path: str | Path,) -> Path:
    """Converts a relative path to an absolute path based on the location of the config file.
    Leaves absolute paths unchanged.

    Examples
    --------
    path  = ./bin/geckodriver.exe 
    config_path = C:/project/my_tool/config.yaml
    --> absolute path = C:/project/my_tool/bin/geckodriver.exe
     
    """
    return (Path(base_path) / path).resolve()

def resolve_relative_paths(config: dict, base_path: str | Path) -> dict:
    """Resolve all values whose key contains 'path' to absolute paths with base_path as reference."""
    resolved = {}
    for key, value in config.items():
        if isinstance(value, dict):
            resolved[key] = resolve_relative_paths(config=value, base_path=base_path)
        elif isinstance(value, str) and "path" in key.lower():
            resolved[key] = relative_to_absolute_path(path=value, base_path=base_path)
        else:
            resolved[key] = value
    return resolved


def load_config_from_dict(config: dict, base_path: str | Path) -> dict:
    """Load configuration from dictionary and resolve relative paths."""
    resolved_config = resolve_relative_paths(config=config, base_path=base_path)
    return resolved_config

def load_config_from_yamlfile(config_path: str | Path) -> dict:
    """Load configuration from YAML file and resolve relative paths."""
    config_path = Path(config_path)
    with open(config_path, 'r', encoding='utf-8') as f:
        config_dict = yaml.safe_load(f)
    base_path = Path(config_path).parent
    resolved_config = resolve_relative_paths(config=config_dict, base_path=base_path)
    return resolved_config


def replace_config_placeholder(config: dict, placeholder: str, replacement: str) -> dict:
    """Replace placeholder in all string values of a config dict.

    Example
    -------
    >>> replace_config_placeholder(config, "{flight_folder}", "re112o_250610")

    Before:  "destination": "D:/Recordings/{flight_folder}/apx/"
    After:   "destination": "D:/Recordings/re112o_250610/apx/"
    """
    resolved = {}
    for key, val in config.items():
        if isinstance(val, dict):
            resolved[key] = replace_config_placeholder(config=val, placeholder=placeholder, replacement=replacement)
        elif isinstance(val, str):
            resolved[key] = val.replace(placeholder, replacement)
        else:
            resolved[key] = val
    return resolved


