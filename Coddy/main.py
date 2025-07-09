from fastapi import FastAPI
from .api.routers import files

app = FastAPI(
    title="Coddy - The Sentient Loop",
    description="Your async-native, memory-rich dev companion.",
    version="2.0.0",
)

app.include_router(files.router)

@app.get("/")
async def root():
    """
    Root endpoint for the Coddy API.
    """
    return {"message": "Welcome to the Coddy API. Let's build something with vibe."}