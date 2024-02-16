from pydantic import BaseModel

class offerModel(BaseModel):
    id:str|int|None=None
    sdp:str
    type:str
    msg:str

class  answerModel(BaseModel):
    id:str|int|None=None
    sdp:str
    type:str
    msg:str