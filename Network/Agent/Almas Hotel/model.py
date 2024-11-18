import openai
import yaml
import json
import logging
from typing import NewType, Tuple, List, Dict, Any
from db_chat import ChatDatabase
from hotel_database import HotelDatabase
import re

# Configure the logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ReservationAssistant:
    def __init__(self, config_file='config.json'):
        logging.info("Initializing ReservationAssistant")
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

    def send_message(self, conversation: List[Dict[str, str]], prompt: str, conversation_id: int) -> Dict[str, Any]:
        logging.info("Preparing to send a message to OpenAI GPT")
        
        # Check if conversation should end
        flag, response = self.end_conversation(conversation_id, prompt)
        
        if flag:
            return self.handle_end_conversation(conversation, prompt, response, conversation_id)
        
        # Handle regular conversation flow
        return self.handle_conversation_flow(conversation, prompt, conversation_id)


    def handle_end_conversation(self, conversation: List[Dict[str, str]], prompt: str, response: Dict[str, Any], conversation_id: int) -> Dict[str, Any]:
        """Handles the case when the conversation is flagged to end."""
        conversation.append({"role": "user", "content": prompt})
        conversation.append({"role": "assistant", "content": response})
        
        # Update conversation in the database
        db = ChatDatabase()  # Assuming ChatDatabase is defined elsewhere
        logging.info(f"Updated response with reservation links for chat_id {conversation_id}.")
        db.update_conversation(conversation_id, conversation)

        return {
            "conversation": conversation,
            "assistant_reply": response,
            "flage": True,
        }


    def handle_conversation_flow(self, conversation: List[Dict[str, str]], prompt: str, conversation_id: int) -> Dict[str, Any]:
        """Handles the regular conversation flow when the conversation is ongoing."""
        # conversation.append({"role": "user", "content": prompt})

        # Extract start and end dates
        conversation_copy = conversation.copy()
        conversation_copy.append({"role": "user", "content": prompt})
        start_date, end_date = self.extract_dates(conversation_copy)
        
        # Check for missing dates
        if not self.are_dates_valid(start_date, end_date):
            return self.handle_missing_dates(conversation_copy,conversation_id)

        # Handle room recommendation and link addition
        return self.handle_reservation(conversation, prompt, start_date, end_date, conversation_id)


    def are_dates_valid(self, start_date: str, end_date: str) -> bool:
        """Check if both start and end dates are valid."""
        start_date_flag = start_date is not None and start_date != 'missing'
        end_date_flag = end_date is not None and end_date != 'missing'
        return start_date_flag and end_date_flag


    def handle_reservation(self, conversation: List[Dict[str, str]], prompt: str, start_date: str, end_date: str, conversation_id: int) -> Dict[str, Any]:
        """Handles the reservation flow by recommending rooms and adding reservation links."""
        recommend_rooms_response = self.recommend_rooms(conversation, prompt, start_date, end_date)
        
        response = self.add_link_reservation(recommend_rooms_response)
        assistant_reply = response['assistant_reply']
        conversation.append({"role": "assistant", "content": assistant_reply})

        # Update conversation in the database
        db = ChatDatabase()  # Assuming ChatDatabase is defined elsewhere
        logging.info(f"Updated response with reservation links for chat_id {conversation_id}.")
        db.update_conversation(conversation_id, conversation)

        return response
    def extract_dates(self, conversation: List[Dict[str, str]]) -> List[str]:
        conversation_for_dates = self.prepare_date_extraction_conversation(conversation)
        logging.info("Sending date extraction request to OpenAI")

        date_extraction_response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_for_dates
        )
        logging.info("Date extraction response received")

        return self.parse_dates(date_extraction_response.choices[0].message.content)

    def prepare_date_extraction_conversation(self, conversation: List[Dict[str, str]]) -> List[Dict[str, str]]:
        # Define the system prompt for extracting reservation dates
        system_prompt = (
            "You are an assistant helping with hotel reservations. Please analyze the following conversation to "
            "extract the reservation's start and end dates. Do not provide any additional comments or information. "
            "If either of these dates is missing or incomplete, return 'missing' in front of the date. "
            "Return the result strictly in the following format:\n"
            "```yaml\nstart_date: YYYY-MM-DD\nend_date: YYYY-MM-DD\n```"
            
            "# Example input:\n"
            "'I would like to book a room starting from October 12th and I plan to stay for a week.'\n\n"
            
            "# Expected output:\n"
            "```yaml\nstart_date: 2024-10-12\nend_date: 2024-10-19\n```\n\n"
            
            "# Another example input:\n"
            "'I want to reserve a room from October 5th but I'm not sure how long I will stay yet.'\n\n"
            
            "# Expected output:\n"
            "```yaml\nstart_date: 2024-10-05\nend_date: missing```\n\n"
            
            "# New example input:\n"
            "'I need a standard room for my trip.'\n\n"
            
            "# Expected output using previous conversation context:\n"
            "```yaml\nstart_date: 2024-10-05\nend_date: 2024-10-12\n```\n"
        )
        # Prepare a new conversation list starting with the system prompt
        new_conv = []
        new_conv.append({"role": "system", "content": system_prompt})
        
        context = "Base on the the below communication :"
        # Update the assistant's messages to include a thank you response
        for idx in range(1, len(conversation)):
            if conversation[idx]['role'] == "user":
                context +=f"\nUser: {conversation[idx]['content']}"

        new_conv.append({"role": "user", "content":context})
        # Debug output for tracing the conversation state
        print("********************************Main********************************")
        print(new_conv)
        print("********************************Main********************************")

        return new_conv
    
    def _extract_yaml_block(self, yaml_output: str) -> str:
        """
        Extracts the YAML block from the provided output string.

        Args:
            yaml_output (str): The string containing the YAML content.

        Returns:
            str: Extracted YAML block as a string or an empty string if not found.
        """
        yaml_match = re.search(r'```yaml(.*?)```', yaml_output, re.DOTALL)
        if yaml_match:
            yaml_data = yaml_match.group(1).strip()
            logging.info("YAML block found and extracted.")
            return yaml_data
        else:
            logging.error(f"YAML block not found in the output {yaml_output}.")
            return ""

    def parse_dates(self, yaml_output: str) -> List[str]:
        """
        Parses the provided date information from a string containing YAML content.

        Args:
            yaml_output (str): A string representing the output that contains a YAML block.

        Returns:
            List[str]: A list containing the start and end dates, or ['missing', 'missing'] if parsing fails.
        """
        logging.info(f"Attempting to parse dates from provided output.")

        # Step 1: Extract YAML block from the output
        yaml_data = self._extract_yaml_block(yaml_output)

        if yaml_data:  # Proceed if YAML was successfully extracted
            try:
                # Step 2: Parse the YAML content into a Python dictionary
                date_info = yaml.safe_load(yaml_data)
                logging.info(f"Parsed YAML data: {date_info}")

                # Retrieve the start and end dates from the dictionary
                start_date = date_info.get('start_date', 'missing')
                end_date = date_info.get('end_date', 'missing')

                logging.info(f"Parsed start date: {start_date}, end date: {end_date}")
                return [start_date, end_date]

            except yaml.YAMLError as exc:
                logging.error(f"YAML error: Failed to parse date information: {exc}")
        else:
            logging.error("Failed to extract YAML data.")

        # Return 'missing' for both dates if extraction or parsing fails
        return ['missing', 'missing']

    def handle_missing_dates(self, conversation: List[Dict[str, str]],conversation_id) -> Dict[str, Any]:
        logging.warning("Missing start or end date")
        missing_info_message = "It seems like you're missing the start or end date for your reservation. Could you provide that first?"
        conversation.append({"role": "assistant", "content": missing_info_message})
        
        # print("********************************main********************************")
        # print(conversation)
        # print("********************************main********************************")
        # Update conversation in the database
        db = ChatDatabase()  # Assuming ChatDatabase is defined elsewhere
        logging.info(f"Updated response with reservation links for chat_id {conversation_id}.")
        db.update_conversation(conversation_id, conversation)
        return {
            "conversation": conversation,
            "assistant_reply": missing_info_message,
            "flage":False
        }
    def recommend_rooms(self, conversation: List[Dict[str, str]], prompt: str, start_date: str, end_date: str) -> Dict[str, Any]:
        hotel_db = HotelDatabase()
        logging.info("Fetching available rooms from hotel database")
        available_rooms = hotel_db.get_available_rooms(start_date, end_date)

        # conversation.append({"role": "user", "content": prompt})
        logging.info(f"User prompt appended: {prompt}")

        # conversation.append({"role": "assistant", "content": "Thank you for providing the information."})
        conversation_copy = conversation.copy()
        conversation_copy.pop()
        recommendation_prompt = (
            f"Based on the available rooms between {start_date} and {end_date}, and considering the user's preferences mentioned in the conversation, Answer the Request of User {prompt}.\n\nAvailable Rooms:\n{available_rooms}."
        )
        logging.info("Fetching room recommendations based on dates and preferences")

        conversation.append({"role": "user", "content": recommendation_prompt})
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation
        )
        logging.info("Room recommendation response received from OpenAI")

        assistant_reply = response.choices[0].message.content
        logging.info(f"Assistant reply: {assistant_reply}")
        # conversation.append({"role": "assistant", "content": assistant_reply})

        return {
            "conversation": conversation,
            "assistant_reply": assistant_reply,
            "flage":False
        }
    def end_conversation(self, conversation_id: int, prompt: str) -> Tuple[bool,str]:
        logging.info(f"Checking for Ending conversation with ID {conversation_id}")
        
        # Read system prompt from file
        with open("end_reservation_system_prompt.txt", "r") as file:
            system_prompt = file.read()

        # Create a conversation history
        conversation = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        # Generate a response using OpenAI's chat completions API
        api_response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation
        )
        logging.info("Received response from OpenAI for ending conversation")

        # Extract the YAML output from the response
        yaml_output = api_response.choices[0].message.content
        logging.info(f"YAML output: {yaml_output}")

        # Use regex to extract the YAML block between ```yaml and ```
        yaml_match = re.search(r'```yaml(.*?)```', yaml_output, re.DOTALL)

        if yaml_match:
            # Extract the YAML content between the start and end markers
            yaml_data = yaml_match.group(1).strip()

            try:
                # Parse the YAML data into a Python dictionary
                yaml_dict = yaml.safe_load(yaml_data)
                logging.info(f"Parsed YAML data: {yaml_dict}")
            except yaml.YAMLError as exc:
                logging.error(f"Error parsing YAML data: {exc}")
                return False,yaml_data  # Return False if parsing fails
        else:
            logging.error(f"YAML block not found in the output {yaml_dict}")
            
            return False,yaml_data  # Return False if YAML block is not found

        # Check if the response indicates the conversation should be ended
        flag = yaml_dict.get("end_conversation", False)
        response = yaml_dict.get('assistant_message',"The status of this conversation is {flag}".format(flag=flag))
        if flag:
            logging.info("Ending conversation in the database")
            db = ChatDatabase()  # Assuming ChatDatabase is defined elsewhere
            db.set_conversation_active_status(conversation_id, False)
            db.add_message_to_conversation(conversation_id,{"role": "user", "content": prompt})
            db.add_message_to_conversation(conversation_id,{"role": "assistant", "content": response})
        
        return flag,response

    def add_link_reservation(self, response: Dict[str, Any]) -> Dict[str, Any]:
        logging.info("Adding link reservation")
        
        # Read the conversation prompt from the text file
        with open("link_reservation_system_prompt.txt", "r") as file:
            conversation_prompt = file.read()

        # Extract the assistant reply from the response
        assistant_reply = response['assistant_reply']
        logging.info(f"Assistant reply for link reservation: {assistant_reply}")

        model = 'gpt-4o-mini'  # Default model

        # Generate a response using OpenAI's chat completions API
        conversation = [
            {"role": "system", "content": conversation_prompt},
            {"role": "user", "content": assistant_reply}
        ]

        
        api_response = openai.chat.completions.create(
            model=model,
            messages=conversation
        )
        logging.info("Received response from OpenAI for link reservation")

        # Extract the YAML output from the response
        yaml_output = api_response.choices[0].message.content
        logging.info(f"YAML output: {yaml_output}")

        # Use regex to extract the YAML block between ```yaml and ```
        yaml_match = re.search(r'```yaml(.*?)```', yaml_output, re.DOTALL)

        if yaml_match:
            # Extract the YAML content between the start and end markers
            yaml_data = yaml_match.group(1).strip()

            try:
                # Parse the YAML data into a Python dictionary
                yaml_dict = yaml.safe_load(yaml_data)
                logging.info(f"Parsed YAML data for link reservation: {yaml_dict}")
            except yaml.YAMLError as exc:
                logging.error(f"Error parsing YAML data: {exc}")
                return response  # Return unchanged response if parsing fails
        else:
            logging.error("YAML block not found in the output")
            return response  # Return unchanged response if YAML block is not found

        # Check if there is no change in the reservation link
        if not yaml_dict.get('change', False):
            logging.info("No change in reservation link")
            return response

        # Return the response with the updated assistant reply from the parsed YAML data
        assistant_reply = yaml_dict.get('new_reply', assistant_reply)
        response['assistant_reply'] = assistant_reply
        # response['conversation'].append({"role":'assistant','content':assistant_reply})
        logging.info("Updated assistant reply with new reservation link :{}".format(response['assistant_reply']))

        assistant_reply = response['assistant_reply']
        return response
