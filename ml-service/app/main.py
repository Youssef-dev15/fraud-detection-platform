import logging
import os
import secrets
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse

from app.predictor import Predictor
from app.schemas import HealthResponse, PredictRequest, PredictResponse

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ml-service")

predictor = Predictor()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        predictor.load()
        log.info("Modèle chargé (version %s)", predictor.version)
    except Exception:
        log.exception("Impossible de charger le modèle : /predict répondra 503")
    yield


app = FastAPI(title="Fraud Scoring Service", version="1.0.0", lifespan=lifespan)


def check_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("ML_API_KEY")
    if expected and not (x_api_key and secrets.compare_digest(x_api_key, expected)):
       raise HTTPException(status_code=401, detail="Clé d'API invalide")


@app.post("/predict", response_model=PredictResponse, dependencies=[Depends(check_api_key)])
def predict(req: PredictRequest) -> PredictResponse:
    if not predictor.loaded:
        raise HTTPException(status_code=503, detail="Modèle non chargé")
    score = predictor.predict(req.type.value, req.amount, req.oldbalanceOrg, req.oldbalanceDest)
    return PredictResponse(score=score, modelVersion=predictor.version)


@app.get("/health", response_model=HealthResponse)
def health():
    body = HealthResponse(
        status="ok" if predictor.loaded else "degraded",
        model_loaded=predictor.loaded,
        modelVersion=predictor.version,
    )
    return JSONResponse(status_code=200 if predictor.loaded else 503, content=body.model_dump())