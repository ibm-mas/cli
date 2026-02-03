import yaml


# Convert a string representation of YAML to actual YAML
def toYaml(value: str) -> dict:
    return yaml.safe_load(value)

# Convert a Python object to a nicely formatted YAML string
def to_nice_yaml(value, indent: int = 2) -> str:
    return yaml.dump(value, default_flow_style=False, indent=indent, sort_keys=False)
