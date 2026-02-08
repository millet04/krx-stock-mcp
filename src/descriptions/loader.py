import yaml
from pathlib import Path

def load_description(path: str, latest_date: str) -> str:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    desc = data["description"]
    return desc.replace("{{ latest_date }}", latest_date)