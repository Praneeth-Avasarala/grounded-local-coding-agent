from utils.util_funcs import clean_code_block
import ollama


def generate_chunk_code(
    ollama_model: str,
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
            "3. All relative file paths (such as `data/...` or `output/...`) must be relative to the current "
            "working directory (never relative to `__file__`).\n"
            "4. Always call `Path(filepath).parent.mkdir(parents=True, exist_ok=True)` before creating or saving any file.\n"
            "5. Output ONLY valid Python code inside a single ```python ... ``` block. No explanations."
        )

    user_parts = [
        f"### TARGET FILE: {chunk['target_file']}",
        f"### GOAL:\n{chunk['goal']}",
        f"### INPUT CONTRACT (from previous chunks):\n{chunk['input_contract']}",
        f"### OUTPUT CONTRACT (required for next chunks):\n{chunk['output_contract']}",
        f"### VERIFIED PACKAGE REFERENCE:\n{pkg_docs}",
    ]

    if existing_code and past_errors:
            user_parts.append(f"### PREVIOUS CODE DRAFT:\n```python\n{existing_code}\n```")
            error_history_text = "\n".join(
                f"- Attempt {idx} error: {err}" for idx, err in enumerate(past_errors, start=1)
            )
            user_parts.append(
                f"### ERROR HISTORY TO FIX (do not repeat any of these mistakes):\n{error_history_text}"
            )


    response = ollama.chat(
        model=ollama_model,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": "\n\n".join(user_parts)},
        ],
        options={"temperature": 0.15, "num_ctx": 6144},
    )
    return clean_code_block(response["message"]["content"])