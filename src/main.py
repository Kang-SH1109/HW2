import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from .config import MAX_MESSAGE_LENGTH, MODEL_VERSION, ROOT
from .model import load_model
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger(__name__); model = None
@asynccontextmanager
async def lifespan(_app):
    global model
    try: model = load_model(); log.info("model loaded: %s", MODEL_VERSION)
    except Exception as exc: log.error("model load failed: %s", exc)
    yield
    log.info("server shutdown")
app = FastAPI(title="AI 스팸 문자 탐지", version=MODEL_VERSION, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=ROOT / "web"), name="static")
class MessageRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LENGTH)
    @field_validator("text")
    @classmethod
    def not_blank(cls, value):
        if not value.strip(): raise ValueError("문자 메시지를 입력해 주세요.")
        return value
@app.get("/")
def index(): return FileResponse(ROOT / "web" / "index.html")
@app.get("/api/health")
def health(): return {"status": "ok", "model_loaded": model is not None, "model_version": MODEL_VERSION}
@app.post("/api/predict")
def predict(request: MessageRequest):
    if model is None: raise HTTPException(503, "모델이 준비되지 않았습니다. 서버 로그와 학습 명령을 확인해 주세요.")
    try:
        text = request.text.strip(); label = str(model.predict([text])[0]); probabilities = dict(zip(model.classes_, model.predict_proba([text])[0]))
        return {"label": label, "score": round(float(probabilities[label]) * 100, 2), "model_version": MODEL_VERSION, "explanation": "TF-IDF 문자 패턴을 Logistic Regression이 비교해 산출한 모델 점수입니다. 실제 스팸 여부의 확정이나 정확한 정답 확률이 아닙니다."}
    except Exception as exc:
        log.exception("prediction failed"); raise HTTPException(500, "분석 중 오류가 발생했습니다.") from exc
