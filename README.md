# Zs Electrical Chatbot with MCP

An AI-powered electrical safety chatbot that calculates earth fault loop impedance (Zs = Ze + R1 + R2) and checks MCB compliance.

## Project Structure
- `app.py` — Flask backend + chatbot frontend (UI served at localhost)
- `mcp_server.py` — MCP tools for MCP Inspector

## How to Run

### 1. Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install flask
pip install "mcp[cli]"
```

### 2. Run the Chatbot
```bash
python3 app.py
```
Open http://localhost:5001 in your browser.

### 3. Run MCP Inspector
```bash
mcp dev mcp_server.py
```
Open http://localhost:6274 in your browser.

## Features
- Calculates Ze (parallel combination of earth pits and grid)
- Computes Zs = Ze + (R1 + R2)
- Checks compliance: Zs <= (2/3)(U0/Ia) for MCB Type B/C/D
- Only answers electrical engineering questions
- MCP tools exposed for AI agent integration

## Standards
- Earth pit < 5 ohm
- Earth grid < 1 ohm
- Disconnection limit: Zs <= (2/3)(U0/Ia)
