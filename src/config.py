from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# ROOT_DIR = Path(__file__).resolve().parent.parent
# HOME = Path.home()

OLLAMA_MODEL = "qwen3:4b"
MAX_TRIES = 3

# Make a .env file in the repo directory. Store user-specific information like file paths, API keys, passwords etc.

# Reads the local .env file

## Load API keys
# GEMINI_API_KEY = os.getenv('GOOGLE_GEMINI_API_KEY')

## Set input/outut paths

### This is where your outputs are stored. 
#### Program stores created files here and uses some of them as cache memory.
# PROJECT_DIR = Path(os.getenv('PROJECT_DIR'))
PLAN_CACHE_DIR = Path(os.getenv('PLAN_CACHE_DIR'))
SCRIPTS_DIR = Path(os.getenv('SCRIPTS_DIR'))


### This is where task file is stored. 
### Program needs this to begin web-search.
TASK_FILE = os.getenv('TASK_FILE') # TASK_FILE = path to task file 

