import os
import pickle
import logging
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from starlette.concurrency import run_in_threadpool

import shap

from config import MODEL_PATH, FEATURE_ORDER, SYSTEM_PROMPT
from database import init_db
from endpoints import router
import tools

# ─── Logging Configuration ───
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ─── FastAPI App & Security ───
app = FastAPI()
API_KEY = os.getenv("X_API_KEY", "secret-key")
api_key_header = APIKeyHeader(name="x-api-key")

def get_api_key(x_api_key: str = Depends(api_key_header)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

# ─── Global Exception Handler ───
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception on {request.method} {request.url}: {exc}",
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"}
    )

# ─── Startup Event: Initialize DB & Load Model/Explainer ───
@app.on_event("startup")
async def on_startup():
    # Initialize the database
    await init_db()
    logger.debug("Database initialized")

    # Helper to load model with closed file handle
    def _load_model(path: str):
        with open(path, "rb") as f:
            return pickle.load(f)

    # Load model and SHAP explainer off the event loop
    logger.info("Attempting to load model from %s", os.path.abspath(MODEL_PATH))
    try:
        model = await run_in_threadpool(_load_model, MODEL_PATH)
        explainer = await run_in_threadpool(shap.TreeExplainer, model)
        app.state.model = model
        app.state.explainer = explainer
        app.state.FEATURE_ORDER = FEATURE_ORDER
        app.state.SYSTEM_PROMPT = SYSTEM_PROMPT

        # Also make explainer available in tools
        tools.explainer = explainer

        logger.info("Loaded model and SHAP explainer successfully.")
    except FileNotFoundError:
        app.state.model = None
        app.state.explainer = None
        app.state.FEATURE_ORDER = FEATURE_ORDER
        app.state.SYSTEM_PROMPT = SYSTEM_PROMPT

        # Ensure tools.explainer is also None
        tools.explainer = None

        logger.warning(
            "Model file not found at %s, /explain endpoint will be disabled",
            os.path.abspath(MODEL_PATH)
        )

# ─── Include Router with API Key Dependency ───
app.include_router(
    router,
    dependencies=[Depends(get_api_key)]
)
