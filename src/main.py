import json
from pathlib import Path
from LocalAI import generate_chunk_code
from Validate import validate_chunk, load_completed_chunks, save_completed_chunk
from WebSearch import plan_task_chunks, get_chunk_package_docs, load_or_prefetch_package_docs
from config import PROJECT_DIR, TASK_FILE, OLLAMA_MODEL, MAX_TRIES





def combine_chunks(project_dir: Path, chunks: list[dict]) -> None:
    """Creates a clean `run_pipeline.py` that executes all validated chunks sequentially."""
    script_names = [c["target_file"] for c in chunks]
    lines = [
        "import subprocess",
        "import sys",
        "",
        f"SCRIPTS = {json.dumps(script_names, indent=4)}",
        "",
        "def main():",
        "    for script in SCRIPTS:",
        "        print(f'Running {script}...')",
        "        subprocess.run([sys.executable, script], check=True)",
        "    print('Pipeline finished successfully.')",
        "",
        "if __name__ == 'main':",
        "    main()",
        "",
        ]
    (project_dir / "run_pipeline.py").write_text("\n".join(lines), encoding="utf-8")



# =====================================================================
# MAIN ORCHESTRATOR
# =====================================================================
def main():

    MAX_CHUNK_TRIES = MAX_TRIES
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    if not TASK_FILE.exists():
        raise FileNotFoundError(f"Missing task file: {TASK_FILE.resolve()}")

    task_prompt = TASK_FILE.read_text(encoding="utf-8").strip()

    plan_cache = PROJECT_DIR / ".task_plan.json"
    if plan_cache.exists():
        print("Loaded cached chunk plan from `.task_plan.json`...\n")
        chunks = json.loads(plan_cache.read_text(encoding="utf-8"))
    else:
        print("Step 2: Breaking task into sequential micro-chunks via Gemma 4...\n")
        chunks = plan_task_chunks(task_prompt)
        plan_cache.write_text(json.dumps(chunks, indent=2), encoding="utf-8")


    completed_chunks = load_completed_chunks(PROJECT_DIR)

    pkg_docs_map = load_or_prefetch_package_docs(PROJECT_DIR, chunks, completed_chunks)

    for chunk in chunks:
        cid = chunk["chunk_id"]
        tfile = chunk["target_file"]

        # Skip if already verified and target file is intact
        if cid in completed_chunks and (PROJECT_DIR / tfile).exists():
            print(f"Skipping CHUNK {cid} (`{tfile}`) - already verified in `.completed_chunks.json`.")
            continue
        
        print(f"\n{'='*50}\nCHUNK {cid}: {tfile}\nGoal: {chunk['goal']}\n{'='*50}")

        pkg_cache = PROJECT_DIR / f".pkg_ref_chunk_{cid}.md"
        # if pkg_cache.exists():
        #     pkg_docs = pkg_cache.read_text(encoding="utf-8")
        # else:
        #     pkg_docs = get_chunk_package_docs(chunk)
        #     pkg_cache.write_text(pkg_docs, encoding="utf-8")

        pkg_docs = pkg_docs_map.get(cid) or get_chunk_package_docs(chunk)


        existing_code = ""
        # feedback = ""
        past_errors: list[str] = []
        success = False

        for attempt in range(1, MAX_CHUNK_TRIES + 1):
            print(f"\n[Attempt {attempt}/{MAX_CHUNK_TRIES}] Generating `{tfile}` with local Ollama ({OLLAMA_MODEL})...")
            code = generate_chunk_code(chunk, pkg_docs, existing_code, past_errors)
            (PROJECT_DIR / tfile).write_text(code, encoding="utf-8")
            existing_code = code

            passed, err_type, feedback = validate_chunk(PROJECT_DIR, chunk)
            
            if passed:
                print(f"  [SUCCESS] Chunk {cid} verified!\n")
                save_completed_chunk(PROJECT_DIR, cid)
                success = True
                break

            past_errors.append(feedback)
            print(f"  [FAILED] {feedback}")

            if err_type == "package" and attempt < MAX_CHUNK_TRIES:
                print("  -> Refreshing package API documentation via Gemma before next Ollama retry...")
                try:
                    pkg_docs = get_chunk_package_docs(chunk, error_context=feedback)
                    pkg_cache.write_text(pkg_docs, encoding="utf-8")
                except RuntimeError as api_err:
                    print(f"  -> Web-search API unavailable ({api_err}); continuing retry with existing package docs...")
        if not success: 
            print(f"\nPipeline stopped: Chunk {cid} ({tfile}) failed after {MAX_CHUNK_TRIES} attempts.")
            return
    
    combine_chunks(PROJECT_DIR, chunks)
    print("\nALL CHUNKS COMPLETED AND VALIDATED SUCCESSFULLY! Master runner saved to run_pipeline.py.")



if __name__ == "__main__":
    main()
