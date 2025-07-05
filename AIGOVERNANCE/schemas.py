from pydantic import BaseModel
from typing import Optional, Dict

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

class AgentResponse(BaseModel):
    response: str
    tool_result: Optional[Dict] = None
