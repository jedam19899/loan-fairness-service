from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from starlette.concurrency import run_in_threadpool
import numpy as np
import json

from config import (
    FEATURE_ORDER,
    SQL_COUNT_APPLICATIONS_BY_GROUP,
    SQL_COUNT_APPROVED_BY_GROUP,
    SQL_SELECT_FEATURES_BY_ID,
    SYSTEM_PROMPT
)
from schemas import (
    IngestRequest, IngestResponse,
    DisparateImpactRequest, DisparateImpactResponse,
    ExplainRequest, ExplainResponse,
    AgentRequest, AgentResponse
)
from database import AsyncSessionLocal
from model import Application as ApplicationModel
from tools import call_tool

router = APIRouter()

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

@router.post("/ingest", response_model=IngestResponse)
async def ingest_endpoint(
    req: IngestRequest,
    session: AsyncSession = Depends(get_session)
):
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
    return IngestResponse(status="success")

@router.get("/bias/disparate-impact", response_model=DisparateImpactResponse)
async def disparate_impact_endpoint(
    privileged: str,
    unprivileged: str,
    session: AsyncSession = Depends(get_session)
):
    total_priv = (await session.execute(
        text(SQL_COUNT_APPLICATIONS_BY_GROUP), {"grp": privileged}
    )).scalar() or 0
    total_unpriv = (await session.execute(
        text(SQL_COUNT_APPLICATIONS_BY_GROUP), {"grp": unprivileged}
    )).scalar() or 0
    hired_priv = (await session.execute(
        text(SQL_COUNT_APPROVED_BY_GROUP), {"grp": privileged}
    )).scalar() or 0
    hired_unpriv = (await session.execute(
        text(SQL_COUNT_APPROVED_BY_GROUP), {"grp": unprivileged}
    )).scalar() or 0
    rate_priv = hired_priv / total_priv if total_priv else 0
    rate_unpriv = hired_unpriv / total_unpriv if total_unpriv else 0
    ratio = rate_unpriv / rate_priv if rate_priv else 0
    return DisparateImpactResponse(ratio=ratio)

@router.post("/explain", response_model=ExplainResponse)
async def explain_endpoint(
    req: ExplainRequest,
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    explainer = request.app.state.explainer
    if explainer is None:
        raise HTTPException(status_code=503, detail="Explanation service unavailable")

    result = await session.execute(
        text(SQL_SELECT_FEATURES_BY_ID), {"id": req.application_id}
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")

    raw = row[0]
    try:
        features = json.loads(raw) if isinstance(raw, str) else raw
    except ValueError:
        raise HTTPException(status_code=500, detail="Invalid features JSON")

    x = [features.get(key, 0) for key in FEATURE_ORDER]
    X = np.array([x])
    shap_values = await run_in_threadpool(explainer.shap_values, X)
    contributions = {key: float(val) for key, val in zip(FEATURE_ORDER, shap_values[0])}
    return ExplainResponse(contributions=contributions)

@router.post("/agent", response_model=AgentResponse)
async def agent_endpoint(
    req: AgentRequest
):
    response = await call_tool("agent_dispatch", {"messages": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": req.prompt}
    ]})
    return AgentResponse(**response)
