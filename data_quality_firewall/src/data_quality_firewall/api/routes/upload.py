from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import uuid

from data_quality_firewall.db.session import get_db
from data_quality_firewall.models.run import FileRun

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")

    new_run = FileRun(
        id=uuid.uuid4(),
        filename=file.filename,
        status="RECEIVED"
    )

    db.add(new_run)
    db.commit()
    db.refresh(new_run)

    return {
        "run_id": str(new_run.id),
        "filename": new_run.filename,
        "status": new_run.status,
    }


@router.get("/{run_id}")
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(FileRun).filter(FileRun.id == run_id).first()

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return {
        "run_id": str(run.id),
        "filename": run.filename,
        "status": run.status,
        "created_at": run.created_at,
    }
