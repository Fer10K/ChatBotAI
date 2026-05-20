import uvicorn
import os
from fastapi import FastAPI
from dotenv import load_dotenv
from app.api.routes import sessions, webhook, bots_info

load_dotenv()
app = FastAPI(title= "API ChatBot")

app.include_router(sessions.router, prefix="/api/v1/sessions", tags= ["Sessions"])
app.include_router(bots_info.router, prefix="/api/v1/bots_info", tags=["Bots_info"])
app.include_router(webhook.router, tags=["Webhook"])

if __name__ ==  "__main__":
    port=int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload =True)
