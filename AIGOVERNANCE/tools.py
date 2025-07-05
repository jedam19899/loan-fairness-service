import os
import json
import asyncio
from starlette.concurrency import run_in_threadpool
from openai import OpenAI
from fastapi import HTTPException
from sqlalchemy import text
import numpy as np

from config import (
    SQL_COUNT_APPLICATIONS_BY_GROUP,
    SQL_COUNT_APPROVED_BY_GROUP,
    SQL_SELECT_FEATURES_BY_ID,
    SYSTEM_PROMPT,
    FEATURE_ORDER
)
from schemas import IngestRequest, DisparateImpactRequest, ExplainRequest
from database import AsyncSessionLocal
from model import Application as ApplicationModel

# ─── LLM Configuration ───
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "30.0"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

FUNCTIONS = [
    {
        "name": "ingest_application",
        "description": "Ingest a new loan application",
        "parameters": IngestRequest.schema()
    },
    {
        "name": "disparate_impact",
        "description": "Compute disparate impact ratio",
        "parameters": DisparateImpactRequest.schema()
    },
    {
        "name": "explain_application",
        "description": "Return SHAP-based contributions for each feature",
        "parameters": ExplainRequest.schema()
    }
]

# Module‐level explainer, set in main.py startup
explainer = None

async def call_tool(name: str, args: dict):
    """
    Dispatch tools: database operations and LLM orchestration.
    """
    # ----- Ingest application -----
    if name == "ingest_application":
        async with AsyncSessionLocal() as session:
            app_model = ApplicationModel(
                application_id=args.get("application_id"),
                features=args.get("features"),
                decision=None
            )
            session.add(app_model)
            try:
                await session.commit()
            except Exception:
                await session.rollback()
        return {"status": "success"}

    # ----- Disparate impact calculation -----
    if name == "disparate_impact":
        priv = args.get("privileged")
        unpriv = args.get("unprivileged")
        async with AsyncSessionLocal() as session:
            total_priv = (await session.execute(
                text(SQL_COUNT_APPLICATIONS_BY_GROUP), {"grp": priv}
            )).scalar() or 0
            total_unpriv = (await session.execute(
                text(SQL_COUNT_APPLICATIONS_BY_GROUP), {"grp": unpriv}
            )).scalar() or 0
            hired_priv = (await session.execute(
                text(SQL_COUNT_APPROVED_BY_GROUP), {"grp": priv}
            )).scalar() or 0
            hired_unpriv = (await session.execute(
                text(SQL_COUNT_APPROVED_BY_GROUP), {"grp": unpriv}
            )).scalar() or 0
        rate_priv = hired_priv / total_priv if total_priv else 0
        rate_unpriv = hired_unpriv / total_unpriv if total_unpriv else 0
        ratio = rate_unpriv / rate_priv if rate_priv else 0
        return {"ratio": ratio}

    # ----- SHAP explanation -----
    if name == "explain_application":
        if explainer is None:
            raise HTTPException(status_code=503, detail="Explanation service unavailable")
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(SQL_SELECT_FEATURES_BY_ID),
                {"id": args.get("application_id")}
            )
            row = result.first()
            if not row:
                raise HTTPException(status_code=404, detail="Application not found")
            raw = row[0]

        try:
            features = json.loads(raw) if isinstance(raw, str) else raw
        except ValueError:
            raise HTTPException(status_code=500, detail="Invalid features JSON")

        x = [features.get(k, 0) for k in FEATURE_ORDER]
        X = np.array([x])
        shap_values = await run_in_threadpool(explainer.shap_values, X)
        contributions = {k: float(v) for k, v in zip(FEATURE_ORDER, shap_values[0])}
        return {"contributions": contributions}

    # ----- LLM agent dispatch -----
    if name == "agent_dispatch":
        messages = args.get("messages", [])
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
            raise HTTPException(
                status_code=504,
                detail=f"LLM request timed out after {LLM_TIMEOUT} seconds"
            )

        message = first_resp.choices[0].message
        if message.function_call:
            fn_name = message.function_call.name
            fn_args = json.loads(message.function_call.arguments or "{}")
            tool_result = await call_tool(fn_name, fn_args)

            followup = [
                {"role": "system",   "content": SYSTEM_PROMPT},
                {"role": "function", "name": fn_name, "content": json.dumps(tool_result)}
            ]
            second_resp = await asyncio.wait_for(
                run_in_threadpool(lambda: client.chat.completions.create(
                    model="gpt-4",
                    messages=followup
                )),
                timeout=LLM_TIMEOUT
            )
            return {
                "response": second_resp.choices[0].message.content,
                "tool_result": tool_result
            }

        return {"response": message.content, "tool_result": None}

    raise ValueError(f"Unknown tool: {name}")
