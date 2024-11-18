import openai
import requests
import json
import logging
from typing import NewType, Tuple, List, Dict, Optional
from utils import read_file_as_strings
import re
import yaml

# Configure the logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Custom types for IP, Port, Address, Name, and Friend
IP = NewType('IP', str)
Port = NewType('Port', str)
Address = Tuple[IP, Port]
Name = NewType('Name', str)
Friend = Tuple[Name, Address]
class Steward:
    def __init__(self, config_file='config.json'):
        self.name = 'Mehdi STEWARD'
        logging.info("Initializing Steward")

        # Load the API key from the JSON config file
        try:
            with open(config_file, 'r') as file:
                logging.info("Loading configuration file")
                config = json.load(file)
                api_key = config.get("api_key")
                if not api_key:
                    raise ValueError("API key must be provided.")
                openai.api_key = api_key
                logging.info("API key loaded successfully")
        except FileNotFoundError:
            logging.error("Configuration file not found")
            raise Exception("Configuration file not found.")
        except json.JSONDecodeError:
            logging.error("Error decoding JSON from the configuration file")
            raise Exception("Error decoding JSON from the configuration file.")
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            raise Exception(f"An error occurred: {str(e)}")

    def _send_openai_request(self, system_prompt: str, user_prompt: str) -> str:
        """
        Get a response from the OpenAI API based on system and user prompts.
        """
        logging.info(f"Sending request to OpenAI with system_prompt: {system_prompt} and user_prompt: {user_prompt}")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return self._send_message_openAI(messages)

    def _send_message_openAI(self, messages):
        try:
            logging.info("Sending messages to OpenAI")
            response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
            logging.info("Received response from OpenAI")
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Failed to communicate with OpenAI: {str(e)}")
            return f"Error getting response: {str(e)}"

    def analyze_task(self, user_message: str) -> str:
        """
        Analyzes the user's message to determine which task it corresponds to 
        (hotel reservations, banking, meeting management, buying, or other).
        Returns the identified task in YAML format.
        """
        logging.info(f"Analyzing message: {user_message}")

        system_prompt = (
            "The user might request one of the following tasks: "
            "1. **Hotel Reservations**: User provides dates and location for booking. "
            "2. **Banking**: User inquires about account details, transactions, or balances. "
            "3. **Meeting Management**: User requests to schedule, modify, or cancel a meeting. "
            "4. **Buying**: User seeks assistance with purchasing items or services. "
            "5. **Greeting and Public Conversations**: User discusses greetings or matters related to public interactions, including those involving police. "
            "6. **Other**: User's request does not fit into the above categories. "
            "Analyze the user's message to determine which of these tasks it corresponds to. "
            "Return the result in YAML format with the following structure:\n"
            "```yaml\n"
            "task: <task_name>\n"
            "```"
        )
        user_prompt = user_message
        result = self._send_openai_request(system_prompt, user_prompt)
        logging.info(f"OpenAI response for task analysis: {result}")

        yaml_block = self._extract_yaml_block(result)

        if not yaml_block:
            logging.warning("No YAML block detected, returning 'Other'")
            return "Other"

        output = yaml.safe_load(yaml_block)
        return output.get("task","Other")



    def handler(self, user_prompt: str) -> str:
        """
        Handles the user prompt by analyzing the task and executing the appropriate function.
        """
        logging.info(f"Handling user prompt: {user_prompt}")
        task = self.analyze_task(user_prompt)
        logging.info(f"Identified task: {task}")
        print(task)
        if task == "Hotel Reservations":
            return self.hotel_reservations(user_prompt)
        elif task == "Greeting and Public Conversations":
            return self.greeting_public_conversations(user_prompt) 
        else:
            logging.info(f"Task '{task}' not supported at the moment.")
            return f"I can't help you with the task of {task} now."

    def hotel_reservations(self, user_prompt: str) -> str:
        """
        Handles hotel reservation requests, validating input and interacting with the hub to find hotels.
        """
        logging.info(f"Processing hotel reservation request: {user_prompt}")
        date_flag, city_flag,city_name,new_prompt = self._check_data_validation(user_prompt)

        if date_flag and city_flag:
            logging.info("Valid date and city found, searching for hotels")
            flage, response = self.find_hotels(new_prompt,city_name)  # Assuming you have a method to find hotels
            if not flage:
                logging.warning("No hotels found that match the criteria")
                return response
            hotels = response
            for hotel in hotels:
                succeeded, response = self._hotel_reservation(hotel, new_prompt)
                if succeeded:
                    logging.info(f"Successfully reserved hotel: {hotel}")
                    return response

            logging.warning("No hotels could be reserved with the given requirements")
            return "Unfortunately, I couldn't find any hotel that satisfies the requirements."
        else:
            logging.warning("Invalid or missing date and city information")
            return "Please specify the city and the start and end dates for your reservation."


     
    def _hotel_reservation(self, hotel: Friend, new_prompt: str) -> Tuple[bool, str]:
        """
        Handles hotel reservation by interacting with a chat system, suggesting rooms, 
        and reserving one based on information from the chat session.
        
        Args:
            hotel (Friend): Tuple containing the Name and Address (IP, Port) of the hotel.
            new_prompt (str): The user's new prompt for the reservation.
            
        Returns:
            Tuple[bool, str]: (True, "Reservation successful") if successful, else (False, "Error message").
        """
        hotel_name, hotel_address = hotel
        ip, port = hotel_address

        # Initialize chat by URL (use hotel IP and Port to form the URL)
        chat_url = f"http://{ip}:{port}/create_chat"
        logging.info(f"Attempting to create chat for hotel: {hotel_name} at {chat_url}")

        # Start chat with system prompt for this hotel
        response = requests.post(chat_url)

        if response.status_code != 200:
            logging.error(f"Failed to create chat with {hotel_name}. HTTP Status: {response.status_code}")
            return False, f"Failed to create chat with {hotel_name}. HTTP Status: {response.status_code}"

        chat_data = response.json()
        conversation_id = chat_data.get("conversation_id")
        initial_message = chat_data.get("initial_message")
        if not conversation_id:
            logging.warning("Failed to retrieve conversation ID from chat data.")
            return False, "Failed to retrieve conversation ID."

        logging.info(f"Successfully created chat for {hotel_name}. Conversation ID: {conversation_id}")
        
        specific_preferences = read_file_as_strings("agent_owner_habit_for_hotel_reservation.txt")
        system_prompt = f"""
        You are an assistant tasked with helping to reserve hotel rooms for Mehdi Feghhi based on his specific preferences and habits. Your role is to interact with the hotel receptionist to gather necessary information, suggest room options that match Mehdi's criteria, and facilitate the booking process. Please follow these instructions carefully:

        **Preferences and Criteria:**
        {specific_preferences}

        1. **Introduction:**
           - Introduce yourself as an assistant seeking to reserve a hotel room for Mehdi Feghhi.

        2. **Information Gathering:**
           - Request the **check-in** and **check-out dates** for Mehdi.
           - Confirm the **number of guests** (typically two, as Mehdi often invites a guest).

        3. **Suggesting Rooms:**
           - Based on the information gathered, listen to the receptionist's suggestions for room options.

        4. **Booking Process:**
           - Once a room is selected, ask the receptionist for a **link to complete the booking**.
           - Confirm that Mehdi is satisfied with the choice and inquire if there is anything else needed.

        5. **Ending the Conversation:**
            - Upon receiving a link or a set of rooms that you believe could fulfill your superior Mahdi's request, take a moment to express your appreciation.
            - If you see a link formatted like this: `link: http://other part of link` and realize that the sent link is a reservation link, perform the necessary action related to it.
            - If you notice that the other party cannot answer further questions, politely say goodbye.
            - Conclude the interaction with a polite farewell.


        6. **Handling Special Cases:**
           - If the receptionist mentions anything outside the normal hotel booking (e.g., unrelated topics), politely steer the conversation back to the reservation task.
        
        Example Conversation:
        ### User in this conversation is a reciptionist.
        user: "Welcome! How can I help you?"
        Assistant: "We need a room for two, with check-in on <start date> and check-out on <end date>, preferably in the $150-$180 range with a large bed."
        user: "Great, I recommend the $180 suite with VIP amenities and extra space—here’s the link to complete the reservation: [URL]. Is there anything else I can help with?"
        Assistant: "No, that’s all. Thanks!"
        user: "You’re very welcome! Have a wonderful day!"
        """
       
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": initial_message},
            {"role": "assistant", "content": new_prompt}
        ]
        
        continue_chat = True
        while continue_chat:
            logging.info("Continuing chat for room suggestions.")

            # Continue chatting using the new_prompt to get room suggestions
            chat_url = f"http://{ip}:{port}/chat"
            chat_payload = {
                "chat_id": int(conversation_id),
                "prompt": new_prompt
            }

            logging.info(f"Sending request to chat API at {chat_url} with payload: {chat_payload}")
            response = requests.post(chat_url, json=chat_payload)

            if response.status_code != 200:
                logging.error(f"Error during chat with {hotel_name}. HTTP Status: {response.status_code}. URL: {chat_url}")
                return False, f"Error during chat with {hotel_name}. HTTP Status: {response.status_code}"



            assistant_reply = response.json().get("assistant_reply", "")
            logging.info(f"receptionist: {assistant_reply}")

            if not assistant_reply:
                logging.warning("Assistant did not provide any suggestions.")
                return False, "Assistant did not provide any suggestions."

            # Log the state of continue_chat before checking its value
            continue_chat = response.json().get("continue_chat", False)
            if not continue_chat:
                break
            logging.info(f"Continue chat flag is set to: {continue_chat}")

            messages.append({"role": "user", "content": assistant_reply})

            # Log the messages being sent to OpenAI
            logging.debug(f"Messages to be sent to OpenAI: {messages}")

            new_prompt = self._send_message_openAI(messages)
            messages.append({"role": "assistant", "content": new_prompt})

            # Log the new prompt for the next iteration
            logging.debug(f"New prompt generated for next interaction: {new_prompt}")

        # After the loop, you can log the final state of the conversation
        logging.info("Chat conversation ended.")

        # Extract room suggestions from assistant's reply
        room_suggestion_url,room_suggestion_flage = self.find_best_room(messages)
        if not room_suggestion_flage:
            logging.warning("No room suggestions found.")
            return False, "No room suggestions found."

        # Open the URL for the selected room and reserve it
        reserve_url = room_suggestion_url
        logging.info(f"Reserving room at URL: {reserve_url}")
        reserve_response = requests.get(reserve_url)

        system_prompt = read_file_as_strings("reservation_system_prompt.txt")
        logging.info(f"System prompt loaded: {system_prompt}")
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        script = self._code_python_exatract(self._send_openai_request(system_prompt, reserve_response.text))
        logging.info(f"Script generated from reservation response: {script}")
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        # Dictionary to capture the script's namespace after execution
        namespace = {}
        print("*****************************************************************************************************************")
        # Execute the script safely
        exec(script, namespace)
        print("*****************************************************************************************************************")

        # Retrieve the result, including reservation
        result: dict = namespace.get('result', {})
        if not isinstance(result, dict):
            logging.error("Result is not a dictionary as expected")
            raise ValueError("Result is not a dictionary as expected")

        logging.info("Reservation process completed successfully.")
        print(result)
        return True, result

    def find_best_room(self, messages) -> Tuple[Optional[str], Optional[bool]]:
        """
        Concatenate all user messages and create a system prompt to find the best room URL
        that matches the user's needs, returning the result in YAML format.

        Args:
            messages (list): A list of message dictionaries containing role and content.

        Returns:
            Tuple[Optional[str], Optional[bool]]: The best room URL and a success flag.
        """
        logging.info("Starting find_best_room function")

        # Extract user messages
        user_messages = [msg["content"] for msg in messages if msg["role"] == "user"]
        logging.debug(f"Extracted user messages: {user_messages}")

        # Concatenate user messages into a single string
        input_user_message = " ".join(user_messages)
        logging.debug(f"Concatenated user message: {input_user_message}")

        # Read user habits/preferences from the specified text file
        user_habits = read_file_as_strings("agent_owner_habit_for_hotel_reservation.txt")
        logging.debug(f"Loaded user habits: {user_habits}")

        # Create a system prompt including user habits and a note on expected output format
        system_prompt = (
            "You are a helpful assistant that finds the best room for a user based on their preferences.\n"
            f"The user's features and habits are as follows: {user_habits}\n"
            "The available room information includes various options from the hotel.\n"
            "This means you need to analyze the user's input and determine a suitable room based on their needs.\n"
            "If a room is found, provide the room URL along with a success flag indicating whether the search was successful.\n"
            "Format of input user messages: User preferences about the room.\n"
            "Output:\n"
            "yaml format with include:\n"
            'best_room_url: "http://example.com/room205"\n'
            'success: true\n'
            "```"
        )
        logging.info(f"Generated system prompt: {system_prompt}")

        # Send the prompts to the OpenAI request function
        yaml_output = self._send_openai_request(system_prompt, input_user_message)
        logging.info(f"Received YAML output: {yaml_output}")

        # Extract the YAML block from the model output
        yaml_data = self._extract_yaml_block(yaml_output)
        logging.info(f"Extracted YAML data: {yaml_data}")

        if yaml_data:
            # Parse the YAML data
            parsed_data = yaml.safe_load(yaml_data)
            logging.info(f"Parsed YAML data: {parsed_data}")
            best_room_url = parsed_data.get('best_room_url')
            success_flag = parsed_data.get('success', False)
            logging.info(f"Best room URL: {best_room_url}, Success flag: {success_flag}")
            return best_room_url, success_flag
        
        logging.info("No valid room found")
        return None, False
 

    def _code_python_exatract(self, response: str):
        """
        Finds and returns the text between start_str and end_str in the given response using regex.
        """
        logging.info(f"Extracting Python code from the response.{response}")
        
        # Create a regex pattern to match content between start_str and end_str
        start_str = "```python"
        end_str = "```"
        pattern = rf"{re.escape(start_str)}\s*(.*?)\s*{re.escape(end_str)}"
        
        # Use regex to search for the pattern in the text
        match = re.search(pattern, response, re.DOTALL)
        
        # Raise an error if no match is found
        if not match:
            logging.error(f"Either '{start_str}' or '{end_str}' not found in the response.")
            raise ValueError(f"Either '{start_str}' or '{end_str}' not found in the response.")
        
        # Return the matched content
        logging.info("Python code successfully extracted.")
        return match.group(1).strip()

    def _extract_yaml_block(self, yaml_output: str) -> Optional[str]:
        """
        Extracts the YAML block from the provided output string.
        
        Args:
            yaml_output (str): The string containing the YAML content.
        
        Returns:
            Optional[str]: Extracted YAML block as a string or None if not found.
        """
        logging.info("Extracting YAML block from the output.")
        
        yaml_match = re.search(r'```yaml(.*?)```', yaml_output, re.DOTALL)
        if yaml_match:
            yaml_data = yaml_match.group(1).strip()
            logging.info("YAML block found and extracted.")
            return yaml_data
        else:
            logging.error("YAML block not found in the output.")
            return None

    def _check_data_validation(self, user_prompt: str) -> Tuple[bool, bool, str, str]:
        """
        Validates user input to ensure both city and date range (start and end dates) are provided by utilizing OpenAI's language capabilities.
        The result is expected in YAML format.
        """
        logging.info("Validating user prompt for city and date information.")

        # Updated system prompt to analyze the user prompt and return results in YAML format
        system_prompt = (
            "Analyze the following user prompt and determine if it contains both city and date range (start and end dates) information. "
            "If found, return the results in the following YAML format:\n"
            "```yaml\n"
            "city: <city_name>\n"
            "start_date: <start_date>\n"
            "end_date: <end_date>\n"
            "```\n"
            "User prompt: {user_prompt}"
        ).format(user_prompt=user_prompt)

        user_response = self._send_openai_request(system_prompt, user_prompt)

        # Extracting the YAML block from the response
        yaml_data = self._extract_yaml_block(user_response)

        if yaml_data:
            try:
                # Assuming the extracted YAML block is structured correctly
                yaml_dict = yaml.safe_load(yaml_data)
                city_name = yaml_dict.get("city", "")
                start_date = yaml_dict.get("start_date", "")
                end_date = yaml_dict.get("end_date", "")

                if city_name and start_date and end_date:
                    logging.info("City and date range found in user prompt.")
                    return True, True, city_name, user_prompt
                else:
                    logging.warning("City or date range missing in user prompt.")
                    return False, False, "", user_prompt  # Return empty city name if not found
            except Exception as e:
                logging.error(f"Error processing YAML data: {str(e)}")
                return False, False, "", user_prompt  # Handle YAML parsing errors
        else:
            logging.warning("YAML block not found in the OpenAI response.")
            return False, False, "", user_prompt  # Return empty city name if not found

    def _get_hub_info(self, city_name:str):

        if city_name == "Shiraz":
            logging.info(f"Fetching hub information in {city_name}")
            return "127.0.0.1", 8001,True
        else :
            None, None, False


    def _get_sorted_friends(self, agent_list: List[dict]) -> List[Friend]:
        """
        Sort agents by relevance_rate first, and goodness_rate second, and extract their information.
        """
        logging.info("Sorting agents by relevance and goodness rates.")
        
        sorted_agents = sorted(agent_list, key=lambda x: (-x['relevance_rate'], -x['goodness_rate']))
        
        friends_list = [
            (
                Name(agent['name']),
                (IP(agent['location']['ip']), Port(agent['location']['port']))
            )
            for agent in sorted_agents
        ]
        
        logging.info(f"Sorted friends: {friends_list}")
        return friends_list

    def find_hotels(self, new_prompt: str,city_name:str) -> tuple[bool, List[Friend]]:
        """
        Attempt to reserve a room at the specified hotel based on user input.
        """
        logging.info(f"Attempting to find hotels with the following prompt: {new_prompt}")

        hub_ip, hub_port,flage_fetch = self._get_hub_info(city_name)  # Assume you have a method to get hub information

        if not flage_fetch:
                return False, f"We don't have a hub search for the city name of {city_name}"
        
        hub_url = f"http://{hub_ip}:{hub_port}/search_agent"
            
        payload = {
            "hub_user_search": None,
            "agent_block": None
        }

        try:
            response = requests.post(hub_url, params={'prompt': new_prompt, 'name_agent': self.name},
                                    headers={'accept': 'application/json', 'Content-Type': 'application/json'},
                                    json=payload)
            logging.info(f"POST request sent to {hub_url}, status code: {response.status_code}")
            
            response_data = response.json()
            logging.info(f"Response from hub: {response_data}")

            if response_data.get("status") == "Find":
                logging.info(f"Hotel found for reservation: {response_data.get('agents')}")
                return True, self._get_sorted_friends(response_data.get('agents'))
            else:
                logging.warning(f"No hotel found for reservation: {response_data.get('message')}")
                return False, response_data.get("message", "Reservation failed because hub can't find a hotel for reservation.")
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred: {http_err}")
            return False, f"An HTTP error occurred: {http_err}"
        except Exception as err:
            logging.error(f"An error occurred: {err}")
            return False, f"An error occurred: {err}"
    
    
    
    def greeting_public_conversations(self,user_prompt):
        
        system_prompt = (
            "You are an assistant engaging in greeting and public conversations. "
            "Your goal is to guide the user to address their needs effectively. "
            "If the user expresses a greeting, respond warmly and encourage them to share their needs. "
            "If the user mentions topics related to public interactions, such as inquiries about services or assistance, "
            "try to lead them towards specific tasks:\n"
            "1. **Hotel Reservations**: Ask if they need help booking a hotel. "
            "2. **Banking**: Inquire if they have questions about banking services. "
            "3. **Meeting Management**: Suggest scheduling a meeting if relevant. "
            "4. **Buying**: Prompt them about any items or services they might want to purchase. "
            "Your response should be friendly and open-ended, encouraging the user to provide more information. "
            "Analyze the user's message to determine how to best guide them towards these tasks. "
            "Return your response in a format that aligns with the user's request."
        )
        return self._send_openai_request(system_prompt,user_prompt)
# # Example usage
# if __name__ == "__main__":
#     steward = Steward()
#     user_input = "I want to book a hotel in the city for dates."
#     response = steward.handler(user_input)
#     print(response)




