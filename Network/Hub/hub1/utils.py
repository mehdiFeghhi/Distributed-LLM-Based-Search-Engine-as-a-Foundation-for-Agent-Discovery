import pandas as pd
from typing import Any,List,Dict, NewType,Tuple
IP = NewType('IP address',str)
Port = NewType('Port',str)
Address = Tuple [IP,Port]
Name = NewType('Name',str)
Friend = Tuple[Name,Address]

def is_agent_exist(ip: str, agent_name: str, name_csv: str = "Public_Agent_properties.csv") -> bool:
    try:
        # Load the CSV file into a DataFrame
        df = pd.read_csv(name_csv)
        
        # Check if there is any row that matches both the IP and agent name
        exists = ((df['IP Address'] == ip) & (df['Agent Name'] == agent_name)).any()
        
        return exists
    except FileNotFoundError:
        print(f"The file {name_csv} was not found.")
        return False
    except KeyError:
        print("The specified columns (ip, agent_name) do not exist in the CSV file.")
        return False


 
def agent_activision(ip: str, agent: str, boolean: bool = False, name_csv: str = "Public_Agent_properties.csv") -> bool:
    try:
        # Load the CSV file into a DataFrame
        df = pd.read_csv(name_csv)
        
        # Check if the specified columns exist
        if 'ip' not in df.columns or 'agent_name' not in df.columns or 'active' not in df.columns:
            print("The required columns (ip, agent_name, active) do not exist in the CSV file.")
            return False
        
        # Check if there is any row that matches both the IP and agent name
        match = (df['IP Address'] == ip) & (df['Agent Name'] == agent)
        
        if match.any():
            # Update the activation status of the matching rows
            df.loc[match, 'Active'] = boolean
            
            # Save the updated DataFrame back to the CSV file
            df.to_csv(name_csv, index=False)
            
            return True
        else:
            print("The specified IP and agent name combination was not found.")
            return False

    except FileNotFoundError:
        print(f"The file {name_csv} was not found.")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False




def mapping_ip_to_agent(ip: str, name_csv: str = "Public_Agent_properties.csv"):
    """
    Map an IP address to an agent based on data from a CSV file.

    Parameters:
    - ip (str): The IP address to search for.
    - name_csv (str): The name of the CSV file to load into the DataFrame. Default is 'Agent_properties.csv'.

    Returns:
    - str or None: The name of the agent corresponding to the IP address, or None if no match is found.
    """
    
    # Load the DataFrame from the CSV file
    try:
        df = pd.read_csv(name_csv)
    except FileNotFoundError:
        raise FileNotFoundError(f"The file {name_csv} was not found.")
    
    # Check if 'IP Address' and 'Agent Name' columns exist in the DataFrame
    if 'IP Address' not in df.columns or 'Agent Name' not in df.columns:
        raise ValueError("'IP Address' and/or 'Agent Name' columns not found in the CSV file")
    
    # Search for the IP address in the DataFrame
    result = df[df['IP Address'] == ip]
    
    # If a match is found, return the corresponding 'Agent Name'
    if not result.empty:
        return result.iloc[0]['Agent Name']
    
    # If no match is found, return None or a message
    return None
def read_file_as_strings(filename:str="system_prompt.txt"):
    try:
        with open(filename, 'r') as file:
            # Read the entire content of the file into a string
            content = file.read()
            
            return content
    except FileNotFoundError:
        print(f"Sorry, the file {filename} does not exist.")
        return "You are good assistant."
def find_row_of_data_frame_by_type_agent(list_type: List[str], person_block: List[Friend], name_csv: str = "Public_Agent_properties.csv") -> pd.DataFrame:
    """
    Find rows in a DataFrame where the 'Agent Type' column matches any of the types in list_type,
    the agent is active, and the agent's Name, IP Address, and Port do not match those from the person_block list.
    
    Parameters:
    - list_type (list): A list of agent types to filter by.
    - person_block (list): A list of tuples containing names and addresses of blocked persons.
    - name_csv (str): The name of the CSV file to load into the DataFrame.
    
    Returns:
    - DataFrame: A pandas DataFrame containing the filtered rows of active agents excluding the blocked ones.
    """
    
    # Load the CSV into a DataFrame
    df = pd.read_csv(name_csv)
    
    # Validate required columns
    required_columns = ['Agent Type', 'Active', 'Name', 'IP Address', 'Port']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
    
    # Filter by agent type and active status
    filtered_df = df[(df['Agent Type'].isin(list_type)) & (df['Active'] == True)]
    
    # Exclude blocked persons if the list is provided
    if person_block:
        filtered_df = exclude_blocked_agents(filtered_df, person_block)

    # Remove the 'Active' column before returning
    return filtered_df.drop(columns=['Active'])

def exclude_blocked_agents(df: pd.DataFrame, person_block: List[Friend]) -> pd.DataFrame:
    """
    Exclude rows from the DataFrame where the agent's 'Name', 'IP Address', and 'Port'
    match any of the entries in the person_block list.

    Parameters:
    - df (DataFrame): The DataFrame to filter.
    - person_block (list): A list of tuples containing names and addresses of blocked persons.

    Returns:
    - DataFrame: The filtered DataFrame.
    """
    
    # Convert person_block into a DataFrame for merging
    person_block_df = pd.DataFrame([(friend[0], friend[1][0], int(friend[1][1])) for friend in person_block], 
                                   columns=['Name', 'IP Address', 'Port'])
    print(10 * "*" + "block row person" + 10 * "*")
    print(person_block)
    # Perform a left merge and filter out matches (blocked agents)
    merged_df = df.merge(person_block_df, on=['Name', 'IP Address', 'Port'], how='left', indicator=True)
    
    # Exclude rows that were matched in the merge (i.e., rows with '_merge' == 'both')
    filtered_df = merged_df[merged_df['_merge'] == 'left_only'].drop(columns=['_merge'])
    
    print(10 * "*" + "filtered row person" + 10 * "*")
    print(filtered_df)
    
    return filtered_df

def generate_markdown_table(name_csv: str = "Public_Agent_properties.csv"):
    """
    Generate a Markdown table from the DataFrame containing 'Agent Type' and 'Description' columns.

    Parameters:
    - name_csv (str): The name of the CSV file to load into the DataFrame.

    Returns:
    - str: A Markdown formatted string of the unique table.
    """
    
    # Load the DataFrame from the CSV file
    df = pd.read_csv(name_csv)

    # Check if 'Agent Type' and 'Description' columns exist in the DataFrame
    if 'Agent Type' not in df.columns:
        raise ValueError("'Agent Type' column not found in the CSV file")
    
    if 'Description' not in df.columns:
        raise ValueError("'Description' column not found in the CSV file")

    # Drop duplicate rows based on 'Agent Type'
    unique_df = df.drop_duplicates(subset=['Agent Type'])

    # Create the Markdown table header
    markdown_table = "| Agent Name          | Description                              |\n"
    markdown_table += "|---------------------|------------------------------------------|\n"

    # Append each row from the DataFrame to the Markdown table
    for _, row in unique_df.iterrows():
        agent_name = row['Agent Type']
        description = row['Description']
        markdown_table += f"| {agent_name:<19} | {description:<40} |\n"

    return markdown_table

def make_chat_history(system_prompt:str,prompt:str, markdown_data_retrival:str) -> list:

    """
    Creates a chat history list for a conversation with the assistant.

    Args:
    - system_prompt (str): The initial instruction or context setting for the assistant.
    - user_prompt (str): The question or input provided by the user.
    - markdown_data_retrieval (str): Additional contextual information to assist the assistant.

    Returns:
    - list: A list of dictionaries representing the conversation history.
    """
    chat_history = []

    # Add the system prompt to the chat history if provided
    chat_history.append({
            "role": "system",
            "content": system_prompt
        })

    # Add the user's prompt to the chat history if provided
    user_prompt = "Base on the Below information answer to the question :\n"+"context table:\n"+ markdown_data_retrival+"\n"+"user prompt:\n" + prompt
    chat_history.append({
            "role": "user",
            "content": user_prompt
        })

    
    return chat_history


def make_data_frame_to_text_table(data_frame_retrieval, format_type='markdown', max_rows=25, max_columns=None):
    """
    Convert a DataFrame into a text format suitable for a large language model.

    Parameters:
    - data_frame_retrieval (DataFrame): The pandas DataFrame to convert.
    - format_type (str): The format of the text output. Options are 'table', 'markdown', 'csv'.
    - max_rows (int): Maximum number of rows to include in the output.
    - max_columns (int): Maximum number of columns to include in the output. Default is None (show all).

    Returns:
    - str: The formatted text table.
    """

    # Truncate the DataFrame if it's too large
    if max_columns:
        data_frame_retrieval = data_frame_retrieval.iloc[:, :max_columns]
    if max_rows:
        data_frame_retrieval = data_frame_retrieval.head(max_rows)

    if format_type == 'markdown':
        text_table = data_frame_retrieval.to_markdown(index=False)
    elif format_type == 'csv':
        text_table = data_frame_retrieval.to_csv(index=False)
    else:  # default to plain table format
        text_table = data_frame_retrieval.to_string(index=False)

    # Add metadata
    metadata = f"Rows: {data_frame_retrieval.shape[0]}, Columns: {data_frame_retrieval.shape[1]}"
    formatted_output = f"{metadata}\n\n{text_table}"

    return formatted_output
def add_agent_to_csv(ip: str, name_agent: str, file_path: str, extra_columns: Dict[str, str] = {}):
    import pandas as pd
    
    # Load the existing data
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        df = pd.DataFrame()  # Create an empty DataFrame if the file does not exist
    
    # Create a new row with the IP and agent details
    new_row = {"IP Address": ip, "Agent Name": name_agent}
    if extra_columns is not None:
        new_row.update(extra_columns)  # Add extra columns

    # Convert the new row to a DataFrame
    new_row_df = pd.DataFrame([new_row])
    
    # Append the new row to the DataFrame
    df = pd.concat([df, new_row_df], ignore_index=True)
    
    # Save the updated DataFrame back to the CSV file
    df.to_csv(file_path, index=False)
