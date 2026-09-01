"""
Intelligence Router - Advisory AI Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from pydantic import BaseModel
from app.core.security import get_current_user
from app.modules.intelligence.gateway import (
    IntelligenceGateway,
    ExtractionResult,
    SOPRecommendation,
)

router = APIRouter(prefix="/v1/ai", tags=["Advisory Intelligence"])


class TextExtractionRequest(BaseModel):
    raw_text: str
    language: str = "en"


@router.post("/extract", response_model=ExtractionResult)
async def extract_incident_entities(
    req: TextExtractionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Extract structured incident fields from raw text / voice transcript.
    """
    if not req.raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Raw text cannot be empty",
        )
    return IntelligenceGateway.extract_structured_incident(req.raw_text, req.language)


@router.get("/sop", response_model=SOPRecommendation)
async def get_incident_sop(
    category: str = "RESCUE",
    severity: str = "CRITICAL",
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieve grounded NDMA/SDMA Standard Operating Procedure recommendations.
    """
    return IntelligenceGateway.retrieve_sop(category, severity)
