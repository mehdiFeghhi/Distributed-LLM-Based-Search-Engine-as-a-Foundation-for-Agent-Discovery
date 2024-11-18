from typing import NewType, Tuple, List, Dict
import requests
import openai
import json
import csv
import yaml
import re
from utils import read_file_as_strings

# Custom types for IP, Port, Address, Name, and Friend
IP = NewType('IP', str)
Port = NewType('Port', str)
Address = Tuple[IP, Port]
Name = NewType('Name', str)
Friend = Tuple[Name, Address]

class HealthcareAssistant:
    """
    Manages healthcare tasks such as doctor consultations, pharmacy purchases, and health checkups.
    """

    def __init__(self, name: str) -> None:
        """
        Initialize the HealthcareAssistant with a name and load the OpenAI API key from config.
        """
        self.name = name
        self.chat = []
        self.hubs = self._load_hubs()

        with open('config.json') as config_file:
            config = json.load(config_file)
            self.api_key = config.get("api_key")

        openai.api_key = self.api_key

    def _load_hubs(self) -> List[Friend]:
        """
        Load the active hubs from a CSV file and return a list of friends (hubs).
        """
        hubs = []
        with open("Hubs.csv", mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['Active'] == 'TRUE':
                    name = Name(row['Agent Name'])
                    address = (IP(row['IP Address']), Port(row['Port']))
                    hubs.append((name, address))
        print(hubs)
        return hubs

    def _get_sorted_friends(self, agent_list: List[Dict]) -> List[Friend]:
        """
        Sort agents by relevance and goodness rates, then extract name and address.
        """
        sorted_agents = sorted(agent_list, key=lambda x: (-x['relevance_rate'], -x['goodness_rate']))
        return [(Name(agent['name']), (IP(agent['location']['ip']), Port(agent['location']['port']))) for agent in sorted_agents]

    def _read_file_as_string(self, file_path: str) -> str:
        """
        Read the content of a file and return it as a string.
        """
        with open(file_path, 'r') as file:
            return file.read()

    def _get_openai_response(self, system_prompt: str, user_prompt: str) -> str:
        """
        Get a response from the OpenAI API based on system and user prompts.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        # OpenAI API call (you need to have your API key set up)
        try:
            response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
            return response.choices[0].message.content
        except Exception as e:
            return f"Error getting advice: {str(e)}"



    def _find_word_in_text(self,word, text):
        # Compile a regex pattern to find the word as a whole word, case-insensitive
        pattern = rf'\b{re.escape(word)}\b'
        
        # Search for the word in the text
        if re.search(pattern, text, re.IGNORECASE):
            print (f"The word '{word}' was found in the text.")
            return True

        else:
            print (f"The word '{word}' was not found in the text.")
            return False

    def get_health_status(self, prompt: str) -> str:
        """
        Get the health status from OpenAI based on the user's prompt.
        """
        system_prompt = self._read_file_as_string("system_prompt_health_check.txt")
        return self._get_openai_response(system_prompt, prompt)

    def find_doctor(self, health_condition: str) -> List[Friend]:
        """
        Find a doctor for the given health condition by querying hubs and returning the results.
        """
        system_prompt = self._read_file_as_string("system_prompt_find_doctor.txt")
        doctor_type = self._get_openai_response(system_prompt, f"I need a doctor for {health_condition}.")
        
        # Log the conversation about finding a doctor
        self._log_chat("system", system_prompt, f"I need a doctor for {health_condition}.", doctor_type)
        
        hubs_seen = []
        print(self.hubs)
        for hub in self.hubs:
            hub_ip, hub_port = hub[1]
            hub_url = f"http://{hub_ip}:{hub_port}/search_agent"

            payload = {
                "hub_user_search": self._format_friends(hubs_seen),
                "agent_block": None
            }
            hubs_seen.append(hub)
            try:
                response = requests.post(hub_url, params={'prompt': f"Can you find doctors specializing in {doctor_type}?", 'name_agent': self.name},
                                        headers={'accept': 'application/json', 'Content-Type': 'application/json'},
                                        json=payload)
                response_data = response.json()
                self._log_chat("system", "request to Hub ", f"Can you find doctors specializing in {doctor_type}?",response_data)
                if response_data.get("status") == "Find":
                   return self._get_sorted_friends(response_data.get('agents'))
        
            except requests.exceptions.HTTPError as http_err:
                print(f"HTTP error: {http_err}")
            except Exception as err:
                print(f"An error occurred: {err}")
        return []
    def consult_doctor(self, doctor: Friend, health_status: str) -> str:
        """
        Consult the doctor and return their advice.
        """
        doctor_ip, doctor_port = doctor[1]
        try:
            response = requests.post(f"http://{doctor_ip}:{doctor_port}/consult", json={"situation": health_status})
            return response.json().get('advice', "No advice provided")
        except requests.RequestException as e:
            return f"Error consulting doctor: {e}"

    def buy_medicine(self, pharmacies: List[Friend], prescription: Dict[str, int]) -> str:
        """
        Purchase medicine from the pharmacy based on the given prescription.
        
        Args:
            pharmacies (List[Friend]): A list of pharmacy agents with their details.
            prescription (Dict[str, int]): A dictionary of medicine names and quantities to be purchased.
            
        Returns:
            str: Status message indicating success or failure of the purchase.
        """
        
        for pharmacy in pharmacies:
            pharmacy_name, (pharmacy_ip, pharmacy_port) = pharmacy
            pharmacy_url = f"http://{pharmacy_ip}:{pharmacy_port}/help"
            
            try:
                # Fetch API document from the pharmacy
                api_document = requests.get(pharmacy_url).text
            except requests.RequestException as e:
                print(f"Error fetching API document from pharmacy {pharmacy_ip}:{pharmacy_port} - {e}")
                continue

            try:
                # Generate the purchase script to interact with the pharmacy API
                script = self._pharmacy_purchase_code(prescription, api_document, pharmacy_ip, pharmacy_port)
                print(script)
                namespace = {}
                
                # Execute the generated script
                exec(script, namespace)

                result: dict = namespace.get('result', {})
                if not isinstance(result, dict):
                    raise ValueError("Result is not a dictionary as expected.")

                # Extract the status of the purchase from the result
                purchase_status = result.get('purchase_status', 'Purchase failed')
                
                print(f"Purchase from {pharmacy_name} ({pharmacy_ip}:{pharmacy_port}): {purchase_status}")
                
                if purchase_status == 'Purchase successful':
                    return f"Medicine successfully purchased from {pharmacy_name}."
                else:
                    print(f"Unable to purchase from {pharmacy_name}. Trying the next pharmacy...")

            except Exception as e:
                print(f"Error during script execution for pharmacy {pharmacy_name}: {e}")

        return "Medicine purchase failed from all available pharmacies."

    def _pharmacy_purchase_code(self, prescription: dict, api_document: str, pharmacy_ip: str, pharmacy_port: str) -> str:
        """
        Generates the purchase script based on the pharmacy API document and the prescription.
        
        Args:
            prescription (dict): A dictionary of medicine names and quantities to be purchased.
            api_document (str): The API documentation of the pharmacy.
            pharmacy_ip (str): The IP address of the pharmacy.
            pharmacy_port (str): The port of the pharmacy.
            
        Returns:
            str: The generated Python script to execute the purchase.
        """
        # Read the system prompt for creating purchase scripts
        system_prompt = read_file_as_strings("buy_medicine_system_prompt.txt")
        
        # Prepare the list of medicines for the prompt
        medicine_list = []
        for medicine, quantity in prescription.items():
            medicine_list.append(f"{medicine} ({quantity})")
        
        medicine_str = ', '.join(medicine_list)
        
        # Build the prompt to generate the purchase script
        prompt = (f"I would like to purchase medicines from a pharmacy using the following details:\n"
                f"- Pharmacy IP Address: {pharmacy_ip}\n"
                f"- Port: {pharmacy_port}\n"
                f"- API Documentation: {api_document}\n\n"
                f"Please buy the following medicines:\n{medicine_str}.\n\n"
                "Please set the result in a variable `result` in the following JSON format:\n"
                "{\n"
                "  \"purchase_status\": \"Purchase successful\" or \"Purchase failed\"\n"
                "}\n"
                "Do not use any `if __name__ == \"__main__\": main()` code blocks.\n"
                "Thank you!"
                )

        # Get the response from OpenAI and extract the script
        response = self._get_openai_response(system_prompt, prompt)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
            {"role": "coder", "content": response}
        ]
        self.chat.append(messages)
        
        # Find and return the script part from the response
        script = self._find_code(response, "```python", "```")
        return script
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

    def handle_healthcare(self, health_prompt: str) -> Dict[str, List[Dict]]:
        """
        Handle the healthcare process including health checkup, doctor consultation, and pharmacy purchase.
        """
        health_status = self.get_health_status(health_prompt)
        self._log_chat("system", "Health check system prompt", health_prompt, health_status)

        if self._find_word_in_text("doctor", health_status.lower()):
            doctors = self.find_doctor(health_status)
            if doctors:
                consultation = self.consult_doctor(doctors[0], health_prompt)
                self._log_chat("system", "Doctor consultation", health_prompt, consultation)
                
                if  self._find_word_in_text("prescription", consultation.lower()):
                    pharmacies = self._find_pharmacy()
                    prescription = self._extract_prescription(consultation)
                    purchase_status = self.buy_medicine(pharmacies, prescription)
                    self._log_chat("system", "Pharmacy purchase", prescription, purchase_status)
                
                return {"status": "Healthcare process completed", "chats": self.chat}

            return {"status": "No doctors found", "chats": self.chat}

        if  self._find_word_in_text("prescription", health_status.lower()):
            pharmacies = self._find_pharmacy()
            prescription = self._extract_prescription(health_status)
            purchase_status = self.buy_medicine(pharmacies, prescription)
            self._log_chat("system", "Pharmacy purchase", prescription, purchase_status)

        return {"status": "Healthcare process completed", "chats": self.chat}

    def _log_chat(self, role: str, system_prompt: str, user_content: str, assistant_content: str) -> None:
        """
        Log the conversation in the chat.
        """
        self.chat.append([
            {"role": role, "content": system_prompt},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": assistant_content}
        ])
    def _extract_doctor(self, doctor_type_yaml: str) -> str:
        """
        Extract doctor information from YAML string.

        Args:
        doctor_type_yaml (str): YAML string containing doctor information.

        Returns:
        dict: Dictionary containing extracted doctor information.
        """
        try:
            doctor_info = yaml.safe_load(doctor_type_yaml)
            return doctor_info.get('Type', None)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML: {e}")
            return None


    def _extract_yaml_string(self,text):
        # Use regex to find content between ```yaml and ```
        pattern = r'```yaml\s*(.*?)\s*```'
        match = re.search(pattern, text, re.DOTALL)
        
        if match:
            return match.group(1).strip()  # Return the extracted string without leading/trailing whitespace
        return None  # Return None if no match is found

    def _extract_prescription(self, health_description: str) -> Dict[str, int]:
        """
        Extract the prescription from the health status by using OpenAI to generate
        a YAML response and then convert it to JSON format.
        """
        # System prompt for generating prescription from health description
        system_prompt_prescription = "Extract the prescription in YAML format from the health description."

        # Prepare the OpenAI prompt
        user_prompt = f"Health description: {health_description}. Please provide the prescription in YAML format."

        # Get the response from OpenAI in YAML format
        yaml_prescription = self._get_openai_response(system_prompt_prescription, user_prompt)
        yaml_prescription = self._extract_yaml_string(yaml_prescription)
        try:
            # Convert YAML to JSON (Python dictionary)
            prescription_dict = yaml.safe_load(yaml_prescription)
            
            # Ensure it's in the expected format: Dict[str, int]
            if isinstance(prescription_dict, dict) and all(isinstance(value, int) for value in prescription_dict.values()):
                return prescription_dict
            else:
                raise ValueError("Prescription format is incorrect or missing quantities.")
        
        except yaml.YAMLError as yaml_error:
            print(f"Error parsing YAML: {yaml_error}")
            return {}
        except Exception as e:
            print(f"An error occurred during prescription extraction: {e}")
            return {}

    def _find_pharmacy(self) -> List[Friend]:
        """
        Find pharmacies by querying hubs and returning the results.
        """
  
        
        hubs_seen = []
        for hub in self.hubs:
            hub_ip, hub_port = hub[1]
            hub_url = f"http://{hub_ip}:{hub_port}/search_agent"

            payload = {
                "hub_user_search": self._format_friends(hubs_seen),
                "agent_block": None
            }
            hubs_seen.append(hub)
            
            try:
                # Query the hub to find pharmacies
                response = requests.post(hub_url, 
                                        params={'prompt': f"Can you find pharmacies ?",'name_agent': self.name}, 
                                        headers={'accept': 'application/json', 'Content-Type': 'application/json'}, 
                                        json=payload)
                
                response_data = response.json()
                if response_data.get("status") == "Find":
                    return self._get_sorted_friends(response_data.get('agents'))  # Return the sorted list of pharmacy agents

            except requests.exceptions.HTTPError as http_err:
                print(f"HTTP error occurred while finding pharmacy: {http_err}")
            except Exception as err:
                print(f"An error occurred while finding pharmacy: {err}")
        
        return []


    def _format_friends(self, friends: List[Friend]) -> List[List]:
        """
        Format friends list into a JSON-friendly format.
        """
        if friends :
            return [
                [f_name, [f_ip, f_port]]
                for f_name, (f_ip, f_port) in friends
            ]
        else:
            return None
