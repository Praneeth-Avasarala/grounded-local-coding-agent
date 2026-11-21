import subprocess
import re
import ast
import ollama
# from ollama import ChatResponse, chat
import httpx
from typing import Any
# from . import utils
from pathlib import Path
# from utils.agent_tools import inspect_dataset_schema
from utils.util_funcs import clean_code_block
from utils.context_injector import get_aider_repo_map

# def call_local_model(
#         ollama_model: str,
#         messages:dict,
#         num_ctx:int,
# ) -> 


# from ollama import ChatResponse, chat

# def ask_model(prompt: str) -> ChatResponse:
#     return chat(
#         model="qwen2.5-coder",
#         messages=[{"role": "user", "content": prompt}],
#     )


# from ollama import chat

# def ask_model_text(prompt: str) -> str:
#     response = chat(
#         model="qwen2.5-coder",
#         messages=[{"role": "user", "content": prompt}],
#     )
#     return response.message.content

# from collections.abc import Iterator
# from ollama import ChatResponse, chat

# def stream_model(prompt: str) -> Iterator[ChatResponse]:
#     return chat(
#         model="qwen2.5-coder",
#         messages=[{"role": "user", "content": prompt}],
#         stream=True,
#     )


def call_local_model(
        chunk: dict,
        # plan_data:dict[str, Any],
        ollama_model: str,
        scripts_dir: Path,
        pkg_docs: str,
        past_errors: list[str, str] | None = None,
        mode: str = "generate",
        debug_ref: str | None = None,
        map_tokens: int = 1024,
        num_ctx: int = 8192,        
        ) -> str:
    
    """Ollama call with Injected RepoMap + target file content to generate file edits."""
    target_file = chunk['target_file']

    system_prompt = (
        "You are a precise Python coding assistant. Edit the code inside <target_file> "
        "according to <user_request>.\n"
        "Use <repo_map> to verify exact imports, function names,"
        "and signatures from other project files. Use <reference> for package reference for imports, API syntax and error debugging assistance."
        "Return the complete updated code for "
        f"{target_file} inside a single ```python``` block."
        "Strict Rules:\n"
        "1. Rely strictly on the provided Package Reference for imports and API syntax."
        "If you think the pacakges supplied are not enough for the task, you can then"
        "use more packages or write your own code.\n"

        "2. Strictly honor the Input Contract and Output Contract.\n"
        "3. Never guess or assume variable names in input. Always inspect input files before writing code.\n"
        "4. All relative file paths (such as `data/...` or `output/...`) must be relative to the current "
        "working directory (never relative to `__file__`).\n"
        "5. Always call `Path(filepath).parent.mkdir(parents=True, exist_ok=True)` before creating or saving any file.\n"
        "6. Output ONLY valid Python code inside a single ```python ... ``` block. No explanations.\n"
    )

    user_parts = [
        f"GOAL:\n{chunk['goal']}\n",
        f"INPUT CONTRACT (from previous tasks):\n{chunk['input_contract']}\n",
        f"OUTPUT CONTRACT (required for next tasks):\n{chunk['output_contract']}\n",
        # f"TEST THE CODE NEEDS TO PASS WITHOUT ERRORS:\n{chunk['validation_code']}\n",  
        # f"VERIFIED PACKAGE REFERENCE:\n{pkg_docs}\n"
        # f"""TARGET FILE ({chunk['target_file']}):
        #         ```python
        #         {original_code}
                # ```""",
    ]

    user_prompt = "\n\n".join(user_parts)

    repo_dir = scripts_dir
    target_file = chunk["target_file"]
    target_path = (repo_dir / target_file).resolve()

    # 1. Get structural map of the rest of the project using Aider

    if not target_path.exists():
        # raise FileNotFoundError(f"Target file not found: {target_path}")
        repo_map = get_aider_repo_map(
        directory_path=str(repo_dir),
        # target_file=target_file,
        map_tokens=map_tokens,
        )

        full_user_prompt = (
            f"<user_request>\n{user_prompt}\n</user_request>"
            f"<target_file path=\"{target_file}\"</target_file>\n\n"
            f"<reference>\n{pkg_docs}</reference>\n"
        )
        injected_prompt = (
            f"<repo_map>\n{repo_map}\n</repo_map>\n\n"
            # f"<big_picture>\n{plan_data}\n</big_picture>"
        )


    else:

        
        repo_map = get_aider_repo_map(
            directory_path=str(repo_dir),
            target_file=target_file,
            map_tokens=map_tokens,
        )

        # 2. Read the full source code of the file to be edited
        target_code = target_path.read_text(encoding="utf-8")

        injected_prompt = (
            f"<repo_map>\n{repo_map}\n</repo_map>\n\n"
        )

        full_user_prompt = (
            f"<user_request>\n{user_prompt}\n</user_request>"
            f"<target_file path=\"{target_file}\">\n{target_code}\n</target_file>\n\n"
            f"<reference>\n{pkg_docs}</reference>\n"
        )
    print('i am at local model call')

    # --------------------------------------------
    # Community Tested strategies for using assitant role:
    # --------------------------------------------
        ## • Synthetic Few-Shot Formatting (Priming): 

            # Instead of describing your desired output format in long system instructions, inject a fake user → assistant pair right after system. 
            # Show the model one tiny example of a <target_file> edit and an assistant reply containing only a clean ```python``` block. 
            # Local models mimic the structure of prior assistant turns far more reliably than prose rules.

        ## • Assistant Prefill (Forcing Code Start): 

            # In Ollama's /api/chat (or raw prompt templates), ending your messages list with {"role": "assistant", "content": "```python\n"} forces the model to immediately generate code. 
            # It eliminates conversational chatter ("Sure! Here is your updated file...") and guarantees a parseable code block. 
            # (Note: Avoid prefilling if using a reasoning/thinking model like Qwen3 or DeepSeek-R1, as it skips their <think> block).

        ## • Context Acknowledgment Turn (Used by Aider): 

            # Aider often places the repo-map and read-only files in an initial user message followed by 
            # a synthetic {"role": "assistant", "content": "Ok, I won't try to edit those files yet."} before sending the actual edit request in the next user turn. 
            # This separates background reference state from active edit instructions.




    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": injected_prompt},
        {"role": "assistant", "content": "Ok, I won't try to edit those files yet."}   
        # {"role": "assistant", "content":"<think>\n\n</think>"}
        ]

    messages.append(
        {"role": "user", "content": full_user_prompt}
    )


    # -----------------------------------------------
    # Community Tested strategies for using Error feedback:
    # -----------------------------------------------

    # Research on automated code-repair loops (e.g., Reflexion, IaC feedback loops, and harness engineering) consistently shows that 
    # naive retry loops plateau after 2–3 iterations unless you structure the feedback carefully:

        # 1. Cap Retries at 2–3 Turns: 
            # Effectiveness drops exponentially after iteration 2. If a local model fails twice on the same error, 
            # appending more failed attempts pollutes the context window ("history poisoning"). 
            # At that point, reset the history and fall back to a stronger model or human review.

        # 2. Prune Failed Intermediate Attempts: 
            # When Turn 2 fails a linter or test, do not keep Turn 1's broken code in the messages array
            # if you are doing a 3rd retry. Replace Turn 1's assistant message with the latest attempt so 
            # the model only sees one broken draft + one error trace, rather than 3 conflicting versions of the same file.

        # 3. Send Structured, LLM-Optimized Error Signals: Never dump a 200-line raw traceback. Extract and wrap only:
            # 	• The exact error type and message (e.g., SyntaxError, AssertionError, ruff lint rule).
            # 	• The offending line number and 3 lines of surrounding code.
            # 	• A concrete fix hint (e.g., "Check <repo_map> for the exact signature of normalize_columns").

        # 4. Separate Verification from Generation: Run deterministic checks in Python before calling Ollama again—
                # specifically ast.parse() (instant syntax check), ruff or flake8 (undefined variables/imports), 
                # and pytest (logic check)—and feed those back in a clean user message:

                    # messages.append({"role": "assistant", "content": generated_response})
                    # messages.append({
                    #     "role": "user",
                    #     "content": f"<validation_error>\n{concise_error}\n</validation_error>\nFix the error above and return the complete corrected ```python``` block."
                    # })
    
    if past_errors:

        # messages.append({"role": "assistant", "content": generated_response})
        messages.append({
            "role": "user",
            "content": f"<validation_error>\n{past_errors[-1][0]}\n</validation_error>\n<hint>\n{past_errors[-1][1]}\n</hint>\n\n"
            "Fix the error above and return the complete corrected ```python``` block."
        })


        #   messages.append({'role': 'user', 'content': f"Make sure you avoid this error:\n{past_errors[-1]}\n"})



    response = ollama.chat(
    model=ollama_model,
    # 2. Disable hidden "thinking" blocks if using Qwen3 / DeepSeek-R1  
    # think=False,
    messages=messages,    
    # format=FilePatch.model_json_schema(),
    # 3. Tune runtime options for speed and deterministic code
    
    options={
            "temperature": 0.55, # Low randomness = faster token selection & fewer bugs
            'repeat_penalty': 1.15, # Default is 1.1; 1.0 disables the penalty
            'repeat_last_n': 256, # Default is 64; how many recent tokens to check

            # "num_predict": 2048, # Hard cap on output length so it never rambles
            "num_ctx": num_ctx, # Keep context tight to fit in VRAM without slow CPU offloading  
            # "stop": ["```\n\n"] # Cuts generation right after the closing code fence
            },
    )

    prompt_tokens = response.prompt_eval_count or 0
    output_tokens = response.eval_count or 0
    total_used = prompt_tokens + output_tokens

    print(f"Input (prompt + history): {prompt_tokens} tokens")
    print(f"Output (generated reply): {output_tokens} tokens")
    print(f"Total context used:       {total_used} / {num_ctx} tokens")

    if total_used > (num_ctx * 0.85):
        print("Warning: Approaching context limit — trim older messages!")

    return clean_code_block(response["message"]["content"])
