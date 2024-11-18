# AI-Powered Decentralized Search Engine and Intelligent Agents

## Introduction

This project presents a decentralized AI-powered search engine and a network of intelligent agents, each with unique capabilities, designed to collaborate and manage tasks efficiently. The system is built using Python, leveraging the power of FastAPI for creating a robust API-driven architecture.

## Project Structure

The project is organized into two main folders: **Hub** and **Agent**, each containing the following components:

### Hub Folder
- **AI-Powered Search Engines:**
  - Each search engine is a FastAPI application, representing a decentralized hub for agent matchmaking and collaboration.
  - Run each search engine with: `uvicorn main:app --host 127.0.0.1 --port {port_number}`.
  - Ports for each engine: {list_of_ports}.
  - These hubs facilitate agent discovery and communication, acting as intelligent intermediaries.

### Agent Folder
- **Intelligent Agents:**
  - 9 distinct agents, each with specialized skills, ready to handle various tasks.
  - Run an agent with: `uvicorn main:app --host 127.0.0.1 --port {port_number}`.
  - Agents communicate with the search engines and other agents using standardized protocols.

## Key Features

- **Agent Registration:** Agents register with the search engines, providing their capabilities and contact details.
- **Task Assignment:** Search engines assign tasks to agents based on their capabilities.
- **Agent Search:** Users can search for agents with specific skills using the search engines.
- **Agent Communication:**
  - **Basic Communication:** Agents use `/help` endpoint to retrieve API documentation and adapt to new tasks.
  - **Advanced Communication:** For complex tasks, agents use `/agent_request` for one-time queries and `/create_chat` for multi-turn dialogues.

## Getting Started

### Prerequisites
- Python (version 3.7 or higher)
- FastAPI (`pip install fastapi`)
- Uvicorn (`pip install uvicorn[standard]`)
- Other dependencies listed in [requirements.txt](requirements.txt)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/ai-decentralized-system.git
```

2. Navigate to each folder and install dependencies:
```bash
cd hub/{name_hub}
pip install -r requirements.txt

cd ../agent/{name_agent}
pip install -r requirements.txt
```

### Running the System

1. Start a search engine:
```bash
uvicorn main:app --host 127.0.0.1 --port 8001
```

2. Start an agent:
```bash
uvicorn main:app --host 127.0.0.1 --port 8002
```

3. Access the FastAPI documentation at `http://127.0.0.1:8001/docs` or `http://127.0.0.1:8010/docs` for the respective search engine and agent.

## Usage Examples

- **Cooking Task:** Assign a cooking task to the "Chef Agent," which collaborates with "Pantry Agent" and "Shopping Agent" to gather ingredients and prepare a meal.
- **Medical Consultation:** A "Medical Agent" analyzes symptoms, consults with a "Cardiologist Agent," and procures medications from a "Pharmacy Agent."
- **Hotel Reservation:** The "Consultant Agent" interacts with "Hotel Reservation Agents" to negotiate and book a hotel room.

## Documentation

- **API Documentation:** FastAPI's interactive API documentation is available at each application's respective port (e.g., `http://127.0.0.1:8001/docs`).
- **Code Documentation:** Detailed code comments are included throughout the codebase.
- **Research Paper:** The accompanying [research paper](docs/research_paper.pdf) provides a comprehensive overview of the project.

## Contributing

Contributions are welcome! Please refer to the [Contribution Guidelines](CONTRIBUTING.md) for more information.

## License

This project is licensed under the [MIT License](LICENSE).
