import yaml


# Convert a string representation of YAML to actual YAML
def toYaml(value: str) -> dict:
    return yaml.safe_load(value)
