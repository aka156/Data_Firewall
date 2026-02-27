import uuid
import csv
import os
from io import StringIO

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from data_quality_firewall.db.session import get_db
from data_quality_firewall.db.database import SessionLocal
from data_quality_firewall.models.run import FileRun
from data_quality_firewall.models.run import RunStatus

router = APIRouter(prefix="/files", tags=["files"])

# -----------------------------
# Background Processing Function
# -----------------------------
def process_csv(run_id: uuid.UUID, file_content: bytes):
    db = SessionLocal()

    try:
        run = db.query(FileRun).filter(FileRun.id == run_id).first()
        if not run:
            return

        decoded = file_content.decode("utf-8")
        csv_reader = csv.reader(StringIO(decoded))

        total_rows = 0
        valid_rows = 0
        invalid_rows = 0

        # Skip header
        header = next(csv_reader, None)

        for row in csv_reader:
            total_rows += 1

            # Simple validation rule:
            # A row is valid if no empty cells
            if all(cell.strip() != "" for cell in row):
                valid_rows += 1
            else:
                invalid_rows += 1

        run.total_rows = total_rows
        run.valid_rows = valid_rows
        run.invalid_rows = invalid_rows
        run.status = RunStatus.COMPLETED

    except Exception:
        run.status = RunStatus.FAILED

    finally:
        db.commit()
        db.close()


# -----------------------------
# Upload Endpoint
# -----------------------------
@router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")

    new_run = FileRun(
        id=uuid.uuid4(),
        filename=file.filename,
        status=RunStatus.PROCESSING
    )

    db.add(new_run)
    db.commit()
    db.refresh(new_run)

    # -----------------------------
    # FILEPATH FIX STARTS HERE
    # -----------------------------
    UPLOAD_DIR = "uploads"
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    contents = await file.read()

    file_path = os.path.join(UPLOAD_DIR, f"{new_run.id}.csv")

    with open(file_path, "wb") as f:
        f.write(contents)

    new_run.file_path = file_path
    db.commit()
    # -----------------------------
    # FILEPATH FIX ENDS HERE
    # -----------------------------

    background_tasks.add_task(process_csv, new_run.id, contents)

    return {
        "run_id": str(new_run.id),
        "status": new_run.status,
        "message": "File is being processed"
    }


# -----------------------------
# Get Run Details
# -----------------------------
@router.get("/{run_id}")
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(FileRun).filter(FileRun.id == run_id).first()

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return {
        "run_id": str(run.id),
        "filename": run.filename,
        "status": run.status,
        "total_rows": run.total_rows,
        "valid_rows": run.valid_rows,
        "invalid_rows": run.invalid_rows,
        "created_at": run.created_at,
    }


@router.get("/")
def list_runs(
    status: str | None = None,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    query = db.query(FileRun)

    if status:
        query = query.filter(FileRun.status == status)

    runs = (
        query
        .order_by(FileRun.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return [
        {
            "run_id": str(run.id),
            "filename": run.filename,
            "status": run.status,
            "total_rows": run.total_rows,
            "valid_rows": run.valid_rows,
            "invalid_rows": run.invalid_rows,
            "created_at": run.created_at,
        }
        for run in runs
    ]


@router.post("/{run_id}/retry")
def retry_file(
    run_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    run = db.query(FileRun).filter(FileRun.id == run_id).first()

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.status != RunStatus.FAILED:
        raise HTTPException(
            status_code=400,
            detail="Only failed runs can be retried",
        )

    try:
        with open(run.file_path, "rb") as f:
            file_content = f.read()
    except Exception:
        raise HTTPException(status_code=500, detail="Could not read stored file")

    run.status = RunStatus.PROCESSING
    db.commit()

    background_tasks.add_task(process_csv, run.id, file_content)

    return {
        "message": "Retry started",
        "run_id": run.id,
    }
