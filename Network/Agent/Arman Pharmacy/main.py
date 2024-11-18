import os

from fastapi import FastAPI, HTTPException,Request,status
from fastapi.responses import PlainTextResponse
from typing import Any,List,Dict
from fastapi.middleware.cors import CORSMiddleware
from model import MarketAssistant
from utils import add_agent_to_csv , is_agent_exist
import json

market_agent = MarketAssistant("MehdiMark Supermarket Assistant")
app = FastAPI()
api = "localhost"




port = "8015"
api_number = '127.0.0.1'
origins = [
    f"http://{api}",
    f"http://{api}:{port}",
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

@app.get('/help', status_code=status.HTTP_200_OK)
async def help():
    try:
        with open('Doc.txt', 'r') as file:
            doc_content = file.read()
            return PlainTextResponse(doc_content, status_code=status.HTTP_200_OK)
    except FileNotFoundError:
        return PlainTextResponse("File not found", status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return PlainTextResponse(str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
		



@app.post("/agent_request",status_code=status.HTTP_200_OK)
async def search_agent(req:dict, request: Request):
    ip = request.client.host
    port = request.client.port
    print(ip)
    print(port)
    answer = market_agent.request(req)
    print(answer)
    return answer
 
@app.post("/agent_sell", status_code=status.HTTP_200_OK)
async def sell_agent(req: dict, token: str,  request: Request):
    ip = request.client.host
    port = request.client.port
    print(f"IP: {ip}, Port: {port}")
    

    
    # Proceed with selling the items, and handle any errors raised in the `sell` method.
    try:
        return market_agent.sell(token, req)
    except HTTPException as e:
        raise e  # Re-raise the exception to return appropriate HTTP response.
 

# @app.post("/add_agent", status_code=status.HTTP_201_CREATED)
# async def add_agent(name_agent: str, type_agent: str, request: Request, extra_columns: Dict[str, str]):
#     ip = request.client.host
#     print(ip)
    
#     # Determine the file path based on agent type
#     if type_agent == "Public":
#         file_path = "Public_Agent_properties.csv"
#     elif type_agent == "Private":
#         file_path = "Private_Agent_properties.csv"
#     elif type_agent == "Hub":
#         file_path = "Hub_properties.csv"
#     elif type_agent == "Owner":
#         file_path = "Owner_properties.csv"
#     else:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid agent type specified.")
    
#     # Check if the agent already exists in the relevant CSV file
#     if is_agent_exist(ip, name_agent, file_path):
#         raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"{type_agent} agent already exists.")
    
#     # Add the agent to the CSV file
#     add_agent_to_csv(ip, name_agent, file_path, extra_columns)
    
#     return {"message": "Agent added successfully."}
