import pandas as pd
from typing import Any,List,Dict



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



def read_file_as_strings(filename:str="system_prompt.txt"):
    try:
        with open(filename, 'r') as file:
            # Read the entire content of the file into a string
            content = file.read()
            
            return content
    except FileNotFoundError:
        print(f"Sorry, the file {filename} does not exist.")
        return "You are good assistant."

def find_row_of_data_frame_by_type_agent(list_type, name_csv:str="Agent_properties.csv"):
    """
    Find rows in a DataFrame where the 'Agent Type' column matches any of the types in list_type and is active.
    Parameters:
    - list_type (list): A list of agent types to filter by, where each type also includes an 'Active' status.
    - name_csv (str): The name of the CSV file to load into the DataFrame.

    Returns:
    - DataFrame: A pandas DataFrame containing the filtered rows of active agents.
    """

    # Load the DataFrame from the CSV file
    df = pd.read_csv(name_csv)

    # Check if 'Agent Type' column exists in the DataFrame
    if 'Agent Type' not in df.columns:
        raise ValueError("'Agent Type' column not found in the CSV file")

    # Check if 'Active' column exists in the DataFrame
    if 'Active' not in df.columns:
        raise ValueError("'Active' column not found in the CSV file")

    # Filter the DataFrame based on the list_type and 'Active' status
    filtered_df = df[df['Agent Type'].isin(list_type) & df['Active'] == True]
    # Drop the 'Active' column before returning the DataFrame
    filtered_df = filtered_df.drop(columns=['Active'])
    
    return filtered_df
            



def make_data_frame_to_text_table(data_frame_retrieval, format_type='markdown', max_rows=100, max_columns=None):
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

def markdown_home_food_table():
    """
    Reads the home foods table from 'foods_we_have.csv' and returns it as a markdown-formatted string.
    
    Returns:
    - str: The home foods table formatted as markdown.
    """
    # Read the CSV file into a DataFrame
    try:
        home_foods_df = pd.read_csv('foods_we_have.csv')
    except FileNotFoundError:
        return "Error: 'foods_we_have.csv' file not found."
    
    # Convert the DataFrame to markdown format using the provided helper function
    markdown_table = make_data_frame_to_text_table(home_foods_df, format_type='markdown', max_rows=100)

    return markdown_table

def add_to_home_food_table(list_items: list):
    """
    Adds a list of food items to the 'foods_we_have.csv' file.

    Args:
    - list_items (list): A list of dictionaries, where each dictionary represents a row in the CSV.
                         The keys in the dictionary should correspond to the columns of the CSV file.

    Returns:
    - str: Success or error message indicating the result of the operation.
    """
    # Read the current CSV file into a DataFrame
    try:
        home_foods_df = pd.read_csv('foods_we_have.csv')
    except FileNotFoundError:
        return "Error: 'foods_we_have.csv' file not found."

    # Convert the list of items into a DataFrame
    new_items_df = pd.DataFrame(list_items,columns=['Item'])
    
    # Ensure that the new items have the same columns as the existing DataFrame
    if not all(column in new_items_df.columns for column in home_foods_df.columns):
        return "Error: The provided items don't match the structure of the existing table."

    # Append the new items to the DataFrame
    updated_df = pd.concat([home_foods_df, new_items_df], ignore_index=True)

    # Save the updated DataFrame back to the CSV file
    try:
        updated_df.to_csv('foods_we_have.csv', index=False)
        print("table updated:")
        print(updated_df)
        return "Items successfully added to the home foods table."
    except Exception as e:
        return f"Error: Failed to save the updated table. {e}"

    
