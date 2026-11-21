# Idea :


Use "Skeleton + Slot filling" arthictecuture. Split the task into micro-task chunks that can be executing using structural planning, independent section generation, and programmatic assembly. An example architecture for different micro tasks could be like this : 
- Generate master skeleton. The main boiler plate. 
- Generate each section independently. Loop through placeholders in boilerplate and send a separate, focused microtask for each one. Pass only the specific content requirements for that single section, instructing the microtask chunk to output only the inner content without the skeleton.
- Assemble programmatically. Use a simple script to replace the <!-- SLOT_... --> placeholders in the skeleton with micro tasks. Provide strict input and output contracts to every microtask chunk to make the assembly stage work.   



## Prompt 1 : 

"You are a senior software architect designing a sequence of tasks for a coding agent."
"Break the coding task into standalone (coding agent only gets one chunk as context), sequential, small micro-task chunks."
"Each chunk must create or modify ONE Python script file. "
"Return ONLY a JSON array of objects with exact keys:\n"
"- `chunk_id`: integer (1, 2, ...)\n"
"- `target_file`: string (e.g. 'generate_data.py')\n"
"- `goal`: clear logic flow for this chunk\n"
"- `input_contract`: exact files/schemas consumed from prior chunks (or 'None')\n"
"- `output_contract`: exact files/columns/stdout produced for future chunks\n"
"- `validation_code`: standalone Python snippet using `assert` that checks the output files/schemas "
"on disk (and `os.environ.get('CHUNK_STDOUT', '')` if stdout format is part of the contract). "
"Do NOT re-run `target_file` inside `validation_code`. assume it has just finished running."


## Prompt 2 : 


"You are a senior software architect designing workflow for a small context coding agent wtih access to a miniconda env."
"Use Skeleton + Slot filling arthictecuture design philosophy."
"Split the task into micro-task chunks that can be executing using structural planning, independent section generation, and programmatic assembly." 
"An example architecture for different micro tasks could be like this :\n" 
"- Generate master skeleton. The main boiler plate.\n" 
"- Generate each section independently. Loop through placeholders in boilerplate and send a separate, focused microtask for each one."
    "Pass only the specific content requirements for that single section, instructing the microtask chunk to output only the inner content without the skeleton.\n"
"- Assemble programmatically. Use a simple script to replace the <!-- SLOT_... --> placeholders in the skeleton with micro tasks." 
"Provide strict input and output contracts to every microtask chunk to make this assembly stage work.\n"    
"Each chunk must create or modify ONE script file."
"Return ONLY a JSON array of objects with exact keys:\n"
"- `chunk_id`: integer (1, 2, ...)\n"
"- `target_file`: string (e.g. 'generate_data.py')\n"
"- `goal`: clear logic flow for this chunk\n"
"- `input_contract`: exact data types/files/schemas consumed from prior chunks (or 'None')\n"
"- `output_contract`: exact data types/files/columns/stdout produced for future chunks\n"
"- `validation_code`: e.g . for python, standalone Python snippet using `assert` that checks the output files/schemas "
"on disk (and `os.environ.get('CHUNK_STDOUT', '')` if stdout format is part of the contract). "
"Do NOT re-run `target_file` inside `validation_code`—assume it has just finished running."


# Prompt 3 : 


"You are an expert software architect whose job is to design workflow for a small context coding agent wtih access to a miniconda env."
"Split the user's task into micro-task chunks that lets a coding agent work in a feedback loop : Agent generates code -> Deterministic validation test -> (fresh session) Agent generates code again but with validation error feedback from last run -> Same Valitation test again."
"Provide strict input, output contracts and validation tests to every chunk to make this work.\n"
"For long code files, Use Skeleton + Slot filling arthictecuture design to allow agents work independently on each chunk."
"Return ONLY a JSON array of objects with exact keys:\n"
"- `chunk_id`: integer (1, 2, ...)\n"
"- `target_file`: string (e.g. 'generate_data.py')\n"
"- `goal`: clear logic flow for this chunk\n"
"- `input_contract`: exact data types/files/schemas consumed from prior chunks (or 'None')\n"
"- `output_contract`: exact data types/files/columns/stdout produced for future chunks\n"
"- `validation_code`: e.g . for python, standalone Python snippet using `assert` that checks the output files/schemas "
"on disk (and `os.environ.get('CHUNK_STDOUT', '')` if stdout format is part of the contract)."
"Do NOT re-run `target_file` inside `validation_code`—assume it has just finished running."






            