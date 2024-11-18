from typing import NewType, Tuple, List
import pandas as pd
import requests
import openai
import json
import re
from utils import read_file_as_strings, generate_markdown_table

# Type aliases for clarity
IP = NewType('IP address', str)
Port = NewType('Port', str)
Address = Tuple[IP, Port]
Name = NewType('Name', str)
Friend = Tuple[Name, Address]

class Hub:
    def __init__(self, name: str,address:str,prot:str) -> None:
        """
        Initialize the Hub with a name and load the API key from the configuration file.
        
        Args:
            name (str): The name of the hub.
        """
        self.name = name
        self.address = address  # Placeholder, could be updated with actual address logic
        self.port = prot
        self.hub_friends: List[Address] = self._load_friends_address()
        self.api_key = self._load_api_key()


    def _load_friends_address(self):
        # Load the CSV file
        file_path = "Hub_properties.csv"
        
        # Read the CSV file into a DataFrame
        df = pd.read_csv(file_path)
        
        # Filter rows where the active column is True
        active_friends = df[df['Active'] == True]
        
        # Convert the filtered DataFrame to a list of tuples (Name, Address)
        friends = [
            (Name(row['Agent Name']), (IP(row['IP Address']), Port(row['Port'])))
            for _, row in active_friends.iterrows()
        ]
        
        return friends
    def _load_api_key(self) -> str:
        """
        Load API key from the configuration file.
        
        Returns:
            str: The API key for OpenAI.
        """
        with open('config.json') as config_file:
            config = json.load(config_file)
            return config.get("api_key")

    def hub_search_agent(self, chat_dictionary: str, prompt: str, 
                         hub_user_search: List[Friend] = None, 
                         person_block: List[Friend] = None) -> dict:
        """
        Search for an agent within the hub and its friends.
        
        Args:
            chat_dictionary (str): The dictionary for the chat context.
            prompt (str): The search prompt to find the agent.
            hub_user_search (List[Friend], optional): List of friends already searched.
            person_block (List[Friend], optional): List of blocked persons.
        
        Returns:
            dict: The search result including agent details or status.
        """
        hub_user_search = hub_user_search or []

        # Search within the current hub
        response = self._find_agent(chat_dictionary)
        print(response)
        print(10*"*"+" Response Agents"+10*"*")
        if response.get("status") == "Find":
            return response

        # If not found, ask friends
        if response.get("status") == "Not Found":
            hub_user_search.append((Name(self.name),(IP(self.address),Port(self.port))))
            for friend in self.hub_friends:
                if not self._friend_exist(friend,hub_user_search):
                    
                    response_hub = self._ask_friend(prompt, friend, hub_user_search, person_block)
                    if response_hub.get("status") == "Find":
                        return response_hub

        return response


    def _friend_exist(self, friend: Friend, hub_user_search: list) -> bool:
        """
        Check if a given friend exists in the hub_user_search list.

        Args:
        - friend (Friend): A tuple containing the friend's name and address (IP and port).
        - hub_user_search (list): A list of hubs with their names and addresses.

        Returns:
        - bool: True if the friend exists in the hub_user_search, False otherwise.
        """
        friend_name, (friend_ip, friend_port) = friend

        for hub in hub_user_search:
            print(hub)
            print(friend_name, friend_ip, friend_port)
            hub_name, (hub_ip, hub_port) = hub
            if friend_name == hub_name and friend_ip == hub_ip and str(friend_port) == str(hub_port):
                
                return True  # Friend exists in the hub_user_search list
        
        return False  # Friend not found

    def _find_agent(self, prompt_agent: list) -> dict:
        """
        Find an agent using the OpenAI API.
        
        Args:
            prompt_agent (list): The prompt for finding the agent.
        
        Returns:
            dict: The result including agent details or status.
        
        Raises:
            Exception: If an error occurs during the API call.
        """
        try:
            response_json = self._chat_gpt_api(prompt_agent)
            return self._extract_json_from_text(response_json)
        except Exception as e:
            print(f"Error finding agent: {e}")
            raise

    def _ask_friend(self, prompt_agent: str, friend: Friend, 
                    hub_user_search: List[Friend], 
                    agent_block: List[Friend]) -> dict:
        """
        Ask a friend (external service) for an agent.

        Args:
            prompt_agent (str): The prompt for the agent search.
            friend (Friend): The friend's details (name and address).
            hub_user_search (List[Friend]): List of friends already searched.
            agent_block (List[Friend]): List of blocked agents.

        Returns:
            dict: The response from the friend's service or an error message.
        """
        name, address = friend
        ip, port = address
        http_address = f"http://{ip}:{port}/search_agent"

        # Construct the params and headers for the request
        params = {
            'prompt': prompt_agent,
            'name_agent': self.name
        }

        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }

        # Helper function to format Friend tuples into JSON-friendly format
        def format_friends(friends: List[Friend]) -> List[List]:
            if friends is None:
                return None
            return [
                [f_name, [f_ip, f_port]]
                for f_name, (f_ip, f_port) in friends
            ]

        # Construct the data payload
        data = {
            "hub_user_search": format_friends(hub_user_search),
            "agent_block": format_friends(agent_block)
        }

        print("Payload:", json.dumps(data, indent=4))  # Print the payload for debugging
        print("params:", json.dumps(params, indent=4)) # Print  the params for  debugging
        print("headers:", json.dumps(headers, indent=4)) # Print the headers for debugging
        print("http_address:", http_address) ## Print the http_address for debugging
        print("|"*30)
        try:
            # Send the POST request with params, headers, and data (JSON payload)
            response = requests.post(http_address, params=params, headers=headers, json=data)
            print(response.json())
            print("&"*30)

            response.raise_for_status()  # Raises HTTPError for bad responses

            # Assuming the response is in JSON format
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"Error while asking friend {name}: {e}")
            return {"status": "error", "message": str(e)}
        
    def find_type_agent(self, prompt: str) -> List[dict]:
        """
        Find the type of agent using the OpenAI API.
        
        Args:
            prompt (str): The prompt to determine the type of agent.
        
        Returns:
            List[dict]: List of agents matching the prompt.
        
        Raises:
            Exception: If an error occurs during the API call.
        """
        message = self._create_find_type_message(prompt)
        try:
            response_json = self._chat_gpt_api(message)
            print(response_json)
            print(10*"*"+" Response find type message"+10*"*")
            list_agents = self._extract_json_from_text(response_json).get("agents", [])
            return [item['name'] for item in list_agents]
        except Exception as e:
            print(f"Error finding type of agent: {e}")
            raise

    def _create_find_type_message(self, prompt: str) -> List[dict]:
        """
        Create the message to find the type of agent using OpenAI API.
        
        Args:
            prompt (str): The request prompt for agent types.
        
        Returns:
            List[dict]: List of messages for the OpenAI API.
        """
        system_prompt = read_file_as_strings("find_type_system_prompt.txt")
        agent_markdown_table = generate_markdown_table()
        user_prompt = (
            "Based on the following Markdown table of agents, please identify which agents can satisfy the request.\n\n"
            "### Agent Table\n"
            f"{agent_markdown_table}\n\n"
            "### Request\n"
            f"{prompt}"
        )
        return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]

    def _extract_json_from_text(self, text: str) -> dict:
        """
        Extract JSON data from a text string.
        
        Args:
            text (str): The text containing JSON data.
        
        Returns:
            dict: The extracted JSON data or an empty dictionary if extraction fails.
        """
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        json_string = match.group(1) if match else text
        try:
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON: {e}")
            return {}

    def _chat_gpt_api(self, messages: list) -> str:
        """
        Interact with ChatGPT API for general chat or queries.
        
        Args:
            prompt (str): The query or message to send to ChatGPT.
        
        Returns:
            str: The response from ChatGPT.
        
        Raises:
            Exception: If an error occurs during the API call.
        """
        openai.api_key = self.api_key
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages= messages
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error interacting with ChatGPT API: {e}")
            raise
