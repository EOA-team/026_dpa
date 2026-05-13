
from code.yamlconfig_helper import load_config_from_yamlfile
from code.file_utils import get_base_path

config_path = get_base_path(__file__) / "config.yaml"
config = load_config_from_yamlfile(config_path)


print(config)