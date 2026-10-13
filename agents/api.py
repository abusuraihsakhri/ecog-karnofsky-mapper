"""FastAPI entry point: clinical crosswalk plus legacy demonstration endpoints."""
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ecog_karnofsky import ECOG_TO_KPS, REFERENCE_URL, calculate_metrics
from .base import AuditLogger, PHIGuard, SecurityException
from .models import SystemTaskPayload
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")
app = FastAPI(
    title="ECOG–Karnofsky Mapper",
    description="Illustrative ECOG-ACRIN crosswalk. Legacy audit endpoints are demonstrations.",
    version="3.1.0",
)
INDEX = Path(__file__).resolve().parent.parent / "index.html"


class MappingRequest(BaseModel):
    ecog: Optional[int] = None
    kps: Optional[int] = None


class ChatRequest(BaseModel):
    query: str


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(INDEX, media_type="text/html")


@app.get("/health")
def health():
    return {"status": "ok", "service": "ecog-karnofsky-mapper", "version": "3.1.0"}


@app.get("/api/mapping")
def mapping_reference():
    return {
        "crosswalk": [{"ecog": grade, "kps_values": list(values)}
                      for grade, values in ECOG_TO_KPS.items()],
        "reference": REFERENCE_URL,
        "note": "Illustrative comparison, not an exact individual-patient conversion.",
    }


@app.post("/api/map")
def api_map(req: MappingRequest):
    try:
        return calculate_metrics(ecog=req.ecog, kps=req.kps)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/metrics")
def metrics():
    return {
        "legacy_dossiers_processed_total": len(supervisor.dossier_registry),
        "legacy_audit_blocks_total": len(AuditLogger.get_trail()),
    }


@app.post("/api/audit", deprecated=True)
def api_audit(payload: SystemTaskPayload):
    """Legacy generic audit simulator, not a clinical ECOG/KPS evaluation."""
    try:
        result = supervisor.process_task(payload).to_dict()
        result["demonstration_only"] = True
        return result
    except SecurityException as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/chat", deprecated=True)
def api_chat(req: ChatRequest):
    try:
        return {"response": supervisor.query_supervisory_chat(req.query),
                "demonstration_only": True}
    except SecurityException as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/audit/logs", deprecated=True)
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(),
            "verified": AuditLogger.verify_integrity(),
            "demonstration_only": True}
