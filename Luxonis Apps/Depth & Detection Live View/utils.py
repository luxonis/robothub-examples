from pathlib import Path
import json


def get_labels(model_config_path: str) -> list[str]:
    with Path(model_config_path).open() as f:
        return json.loads(f.read())["mappings"]["labels"]
