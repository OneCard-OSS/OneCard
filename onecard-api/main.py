from fastapi import FastAPI
import uvicorn
from api.v1.login import login_router
from api.v1.oauth import oauth_router
from api.v1.nfc_polling import nfc_router
from api.v1.card_response import card_response_router
from api.v1.manage_card import card_router
from logging_config import setup_logging

setup_logging()

app = FastAPI()

@app.get("/")
def main():
    return{"message" : "Hello from onecard-api!"}

app.include_router(login_router)
app.include_router(card_response_router)
app.include_router(nfc_router)
app.include_router(oauth_router)
app.include_router(card_router)

if __name__ == "__main__":
    uvicorn.run(app, 
                host="0.0.0.0",
                port=8001)
