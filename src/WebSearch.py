import os
import time
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types
from google.genai import types
from google.genai.errors import ServerError
from utils.util_funcs import clean_json_str
# from src.config import PLAN_CACHE_DIR, SCRIPTS_DIR, TASK_FILE, OLLAMA_MODEL, MAX_TRIES
from src.Validate import load_completed_chunks



# GEMINI_API_KEY = os.environ.get("GOOGLE_GEMINI_API_KEY")

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
    if not os.environ.get("GOOGLE_GEMINI_API_KEY"):
        raise ValueError("Missing GEMINI_API_KEY environment variable.")

    client = genai.Client(api_key=os.environ.get("GOOGLE_GEMINI_API_KEY"))
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
                    print(f"            [Gemini {model_name}] {e.code} busy, retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise
    raise RuntimeError(f"All Gemini models failed: {last_err}")



def plan_task_chunks(task_prompt: str) -> list[dict]:
    """Decomposes the user task into sequential micro-chunks with strict I/O contracts."""
    sys_prompt = (
        "You are an expert software architect whose job is to design workflow for a small context coding agent wtih access to a miniconda env."
        "Split the user's task into micro-task chunks that lets a coding agent work in a feedback loop : Agent generates code -> Deterministic validation test -> (fresh session) Agent generates code again but with validation error feedback from last run -> Same Valitation test again."
        "Provide strict input, output contracts and validation tests to every chunk to make this work.\n"
        # "Vault validation should verify extraction of metadata and titles.\n"
        "For long code files, Use Skeleton + Slot filling arthictecuture design to allow agents work independently on each chunk."
        "Return ONLY a JSON array of objects with exact keys:\n"
        "- `chunk_id`: integer (1, 2, ...)\n"
        "- `target_file`: string (e.g. 'generate_data.py')\n"
        "- `goal`: clear logic flow for this chunk\n"
        "- `input_contract`: exact data types/files/schemas consumed from prior chunks (or 'None')\n"
        "- `output_contract`: exact data types/files/columns/stdout produced for future chunks\n"
        "- `validation_code`: e.g . for python, standalone Python snippet using `assert` that checks the output files/schemas "
        "on disk (and `os.environ.get('CHUNK_STDOUT', '')` if stdout format is part of the contract)."
        "Do NOT re-run `target_file` inside `validation_code`—assume it has just finished running.\n" 
        "Maximimise parallel working ability in each of these chunks"
            )
    raw = call_gemini(f"Task:\n{task_prompt}", sys_prompt, temperature=0.1, json_mode=True)
    return json.loads(clean_json_str(raw))

# =====================================================================
# LOOP STEP B: Compact Package & API Reference for Current Chunk
# =====================================================================
def get_chunk_package_docs(chunks, chunk: dict, error_context: str = "") -> str:
    """Fetches compact package names, conda commands, and line snippets for one chunk."""
    sys_prompt = (
        "You are a concise package reference assistant.\n"
        "You are provided chunk goal and also context about how this goal fits into the bigger project. You are working on your chunk. Other workers are working on other chunks\n"
        "For ONLY specific micro-task specified as Chunk goal,"
        "list ONLY the required third-party packages, their `conda install` commands, and a few lines of "
        "current usage snippet for each for the operations needed in the task. Keep output to only what's necessary with zero filler. \n"
    )
    user_prompt = (
        f"Bigger Plan: {chunks}\n"
        f"MAIN GOAL for this task: {chunk['goal']}\n"
        f"Input Contract: {chunk['input_contract']}\n"
        f"Output Contract: {chunk['output_contract']}"
    )

    
    return call_gemini(user_prompt, sys_prompt, temperature=0.2)



def load_or_prefetch_package_docs(
    project_dir: Path,
    chunks: list[dict],
    completed_chunks: set[int],
    max_workers: int = 3,
    stagger_sec: float = 1.0,
) -> dict[int, str]:
    """Loads cached package docs from disk and fetches only missing ones in parallel."""
    docs_map: dict[int, str] = {}
    pending: list[tuple[dict, Path]] = []

    for chunk in chunks:
        cid = chunk["chunk_id"]
        if cid in completed_chunks:
            continue
        pkg_cache = project_dir / f".pkg_ref_chunk_{cid}.md"
        if pkg_cache.exists() and pkg_cache.stat().st_size > 0:
            docs_map[cid] = pkg_cache.read_text(encoding="utf-8")
        else:
            pending.append((chunk, pkg_cache))

    if not pending:
        return docs_map

    # if len(pending) < max_workers:
    #     max_workers = len(pending)

    print(f"Fetching missing package docs for {len(pending)}/{len(chunks)} chunk(s) (parallel workers={max_workers})...\n")



    def _fetch_one(item: tuple[dict, Path], delay: float) -> tuple[int, str]:
        chunk_obj, cache_path = item
        if delay > 0:
            time.sleep(delay)
        docs = get_chunk_package_docs(chunks, chunk_obj)
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


def websearch_chunk(
        task_plan:str,
        chunk:dict,
        code:str,
        past_errors:str,
            ):

    sys_prompt = (
    "You are an expert in software design and architecture."
    "You job is to provide debugging assistance to a local coding agent.\n"
    # "You are given the agent's goal and also context about how this goal fits into the bigger project."
    # "This agent is assigned one chunk. Other workers are working on other chunks\n"
    "You are provided the project plan, existing code for a part of the plan and latest error.\n" 
    "Return ONLY a JSON array of objects with exact keys:\n"
    # "List ONLY the code snippets and 3-4 lines of explanation for each if necessary. Zero filler.\n"
        "- `Possible_error_cause`: short explanation\n"
        "- `Possible_solution_code`: e.g . for python, standalone Python snippet\n"
        

)
    user_prompt += (
        f"\n\nProject Plan:\n{task_plan}\n"
        f"\n\nGoal for code provided:\n{chunk['goal']}\n"
        f"\n\nCode: \n{code}\n"
        f"\n\nError:\n{past_errors[-1][0]}\n"
        f""
        "Infer probable causes and provide code snippets for an error-free code."
    )

    # for i in chunks:

    user_parts = [
        f"GOAL:\n{chunk['goal']}\n",
        f"INPUT CONTRACT (from previous tasks):\n{chunk['input_contract']}\n",
        f"OUTPUT CONTRACT (required for next tasks):\n{chunk['output_contract']}\n",
        f"TEST THE CODE NEEDS TO PASS WITHOUT ERRORS:\n{chunk['validation_code']}\n",  
        # f"VERIFIED PACKAGE REFERENCE:\n{pkg_docs}\n"
        # f"""TARGET FILE ({chunk['target_file']}):
        #         ```python
        #         {original_code}
                # ```""",
    ]

    return call_gemini(user_prompt, sys_prompt, temperature=0.2)


def WebSearch_Task(
        PLAN_CACHE_DIR: Path,
        SCRIPTS_DIR: Path,
        TASK_FILE: Path,
):
        
        

        # PROJECT_DIR.mkdir(parents=True, exist_ok=True)
        PLAN_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)


        if not TASK_FILE.exists():
            raise FileNotFoundError(f"Missing task file: {TASK_FILE.resolve()}")

        task_prompt = TASK_FILE.read_text(encoding="utf-8").strip()

        plan_file =  PLAN_CACHE_DIR / ".task_plan.json"
        if plan_file.exists():
            print("Loaded cached chunk plan from `.task_plan.json`...\n", flush=True)
            chunks = json.loads(plan_file.read_text(encoding="utf-8"))
        else:
            print("Breaking task into sequential micro-chunks via Gemma 4...\n", flush=True)
            chunks = plan_task_chunks(task_prompt)
            plan_file.write_text(json.dumps(chunks, indent=2), encoding="utf-8")

        chunk_plan = []

        for chunk in chunks:

            chunk_plan.append(
                f"Step {chunk['chunk_id']}:\n{chunk['goal']}\n"
                f"Target File:\n{chunk['target_file']}\n"
                # f"INPUT CONTRACT (from previous tasks):\n{chunk['input_contract']}\n",
                # f"OUTPUT CONTRACT (required for next tasks):\n{chunk['output_contract']}\n",
                # f"TEST THE CODE NEEDS TO PASS WITHOUT ERRORS:\n{chunk['validation_code']}\n",  
                            )      
    
        task_plan = "\n\n".join(chunk_plan)


        completed_chunks = load_completed_chunks(PLAN_CACHE_DIR)

        pkg_docs_map = load_or_prefetch_package_docs(PLAN_CACHE_DIR, chunks, completed_chunks)

        print(f"\n{'='*50}\nWeb-Search Stage Complete\n{'='*50}\n")

        # print(task_plan)

        return task_plan, chunks, pkg_docs_map




    


