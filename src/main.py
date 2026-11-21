# import json
from pathlib import Path
from src.config import TASK_FILE, PLAN_CACHE_DIR, OLLAMA_MODEL, MAX_TRIES, SCRIPTS_DIR, TESTS_DIR
from src.Local_model import call_local_model
from src.Validate import validate_chunk, load_completed_chunks, save_completed_chunk
from src.WebSearch import get_chunk_package_docs, WebSearch_Task



# def combine_chunks(scripts_dir: Path, chunks: list[dict]) -> None:
#     """Creates a clean `run_pipeline.py` that executes all validated chunks sequentially."""
#     script_names = [c["target_file"] for c in chunks]
#     lines = [
#         "import subprocess",
#         "import sys",
#         "",
#         f"SCRIPTS = {json.dumps(script_names, indent=4)}",
#         "",
#         "def main():",
#         "    for script in SCRIPTS:",
#         "        print(f'Running {script}...')",
#         "        subprocess.run([sys.executable, script], check=True)",
#         "    print('Pipeline finished successfully.')",
#         "",
#         "if __name__ == 'main':",
#         "    main()",
#         "",
#         ]
#     (scripts_dir / "run_pipeline.py").write_text("\n".join(lines), encoding="utf-8")



# =====================================================================
# MAIN ORCHESTRATOR
# =====================================================================
def main(
        chunks, 
        pkg_docs_map,
        plan_cache_dir: Path,
        max_tries:int = 3):


    MAX_CHUNK_TRIES = max_tries

    completed_chunks = load_completed_chunks(PLAN_CACHE_DIR)

    prev_chunk = None
    mode = "generate"
    action = "Generating"

    for chunk in chunks:

        cid = chunk["chunk_id"]
        tfile = chunk["target_file"]

        if not prev_chunk==None:
            print(tfile)
            print(prev_chunk['target_file'])
            if tfile == prev_chunk['target_file']:
                mode = "edit"
                action = "Editing"

        prev_chunk = chunk

        # Skip if already verified and target file is intact
        if cid in completed_chunks and (SCRIPTS_DIR / tfile).exists():
            print(f"Skipping CHUNK {cid} (`{tfile}`) - already verified in `.completed_chunks.json`.", flush=True)
            continue

        print(f"\n{'='*50}\nCHUNK {cid}: {tfile}\nGoal: {chunk['goal']}\n{'='*50}")

        pkg_cache = plan_cache_dir / f".pkg_ref_chunk_{cid}.md"
        # if pkg_cache.exists():
        #     pkg_docs = pkg_cache.read_text(encoding="utf-8")
        # else:
        #     pkg_docs = get_chunk_package_docs(chunk)
        #     pkg_cache.write_text(pkg_docs, encoding="utf-8")

        pkg_docs = pkg_docs_map.get(cid) or get_chunk_package_docs(chunks=chunks, chunk=chunk)


        existing_code = ""
        # feedback = ""
        past_errors: list[str] = []
        success = False
        debug_ref = None

        # Saving target file only if it passes validation


        # First attempt cases:

            # (1) if target file doesnt exist : 
                # generate, validate, regenerate or edit with error feedback

            # (2) if target file exists : previous succesful chunk create this target file    
                # - DO NOT GENERATE AGAIN. edit existing file. add new lines according to user task. 
                # - also pass previous chunk's validation script along with current chunk's validation script
                # - test validations for both chunks.

        # Next attempt cases:  

            # (1) if target file exists : (if this chunk generated it, file passes validation and attempts loop breaks.)
                # generated in previous chunk that was successfully validated - do not regenerate. only edit 
            # (2) if target file doesnt exist : (hasn't passed validation yet)
                # regenerate with error feedback


        print(mode)

        for attempt in range(1, MAX_CHUNK_TRIES + 1):

            if attempt == 1 and (SCRIPTS_DIR / tfile).exists(): 

                code = (SCRIPTS_DIR / tfile).read_text(encoding="utf-8")

            else:

                print(f"\n[Attempt {attempt}/{MAX_CHUNK_TRIES}] {action} `{tfile}` with local ({OLLAMA_MODEL})...", flush=True)
                # code = generate_chunk_code(ollama_model=OLLAMA_MODEL, chunk=chunk, pkg_docs=pkg_docs, past_errors=past_errors)
                code = call_local_model(mode=mode, scripts_dir=SCRIPTS_DIR ,ollama_model=OLLAMA_MODEL, chunk=chunk, pkg_docs=pkg_docs, past_errors=past_errors)
                

            print(f"\nValidating '{tfile}'", flush=True)
            passed, err_type, feedback, error_output, hint = validate_chunk(code, scripts_dir=SCRIPTS_DIR, tests_dir=TESTS_DIR, chunk=chunk)

            if passed:
                print(f"  [SUCCESS] Chunk {cid} verified!\n", flush=True)
                # (SCRIPTS_DIR / tfile).write_text(code, encoding="utf-8")
                save_completed_chunk(PLAN_CACHE_DIR, cid)
                success = True
                break

            past_errors.append([feedback, hint])
            print(f"  [FAILED] {error_output}")
                                # if err_type == "package" and attempt < MAX_CHUNK_TRIES:
            # if attempt == MAX_CHUNK_TRIES-2: 
            #     print("  -> Refreshing package API documentation via Gemma before next Ollama retry...", flush=True)
            #     try:
            #         debug_ref = get_chunk_package_docs(chunks, chunk, error_context=feedback)
            #         # with pkg_cache.open(mode="a", encoding="utf-8") as f:
            #         #     f.write(f"\n{pkg_docs}\n")
            #         # pkg_cache.write_text(pkg_docs, encoding="utf-8")
            #     except RuntimeError as api_err:
            #         print(f"  -> Web-search API unavailable ({api_err}); continuing retry with existing package docs...", flush=True)


        if not success: 
            # print(f"\nPipeline stopped: Chunk {cid} ({tfile}) failed after {MAX_CHUNK_TRIES} attempts.", flush=True)
            # return
            print(f"\nMoving on to the next chunk", flush=True)


                    
    # combine_chunks(SCRIPTS_DIR, chunks)
    # print("\nALL CHUNKS COMPLETED AND VALIDATED SUCCESSFULLY! Master runner saved to run_pipeline.py.")

    # completed_chunks = load_completed_chunks(PLAN_CACHE_DIR)
    
    # print(f"\nCHUNKS THAT PASSED GEMINI'S PREDEFINED VALIDATION TESTS : {sorted(completed_chunks)}.")
    # print("\nREVIEW ALL CHUNKS REGARDLESS. DON'T TRUST VALIDATED OR INVALIDATED OUTPUTS WITHOUT HUMAN VERIFICATION")

if __name__ == "__main__":

    task_plan, chunks, pkg_docs_map = WebSearch_Task(PLAN_CACHE_DIR=PLAN_CACHE_DIR,
                                    SCRIPTS_DIR=SCRIPTS_DIR,
                                    TASK_FILE=TASK_FILE)

    # main(chunks=chunks,
    #     pkg_docs_map=pkg_docs_map,
    #     plan_cache_dir=PLAN_CACHE_DIR,
    #     max_tries=MAX_TRIES)
    
    main(chunks=chunks,
        pkg_docs_map=pkg_docs_map,
        plan_cache_dir=PLAN_CACHE_DIR,
        max_tries=MAX_TRIES)
