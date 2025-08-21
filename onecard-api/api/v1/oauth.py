from fastapi import APIRouter, Query, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jose import JWTError
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
from core.database import get_db
from core.token import Token
from services.init_login import init_login
from services.get_authorization import issue_authorization_code
from services.token_service import handle_token_request
from services.logout import logout_user
from utils.get_current_session import get_current_session, get_employee_from_session_id
from schemas.userinfo import UserInfoResponse
from logging import getLogger
from logging_config import EndPointAdapter

token = Token()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")
oauth_router = APIRouter(prefix="/api/v1", tags=["OAuth API"])
templates = Jinja2Templates(directory="templates")

@oauth_router.api_route("/authorize", methods=["GET", "POST"])
async def handle_authorization_flwo(request:Request,
                                    db:Session=Depends(get_db)):
    """
    Orchestrate the entire authentication / authorization flow for OIDC compatiblity
    - GET(First Time): Save parameters to session(FastAPI Session) and display employee number enrty page
    - POST: Initiates a login attempt with the session parameters and the entered employee number and displays a waiting page
    - GET (with attempt_id) : Authorization Code issuance and redirectrion after NFC authentication success
    """
    logger = getLogger(__name__)
    adapter = EndPointAdapter(logger, {"endpoint":f"{request.method} /api/v1/authorize"})
    
    # --- Processing POST request (STEP 2: Login attempt)
    if request.method == "POST":
        # Parameters from server session
        oauth_params = request.session.pop('oauth_params', None)
        if not oauth_params:
            raise HTTPException(status_code=400, 
                                detail="Session expired or invalid request. Please start the login process again")
        client_id = oauth_params.get("client_id")
        redirect_uri = oauth_params.get("redirect_uri")
        state = oauth_params.get("state")
        
        form_data = await request.form()
        emp_no = form_data.get("emp_no")
        
        if not emp_no:
            raise HTTPException(status_code=400, detail="Employee number is required.")
        
        new_attempt_id = await init_login(
            emp_no=emp_no,
            client_id=client_id,
            redirect_uri=redirect_uri,
            state=state,
            db=db,
            logger=adapter
        )
        return templates.TemplateResponse("waiting.html", {
            "request" : request,
            "attempt_id" : new_attempt_id,
            "client_id" : client_id,
            "redirect_uri" : redirect_uri,
            "state" : state,
            "polling_interval" : 3000 # 3 seconds
        })
    # --- Processing GET request ---
    elif request.method == "GET":
        params = request.query_params
        attempt_id = params.get("attempt_id")
        
        # If attempt_id exists (final authorization code issued after NFC success)
        if attempt_id:
            return issue_authorization_code(
                response_type=params.get("response_type"),
                client_id=params.get("client_id"),
                redirect_uri=params.get("redirect_uri"),
                state=params.get("state"),
                attempt_id=attempt_id,
                db=db,
                logger=adapter
            )
        # --- First entry: Display the page to enter employee number ---
        else:
            response_type = params.get("response_type")
            client_id = params.get("client_id")
            redirect_uri = params.get("redirect_uri")
            state = params.get("state")
            
            if not all([response_type, client_id, redirect_uri]):
                raise HTTPException(status_code=400,
                                    detail="Missing required query parameteres")
            # Store parameters in server-side session
            request.session['oauth_params'] = {
                "client_id" : client_id,
                "redirect_uri" : redirect_uri,
                "state" : state
            }
            return templates.TemplateResponse("login.html", {
                "request" : request
            })

# @oauth_router.api_route("/authorize", methods=["GET", "POST"])
# def authorize(request:Request,
#               response_type:str=Query(...),
#               client_id:str=Query(...),
#               redirect_uri:str=Query(...),
#               state:Optional[str]=Query(None),
#               attempt_id:Optional[str]=Query(None),
#               emp_no:Optional[str]=Form(None),
#               db:Session=Depends(get_db)):
    
#     logger = getLogger(__name__)
#     adapter = EndPointAdapter(logger, {"endpoint":"GET /api/v1/authorize"})
    
#     return get_authorization(response_type=response_type,
#                              client_id=client_id,
#                              redirect_uri=redirect_uri,
#                              state=state,
#                              attempt_id=attempt_id,
#                              db=db,
#                              logger=adapter)
    
@oauth_router.post("/token")
def token(
    grant_type: str = Form(..., description="The type of grant being requested. 'authorization_code' or 'refresh_token'."),
    client_id: str = Form(..., description="The service's unique identifier."),
    client_secret: str = Form(..., description="The service's secret key."),
    redirect_uri: Optional[str] = Form(None, description="The redirection URI used in the initial authorization request."),
    code: Optional[str] = Form(None, description="The authorization code received from the authorization endpoint."),
    refresh_token: Optional[str] = Form(None, description="The refresh token issued to the client."),
    db: Session = Depends(get_db)):
    """
    Handles token requests for both Authorization Code and Refresh Token grants.
    """
    logger = getLogger(__name__)
    adapter = EndPointAdapter(logger, {"endpoint":"POST /api/v1/token"})
    
    return handle_token_request(
        grant_type=grant_type,
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        code=code,
        refresh_token=refresh_token,
        db=db,
        logger=adapter
    )

@oauth_router.post("/logout")
def logout(access_token:str=Depends(oauth2_scheme)):
    logger = getLogger(__name__)
    adapter = EndPointAdapter(logger, {"endpoint" : "POST /api/v1/logout"})
    try:
        payload = token.verify_token(access_token, is_refresh=False)
        s_id = payload.get("sub")
        if not s_id:
            adapter.warning(f"Invalid Session ID", extra={"payload":payload})
            raise HTTPException(status_code=401,
                                detail="Invalid Session ID")
        return logout_user(s_id=s_id, access_token=access_token, logger=adapter)
    except JWTError as je:
        logger.error(f"JWTError Occured: {str(je)}")
        raise HTTPException(status_code=401,
                            detail="Invalid Token")
    except Exception as e:
        adapter.error(f"Unexpected error during logout:{str(e)}", exc_info=True)
        raise HTTPException(status_code=500,
                            detail="Internal Server Error")
        
@oauth_router.get("/userinfo", response_model=UserInfoResponse)
def get_userinfo(s_id:str=Depends(get_current_session), db:Session=Depends(get_db)):
    
    employee = get_employee_from_session_id(s_id=s_id, db=db)
    
    return UserInfoResponse(
        sub=employee.emp_no,
        name=employee.name,
        email=employee.email
    )