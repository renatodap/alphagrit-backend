import yaml
from functools import lru_cache


@lru_cache(maxsize=2)
def _load_lang(lang: str) -> dict:
    with open(f"app/shared/i18n/{lang}.yml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def t(lang: str, key: str) -> str:
    data = _load_lang(lang)
    # naive dot resolver like "errors.invalid_token"
    cur = data
    for part in key.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return key
    return cur if isinstance(cur, str) else key
