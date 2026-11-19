from pathlib import Path
import os

ROOT_DIR = Path(__file__).resolve().parent.parent
HOME = Path.home()


PROJECT_DIR = HOME / "path/to/project_folder"    # Where you want the outputs to be stored
TASK_FILE = HOME / "path/to/task_file"  # Where the task file is located
OLLAMA_MODEL = "qwen3:4b"
MAX_TRIES = 3

GEMINI_API_KEY = os.environ('GOOGLE_GEMINI_API_KEY')