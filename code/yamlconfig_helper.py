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


def load_config(config_path: str | Path) -> dict:
    """Load YAML config as dictionary."""
    config_path = Path(config_path)
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

def load_config_section(config_path: str | Path, section: str) -> dict:
    """Load configuration section from YAML file.
    Examples
    --------
    >>> load_config_section("config.yaml", "trajectory_scraper")
    >>> load_config_section("config.yaml", "file_transfer")
    """
    config_dict = load_config(config_path)[section]
    if section not in config_dict:
        raise KeyError(f"Section '{section}' not found in config file: {config_path}")
    return config_dict[section]

