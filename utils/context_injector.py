import os
import re
from pathlib import Path
import ollama
import pandas as pd


def extract_workspace_schemas(
    user_prompt: str, workspace_dir: str = "."
) -> str:
    """Scans the user prompt (and optionally the folder) for data files,

    reads their columns/types, and formats them as plain text context.
    """
    workspace = Path(workspace_dir)

    # 1. Find any data filenames mentioned in the prompt (e.g., sales.csv, data.parquet)
    mentioned_files = re.findall(
        r"[\w\-./]+\.(?:csv|xlsx|xls|parquet|json)", user_prompt, re.IGNORECASE
    )

    # Fallback: if no specific file was named in the prompt, grab all CSV/Parquet files in the folder
    if not mentioned_files:
        target_files = list(workspace.glob("*.csv")) + list(
            workspace.glob("*.parquet")
        )
    else:
        target_files = [workspace / f for f in mentioned_files]

    schema_blocks = []
    for file_path in target_files:
        if not file_path.exists():
            continue

        try:
            # Read only the first 3 rows for speed and low memory usage
            if file_path.suffix.lower() == ".csv":
                df = pd.read_csv(file_path, nrows=3)
            elif file_path.suffix.lower() in [".xlsx", ".xls"]:
                df = pd.read_excel(file_path, nrows=3)
            elif file_path.suffix.lower() == ".parquet":
                df = pd.read_parquet(file_path).head(3)
            elif file_path.suffix.lower() == ".json":
                df = pd.read_json(file_path).head(3)
            else:
                continue

            cols = df.columns.tolist()
            dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
            sample_row = (
                df.iloc[0].to_dict() if not df.empty else "No rows found"
            )

            schema_blocks.append(
                f"File: '{file_path.name}'\n"
                f"  - Exact Columns: {cols}\n"
                f"  - Data Types: {dtypes}\n"
                f"  - Sample Row 1: {sample_row}"
            )
        except Exception as e:
            schema_blocks.append(f"File: '{file_path.name}' (Read error: {e})")

    if not schema_blocks:
        return ""

    return (
        "\n\n[VERIFIED DATASET SCHEMAS IN WORKSPACE]\n"
        + "\n".join(schema_blocks)
    )


# def generate_script(
#     user_prompt: str, output_filename: str, workspace_dir: str = "."
# ):
#     """Injects verified schemas into the prompt, calls qwen3:4b, and saves the clean code."""
#     # 1. Silently gather column names before calling Ollama
#     schema_context = extract_workspace_schemas(user_prompt, workspace_dir)

#     system_prompt = (
#         "You are an expert Python developer. Write clean, standalone Python"
#         " scripts using standard libraries like pandas. When dataset schemas"
#         " are provided in the prompt, you MUST use the exact column names"
#         " (including exact capitalization and spaces). Do NOT invent helper"
#         " functions. Output ONLY a single ```python code block."
#     )

#     full_prompt = f"{user_prompt}{schema_context}"

#     # 2. Call qwen3:4b WITHOUT any `tools` parameter
#     response = ollama.chat(
#         model="qwen3:4b",
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": full_prompt},
#         ],
#         options={
#             "temperature": 0,  # Prevents creative renaming of columns
#             "num_ctx": 8192,
#         },
#     )

#     raw_output = response["message"]["content"]

#     # 3. Parse the markdown code block and write the file
#     match = re.search(r"```python\s*(.*?)```", raw_output, re.DOTALL)
#     if not match:
#         raise ValueError("Model did not return a valid Python code block.")

#     clean_code = match.group(1).strip()

#     output_path = Path(workspace_dir) / output_filename
#     output_path.write_text(clean_code, encoding="utf-8")
#     print(f"Saved clean script to: {output_path}")


# # --- Example Usage ---
# if __name__ == "__main__":
#     task = (
#         "Write a script that loads sales_data.csv, drops rows with missing"
#         " totals, and prints average revenue by region."
#     )
#     generate_script(
#         user_prompt=task,
#         output_filename="analyze_sales.py",
#         workspace_dir="./my_scripts_folder",
#     )
