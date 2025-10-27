from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import chat, files
from dotenv import load_dotenv
import os

load_dotenv()

# Debug prints to confirm environment is loaded
print("Loaded API key:", os.getenv("CHATGROQ_API_KEY"))
print("Azure Storage Connection:", bool(os.getenv("AZURE_STORAGE_CONNECTION_STRING")))

app = FastAPI(title="Chatbot API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api")
app.include_router(files.router, prefix="/api/files")

@app.get("/health")
async def health():
    return {"status": "ok"}
