from pathlib import Path
import os
from dotenv import load_dotenv


# OLLAMA_MODEL = "qwen3:4b"
# OLLAMA_MODEL = "qwen3:8b"
OLLAMA_MODEL = "qwen2.5-coder:latest"
MAX_TRIES = 6

# RECOMMENDED : Make a .env file in the root directory. 
# Store user-specific information like file paths, API keys, passwords etc.
# Load this info from .env file

load_dotenv()

## GEMINI_API_KEY = os.getenv('GOOGLE_GEMINI_API_KEY')

### This is where your outputs are stored. 

ROOT_DIR = Path(__file__).resolve().parent.parent

PLAN_CACHE_DIR = Path(os.getenv('PLAN_CACHE_DIR')) or (ROOT_DIR / "output")

SCRIPTS_DIR = Path(os.getenv('SCRIPTS_DIR')) or (ROOT_DIR / "output")


### This is where task file is stored. 
### Program needs this to begin web-search.
TASK_FILE = Path(os.getenv('TASK_FILE')) # TASK_FILE = path to task file 
TESTS_DIR = Path(os.getenv('TESTS_DIR'))




