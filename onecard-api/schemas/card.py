from pydantic import BaseModel

class CardDataRequest(BaseModel):
    card_data:str
    attempt_id:str
    client_id:str