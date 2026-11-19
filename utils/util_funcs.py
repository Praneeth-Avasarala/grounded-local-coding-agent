import os
import re
import json

def get_clean_subprocess_env() -> dict[str, str]:
    """Returns an environment configured for headless execution under isolated users."""
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"  # Prevents X11 'Authorization required' warnings from matplotlib
    env["PYTHONUNBUFFERED"] = "1"
    return env

def clean_code_block(text: str) -> str:
    """Extracts clean Python code from LLM markdown responses."""
    match = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip() + "\n"
    return text.strip() + "\n"


def clean_json_str(text: str) -> str:
    """Strips accidental markdown fences around JSON."""
    return text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()