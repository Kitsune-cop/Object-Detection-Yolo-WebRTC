from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import server
import uvicorn


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(server.router)

if __name__ == "__main__":
    uvicorn.run("__main__:app", host="127.0.0.1", port=8443, reload=True)

