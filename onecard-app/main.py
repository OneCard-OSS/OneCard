from fastapi import FastAPI
import uvicorn
from api.login import app_login_router

app = FastAPI()

app.include_router(app_login_router)

if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port='8002')
