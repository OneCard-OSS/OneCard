from fastapi import FastAPI
import uvicorn
from api.v1.user import user_router

app = FastAPI()

@app.get("/")
def main():
    return {"Message" : "Server Start"}

app.include_router(user_router)

if __name__ == "__main__":
    uvicorn.run(app, 
                host="0.0.0.0",
                port=8000)
