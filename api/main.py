from fastapi import FastAPI
from pydantic import BaseModel

from src.pipeline import run_pipeline
from src.schemas import GiftResponseSchema

app = FastAPI(title="Mumzworld AI Gift Finder")


class QueryRequest(BaseModel):
    query: str


@app.post("/recommend", response_model=GiftResponseSchema)
def recommend_endpoint(request: QueryRequest) -> GiftResponseSchema:
    return run_pipeline(request.query)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
