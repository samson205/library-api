from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.genres.router import router as genres_router

app = FastAPI(title="Library API", version="0.1.0")
app.include_router(auth_router)
app.include_router(genres_router)


@app.get("/")
async def root():
    return {"message": "Welcome!"}
