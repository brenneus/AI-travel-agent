# AI Travel Agent

An AI-powered travel agent that can help you plan and book your next vacation. This project uses a combination of large language models (LLMs) and web automation to provide a seamless experience for planning your travel.

## Features

* **Natural Language Interaction**: Plan your trip via a conversational agent.
* **Real-time Flight Search**: Uses Playwright to scrape live flight data based on agent logic.
* **Agentic State Management**: Built with LangGraph to handle complex, multi-step travel research tasks.
* **Modern UI**: Responsive dashboard for viewing flight results and chat history.

## Project Structure

The project is a monorepo with two main components:

*   `backend/`: A Python-based backend using FastAPI, LangChain, and Playwright.
*   `frontend/`: A Next.js and React-based frontend.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

*   Python 3.8+
*   Node.js 18.x or later
*   `pip` for Python package management
*   `npm` or `yarn` for Node.js package management
*   Google AI Studio API Key (available [here](https://aistudio.google.com) for free)
### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/brenneus/AI-travel-agent.git
    cd AI-travel-agent
    ```

2.  **Backend Setup:**
    Navigate to the `backend` directory and install the required Python packages.
    ```bash
    cd backend
    pip install -r requirements.txt
    playwright install
    ```
    You will also need to create a `.env` file in the `backend` directory and add your API keys. You can use the `.env.example` as a template.

3.  **Frontend Setup:**
    Navigate to the `frontend` directory and install the required Node.js packages.
    ```bash
    cd ../frontend
    npm install
    ```

## Usage

1.  **Start the backend server:**
    ```bash
    cd backend
    uvicorn main:app --reload
    ```

2.  **Start the frontend development server:**
    ```bash
    cd ../frontend
    npm run dev
    ```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.
