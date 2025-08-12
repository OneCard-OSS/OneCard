from pydantic import BaseModel

class ManageCard(BaseModel):
    emp_no:str
    pubkey:str
    
class CardData(BaseModel):
    card_data:str
    
class Card_data_with_attempt(CardData):
    attempt_id:str