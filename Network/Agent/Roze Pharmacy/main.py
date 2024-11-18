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




port = "8020"
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
 

