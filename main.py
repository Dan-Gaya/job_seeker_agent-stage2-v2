# main.py
import os
from fastapi import FastAPI
from controllers.a2a_controller import router as a2a_router
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware


load_dotenv()

app = FastAPI(title="JobSeekerAI A2A (JSON-RPC mode)", version="0.1.0")


# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(a2a_router)
@app.get("/")
async def root():
    return {"message": "Welcome to the JobSeekerAI API"}

@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "jobseeker"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
