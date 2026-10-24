import json
from pathlib import Path


CONTENT_PATH = Path("app/utils/content.json")

def load_content():
    with CONTENT_PATH.open(encoding="utf-8") as file:
        return json.load(file)

def normalize_language(value):
    if not isinstance(value, str):
        return "en"
    code = value.strip().lower().replace("_", "-").split("-")[0]
    return code if code in {"fr", "en"} else "en"
