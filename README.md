# JobSeekerAI A2A

## Setup
1. Create venv & install:
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

2. Download spaCy model:
   python -m spacy download en_core_web_sm

3. Copy `.env.example` to `.env` and set `JSEARCH_API_KEY` (optional).

4. Run:
   python main.py
   # or
   uvicorn main:app --reload --port 5002

## Test (curl)
curl -X POST http://localhost:5002/a2a/jobseeker \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "id":"test-001",
    "method":"message/send",
    "params":{
      "message":{
        "kind":"message",
        "role":"user",
        "parts":[
          { "kind":"text","text":"backend python remote nigeria" }
        ],
        "messageId":"msg-001",
        "taskId":"task-001"
      },
      "configuration":{
        "blocking": true
      }
    }
  }'
