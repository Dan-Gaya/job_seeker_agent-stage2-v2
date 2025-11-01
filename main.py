# main.py
import os
from fastapi import FastAPI
from controllers.a2a_controller import router as a2a_router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="JobSeekerAI A2A (JSON-RPC mode)", version="0.1.0")
app.include_router(a2a_router)

@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "jobseeker"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 5002))
    uvicorn.run(app, host="0.0.0.0", port=port)
