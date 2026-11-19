import os
import time
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types
from google.genai import types
from google.genai.errors import ServerError
from config import PROJECT_DIR
from utils.util_funcs import clean_json_str


GEMINI_API_KEY = os.environ.get("GOOGLE_GEMINI_API_KEY")

GEMINI_MODEL_FALLBACKS = [
    "gemma-4-31b-it",         # Primary: Strongest reasoning & JSON/code planning
    "gemma-4-26b-a4b-it",     # Secondary: Fast MoE model for package lookups
]


# =====================================================================
# STEP 2: Break User Task into Sequential Micro-Task Chunks (JSON Plan)
# =====================================================================

def call_gemini(
    contents: str,
    system_instruction: str,
    temperature: float = 0.2,
    json_mode: bool = False,
    max_retries: int = 3,
) -> str:
    """Resilient Gemini caller with exponential backoff and model fallback."""
    if not GEMINI_API_KEY:
        raise ValueError("Missing GEMINI_API_KEY environment variable.")

    client = genai.Client(api_key=GEMINI_API_KEY)
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=temperature,
        response_mime_type="application/json" if json_mode else None,
    )

    last_err = None
    for model_name in GEMINI_MODEL_FALLBACKS:
        for attempt in range(max_retries):
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config,
                )
                return resp.text
            except ServerError as e:
                last_err = e
                if getattr(e, "code", None) in (429, 503):
                    wait = 2 ** (attempt + 1)
                    print(f"  [Gemini {model_name}] {e.code} busy, retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise
    raise RuntimeError(f"All Gemini models failed: {last_err}")



def plan_task_chunks(task_prompt: str) -> list[dict]:
    """Decomposes the user task into sequential micro-chunks with strict I/O contracts."""
    sys_prompt = (
        "You are a senior software architect. Break the coding task into sequential, small micro-task chunks. "
        "Each chunk must create or modify ONE Python script file. "
        "Return ONLY a JSON array of objects with exact keys:\n"
        "- `chunk_id`: integer (1, 2, ...)\n"
        "- `target_file`: string (e.g. 'generate_data.py')\n"
        "- `goal`: clear logic flow for this chunk\n"
        "- `input_contract`: exact files/schemas consumed from prior chunks (or 'None')\n"
        "- `output_contract`: exact files/columns/stdout produced for future chunks\n"
        "- `validation_code`: standalone Python snippet using `assert` that checks the output files/schemas "
        "on disk (and `os.environ.get('CHUNK_STDOUT', '')` if stdout format is part of the contract). "
        "Do NOT re-run `target_file` inside `validation_code`—assume it has just finished running."
            )
    raw = call_gemini(f"Task:\n{task_prompt}", sys_prompt, temperature=0.1, json_mode=True)
    return json.loads(clean_json_str(raw))

# =====================================================================
# LOOP STEP B: Compact Package & API Reference for Current Chunk
# =====================================================================
def load_or_prefetch_package_docs(
    project_dir: Path,
    chunks: list[dict],
    completed_chunks: set[int],
    max_workers: int = 2,
    stagger_sec: float = 1.0,
) -> dict[int, str]:
    """Loads cached package docs from disk and fetches only missing ones in parallel."""
    docs_map: dict[int, str] = {}
    pending: list[tuple[dict, Path]] = []

    for chunk in chunks:
        cid = chunk["chunk_id"]
        if cid in completed_chunks:
            continue
        pkg_cache = PROJECT_DIR / f".pkg_ref_chunk_{cid}.md"
        if pkg_cache.exists() and pkg_cache.stat().st_size > 0:
            docs_map[cid] = pkg_cache.read_text(encoding="utf-8")
        else:
            pending.append((chunk, pkg_cache))

    if not pending:
        return docs_map

    print(f"Fetching missing package docs for {len(pending)} chunk(s) (workers={max_workers})...\n")

    def _fetch_one(item: tuple[dict, Path], delay: float) -> tuple[int, str]:
        chunk_obj, cache_path = item
        if delay > 0:
            time.sleep(delay)
        docs = get_chunk_package_docs(chunk_obj)
        cache_path.write_text(docs, encoding="utf-8")
        return chunk_obj["chunk_id"], docs

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_fetch_one, item, idx * stagger_sec): item[0]["chunk_id"]
            for idx, item in enumerate(pending)
        }
        for future in as_completed(futures):
            cid = futures[future]
            try:
                fetched_id, fetched_docs = future.result()
                docs_map[fetched_id] = fetched_docs
                print(f"  [Cached] Package docs ready for Chunk {fetched_id}.")
            except Exception as exc:
                print(f"  [Warning] Prefetch failed for Chunk {cid} ({exc}); will retry inline.")

    return docs_map



def get_chunk_package_docs(chunk: dict, error_context: str = "") -> str:
    """Fetches compact package names, conda commands, and 2-3 line snippets for one chunk."""
    sys_prompt = (
        "You are a concise Python package reference assistant. For this specific micro-task chunk, "
        "list ONLY the required third-party packages, their `conda install` commands, and a 2-to-3 line "
        "current usage snippet for each. Keep output under 250 words with zero filler."
    )
    prompt = (
        f"Chunk Goal: {chunk['goal']}\n"
        f"Input Contract: {chunk['input_contract']}\n"
        f"Output Contract: {chunk['output_contract']}"
    )
    if error_context:
        prompt += (
            f"\n\nPREVIOUS API ERROR:\n{error_context}\n"
            "Provide a working 2-line Python snippet using `pandas` or `numpy` that avoids this exact error."
        )
    return call_gemini(prompt, sys_prompt, temperature=0.2)