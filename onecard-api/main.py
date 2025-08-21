from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
from api.v1.oauth import oauth_router
from api.v1.nfc_polling import nfc_router
from api.v1.card_response import card_response_router
from logging_config import setup_logging
import os 
from dotenv import load_dotenv

load_dotenv()

setup_logging()

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY"),
    session_cookie="onecardsess",
    max_age=1800 
)

@app.get("/.well-known/openid-configuration", tags=["OIDC discovery"])
def get_openid_configuration(request:Request):
    """
    OIDC discovery endpoint
    Provides standard configuration information to automatically discover authentication server's endpoint information
    """
    baseurl = str(request.base_url).rstrip('/')
    return JSONResponse({
        "issuer" : baseurl,
        "authorization_endpoint" : f"{baseurl}/api/v1/authorize",
        "token_endpoint" : f"{baseurl}/api/v1/token",
        "userinfo_endpoint" : f"{baseurl}/api/v1/userinfo",
        "response_types_supported": ["code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["HS256"]
    })
    
app.include_router(card_response_router)
app.include_router(nfc_router)
app.include_router(oauth_router)

if __name__ == "__main__":
    uvicorn.run(app, 
                host="0.0.0.0",
                port=8001)
