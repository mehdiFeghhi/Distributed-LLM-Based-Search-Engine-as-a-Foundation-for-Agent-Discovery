from pydantic import BaseModel
import openai
import json
# Request and Response models
class ConsultationRequest(BaseModel):
    situation: str

class ConsultationResponse(BaseModel):
    advice: str

class Doctor:
    """
    A class representing a doctor, with methods to provide medical advice
    based on the health status of a patient using OpenAI API.
    """
    
    def __init__(self, name: str):
        self.name = name
        with open('config.json') as config_file:
            config = json.load(config_file)
            self.api_key = config.get("api_key")
        openai.api_key = self.api_key

    def consult(self, health_status: str) -> str:
        """
        Provide advice based on the patient's health status.
        """
        return self.get_doctor_advice(health_status)

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

    def get_doctor_advice(self, health_status: str) -> str:
        """
        Get the doctor's advice using the OpenAI API.
        """
        # System prompt that gives context to the AI model
        system_prompt = (
            "You are a highly experienced medical doctor specializing in diagnosing and treating a wide range of health conditions. "
            "Your goal is to carefully evaluate the patient's symptoms and provide clear, concise, and professional medical advice. "
            "If the symptoms indicate the need for further treatment or prescription medication, suggest the appropriate prescription at the end. "
            "Always prioritize the patient's well-being, and consider both immediate care and long-term health in your advice."
        )

        # Use the health_status as the user input
        user_prompt = f"The patient has the following health status: {health_status}"

        # Get the response from OpenAI API
        return self._get_openai_response(system_prompt, user_prompt)
