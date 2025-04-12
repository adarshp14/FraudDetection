# 🕵️‍♂️ Real-Time Fraud Detection System

An autonomous, LLM-powered fraud detection system using CrewAI and Gemini API, with an interactive Streamlit UI.

## Features

- 🤖 Autonomous AI Agents for fraud detection
- 🧠 Gemini API-powered decision making
- 🎨 Beautiful Basalt-style Streamlit UI
- 🎬 Real-time agent simulation visualization
- 📊 Comprehensive risk assessment

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd FraudDetection
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your Gemini API key:
```
GEMINI_API_KEY=your_api_key_here
```

4. Run the Streamlit app:
```bash
streamlit run app.py
```

## Demo Inputs

Try these example transactions:

1. Fraudulent Transaction:
```json
{
    "amount": 9999,
    "location": "Dubai",
    "description": "Luxury bag store"
}
```

2. Legitimate Transaction:
```json
{
    "amount": 45,
    "location": "Delhi",
    "description": "Metro ticket"
}
```

## System Architecture

- `crew.py`: CrewAI agents and tasks
- `app.py`: Streamlit UI with simulation
- `utils/llm.py`: Gemini API integration
- `requirements.txt`: Project dependencies

## Agents

1. Data Ingestion Agent
2. Anomaly Detection Agent
3. Risk Assessment Agent
4. Investigation Agent
5. Decision Agent

## License

MIT License 