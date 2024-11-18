from db_chat import ChatDatabase
from hotel_database import HotelDatabase
from pydantic import BaseModel
from datetime import datetime
from fastapi import FastAPI, HTTPException,Request,status, Query
from typing import Any,List,Dict
from fastapi.middleware.cors import CORSMiddleware
from model import ReservationAssistant
from utils import add_agent_to_csv , is_agent_exist
import sqlite3
import logging
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


app = FastAPI()
api = "localhost"

port = "8025"
api_number = '127.0.0.1'
origins = [
    f"http://{api}",
    f"http://{api}:{port}",
    f"http://{api}:{port}",
    f"https://{api}:{port}/chat",
    f"https://{api}:{port}/room",
    f"https://{api}:{port}/create_chat",
    f"https://{api}:{port}/reservation"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Initialize ReservationAssistant and ChatDatabase
assistant = ReservationAssistant()
chat_db = ChatDatabase()
hotel_db = HotelDatabase()

@app.post("/create_chat", status_code=status.HTTP_200_OK)
async def create_chat():
    """
    Initializes a new chat session with a system prompt loaded from a file.
    """
    # Load system prompt from a text file
    try:
        with open("system_prompt_for_reservation.txt", "r") as file:
            system_prompt = file.read()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="System prompt file not found.")

    # Create the initial conversation with the system prompt
    initial_conversation = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": "How can I help you with your reservation today?"}
    ]

    # Insert conversation into the chat database
    conversation_id = chat_db.insert_conversation(initial_conversation)

    return {
        "conversation_id": conversation_id,
        "initial_message": initial_conversation[1]["content"]  # Return the assistant's message
    }
class ChatRequest(BaseModel):
    chat_id: int
    prompt: str

@app.post("/chat", status_code=status.HTTP_200_OK)
async def chat(request: ChatRequest):
    """
    Continues an existing chat session, interacting with the assistant.
    """
    
    chat_id = request.chat_id
    prompt = request.prompt

    logger.info(f"Received chat request for chat_id: {chat_id}")

    # Retrieve conversation data
    conversation_data = chat_db.get_conversation(chat_id)
    print("Conversation data :")
    print(conversation_data)
    print("--------------------------------")
    
    if not conversation_data or not conversation_data["active"]:
        logger.warning(f"Chat ID {chat_id} does not exist or has ended.")
        raise HTTPException(status_code=400, detail="This conversation has ended or does not exist.")

    conversation = conversation_data["conversation"]
    logger.info(f"Continuing conversation for chat_id {chat_id}. Prompt: {prompt}")

    # Send message to assistant
    response = assistant.send_message(conversation, prompt, chat_id)
    conversation = response['conversation']
    assistant_reply = response['assistant_reply']
    should_end_conversation = response['flage']
    
    if should_end_conversation:
        logger.info(f"Ending conversation for chat_id {chat_id}.")
        return {"assistant_reply": assistant_reply, "continue_chat": not should_end_conversation}

    logger.info(f"Assistant reply for chat_id {chat_id}: {assistant_reply}")
    print('conversation:')
    print(conversation)
    print("________________________________________________________________")
    
    return {"assistant_reply": assistant_reply, "continue_chat": not should_end_conversation}
class ReservationRequest(BaseModel):
    name: str
    room_id: int
    start_date: str
    end_date: str
    
@app.post("/reservation", status_code=status.HTTP_200_OK)
async def reservation(reservation_input: ReservationRequest):
    # Parse the dates
    try:
        start_date = datetime.strptime(reservation_input.start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(reservation_input.end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format. Use 'YYYY-MM-DD'.")

    # Validate dates (start and end dates must be after today, end_date after start_date)
    today = datetime.now().date()
    if start_date < today or end_date < today:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reservation dates must be in the future.")
    if start_date >= end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="End date must be after the start date.")

    # Check if the room is available for the given date range
    available_rooms = hotel_db.get_available_rooms(reservation_input.start_date, reservation_input.end_date)
    if not any(room['room_number'] == reservation_input.room_id for room in available_rooms):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Room is not available for the given dates.")

    # Insert reservation
    try:
        hotel_db.insert_reservation(reservation_input.room_id, reservation_input.start_date, reservation_input.end_date)
    except sqlite3.Error as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {e}")

    # Return success response
    return {"message": "Reservation successfully created", "name": reservation_input.name, "room_id": reservation_input.room_id}


@app.get("/room/room", response_class=HTMLResponse)
async def get_room_info(
    room_number: int = Query(...),  # Make room_number a query parameter
    date_start: str = Query(...),    # Make date_start a query parameter
    date_end: str = Query(...)        # Make date_end a query parameter
):    # Retrieve room information from the database
    room = hotel_db.get_room(room_number)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found.")

    # Create an HTML response with enhanced styling and structure
    html_content = f"""
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Room Information - Room {room['room_number']}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                padding: 20px;
                border: 1px solid #ccc;
                border-radius: 8px;
                background-color: #f9f9f9;
            }}
            h1, h2 {{
                color: #333;
            }}
            p {{
                font-size: 16px;
            }}
            form {{
                margin-top: 20px;
            }}
            input[type="text"], input[type="date"] {{
                padding: 10px;
                margin: 5px 0;
                width: 100%;
                border: 1px solid #ccc;
                border-radius: 4px;
            }}
            button {{
                padding: 10px 15px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }}
            button:hover {{
                background-color: #45a049;
            }}
            .method-info {{
                margin-top: 30px;
                padding: 10px;
                background-color: #e9ecef;
                border-left: 5px solid #007bff;
            }}
        </style>
    </head>
    <body>
        <h1>Room Details</h1>
        <p><strong>Room Number:</strong> {room['room_number']}</p>
        <p><strong>Room Type:</strong> {room['room_type']}</p>
        <p><strong>Beds:</strong> {room['beds']}</p>
        <p><strong>View:</strong> {room['view']}</p>
        <p><strong>Price:</strong> ${room['price']} per night</p>
        
        <h2>Make a Reservation</h2>
        <p>Please fill in the details below to reserve this room:</p>
        <form action="/reservation" method="post">
            <input type="hidden" name="room_id" value="{room['room_number']}">
            <label for="name">Your Name:</label>
            <input type="text" name="name" placeholder="Enter your name" required>
            
            <label for="start_date">Start Date:</label>
            <input type="date" name="start_date" value="{date_start}" required>
            
            <label for="end_date">End Date:</label>
            <input type="date" name="end_date" value="{date_end}" required>
            
            <button type="submit">Reserve Room</button>
        </form>

        <div class="method-info">
            <h2>How to Call the Reservation Method in Python</h2>
            <p>To make a reservation, use the <strong>requests</strong> library to send a POST request to the following URL:</p>
            <pre>
POST http://127.0.0.1:8025/reservation
            </pre>
            <p>Include the following parameters in your request:</p>
            <pre>
{{
    "name": "Your Name",            # Your name from the form input
    "room_id": {room['room_number']},  # ID of the room, filled automatically
    "start_date": "{date_start}",  # Start date from the form input
    "end_date": "{date_end}"        # End date from the form input
}}
            </pre>
            <p>Example of making a reservation:</p>
            <pre>
import requests

url = "http://127.0.0.1:8025/reservation"
data = {{
    "name": "< your name >",               # Replace with the actual name entered
    "room_id": {room['room_number']},  # Automatically filled from the form
    "start_date": "{date_start}",       # Replace with the actual start date entered
    "end_date": "{date_end}"          # Replace with the actual end date entered
}}

response = requests.post(url, json=data)
result = response.json()
print(result)
            </pre>
            <p>This will return a confirmation message if the reservation is successfully created.</p>
        </div>
    </body>
</html>
"""
    return HTMLResponse(content=html_content)

