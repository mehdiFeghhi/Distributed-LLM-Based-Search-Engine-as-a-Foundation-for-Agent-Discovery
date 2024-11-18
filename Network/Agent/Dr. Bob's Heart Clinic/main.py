from fastapi import FastAPI, HTTPException
from model import Doctor, ConsultationRequest, ConsultationResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
api = "localhost"



port = "8021"
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
# Initialize a Doctor instance (this can be extended to multiple doctors)
doctor = Doctor(name="Dr. Bob's Heart Clinic")

@app.post("/consult", response_model=ConsultationResponse)
async def consult_doctor(consult_request: ConsultationRequest) -> ConsultationResponse:
    """
    Endpoint for consulting the doctor. 
    Receives the health status from the user and returns doctor's advice.
    """
    try:
        # Get health status from the request
        health_status = consult_request.situation

        # Use the doctor instance to get the consultation advice
        advice = doctor.consult(health_status)

        # Return the doctor's advice in a structured format
        return ConsultationResponse(advice=advice)

    except Exception as e:
        # Handle errors and send appropriate HTTP responses
        raise HTTPException(status_code=500, detail=f"An error occurred during consultation: {str(e)}")
