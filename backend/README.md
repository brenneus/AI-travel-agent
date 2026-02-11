# AI Travel Agent - Backend

This directory contains the backend for the AI Travel Agent. It is a Python-based application using FastAPI, LangChain, and Playwright to power the AI agent.

## Getting Started

### Prerequisites

* Python 3.8+
* `pip` for Python package management

### Installation

1.  **Install dependencies:**
    From the `backend` directory, run:
    ```bash
    pip install -r requirements.txt
    playwright install
    ```

2.  **Create `.env` file:**
    Create a `.env` file in this directory and add the necessary API keys. You can use `.env.example` as a template.
    A Google AI Studio API KEY available [here](https://aistudio.google.com) for free. 

### Testing the agent locally

To test the agent's logic directly from the terminal without running the web server, run the following commands from the `backend` directory:
```bash
python3 -m src.agent
```

### Running the server

To start the backend server, run the following command from the `backend` directory:
```bash
uvicorn main:app --reload
```
The API server will be available at `http://localhost:8000`.

## API

The backend exposes a FastAPI server with the following main endpoint:

* **POST** `/invoke`: The main endpoint to interact with the AI agent. It takes a JSON body with the current state and returns the updated state.