import json
from pathlib import Path

CONTENT_PATH = Path(__file__).with_name("content.json")

def load_content():
    with CONTENT_PATH.open(encoding="utf-8") as file:
        return json.load(file)

def normalize_language(value):
    if not isinstance(value, str):
        return "fr"
    code = value.strip().lower().replace("_", "-").split("-")[0]
    return code if code in {"fr", "en"} else "fr"
