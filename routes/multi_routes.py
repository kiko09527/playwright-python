# promotion.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

class PromotionRequest(BaseModel):
    name: str
    discount: float
    items: List[str]

class PromotionResponse(BaseModel):
    message: str
    promotion_id: int

@app.post("/test", response_model=PromotionResponse)
def create_promotion(request: PromotionRequest):
    promotion_id = 1  # 模拟生成的 ID
    return PromotionResponse(
        message="Promotion created successfully",
        promotion_id=promotion_id
    )