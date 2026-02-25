from fastapi import APIRouter, UploadFile, File, HTTPException
from uuid import UUID

from data_quality_firewall.core.run_service import RunService

router = APIRouter(tags=["files"])  # ← REMOVE prefix here

run_service = RunService()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")

    run = run_service.create_run(file.filename)

    return {
        "run_id": str(run.id),
        "filename": run.filename,
        "status": run.status
    }


@router.get("/{run_id}")
def get_run(run_id: str):
    run = run_service.get_run(UUID(run_id))
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return run.model_dump()
