def normalize_language(value):
    """Map a browser locale to a supported language without guessing payloads."""
    if not isinstance(value, str):
        return "fr"
    code = value.strip().lower().replace("_", "-").split("-")[0]
    return code if code in {"fr", "en"} else "fr"
