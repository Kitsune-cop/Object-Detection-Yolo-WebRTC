from fastapi import APIRouter, HTTPException, status
import json
from models import offerModel,answerModel

router = APIRouter()

data = {}

@router.get("/")
async def test():
    return status.HTTP_200_OK

@router.post("/offer")
async def offer(offer:offerModel):
    if offer.type == "offer":
        data["offer"] = {"id":offer.id, "sdp":offer.sdp, "type":offer.type, "msg":offer.msg}
        print("CREATED_OFFER")
        return status.HTTP_200_OK
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
@router.post("/answer")
async def answer(answer:answerModel):
    if answer.type == "answer":
        data["answer"] = {"id":answer.id, "sdp":answer.sdp, "type":answer.type, "msg":answer.msg}
        print("CREATED_ANSWER")
        return status.HTTP_200_OK
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

@router.get("/get_offer")
async def getOffer():
    if "offer" in data:
        offer = data["offer"]
        print(f'Get_OFFER --> ID:{offer["id"]}, Type:{offer["type"]}')
        del data["offer"]
        return offer
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
@router.get("/get_answer")
async def getAnswer():
    # print(data)
    if "answer" in data:
        # answer = json.dumps(data["answer"])
        answer = data["answer"]
        print(f'Get_ANSWER --> ID:{answer["id"]}, Type:{answer["type"]}')
        del data["answer"]
        return answer
    else:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)