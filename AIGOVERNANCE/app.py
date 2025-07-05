import os
import json
import logging
import asyncio
import pickle
import shap
import numpy as np  # For array conversion

from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool
from openai import OpenAI

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

# ─── DATABASE INTEGRATION IMPORTS ───
from database import init_db, AsyncSessionLocal
from model import Application as ApplicationModel

# ─── MODEL & SHAP EXPLAINER SETUP ───
MODEL_PATH = os.getenv("MODEL_PATH", "model.pkl")
FEATURE_ORDER = [
    "age",
    "score",
    "income",
    # … other feature keys …
]

def _load_model(path: str):
    with open(path, "rb") as f:
        return pickle.load(f)

# ─── Raw SQL query constants ───
SQL_COUNT_APPLICATIONS_BY_GROUP = (
    "SELECT COUNT(*) FROM applications "
    "WHERE json_extract(features, '$.group') = :grp"
)
SQL_COUNT_APPROVED_BY_GROUP = (
    "SELECT COUNT(*) FROM applications "
    "WHERE json_extract(features, '$.group') = :grp AND decision='approved'"
)
SQL_SELECT_FEATURES_BY_ID = (
    "SELECT features FROM applications "
    "WHERE application_id = :id"
)

# ─── Load System Prompt ───
PROMPT_PATH = Path(__file__).parent / "prompts" / "fairness_agent.txt"
try:
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        system_prompt = f.read()
except FileNotFoundError:
    system_prompt = "You are FairnessAgent. Use function-calling with defined FUNCTIONS."
    logging.getLogger(__name__).warning(
        f"Prompt file not found at {PROMPT_PATH}, using default prompt"
    )

# ─── Logging ───
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
)
logger = logging.getLogger(__name__)
logger.info("Configured MODEL_PATH = %s", os.path.abspath(MODEL_PATH))

# ─── FastAPI setup & security ───
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

# ─── Startup: init DB + load model/explainer ───
@app.on_event("startup")
async def on_startup():
    # Initialize database
    await init_db()
    logger.debug("Database initialized")
    
    # Load model & explainer
    logger.info("Attempting to load model from %s", os.path.abspath(MODEL_PATH))
    try:
        model = await run_in_threadpool(_load_model, MODEL_PATH)
        explainer = await run_in_threadpool(shap.TreeExplainer, model)
        app.state.model = model
        app.state.explainer = explainer
        logger.info("Loaded model and SHAP explainer successfully.")
    except FileNotFoundError:
        app.state.model = None
        app.state.explainer = None
        logger.warning(
            "Model file not found at %s, /explain endpoint disabled",
            os.path.abspath(MODEL_PATH)
        )

# ─── Pydantic schemas ───
class IngestRequest(BaseModel):
    application_id: str
    features: dict

class IngestResponse(BaseModel):
    status: str

class DisparateImpactRequest(BaseModel):
    privileged: str
    unprivileged: str

class DisparateImpactResponse(BaseModel):
    ratio: float

class ExplainRequest(BaseModel):
    application_id: str

class ExplainResponse(BaseModel):
    contributions: dict

class AgentRequest(BaseModel):
    prompt: str

# ─── DB session dependency ───
async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# ─── /ingest endpoint ───
@app.post("/ingest", response_model=IngestResponse)
async def ingest_endpoint(
    req: IngestRequest,
    api_key: str = Depends(get_api_key),
    session: AsyncSession = Depends(get_session)
):
    logger.debug("Ingesting application %s", req.application_id)
    app_model = ApplicationModel(
        application_id=req.application_id,
        features=req.features,
        decision=None
    )
    session.add(app_model)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        logger.warning("Application %s already exists; skipping insert", req.application_id)
    return IngestResponse(status="success")

# ─── /bias/disparate-impact endpoint ───
@app.get("/bias/disparate-impact", response_model=DisparateImpactResponse)
async def disparate_impact_endpoint(
    privileged: str,
    unprivileged: str,
    api_key: str = Depends(get_api_key),
    session: AsyncSession = Depends(get_session)
):
    logger.debug("Compute DI for privileged=%s unprivileged=%s", privileged, unprivileged)
    total_priv = (await session.execute(
        text(SQL_COUNT_APPLICATIONS_BY_GROUP),
        {"grp": privileged}
    )).scalar() or 0
    total_unpriv = (await session.execute(
        text(SQL_COUNT_APPLICATIONS_BY_GROUP),
        {"grp": unprivileged}
    )).scalar() or 0
    hired_priv = (await session.execute(
        text(SQL_COUNT_APPROVED_BY_GROUP),
        {"grp": privileged}
    )).scalar() or 0
    hired_unpriv = (await session.execute(
        text(SQL_COUNT_APPROVED_BY_GROUP),
        {"grp": unprivileged}
    )).scalar() or 0
    rate_priv = hired_priv / total_priv if total_priv else 0
    rate_unpriv = hired_unpriv / total_unpriv if total_unpriv else 0
    ratio = rate_unpriv / rate_priv if rate_priv else 0
    return DisparateImpactResponse(ratio=ratio)

# ─── /explain endpoint ───
@app.post("/explain", response_model=ExplainResponse)
async def explain_endpoint(
    req: ExplainRequest,
    api_key: str = Depends(get_api_key),
    session: AsyncSession = Depends(get_session)
):
    logger.debug("Explain requested for %s", req.application_id)
    if app.state.explainer is None:
        raise HTTPException(status_code=503, detail="Explanation service unavailable")

    result = await session.execute(
        text(SQL_SELECT_FEATURES_BY_ID),
        {"id": req.application_id}
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Application {req.application_id} not found")

    raw = row[0]
    try:
        features = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid features JSON for application")

    x = [features.get(key, 0) for key in FEATURE_ORDER]
    X = np.array([x])
    shap_values = await run_in_threadpool(app.state.explainer.shap_values, X)
    contributions = {key: float(val) for key, val in zip(FEATURE_ORDER, shap_values[0])}
    return ExplainResponse(contributions=contributions)

# ─── Tool dispatcher ───
async def call_tool(name: str, args: dict):
    logger.debug("Tool call %s args=%s", name, args)
    if name == "ingest_application":
        async with AsyncSessionLocal() as session:
            app_model = ApplicationModel(
                application_id=args["application_id"],
                features=args["features"],
                decision=None
            )
            session.add(app_model)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                logger.warning("Tool ingest: application %s already exists", args["application_id"])
        return {"status": "success"}

    if name == "disparate_impact":
        priv = args.get("privileged")
        unpriv = args.get("unprivileged")
        async with AsyncSessionLocal() as session:
            total_priv = (await session.execute(
                text(SQL_COUNT_APPLICATIONS_BY_GROUP),
                {"grp": priv}
            )).scalar() or 0
            total_unpriv = (await session.execute(
                text(SQL_COUNT_APPLICATIONS_BY_GROUP),
                {"grp": unpriv}
            )).scalar() or 0
            hired_priv = (await session.execute(
                text(SQL_COUNT_APPROVED_BY_GROUP),
                {"grp": priv}
            )).scalar() or 0
            hired_unpriv = (await session.execute(
                text(SQL_COUNT_APPROVED_BY_GROUP),
                {"grp": unpriv}
            )).scalar() or 0
        rate_priv = hired_priv / total_priv if total_priv else 0
        rate_unpriv = hired_unpriv / total_unpriv if total_unpriv else 0
        ratio = rate_unpriv / rate_priv if rate_priv else 0
        return {"ratio": ratio}

    if name == "explain_application":
        # Use same logic as /explain endpoint
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(SQL_SELECT_FEATURES_BY_ID), {"id": args.get("application_id")} )
            row = result.first()
            if not row:
                return {"contributions": {}}
            raw = row[0]
            feats = json.loads(raw) if isinstance(raw, str) else raw
            x_vec = [feats.get(key, 0) for key in FEATURE_ORDER]
            X_arr = np.array([x_vec])
            contribs = await run_in_threadpool(app.state.explainer.shap_values, X_arr)
        return {"contributions": {k: float(v) for k, v in zip(FEATURE_ORDER, contribs[0])}}

    raise ValueError(f"Unknown tool: {name}")

# ─── LLM Agent Orchestrator ───
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "30.0"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
FUNCTIONS = [
    {"name": "ingest_application",  "description": "Ingest a new loan application",  "parameters": IngestRequest.schema()},
    {"name": "disparate_impact",    "description": "Compute disparate impact ratio", "parameters": DisparateImpactRequest.schema()},
    {"name": "explain_application", "description": "Return SHAP-based contributions",  "parameters": {"type":"object","properties":{"application_id":{"type":"string"}},"required":["application_id"]}}
]

@app.post("/agent")
async def agent_endpoint(
    req: AgentRequest,
    api_key: str = Depends(get_api_key)
):
    logger.debug("LLM request with functions: %s", [f["name"] for f in FUNCTIONS])
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": req.prompt}
    ]
    try:
        first_resp = await asyncio.wait_for(
            run_in_threadpool(lambda: client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                functions=FUNCTIONS,
                function_call="auto"
            )),
            timeout=LLM_TIMEOUT
        )
    except asyncio.TimeoutError:
        logger.error("First LLM call timed out (%s s)", LLM_TIMEOUT)
        raise HTTPException(status_code=504, detail=f"LLM request timed out after {LLM_TIMEOUT} seconds")
    except Exception as e:
        logger.error("LLM first call error", exc_info=True)
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    message = first_resp.choices[0].message
    if message.function_call:
        fn_name = message.function_call.name
        fn_args = json.loads(message.function_call.arguments or "{}")
        tool_result = await call_tool(fn_name, fn_args)
        followup = [
            {"role": "system",   "content": system_prompt},
            {"role": "user",     "content": req.prompt},
            {"role": "function", "name": fn_name, "content": json.dumps(tool_result)}
        ]
        try:
            second_resp = await asyncio.wait_for(
                run_in_threadpool(lambda: client.chat.completions.create(
                    model="gpt-4",
                    messages=followup
                )),
                timeout=LLM_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.error("Second LLM call timed out (%s s)", LLM_TIMEOUT)
            raise HTTPException(status_code=504, detail=f"LLM follow-up timed out after {LLM_TIMEOUT} seconds")
        return {"response": second_resp.choices[0].message.content, "tool_result": tool_result}
    return {"response": message.content, "tool_result": None}
