# Multi-LLM Judge Aggregator (AsyncSQL + FastAPI + Streamlit)

## Overview
**Multi-LLM Judge** is a powerful AI aggregation platform that leverages the "LLM-as-a-Judge" pattern. It queries two different Large Language Models (LLMs) in parallel via FastAPI (asynchronous processing), compares their outputs, and uses a third "Judge" model to synthesize a final, high-quality answer. The results are stored in an SQLite database for history tracking and analytics, and the entire system is accessible via a user-friendly Streamlit interface

### Key Features

- **Async Parallel Execution: Queries multiple models simultaneously to minimize latency**
- **AI Judge System: Automatically evaluates and merges answers from different models into one cohesive response**
- **Persistent Storage: Logs all requests, responses, model names, and execution times into a local SQLite database**
- **Analytics: Built-in endpoints to track model performance (latency, request counts)**
- **Interactive UI: Clean web interface built with Streamlit for easy interaction and history browsing**

## Repository structure
```bash
Multi-LLM-Judge-AsyncSQL-FastAPI-Streamlit/
│
├── aggregator_fast_api.py      # FastAPI
├── test_streamlit.py           # Streamlit 
├── .env                        # API keys
├── requirements.txt            # requirements
├── my_aggregator.db            # SQLite db
└── README.md                   # documentaion
```

## Architecture
```bash
[Streamlit UI] 
      ↓
  (HTTP POST /ask)
      ↓
[FastAPI Backend]
 ├─ async call → [LLM 1]
 ├─ async call → [LLM 2]
 └─ judge → [LLM 3]
      ↓
[SQLite DB]
      ↓
[Response → Streamlit UI]

┌─────────────┐      ┌─────────────┐     ┌─────────────────┐
│   Streamlit │────▶ │   FastAPI   │────▶│   OpenRouter    │
│   (UI)      │◀────│   (Backend) │◀────│   (LLM API)     │
└─────────────┘      └─────────────┘     └─────────────────┘
                           │                     │
                           ▼                     ▼
                    ┌─────────────┐     ┌─────────────────┐
                    │  SQLite DB  │     │   Judge (LLM)   │
                    │  (History)  │     │   (Analysis)    │
                    └─────────────┘     └─────────────────┘
```

## Tech Stack
- **Python 3.10+**
- **LangChain**
- **SQLite3**
- **dotenv**
- **langchain-openai**
- **langchain-core**
- **OpenRouter API**
- **asyncio**
- **Uvicorn**
- **FastAPI**
- **Streamlit**

## Project Structure
```bash
Multi-LLM-Judge/
├── aggregator_fast_api.py  # Main FastAPI backend application
├── test_streamlit.py       # Streamlit frontend application
├── my_aggregator.db        # SQLite database (auto-generated)
├── .env                    # Environment variables (API Keys)
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

## Installation & Setup
### 1. Clone the repository
```bash
git clone https://github.com/MykhailoTymoshenko08/Multi-LLM-Judge-AsyncSQL-FastAPI-Streamlit.git
cd Multi-LLM-Judge-AsyncSQL-FastAPI-Streamlit
```

### 2. Set up Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
Create a requirements.txt file (or install manually) with the following packages:
```bash
fastapi
uvicorn
streamlit
langchain-openai
langchain-core
python-dotenv
requests
pydantic
```
Install them:
```bash
pip install -r requirements.txt
```
or in cmd:
```bash
py -m pip install -r requirements.txt
```

### 4. Configuration
Create a .env file in the root directory and add your OpenRouter API key:
```bash
API_KEY=your_openrouter_api_key_here
```

## Usage
You need to run the Backend and the Frontend in two separate terminal windows
### Terminal 1: Start the Backend (API)
```bash
uvicorn aggregator_fast_api:app --reload
```
The API will start at http://localhost:8000. 
Swagger documentation is available at http://localhost:8000/docs

### Terminal 2: Start the Frontend (UI)
```bash
streamlit run test_streamlit.py
```
The web interface will open automatically in your browser (at http://localhost:8501)

## API Endpoints
### Core Logic
#### POST /ask
Runs simultaneous queries to two LLMs, passes the results to the “judge,” and returns the final result

Request's body:
```json
{
  "question": "Explain quantum computing in simple terms"
}
```

Answer:
```json
{
  "status": "success",
  "question": "Explain quantum computing in simple terms",
  "model1": {
    "name": "meta-llama/llama-3.3-70b-instruct:free",
    "answer": "...",
    "duration": "3.24s"
  },
  "model2": {
    "name": "google/gemma-3-27b-it:free",
    "answer": "...",
    "duration": "2.89s"
  },
  "final_answer": "Quantum computing uses qubits ...",
  "total_duration": "6.45s"
}
```

### Data & Statistics
#### GET /stats
Returns query execution statistics for each model.

Example response:
```json
{
  "statistics": [
    {
      "model": "meta-llama/llama-3.3-70b-instruct:free",
      "request_count": 10,
      "avg_duration": "2.50s",
      "min_duration": "1.80s",
      "max_duration": "3.10s"
    },
    {
      "model": "google/gemma-3-27b-it:free",
      "request_count": 10,
      "avg_duration": "2.40s",
      "min_duration": "1.70s",
      "max_duration": "2.90s"
    }
  ],
  "total_requests": 30
}
``` 

#### GET /history
Returns the history of recent queries.

Parameters:
limit — number of recent records (default 10)

Example response:
```json
{
  "history": [
    {
      "timestamp": "2026-01-09 12:42:11",
      "question": "What is AI?",
      "model": "meta-llama/llama-3.3-70b-instruct:free",
      "duration": "2.34s"
    }
  ]
}
```

#### GET /info
Returns basic information about the system.

### Management
#### DELETE /clear
Clears all query history:
```bash
curl -X DELETE http://localhost:8000/clear
```
