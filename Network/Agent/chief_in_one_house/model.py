from typing import NewType, Tuple, List
import requests
import openai
import os
import json
from utils import read_file_as_strings,markdown_home_food_table,add_to_home_food_table
import re
import csv
import pandas as pd
IP = NewType('IP address', str)
Port = NewType('Port', str)
Address = Tuple[IP, Port]
Name = NewType('Name', str)
Friend = Tuple[Name, Address]


class CulinaryAssistant:
    """
    A class to manage the cooking process, including requirements gathering, food buying, and cooking instructions.
    """

    def __init__(self, name: str) -> None:
        """
        Initialize the CulinaryAssistant with a name and API key for OpenAI.
        """
        self.name = name
        self.chat = []

        # Load API key from configuration file
        with open('config.json') as config_file:
            config = json.load(config_file)
            self.api_key = config.get("api_key")

        # Initialize OpenAI API
        openai.api_key = self.api_key

    def _search_agent(self, prompt: str):
        """
        Placeholder method for searching an agent based on a prompt.
        """
        pass

    def cook(self, prompt: str) -> dict:
        """
        Main method to manage the cooking process:
        1. Generate requirements.
        2. Determine which foods need to be bought.
        3. Classify and buy foods from shopes.
        4. Check if all items are available.
        5. Provide cooking instructions.
        """
        # Load system prompts
        system_prompt_requirements = read_file_as_strings("system_prompt_requirements.txt")
        system_prompt_to_food_control = read_file_as_strings("system_prompt_to_food_control.txt")
        system_prompt_classify_foods = read_file_as_strings("system_prompt_classify_foods_to_buy.txt")
        system_prompt_check_requirements = read_file_as_strings("system_prompt_to_find_out_chief_have_all_requirements.txt")
        system_prompt_to_cook = read_file_as_strings("system_prompt_to_cook.txt")

        # Generate cooking requirements
        requirements = self._get_openai_response(system_prompt_requirements, prompt)
        print(requirements)
        print(10*"*"+"requirements"+10*"*")
        self.chat.append([
            {"role": "system", "content": system_prompt_requirements},
            {"role": "user", "content": prompt},
            {"role": "Cook", "content": requirements}
        ])

        # Determine which foods to buy
        table_of_food_home_have = markdown_home_food_table()
        prompt_food_control = (
            f"Based on the below table of foods and requirements, say which foods we need to buy.\n"
            f"### Table Foods \n{table_of_food_home_have}\n"
            f"### Requirements:\n{requirements}"
        )
        response = self._get_openai_response(system_prompt_to_food_control, prompt_food_control)
        print(response)
        foods_to_buy = self._extract_json_from_text(response)['missing_items']
        
        print(10*"*"+"foods_to_buy"+10*"*")
        self.chat.append([
            {"role": "system", "content": system_prompt_to_food_control},
            {"role": "Chief", "content": prompt_food_control},
            {"role": "home_food_control", "content": foods_to_buy}
        ])

        if len(foods_to_buy) > 0 :
            # Classify foods by jobs
            prompt_classify_foods = f"Classify these foods by jobs that sell them:\n{foods_to_buy}"
            classified_foods = self._get_openai_response(system_prompt_classify_foods, prompt_classify_foods)
            print(classified_foods)
            print(10*"*"+"classified_foods"+10*"*")

            classified_foods_json:json = self._extract_json_from_text(classified_foods)
            # classified_foods_json = json.loads(classified_foods_just_json)
            self.chat.append([
                {"role": "system", "content": system_prompt_classify_foods},
                {"role": "home_food_control", "content": prompt_classify_foods},
                {"role": "home_food_control", "content": classified_foods}
            ])

            # Buy classified foods
            for job_name, items in classified_foods_json.items():
                self._buy_foods(job_name, items)

        # Check if all items are available
        table_of_food_home_have = markdown_home_food_table()
        prompt_check_availability = (
            f"Based on the below table of foods and requirements, say if we can cook the foods or not.\n"
            f"### Table Foods \n{table_of_food_home_have}\n"
            f"### Requirements:\n{requirements}"
        )
        availability_status = self._get_openai_response(system_prompt_check_requirements, prompt_check_availability)
        print(availability_status)
        print(10*"*"+"availability_status"+10*"*")

        availability_status_json = self._extract_json_from_text(availability_status)
        # availability_status_json = json.loads(availability_status)
        self.chat.append([
            {"role": "system", "content": system_prompt_check_requirements},
            {"role": "home_food_control", "content": prompt_check_availability},
            {"role": "home_food_control", "content": availability_status}
        ])

        if availability_status_json.get('status') == 'Not completed':
            return {"status": "We don't have all the items needed to cook", "chats": self.chat}

        # Provide cooking instructions
        cooking_instructions = self._get_openai_response(system_prompt_to_cook, prompt)
        print(cooking_instructions)
        print(10*"*"+"cooking_instructions"+10*"*")

        self.chat.append([
            {"role": "system", "content": system_prompt_to_cook},
            {"role": "user", "content": prompt},
            {"role": "chief", "content": cooking_instructions}
        ])

        return {"status": "Cooked successfully", "chats": self.chat}

    def _get_openai_response(self, system_prompt: str, user_prompt: str) -> str:
        """
        Helper method to interact with the OpenAI API and get a response.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
        return response.choices[0].message.content


    def _find_usefull_agents(self, public_agents: str, jab_name: str , items_must_buy:list) -> list[Friend]:
        system_prompt = read_file_as_strings("find_agents.txt")
        prompt_find_agent = (
        f"I need to find an agent who can help with purchasing or acquiring the required items. The job should be similar to {jab_name}. "
        f"Please review the agent table below and identify which agent(s) could fulfill these requirements.\n"
        f"### Agent Table: \n{public_agents}\n"
        f"### Items to Acquire: \n{items_must_buy}")
        print(public_agents)
        response = self._get_openai_response(system_prompt,prompt_find_agent)
        print(response)
        response_json = self._extract_json_from_text(response)
        # print(response_json)
        print(10*"*"+"find agents for buy"+10*"*")
        list_of_usefull_friends = self._make_json_to_friend_type(response_json)
        return list_of_usefull_friends



    def _make_json_to_friend_type(self,response_json: dict) -> List[Friend]:
        friends_list = []
        
        for agent in response_json.get("matching_agents", []):
            name = agent.get("name")
            ip = agent.get("IP_Address")
            port = agent.get("Port")
            
            if name and ip and port:
                friend = (Name(name), (IP(ip), Port(port)))
                friends_list.append(friend)

        return friends_list

    def _get_sorted_friends(self, agent_list: List[dict]) -> List[Friend]:
            # Sort agents by relevance_rate first, and goodness_rate second
            sorted_agents = sorted(agent_list, key=lambda x: (-x['relevance_rate'], -x['goodness_rate']))
            
            # Extract name and address (IP, Port) for each agent
            friends_list = [
                (
                    Name(agent['name']),
                    (IP(agent['location']['ip']), Port(agent['location']['port']))
                )
                for agent in sorted_agents
            ]
            
            return friends_list
    def _buy_from_agent(self, agent: Friend, item_frequency: dict) -> dict:
        """
        Makes a request to the agent's shop API and attempts to buy items based on the agent's stock availability.
        
        Args:
            agent (Friend): The agent with IP and Port information.
            item_frequency (dict): A dictionary of items and the quantities to be bought.
            
        Returns:
            dict: Updated item_frequency with the remaining items after purchase.
        """
        agent_ip, agent_port = agent[1][0], agent[1][1]
        agent_url = f"http://{agent_ip}:{agent_port}/help"
        
        try:
            # Fetch API document from the agent's shop
            api_document = requests.get(agent_url).text
        except requests.RequestException as e:
            print(f"Error fetching API document from agent {agent_ip}:{agent_port} - {e}")
            return item_frequency

        try:
            # Generate the script to be executed based on agent's API document and item details
            script = self._agent_code(item_frequency, api_document, agent_ip, agent_port)
            print(script)
            # Dictionary to capture the script's namespace after execution
            namespace = {}

            # Execute the script safely
            exec(script, namespace)

            # Retrieve the result, including bought items
            result: dict = namespace.get('result', {})
            if not isinstance(result, dict):
                raise ValueError("Result is not a dictionary as expected")

            # print(result)
            print("+--------------------------------+--------------------------------+")
            buy_items = result.get('buy_items', [])
            
            if not isinstance(buy_items, list):
                raise ValueError("buy_items should be a list")

            print(10 * "*" + str(buy_items) + 10 * "*")
            
            
            print(f"buy items from the {agent[0]} with IP Address {agent[1][0]} and port {agent[1][1]}")
            print(10 * "*" + "End Shopping" + 10 * "*")
            list_items_bought = []
            # Process the "buy_items" list which is a list of dictionaries
            for item_info in buy_items:
                item_name = item_info.get('item')
                quantity_bought = item_info.get('quantity', 0)
                if quantity_bought > 0:
                    list_items_bought.append(item_name)

                if item_name in item_frequency:
                
                    del item_frequency[item_name]  # Remove items with zero or negative quantities

            # Return updated item_frequency with remaining items
            print("////////////////////////////////")
            print(list_items_bought)
            print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")

            message = add_to_home_food_table(list_items_bought)
            
            print(message)
            print("Item Remind:")
            return item_frequency        
        
        except Exception as e:
                print(f"Error during script execution: {e}")
                return item_frequency
            

    def _agent_code(self, response_json_item_frequency:dict, api_document:str,api_address:str,api_port:str):
        system_prompt = read_file_as_strings("buy_system_prompt.txt")
        # Extract items from the JSON
        items = response_json_item_frequency
        # Build the item list for the prompt
        item_list = []
        for item_info in items:
            item_name = item_info
            quantity = items[item_info]
            item_list.append(f"{item_name} ({quantity})")



        # Join items with commas and prepare the prompt
        item_str = ', '.join(item_list)
                    # f"Please proceed to buy the following items:\n{item_str}.\n\n"

                    # "Important Instructions:\n"
                    # "- If the available stock of any item is less than 50% of the requested quantity, do not purchase any items.\n"
                    # "- However, if the shortage across all items is less than 50%, buy as many of each item as possible up to the specified quantities.\n\n"
        prompt =   (f"I would like to make a purchase from the shop using the following details:\n"
                    f"- Shop IP Address: {api_address}\n"
                    f"- Port: {api_port}\n"
                    f"- API Documentation: {api_document}\n\n"
                    f"Please proceed to buy the following items:\n{item_str}.\n\n"
                    "Please set the result in variable result in the following JSON format:\n"
                    "{\n"
                    "  \"buy_items\": [\n"
                    "    {\"item\": \"<item_name>\", \"quantity\": <quantity_bought>},\n"
                    "    ...\n"
                    "  ]\n"
                    "}\n"
                    "If no items are bought, return an empty list for \"buy_items\".\n\n"
                    "Do not use the following code:\n"
                    "in if __name__ == \"__main__\":\n"
                    "    main()\n\n"
                    "Thank you!"
                    )
        # print(prompt)
        print("--------------------------------")
        response = self._get_openai_response(system_prompt,prompt)
        # print(response)
        messages = [
              {"role": "system", "content": system_prompt},
              {"role": "user", "content": prompt},
              {"role": "coder for api","content": response}
         ]
        self.chat.append(messages)
        strat_str = "```python"
        end_str = "```"
        code_script = self._find_code(response,strat_str,end_str)
        return code_script


    def _find_code(self,txt:str,start_str:str,end_str:str):
            """Finds and returns the text between start_str and end_str in the given txt using regex."""
            # Create a regex pattern to match content between start_str and end_str
            pattern = rf"{re.escape(start_str)}\s*(.*?)\s*{re.escape(end_str)}"
            
            # Use regex to search for the pattern in the text
            match = re.search(pattern, txt, re.DOTALL)
            
            # Raise an error if no match is found
            if not match:
                raise ValueError(f"Either '{start_str}' or '{end_str}' not found in the text.")

            # Return the matched content
            return match.group(1).strip()


    
    def _buy_with_hub(self, hub: Friend, items_must_buy: list, response_json_item_frequency: dict, public_agents_seen:list[Friend], hubs_seen:list[Friend]):
        hub_ip, hub_port = hub[1][0], hub[1][1]
        hub_url = f"http://{hub_ip}:{hub_port}/search_agent"
        # Helper function to format Friend tuples into JSON-friendly format
        def format_friends(friends: List[Friend]) -> List[List]:
            if len(friends) == 0:
                 return None
            return [
                [f_name, [f_ip, f_port]]
                for f_name, (f_ip, f_port) in friends
            ]

        # Prepare the payload for the request
        prompt = "Please help me buy the following items: " + ", ".join(items_must_buy)
        # Construct the params and headers for the request
        params = {
            'prompt': prompt,
            'name_agent': self.name
        }

        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }

        # Construct the data payload
        data = {
            "hub_user_search":format_friends(hubs_seen),
            "agent_block": format_friends(public_agents_seen)
        }
        print("Payload:", json.dumps(data, indent=4))  # Print the payload for debugging
        print("=-=" * 30)
        try:
            # Send the POST request with params, headers, and data (JSON payload)
            response = requests.post(hub_url, params=params, headers=headers, json=data)
            response_data = response.json()
            print(response_data)
            print("&" * 30)
            # Process the response JSON
            

            list_agents = self._get_sorted_friends(response_data.get('agents'))
            print(20*"-")
            print(list_agents)
            print(10*"*"+"Hub find agents"+10*"*")
            for agent in list_agents:
                
                response_json_item_frequency =  self._buy_from_agent(agent, response_json_item_frequency)
                
                public_agents_seen.append(agent)
                items_must_buy = list(response_json_item_frequency.keys())
                if len(items_must_buy):
                        break
            hubs_seen.append(hub)
            return response_json_item_frequency, hubs_seen, public_agents_seen

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")  # Log the error
            return response_json_item_frequency, hubs_seen, public_agents_seen
        except Exception as err:
            print(f"An error occurred: {err}")  # Log any other errors
            return response_json_item_frequency, hubs_seen, public_agents_seen

        
         
    def _buy_foods(self, job_name: str, items_must_buy: list):

        """
        Placeholder method for buying foods based on job name and items.
        """
        hubs = self._knowing_hubs()
        private_agents = self._private_agents()
        public_agents = self._public_agents()



        system_prompt = read_file_as_strings("find_quentity_item.txt")
        prompt_for_find_item_frequency = (
            f"I need to know how much of this items of list must to buy: "
            f"### List Items must buy: \n{items_must_buy}\n"
        )
        items = self._get_openai_response(system_prompt, prompt_for_find_item_frequency)
        self.chat.append([
            {"role": "system", "content": system_prompt},
            {"role": "Purchasing Manager", "content": prompt_for_find_item_frequency},
            {"role": "chief", "content": items}])
        print(items)
        print(3*"*"+"items and number of items must be buy"+10*"*")

        response_json_item_frequency = self._extract_json_from_text(items)
        ### response_json_item_frequency is dict, for example: {"Apple": 5, "Lemon": 3}


        print(2*"\n")
        print("Items can be buy by public agent")
        public_agents_can_help = self._find_usefull_agents(public_agents,job_name,items_must_buy)
        for agent in public_agents_can_help:
                response_json_item_frequency = self._buy_from_agent(agent, response_json_item_frequency)
                print("item frequency ",response_json_item_frequency)
                items_must_buy = list(response_json_item_frequency.keys())
                if len(items_must_buy) == 0:
                    return

        print(2*"\n")
        print("Items can be buy by private agent")
        private_agents_can_help = self._find_usefull_agents(private_agents,job_name,items_must_buy)
        for agent in private_agents_can_help:
                response_json_item_frequency = self._buy_from_agent(agent, response_json_item_frequency)
                items_must_buy = list(response_json_item_frequency.keys())
                if len(items_must_buy) == 0:
                        return

        public_agents_seen = public_agents_can_help
        hubs_seen = []
        print(2*"\n")
        print("Items can be buy by hub")
        for hub in hubs:

            response_json_item_frequency,hubs_seen,public_agents_seen = self._buy_with_hub(hub, items_must_buy ,response_json_item_frequency, public_agents_seen, hubs_seen)
            items_must_buy = list(response_json_item_frequency.keys())
            if len(items_must_buy) == 0:
                        return

        return 

    def _knowing_hubs(self):
        
        file_path = "Hubs.csv"
        # Read the CSV file and create a list of friends
        hubs = []
        with open(file_path, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['Active'] == 'TRUE':
                    name = Name(row['Agent Name'])
                    address = (IP(row['IP Address']), Port(row['Port']))
                    hubs.append((name, address))
        return hubs
    
    def _private_agents(self) -> str:
        
        file_path = "Private_Agent_properties.csv"
        # Read the CSV file into a DataFrame
        df = pd.read_csv(file_path)
        
        # Filter rows where 'Active' column is 'TRUE'
        active_agents_df = df[df['Active'] == True]
        
        # Convert the filtered DataFrame to a markdown table format
        markdown_table = active_agents_df.to_markdown(index=False)
        
        # Return the markdown table
        return markdown_table
    def _public_agents(self) -> str:
        # Path to the CSV file containing agent properties
        file_path = "Public_Agent_properties.csv"
        
        # Read the CSV file into a DataFrame
        df = pd.read_csv(file_path)
        
        # Filter rows where 'Active' column is 'TRUE'
        active_agents_df = df[df['Active'] == True]
        
        # Convert the filtered DataFrame to a markdown table format
        markdown_table = active_agents_df.to_markdown(index=False)
        
        # Return the markdown table
        return markdown_table
    def _extract_json_from_text(self,text):
        # Use regex to find content between ''' json ''' and extract it
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            json_string = match.group(1)
            try:
                # Convert JSON string to dictionary
                data_dict = json.loads(json_string)
                return data_dict
            except json.JSONDecodeError:
                print("Error parsing JSON.")
                return None
        else:
            print("JSON text not found.")
            return json.loads(text)

   
