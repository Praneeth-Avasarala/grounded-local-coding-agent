import json
import pandas as pd
# from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
# from langchain_ollama import ChatOllama

# Add task specific functions to help model in the task

def inspect_dataset_schema(file_path: str) -> str:
    """Reads a CSV or Parquet file and returns its exact column names, types, and 2 sample rows."""
    try:
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path, nrows=5)
        elif file_path.endswith(".parquet"):
            df = pd.read_parquet(file_path)
        else:
            return "Error: Unsupported file format."

        schema_info = {
            "columns": df.columns.tolist(),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "sample_rows": df.head(2).to_dict(orient="records"),
        }
        return json.dumps(schema_info, indent=2)
    except Exception as e:
        return f"Error reading file: {str(e)}"


# # 1. Load the DataFrame
# df = pd.read_csv("your_data.csv")

# # 2. Initialize a local model that supports tool/code generation
# llm = ChatOllama(model="qwen2.5-coder", temperature=0)

# # 3. Create the agent (requires allow_dangerous_code=True to execute Python)
# agent = create_pandas_dataframe_agent(
#     llm, df, verbose=True, allow_dangerous_code=True
# )

# # 4. Ask the model to check the columns
# response = agent.invoke("What are the exact column names in this dataframe?")
# print(response["output"])