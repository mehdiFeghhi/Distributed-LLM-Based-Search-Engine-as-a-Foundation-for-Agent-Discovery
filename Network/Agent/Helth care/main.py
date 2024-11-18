import os
import openai

from fastapi import FastAPI, HTTPException,Request,status
from typing import Any,List,Dict
from fastapi.middleware.cors import CORSMiddleware
from model import HealthcareAssistant
from utils import add_agent_to_csv , is_agent_exist
import json

app = FastAPI()
api = "localhost"

port = "8002"
api_number = '127.0.0.1'
origins = [
    f"http://{api}",
    f"http://{api}:{port}",
    f"http://{api}:{port}",
    # f"https://{api}:{port}/activation_status",
    f"https://{api}:{port}/agent_request",
    f"https://{api}:{port}/add_agent",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST", "PUT"],
    allow_headers=["*"],
)




@app.post("/agent_request",status_code=status.HTTP_200_OK)
async def search_agent(prompt, name_agent: str, request: Request):
    ip = request.client.host
    port = request.client.port
    print(ip)
    print(port)
    helthcare_agent = HealthcareAssistant("Hanson family helthcare")
    flag_access_owner_user = is_agent_exist(ip,name_agent, "Owner_properties.csv")
    if not (flag_access_owner_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Your are not allowed to access {HealthcareAssistant.name}.")

    
    health_res = helthcare_agent.handle_healthcare(prompt)
    return health_res
 

 

@app.post("/add_agent", status_code=status.HTTP_201_CREATED)
async def add_agent(name_agent: str, type_agent: str, request: Request, extra_columns: Dict[str, str]):
    ip = request.client.host
    print(ip)
    
    # Determine the file path based on agent type
    if type_agent == "Public":
        file_path = "Public_Agent_properties.csv"
    elif type_agent == "Private":
        file_path = "Private_Agent_properties.csv"
    elif type_agent == "Hub":
        file_path = "Hub_properties.csv"
    elif type_agent == "Owner":
        file_path = "Owner_properties.csv"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid agent type specified.")
    
    # Check if the agent already exists in the relevant CSV file
    if is_agent_exist(ip, name_agent, file_path):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"{type_agent} agent already exists.")
    
    # Add the agent to the CSV file
    add_agent_to_csv(ip, name_agent, file_path, extra_columns)
    
    return {"message": "Agent added successfully."}
