from fastapi import FastAPI
import uvicorn
from api.v1.user import user_router
from api.v1.service import service_router
from api.v1.permission import perm_router
from api.v1.manage_card import card_router
from api.v1.logs import router as logs_router
from routers.routers import admin_router

app = FastAPI()

app.include_router(admin_router)
app.include_router(user_router)
app.include_router(service_router)
app.include_router(perm_router)
app.include_router(card_router)
app.include_router(logs_router)

if __name__ == "__main__":
    uvicorn.run(app, 
                host="0.0.0.0",
                port=8000)
