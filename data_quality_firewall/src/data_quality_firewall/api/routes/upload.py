import uuid
import csv
from io import StringIO

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from data_quality_firewall.db.session import get_db
from data_quality_firewall.db.database import SessionLocal
from data_quality_firewall.models.run import FileRun


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
        run.status = "COMPLETED"

    except Exception:
        run.status = "FAILED"

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
        status="PROCESSING"
    )

    db.add(new_run)
    db.commit()
    db.refresh(new_run)

    contents = await file.read()

    # Add background task
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
