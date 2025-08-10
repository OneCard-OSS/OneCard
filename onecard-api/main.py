from fastapi import FastAPI
import uvicorn
from api.v1.login import login_router
from api.v1.oauth import oauth_router

app = FastAPI()

@app.get("/")
def main():
    return{"message" : "Hello from onecard-api!"}

app.include_router(login_router)
app.include_router(oauth_router)

if __name__ == "__main__":
    uvicorn.run(app, 
                host="0.0.0.0",
                port=8001)
