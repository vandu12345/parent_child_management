import uvicorn
from fastapi import FastAPI

from rest_api.ApiController import router as api_router

app = FastAPI()
# TODO Add middleware to avoid cors issue
app.include_router(api_router)


def start():
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="config/key.pem",
        ssl_certfile="config/cert.pem",
    )


if __name__ == "__main__":
    start()
