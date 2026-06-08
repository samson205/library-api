from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.genres.router import router as genres_router
from app.authors.router import router as authors_router
from app.books.router import router as books_router
from app.users.router import router as users_router
from app.shelves.router import router as shelves_router
from app.reviews.router import router as reviews_router

app = FastAPI(title="Library API", version="0.1.0")
app.include_router(auth_router)
app.include_router(genres_router)
app.include_router(authors_router)
app.include_router(books_router)
app.include_router(users_router)
app.include_router(shelves_router)
app.include_router(reviews_router)


@app.get("/")
async def root():
    return {"message": "Welcome!"}
