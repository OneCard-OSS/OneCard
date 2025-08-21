from fastapi import APIRouter, Query
from services.nfc_satus import get_nfc_authentication_status
from schemas.nfc import NfcStatusResponse

nfc_router = APIRouter(prefix="/api/v1", tags=["NFC status polling"])

@nfc_router.get("/nfc-status/{attempt_id}", response_model=NfcStatusResponse)
def nfc_status(attempt_id:str,
               client_id:str):
    
    return get_nfc_authentication_status(attempt_id=attempt_id,
                                         client_id=client_id)