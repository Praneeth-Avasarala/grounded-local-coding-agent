import ollama
# from . import utils
from pathlib import Path
from utils.agent_tools import inspect_dataset_schema
from utils.util_funcs import clean_code_block
from utils.context_injector import extract_workspace_schemas


def generate_chunk_code(
    ollama_model: str,
    scripts_dir: Path,
    chunk: dict,
    pkg_docs: str,
    existing_code: str = "",
    # error_feedback: str = "",
    past_errors: list[str] | None = None,
) -> str:
    """Calls local Ollama directly to write the complete target Python file."""



    sys_prompt = (
            "You are an expert Python developer. Write the COMPLETE, runnable Python code for the requested file.\n"
            "Strict Rules:\n"
            "1. Rely strictly on the provided Package Reference for imports and API syntax.\n"
            "2. Strictly honor the Input Contract and Output Contract.\n"
            "3. Never guess or assume variable names in input. Always inspect input files before writing code."
            "4. All relative file paths (such as `data/...` or `output/...`) must be relative to the current "
            "working directory (never relative to `__file__`).\n"
            "5. Always call `Path(filepath).parent.mkdir(parents=True, exist_ok=True)` before creating or saving any file.\n"
            "6. Output ONLY valid Python code inside a single ```python ... ``` block. No explanations.\n"
        )

    user_parts = [
        f"### TARGET FILE: {chunk['target_file']}",
        f"### GOAL:\n{chunk['goal']}",
        f"### INPUT CONTRACT (from previous tasks):\n{chunk['input_contract']}",
        f"### OUTPUT CONTRACT (required for next tasks):\n{chunk['output_contract']}",
        # f"### VALIDATION SCRIPT (your code will be tests on this):\n{chunk['validation_code']}",
        f"### VERIFIED PACKAGE REFERENCE:\n{pkg_docs}",
    ]



    if existing_code and past_errors:
            user_parts.append(f"### PREVIOUS CODE DRAFT:\n```python\n{existing_code}\n```")
            user_parts.append(f"### VALIDATION TEST THAT THIS CODE NEEDS TO PASS:\n```python\n{chunk['validation_code']}\n```")
            error_history_text = "\n".join(
                f"- Attempt {idx} error: {err}" for idx, err in enumerate(past_errors, start=1)
            )
            user_parts.append(
                f"### VALIDATION TEST ERROR HISTORY TO FIX (do not repeat any of these mistakes):\n{error_history_text}"
            )

            # sys_prompt_error = (

            #              "You are an expert Python developer. You are provided code and error history\n"
            #              "Keep your answer very short and to the point. Output ONLY valid Python code inside a single ```python ... ``` block. No explanations."
            # )

            # err_response = ollama.chat(
            #     model=ollama_model,
            #     messages=[
            #         {"role": "system", "content": sys_prompt_error},
            #         {"role": "user", "content": "\n\n".join(user_parts)},
            #     ],
            #     # tools=[inspect_dataset_schema],
            #     # thinking = False, # Keeps smaller models focused on executing tools cleanly
            #     options={"temperature": 0.15, "num_ctx": 8192},
            # )

            # return clean_code_block(response["message"]["content"])

    user_prompt = "\n\n".join(user_parts)


    """Injects verified schemas into the prompt, calls qwen3:4b, and saves the clean code."""

    # Silently gather column names before calling Ollama
    schema_context = extract_workspace_schemas(user_prompt, scripts_dir)
    
    full_user_prompt = f"{user_prompt}{schema_context}"
    
    response = ollama.chat(
        model=ollama_model,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": full_user_prompt},
        ],
        options={"temperature": 0, "num_ctx": 8192},
    )
    return clean_code_block(response["message"]["content"])