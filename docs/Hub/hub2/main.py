
import os
import openai
from fastapi import FastAPI, HTTPException,Request,status
from typing import Any,List,Dict, NewType,Tuple
from fastapi.middleware.cors import CORSMiddleware
from utils import is_agent_exist, read_file_as_strings, find_row_of_data_frame_by_type_agent, make_chat_history, agent_activision, make_data_frame_to_text_table,add_agent_to_csv
from model import Hub 
import json

app = FastAPI()
api = "localhost"
port = "8010"
api_number = '127.0.0.1'
hub2_agent = Hub("Hub2",api_number, port)
IP = NewType('IP address',str)
Port = NewType('Port',str)
Address = Tuple [IP,Port]
Name = NewType('Name',str)
Friend = Tuple[Name,Address]

origins = [
    f"http://{api}",
    f"http://{api}:{port}",
    f"http://{api}:{port}",
    f"https://{api}:{port}/activation_status",
    f"https://{api}:{port}/search_agent",
    f"https://{api}:{port}/add_agent",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST", "PUT"],
    allow_headers=["*"],
)



@app.put("/activation_status",status_code=status.HTTP_200_OK)
async def post_active(boolean: bool,name_agent: str,request: Request):
    
    ip = request.client.host
    print(ip)
    flage = agent_activision(ip,name_agent,boolean)
    if flage is False:
        raise HTTPException(status_code=400, detail="Your request have problems.")

    return {"message":"Success to update your activision."}


@app.post("/search_agent",status_code=status.HTTP_200_OK)
async def search_agent(prompt, name_agent: str, request: Request, hub_user_search:List[Friend] = None, agent_block:List[Friend] = None):
    ip = request.client.host
    print(ip,name_agent)
    flag_access_freind = is_agent_exist(ip,name_agent, "Hub_properties.csv")
    flag_access_private_user = is_agent_exist(ip,name_agent, "Private_Agent_properties.csv")
    flag_access_pulic_user = is_agent_exist(ip,name_agent, "Public_Agent_properties.csv")
    if not (flag_access_private_user or flag_access_pulic_user or flag_access_freind):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your are not allowed to access this hub.")

    system_prompt = read_file_as_strings("system_prompt.txt")
    list_type_agent = hub2_agent.find_type_agent(prompt)
    data_frame_retrival = find_row_of_data_frame_by_type_agent(list_type_agent, agent_block)
    # print(data_frame_retrival)
    markdown_data_retrival = make_data_frame_to_text_table(data_frame_retrival)
    print(markdown_data_retrival)
    chat_dictionary = make_chat_history(system_prompt,prompt, markdown_data_retrival)
    return hub2_agent.hub_search_agent(chat_dictionary,prompt, hub_user_search, agent_block)

@app.post("/add_agent", status_code=status.HTTP_201_CREATED)
async def add_agent(name_agent: str, type_agent: str, request: Request, extra_columns: Dict[str, str]):
    ip = request.client.host
    print(ip)
    
    # Determine the file path based on agent type
    if type_agent == "Public":
        file_path = "Public_Agent_properties.csv"
    elif type_agent == "Private":
        file_path = "Private_Agent_properties.csv"
    elif type_agent == "Friend":
        file_path = "Hub_properties.csv"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid agent type specified.")
    
    # Check if the agent already exists in the relevant CSV file
    if is_agent_exist(ip, name_agent, file_path):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"{type_agent} agent witt name {name_agent} already exists.")
    
    # Add the agent to the CSV file
    add_agent_to_csv(ip, name_agent, file_path, extra_columns)
    
    return {"message": "Agent added successfully."}
