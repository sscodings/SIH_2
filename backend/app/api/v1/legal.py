from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException
from app.legal.provisions import get_citation, get_legal_provisions_registry

router = APIRouter(prefix="/legal", tags=["Legal Provisions"])

@router.get("/provisions")
def list_provisions():
    """List all configured legal provisions and commencement information."""
    registry = get_legal_provisions_registry()
    return {
        "commencement": registry.commencement,
        "provisions": registry.provisions
    }

@router.get("/citation")
def get_provision_citation(
    key: str = Query(..., description="Provision key from provisions.yaml"),
    offence_date: Optional[str] = Query(None, description="Date of alleged offence (YYYY-MM-DD)"),
    proceeding_pending_at_commencement: Optional[bool] = Query(None, description="Whether investigation/proceeding was pending before 2024-07-01")
):
    """
    Fetch exact citation details for a statutory provision based on case timeline.
    Returns current/legacy code or ambiguous flag with required warnings.
    """
    try:
        context = {
            "offence_date": offence_date,
            "proceeding_pending_at_commencement": proceeding_pending_at_commencement
        }
        return get_citation(key, context)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
